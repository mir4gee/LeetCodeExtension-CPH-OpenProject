import * as vscode from 'vscode';
import { exec } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as Diff from 'diff';

interface WebviewMessage {
    command: string;
    text?: string;
}

interface CodeSnippet {
    lang: string;
    langSlug: string;
    code: string;
}

interface Example {
    input: string;
    output: string;
}

interface LeetCodeData {
    id: string;
    title: string;
    description: string;
    difficulty: string;
    examples: Record<string, string>;
    codeSnippets: Record<string, string>;
    dataStructures: {
        'C++': Record<string, string>;
        'Python3': Record<string, string>;
    };
}

const EXTENSION_COMMANDS = {
    SHOW_WEBVIEW: 'extension.showWebview',
};

class FileManager {
    static async createTestCaseDirectory(): Promise<string> {
        const testcaseDir = path.join(__dirname, 'testcases');
        if (fs.existsSync(testcaseDir)) {
            fs.rmSync(testcaseDir, { recursive: true });
        }
        fs.mkdirSync(testcaseDir, { recursive: true });
        return testcaseDir;
    }

    static async createFile(
        workspaceFolders: readonly vscode.WorkspaceFolder[] | undefined,
        fileName: string,
        fileContent: string
    ): Promise<void> {
        const folder = workspaceFolders?.[0];
        const filePath = folder
            ? path.join(folder.uri.fsPath, fileName)
            : path.join(await this.getFolderFromDialog(), fileName);

        fs.writeFileSync(filePath, fileContent);
        const document = await vscode.workspace.openTextDocument(filePath);
        await vscode.window.showTextDocument(document, vscode.ViewColumn.Two);
    }

    static async saveTestCase(dir: string, inputCounter: number, input: string, output: string): Promise<void> {
        fs.writeFileSync(path.join(dir, `input_${inputCounter}.txt`), input);
        fs.writeFileSync(path.join(dir, `output_${inputCounter}.txt`), output);
    }

    private static async getFolderFromDialog(): Promise<string> {
        const folders = await vscode.window.showOpenDialog({ canSelectFolders: true });
        if (!folders || folders.length === 0) {
            throw new Error('No folder selected');
        }
        return folders[0].fsPath;
    }
}

class WebviewContentProvider {
    static getInitialContent(): string {
        return `
            <!DOCTYPE html>
            <html>
            <body>
                <h1>LeetCode Problem Helper</h1>
                <form onsubmit="submitSlug(event)">
                    <input type="text" id="slugInput" placeholder="Enter problem slug (e.g., two-sum)" required />
                    <button type="submit">Load Problem</button>
                </form>
                <script>
                    const vscode = acquireVsCodeApi();
                    function submitSlug(event) {
                        event.preventDefault();
                        const slug = document.getElementById('slugInput').value;
                        vscode.postMessage({ command: 'submitString', text: slug });
                    }
                </script>
            </body>
            </html>
        `;
    }

    static formatProblemData(data: LeetCodeData): string {
        const examples = Object.entries(data.examples)
            .map(([key, example]) => `
                <h3>${key}</h3>
                <pre>${example}</pre>
            `)
            .join('');
    
        return `
            <!DOCTYPE html>
            <html>
            <body>
                <h1>${data.title}</h1>
                <div class="difficulty ${data.difficulty.toLowerCase()}">${data.difficulty}</div>
                <div class="examples">
                    ${examples}
                </div>
                <div class="actions">
                    <button onclick="openFile('cpp')">Open in C++</button>
                    <button onclick="openFile('python')">Open in Python</button>
                    <button onclick="runCppTests()">Run C++ Tests</button>
                    <button onclick="runPyTests()">Run Python Tests</button>
                </div>
                <script>
                    const vscode = acquireVsCodeApi();
                    function openFile(language) {
                        vscode.postMessage({ command: 'openFile', text: language });
                    }
                    function runCppTests() {
                        vscode.postMessage({ command: 'runTests' });
                    }
                    function runPyTests() {
                        vscode.postMessage({ command: 'runPythonTests' });
                    }
                </script>
                <style>
                    .difficulty {
                        padding: 4px 8px;
                        border-radius: 4px;
                        display: inline-block;
                        margin: 8px 0;
                    }
                    .difficulty.easy { background: #44b444; }
                    .difficulty.medium { background: #f0ad4e; }
                    .difficulty.hard { background: #d9534f; }
                    .examples { margin: 16px 0; }
                    .actions { margin-top: 16px; }
                    button { margin-right: 8px; }
                </style>
            </body>
            </html>
        `;
    }
    
}

