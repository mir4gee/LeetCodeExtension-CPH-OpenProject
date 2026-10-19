import * as vscode from 'vscode';
import { execFile } from 'child_process';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';

type Lang = 'cpp' | 'python';
type CliResult = { error?: string | null } & Record<string, unknown>;

const LANGS: readonly Lang[] = ['cpp', 'python'];
const EDITABLE = ['solution.cpp', 'solution.py', 'brute.cpp', 'brute.py', 'gen.py', 'tests.json'];
const PROBLEM_URL = /^https:\/\/leetcode\.com\/problems\/[a-z0-9-]+\/$/;

function settings() {
    const c = vscode.workspace.getConfiguration('cphLeetcode');
    return {
        python: c.get<string>('pythonPath', 'python3'),
        compiler: c.get<string>('cppCompiler', 'g++'),
        timeLimitMs: c.get<number>('timeLimitMs', 2000),
        memoryLimitMb: c.get<number>('memoryLimitMb', 256),
        stressRounds: c.get<number>('stressRounds', 200),
    };
}

/** Runs `python -m cph ...` with an argument array (no shell) and parses its one JSON line. */
function runCli(extensionPath: string, args: string[], timeoutMs: number): Promise<CliResult> {
    const { python } = settings();
    return new Promise((resolve, reject) => {
        execFile(
            python,
            ['-m', 'cph', ...args],
            {
                env: { ...process.env, PYTHONPATH: path.join(extensionPath, 'python') },
                maxBuffer: 64 * 1024 * 1024,
                timeout: timeoutMs,
            },
            (err, stdout, stderr) => {
                try {
                    resolve(JSON.parse(stdout));
                } catch {
                    const reason = err && (err as NodeJS.ErrnoException).code === 'ENOENT'
                        ? `Python not found at '${python}'. Set cphLeetcode.pythonPath.`
                        : (stderr || err?.message || 'no output').trim().slice(-2000);
                    reject(new Error(reason));
                }
            },
        );
    });
}

function problemDirOf(file: string): string | undefined {
    const dir = path.dirname(file);
    return fs.existsSync(path.join(dir, 'problem.json')) ? dir : undefined;
}

class ProblemPanel {
    private static panels = new Map<string, ProblemPanel>();
    private busy = false;
    private readonly panel: vscode.WebviewPanel;

    static show(context: vscode.ExtensionContext, dir: string): ProblemPanel {
        const existing = ProblemPanel.panels.get(dir);
        if (existing) {
            existing.panel.reveal(vscode.ViewColumn.Beside, true);
            existing.sendProblem();
            return existing;
        }
        const created = new ProblemPanel(context, dir);
        ProblemPanel.panels.set(dir, created);
        return created;
    }

    private constructor(private readonly context: vscode.ExtensionContext, private readonly dir: string) {
        const media = vscode.Uri.joinPath(context.extensionUri, 'media');
        this.panel = vscode.window.createWebviewPanel('cphLeetcode', path.basename(dir), {
            viewColumn: vscode.ViewColumn.Beside, preserveFocus: true,
        }, { enableScripts: true, localResourceRoots: [media], retainContextWhenHidden: true });
        this.panel.webview.html = this.html(media);
        this.panel.onDidDispose(() => ProblemPanel.panels.delete(this.dir));
        this.panel.webview.onDidReceiveMessage((msg) => this.onMessage(msg));
    }

