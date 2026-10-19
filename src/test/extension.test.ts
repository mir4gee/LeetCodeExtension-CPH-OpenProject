import * as assert from 'assert';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

type Result = Record<string, unknown> & { error?: string | null };
type TestResult = { status: string };

const workspace = () => vscode.workspace.workspaceFolders![0].uri.fsPath;

async function openAndEdit(file: string, find: string, replace: string): Promise<void> {
    const doc = await vscode.workspace.openTextDocument(file);
    const editor = await vscode.window.showTextDocument(doc);
    const text = doc.getText();
    const at = text.indexOf(find);
    assert.ok(at >= 0, `'${find.trim()}' not found in ${path.basename(file)}`);
    await editor.edit((e) => e.replace(new vscode.Range(doc.positionAt(at), doc.positionAt(at + find.length)), replace));
    // Left unsaved on purpose: running tests must save open files first.
}

suite('CPH for LeetCode', function () {
    this.timeout(180_000);

    test('fetches a problem, judges a C++ solution, and finds a bug by stress testing', async () => {
        fs.rmSync(path.join(workspace(), 'leetcode'), { recursive: true, force: true });
        const fetched = await vscode.commands.executeCommand<Result>('cphLeetcode.openProblem', 'two-sum');
        assert.ok(!fetched.error, String(fetched.error));
        const dir = path.join(workspace(), 'leetcode', 'two-sum');
        for (const f of ['problem.json', 'tests.json', 'solution.cpp', 'solution.py', 'brute.cpp', 'gen.py']) {
            assert.ok(fs.existsSync(path.join(dir, f)), `${f} missing`);
        }

        const empty = '{\n        \n    }';
        const brute = `{
        for (int i = 0; i < (int)nums.size(); ++i)
            for (int j = i + 1; j < (int)nums.size(); ++j)
                if (nums[i] + nums[j] == target) return {i, j};
        return {};
    }`;
        await openAndEdit(path.join(dir, 'brute.cpp'), empty, brute);
        await openAndEdit(path.join(dir, 'solution.cpp'), empty,
            brute.replace('== target)', '== target && nums[i] >= 0)'));   // bug: skips negatives

        const run = await vscode.commands.executeCommand<Result>('cphLeetcode.runTests');
        assert.ok(!run.error && !run.compile_error, JSON.stringify(run).slice(0, 2000));
        assert.deepStrictEqual((run.results as TestResult[]).map((r) => r.status), ['AC', 'AC', 'AC']);

        const stress = await vscode.commands.executeCommand<Result>('cphLeetcode.stressTest');
        assert.ok(!stress.error, String(stress.error));
        const mismatch = stress.mismatch as { input: string[]; status: string } | null;
        assert.ok(mismatch, 'stress test should find the planted bug');
        assert.strictEqual(mismatch.status, 'WA');
    });

    test('reports an unknown problem without crashing', async () => {
        const result = await vscode.commands.executeCommand<Result>('cphLeetcode.openProblem', 'no-such-problem-xyz');
        assert.match(String(result.error), /No LeetCode problem/);
    });
});