class ExtensionManager {
    private context: vscode.ExtensionContext;
    private testcaseDir: string | null = null;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    async handleMessage(message: WebviewMessage, panel: vscode.WebviewPanel): Promise<void> {
    switch (message.command) {
        case 'submitString':
            await this.handleProblemSubmission(message.text || '', panel);
            break;
        case 'openFile':
            await this.openFile(message.text as 'cpp' | 'python');
            break;
        case 'runTests':
            await this.runTests();
            break;
        case 'runPythonTests':
            await this.runPythonTests();
            break;
        default:
            vscode.window.showErrorMessage(`Unknown command: ${message.command}`);
    }
}

private async runPythonTests(): Promise<void> {
    if (!this.testcaseDir) {
        vscode.window.showErrorMessage('No test cases available. Please load a problem first.');
        return;
    }

    const pythonPath = '/home/mir4ge/testcases/python3.py';
    if (!fs.existsSync(pythonPath)) {
        vscode.window.showErrorMessage('Python solution file not found.');
        return;
    }

    try {
        const pythonScriptPath = '/home/mir4ge/Desktop/extension/src/run_testcases_py.py';
        const testcasedirect = '/home/mir4ge/testcases';

        const results = await this.runPythonTestRunner(pythonScriptPath, testcasedirect, pythonPath);
        console.log(results);
        await this.displayTestResults(results);
    } catch (error) {
        vscode.window.showErrorMessage(`Error running Python tests: ${error instanceof Error ? error.message : String(error)}`);
    }
}