    private html(media: vscode.Uri): string {
        const nonce = crypto.randomBytes(16).toString('base64');
        const webview = this.panel.webview;
        const script = webview.asWebviewUri(vscode.Uri.joinPath(media, 'panel.js'));
        const style = webview.asWebviewUri(vscode.Uri.joinPath(media, 'panel.css'));
        return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="${style}">
<title>LeetCode problem</title>
</head>
<body>
<main id="app" aria-live="polite"></main>
<script nonce="${nonce}" src="${script}"></script>
</body>
</html>`;
    }

    sendProblem(): void {
        const read = (name: string) => JSON.parse(fs.readFileSync(path.join(this.dir, name), 'utf-8'));
        try {
            this.post({ type: 'problem', problem: read('problem.json'), tests: read('tests.json') });
        } catch (e) {
            this.post({ type: 'error', message: `Couldn't read this problem's files: ${e instanceof Error ? e.message : e}` });
        }
    }

    private post(message: unknown): void {
        void this.panel.webview.postMessage(message);
    }

    /** Messages come from the webview: validate every field before acting on it. */
    private async onMessage(msg: unknown): Promise<void> {
        if (!msg || typeof msg !== 'object') { return; }
        const m = msg as Record<string, unknown>;
        if (m.type === 'ready') { this.sendProblem(); return; }
        if (m.type === 'open' && typeof m.file === 'string' && EDITABLE.includes(m.file)) {
            const doc = await vscode.workspace.openTextDocument(path.join(this.dir, m.file));
            await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
            return;
        }
        if (m.type === 'openUrl' && typeof m.url === 'string' && PROBLEM_URL.test(m.url)) {
            await vscode.env.openExternal(vscode.Uri.parse(m.url));
            return;
        }
        if (m.type === 'anyOrder' && typeof m.value === 'boolean') {
            const file = path.join(this.dir, 'problem.json');
            const problem = JSON.parse(fs.readFileSync(file, 'utf-8'));
            problem.anyOrder = m.value;
            fs.writeFileSync(file, JSON.stringify(problem, null, 2));
            return;
        }
        if (m.type === 'addTest' && Array.isArray(m.input) && m.input.every((x) => typeof x === 'string')
            && typeof m.output === 'string') {
            const file = path.join(this.dir, 'tests.json');
            const tests = JSON.parse(fs.readFileSync(file, 'utf-8')) as unknown[];
            tests.push({ input: m.input, output: m.output });
            fs.writeFileSync(file, JSON.stringify(tests, null, 2));
            this.sendProblem();
            vscode.window.showInformationMessage(`Added test ${tests.length} to tests.json.`);
            return;
        }
        const lang = LANGS.find((l) => l === m.lang);
        if (m.type === 'run' && lang) { await this.run(lang, m.file === 'brute' ? 'brute' : 'solution'); }
        if (m.type === 'stress' && lang) { await this.stress(lang); }
    }

    private async saveOpenFiles(): Promise<void> {
        await Promise.all(vscode.workspace.textDocuments
            .filter((d) => d.isDirty && path.dirname(d.uri.fsPath) === this.dir)
            .map((d) => d.save()));
    }

    run(lang: Lang, file: 'solution' | 'brute' = 'solution'): Promise<CliResult | undefined> {
        return this.exclusive('run', lang, () => {
            const s = settings();
            const tests = JSON.parse(fs.readFileSync(path.join(this.dir, 'tests.json'), 'utf-8')) as unknown[];
            return runCli(this.context.extensionPath, ['run', this.dir, lang, '--file', file,
                '--time-limit', String(s.timeLimitMs), '--memory-limit', String(s.memoryLimitMb),
                '--compiler', s.compiler, '--python', s.python],
                120_000 + tests.length * (s.timeLimitMs + 1000));
        });
    }

    stress(lang: Lang): Promise<CliResult | undefined> {
        return this.exclusive('stress', lang, () => {
            const s = settings();
            return runCli(this.context.extensionPath, ['stress', this.dir, lang,
                '--rounds', String(s.stressRounds), '--time-limit', String(s.timeLimitMs),
                '--memory-limit', String(s.memoryLimitMb), '--compiler', s.compiler, '--python', s.python],
                180_000 + s.stressRounds * (6 * s.timeLimitMs + 1000));
        });
    }

    /** One job at a time per problem; the panel shows progress and the outcome. */
    private async exclusive(kind: 'run' | 'stress', lang: Lang, job: () => Promise<CliResult>): Promise<CliResult | undefined> {
        if (this.busy) {
            vscode.window.showInformationMessage('Still running the previous job for this problem.');
            return undefined;
        }
        this.busy = true;
        this.post({ type: 'busy', kind, lang });
        try {
            await this.saveOpenFiles();
            const result = await job();
            this.post({ type: kind === 'run' ? 'results' : 'stressResult', lang, result });
            return result;
        } catch (e) {
            const message = e instanceof Error ? e.message : String(e);
            this.post({ type: 'error', message });
            vscode.window.showErrorMessage(`LeetCode ${kind} failed: ${message}`);
            return { error: message };
        } finally {
            this.busy = false;
            this.post({ type: 'idle' });
        }
    }
}

function activeProblem(): { dir: string; lang: Lang; file: 'solution' | 'brute' } | undefined {
    const doc = vscode.window.activeTextEditor?.document;
    const dir = doc && problemDirOf(doc.uri.fsPath);
    const m = doc && /^(solution|brute)\.(cpp|py)$/.exec(path.basename(doc.uri.fsPath));
    if (!dir || !m) {
        vscode.window.showWarningMessage('Open a solution.cpp or solution.py from a leetcode/<problem> folder first.');
        return undefined;
    }
    return { dir, lang: m[2] === 'cpp' ? 'cpp' : 'python', file: m[1] as 'solution' | 'brute' };
}

export function activate(context: vscode.ExtensionContext): void {
    context.subscriptions.push(
        vscode.commands.registerCommand('cphLeetcode.openProblem', async (slugArg?: string) => {
            const folder = vscode.workspace.workspaceFolders?.[0];
            if (!folder) {
                vscode.window.showErrorMessage('Open a folder first: problems are saved under leetcode/<problem> in it.');
                return undefined;
            }
            const slug = slugArg ?? await vscode.window.showInputBox({
                prompt: 'LeetCode problem slug or URL',
                placeHolder: 'two-sum or https://leetcode.com/problems/two-sum/',
                ignoreFocusOut: true,
            });
            if (!slug) { return undefined; }
            const result = await vscode.window.withProgress(
                { location: vscode.ProgressLocation.Notification, title: `Fetching ${slug}…` },
                () => runCli(context.extensionPath, ['fetch', slug, folder.uri.fsPath], 60_000)
                    .catch((e: Error): CliResult => ({ error: e.message })),
            );
            if (result.error) {
                vscode.window.showErrorMessage(String(result.error));
                return result;
            }
            const dir = String(result.folder);
            const doc = await vscode.workspace.openTextDocument(path.join(dir, 'solution.cpp'));
            await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
            ProblemPanel.show(context, dir);
            return result;
        }),
        vscode.commands.registerCommand('cphLeetcode.runTests', () => {
            const active = activeProblem();
            return active && ProblemPanel.show(context, active.dir).run(active.lang, active.file);
        }),
        vscode.commands.registerCommand('cphLeetcode.stressTest', () => {
            const active = activeProblem();
            return active && ProblemPanel.show(context, active.dir).stress(active.lang);
        }),
    );
}

export function deactivate(): void {}