    private async openFile(language: 'cpp' | 'python'): Promise<void> {
        if (!this.testcaseDir) {
            vscode.window.showErrorMessage('Please load a problem first.');
            return;
        }
    
        try {
            const filePath = path.join('/home/mir4ge/testcases', language === 'cpp' ? 'c++.cpp' : 'python3.py');

            if (!fs.existsSync(filePath)) {
                vscode.window.showErrorMessage(`No ${language.toUpperCase()} solution file found.`);
                return;
            }
    
            const document = await vscode.workspace.openTextDocument(filePath);
            await vscode.window.showTextDocument(document, {
                viewColumn: vscode.ViewColumn.Two,
                preview: false
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Error opening ${language.toUpperCase()} file: ${error}`);
        }
    }

    private async runTests(): Promise<void> {
        if (!this.testcaseDir) {
            vscode.window.showErrorMessage('No test cases available. Please load a problem first.');
            return;
        }

        const cppPath = '/home/mir4ge/testcases/c++.cpp';
        console.log(cppPath);
        if (!fs.existsSync(cppPath)) {
            vscode.window.showErrorMessage('C++ solution file not found.');
            return;
        }

        try {
            const pythonScriptPath = '/home/mir4ge/Desktop/extension/src/run_testcases.py';
            console.log(pythonScriptPath);
            const testcasedirect = '/home/mir4ge/testcases';
            const results = await this.runPythonTestRunner(pythonScriptPath, testcasedirect, cppPath);
            console.log(results);
            await this.displayTestResults(results);
        } catch (error) {
            vscode.window.showErrorMessage(`Error running tests: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    private async runPythonTestRunner(scriptPath: string, testcaseDir: string, filePath: string): Promise<Record<string, string>> {
        return new Promise((resolve, reject) => {
            exec(
                `python "${scriptPath}" "${testcaseDir}" "${filePath}"`,
                (err, stdout, stderr) => {
                    if (err || stderr) {
                        reject(new Error(err?.message || stderr));
                        return;
                    }
    
                    try {
                        const resultsPath = path.join(testcaseDir, 'results.json');
                        const results = JSON.parse(fs.readFileSync(resultsPath, 'utf-8'));
                        resolve(results);
                    } catch (error) {
                        reject(new Error(`Failed to parse test results: ${error}`));
                    }
                }
            );
        });
    }
    

    private async displayTestResults(results: Record<string, any>): Promise<void> {
        const resultsPanel = vscode.window.createWebviewPanel(
            'testResults',
            'Test Results',
            vscode.ViewColumn.Three,
            { enableScripts: true }
        );
    
        const formatResult = (testCase: string, status: string, details?: { Expected: string, Got: string }) => {
            const getColor = (status: string) => {
                switch (status.toLowerCase()) {
                    case 'failed': return 'red';
                    case 'passed': return 'green';
                    case 'error': return 'yellow';
                    default: return 'gray';
                }
            };
    
            const statusColor = getColor(status);
    
            if (details) {
                return `
                    <div style="border: 1px solid ${statusColor}; padding: 8px; border-radius: 4px; margin: 8px 0;">
                        <strong style="color: ${statusColor};">${testCase}:</strong> ${status}
                        <div style="margin-left: 16px;">
                            <strong>Expected:</strong>
                            <pre>${details.Expected}</pre>
                            <strong>Got:</strong>
                            <pre>${details.Got}</pre>
                        </div>
                    </div>
                `;
            }
    
            return `
                <div style="border: 1px solid ${statusColor}; padding: 8px; border-radius: 4px; margin: 8px 0;">
                    <strong style="color: ${statusColor};">${testCase}:</strong> ${status}
                </div>
            `;
        };
    
        const resultsHtml = `
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    pre {
                        background-color: rgb(87, 58, 58);
                        padding: 8px;
                        border-radius: 4px;
                        margin: 4px 0;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }
                    div {
                        font-family: Arial, sans-serif;
                    }
                    h2 {
                        color: #333;
                    }
                </style>
            </head>
            <body>
                <h2>Test Results</h2>
                ${Object.entries(results)
                    .filter(([key]) => !key.endsWith('Details'))
                    .map(([testCase, status]) => {
                        const detailsKey = `${testCase} Details`;
                        const details = results[detailsKey] as { Expected: string, Got: string } | undefined;
                        return formatResult(testCase, status as string, details);
                    })
                    .join('')}
            </body>
            </html>
        `;
    
        resultsPanel.webview.html = resultsHtml;
    }
    


    private async handleProblemSubmission(slug: string, panel: vscode.WebviewPanel): Promise<void> {
        try {
            const pythonOutput = await this.runPythonScript(slug);
            
            const jsonMatch = pythonOutput.match(/(\{[\s\S]*\})/);
            if (!jsonMatch) {
                throw new Error('No valid JSON found in Python script output');
            }
            
            const problemData: LeetCodeData = JSON.parse(jsonMatch[0]);
    
            this.testcaseDir = await FileManager.createTestCaseDirectory();
    
            panel.webview.html = WebviewContentProvider.formatProblemData(problemData);
        } catch (error) {
            vscode.window.showErrorMessage(`Error: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    private async runPythonScript(slug: string): Promise<string> {
        const scriptPath = '/home/mir4ge/Desktop/extension/src/script.py';
        return new Promise((resolve, reject) => {
            exec(`python "${scriptPath}" --titleSlug "${slug}"`, (err, stdout, stderr) => {
                if (err) {
                    reject(new Error(err.message));
                    return;
                }
                
                if (stderr) {
                    console.warn('Python script stderr:', stderr);
                }
                
                resolve(stdout);
            });
        });
    }
}

export function activate(context: vscode.ExtensionContext): void {
    const manager = new ExtensionManager(context);

    context.subscriptions.push(
        vscode.commands.registerCommand(EXTENSION_COMMANDS.SHOW_WEBVIEW, () => {
            const panel = vscode.window.createWebviewPanel(
                'leetcodeHelper',
                'LeetCode Helper',
                vscode.ViewColumn.One,
                {
                    enableScripts: true
                }
            );

            panel.webview.html = WebviewContentProvider.getInitialContent();
            panel.webview.onDidReceiveMessage(
                (message) => manager.handleMessage(message, panel),
                undefined,
                context.subscriptions
            );
        })
    );
}

export function deactivate(): void {}