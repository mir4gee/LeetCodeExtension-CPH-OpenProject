// Problem panel. Everything shown comes from LeetCode or the user's program, so it is
// inserted with textContent only, never innerHTML.
(function () {
    const vscode = acquireVsCodeApi();
    const app = document.getElementById('app');
    let state = { problem: null, tests: [], lang: 'cpp', busy: null, results: null, stress: null, error: null };

    function el(tag, attrs, ...children) {
        const node = document.createElement(tag);
        for (const [k, v] of Object.entries(attrs || {})) {
            if (k === 'onclick') { node.addEventListener('click', v); }
            else if (k === 'onchange') { node.addEventListener('change', v); }
            else if (v === true) { node.setAttribute(k, ''); }
            else if (v !== false && v != null) { node.setAttribute(k, v); }
        }
        for (const c of children.flat()) {
            if (c == null || c === false) { continue; }
            node.append(typeof c === 'string' || typeof c === 'number' ? document.createTextNode(String(c)) : c);
        }
        return node;
    }

    const VERDICT = {
        AC: 'Accepted', WA: 'Wrong answer', TLE: 'Time limit exceeded', MLE: 'Memory limit exceeded',
        RE: 'Runtime error', OLE: 'Output limit exceeded', CE: 'Compile error',
    };

    function button(label, onclick, opts = {}) {
        return el('button', { type: 'button', class: opts.secondary ? 'secondary' : '', onclick, disabled: !!state.busy }, label);
    }

    function header(p) {
        return el('header', {},
            el('h1', {}, `${p.id}. ${p.title}`),
            el('div', { class: 'meta' },
                el('span', { class: `difficulty ${p.difficulty.toLowerCase()}` }, p.difficulty),
                el('a', { href: '#', onclick: (e) => { e.preventDefault(); vscode.postMessage({ type: 'openUrl', url: p.url }); } },
                    'Open on LeetCode')));
    }

    function toolbar() {
        const langs = el('div', { class: 'segmented', role: 'group', 'aria-label': 'Language' },
            ...[['cpp', 'C++'], ['python', 'Python']].map(([id, label]) =>
                el('button', {
                    type: 'button', 'aria-pressed': String(state.lang === id),
                    onclick: () => { state.lang = id; render(); },
                }, label)));
        const ext = state.lang === 'cpp' ? 'cpp' : 'py';
        return el('div', { class: 'toolbar' }, langs,
            button('Run tests', () => vscode.postMessage({ type: 'run', lang: state.lang })),
            state.problem.supported && button('Stress test', () => vscode.postMessage({ type: 'stress', lang: state.lang }), { secondary: true }),
            button(`Edit solution.${ext}`, () => vscode.postMessage({ type: 'open', file: `solution.${ext}` }), { secondary: true }));
    }

    function status() {
        if (state.busy) {
            const what = state.busy.kind === 'stress' ? 'Stress testing' : 'Running tests';
            return el('p', { class: 'status', role: 'status' }, `${what}…`);
        }
        if (state.error) { return el('p', { class: 'error', role: 'alert' }, state.error); }
        return null;
    }

    function block(label, text) {
        return el('div', { class: 'io' }, el('div', { class: 'label' }, label), el('pre', {}, text));
    }

    function results() {
        const r = state.results;
        if (!r) { return null; }
        if (r.error) { return el('p', { class: 'error', role: 'alert' }, r.error); }
        if (r.compile_error) {
            return el('section', { class: 'card bad' }, el('h2', {}, VERDICT.CE), el('pre', { class: 'scroll' }, r.compile_error));
        }
        const list = r.results || [];
        const passed = list.filter((t) => t.status === 'AC').length;
        return el('section', {},
            el('h2', {}, `${passed} / ${list.length} passed`),
            ...list.map((t) => el('details', { class: `card ${t.status === 'AC' ? 'ok' : 'bad'}`, open: t.status !== 'AC' },
                el('summary', {},
                    el('span', { class: 'verdict' }, `Test ${t.test}: ${VERDICT[t.status] || t.status}`),
                    el('span', { class: 'usage' }, `${t.time_ms} ms`, t.memory_kb ? ` · ${(t.memory_kb / 1024).toFixed(1)} MB` : '')),
                block('Input', t.input.join('\n')),
                t.expected != null && block('Expected', t.expected),
                block('Output', t.got || '(empty)'),
                t.stderr && block(t.signal ? `Stderr (${t.signal})` : 'Stderr', t.stderr))));
    }

    function stress() {
        const s = state.stress;
        if (!s) { return null; }
        if (s.error) { return el('section', { class: 'card bad' }, el('h2', {}, 'Stress test stopped'), el('pre', { class: 'scroll' }, s.error)); }
        if (!s.mismatch) {
            return el('section', { class: 'card ok' }, el('h2', {}, `No difference in ${s.rounds_run} random tests`),
                el('p', { class: 'hint' }, 'Your solution matched brute.' + (state.lang === 'cpp' ? 'cpp' : 'py') + ' every time.'));
        }
        const m = s.mismatch;
        return el('section', { class: 'card bad' },
            el('h2', {}, `Counterexample after ${s.rounds_run} tests: ${VERDICT[m.status] || m.status}`),
            block('Input', m.input.join('\n')), block('Brute force', m.expected), block('Your solution', m.got || '(empty)'),
            m.stderr && block('Stderr', m.stderr),
            el('p', { class: 'hint' }, `Reproduce with: python gen.py ${m.seed}`),
            button('Add as a test', () => {
                vscode.postMessage({ type: 'addTest', input: m.input, output: m.expected });
            }, { secondary: true }));
    }

    function testsSection() {
        const p = state.problem;
        return el('section', {},
            el('h2', {}, `Tests (${state.tests.length})`),
            el('div', { class: 'toolbar' },
                button('Edit tests.json', () => vscode.postMessage({ type: 'open', file: 'tests.json' }), { secondary: true }),
                p.supported && button('Edit brute force', () => vscode.postMessage({ type: 'open', file: state.lang === 'cpp' ? 'brute.cpp' : 'brute.py' }), { secondary: true }),
                p.supported && button('Edit gen.py', () => vscode.postMessage({ type: 'open', file: 'gen.py' }), { secondary: true })),
            el('label', { class: 'check' },
                el('input', { type: 'checkbox', checked: !!p.anyOrder, onchange: (e) => {
                    p.anyOrder = e.target.checked;
                    vscode.postMessage({ type: 'anyOrder', value: e.target.checked });
                } }),
                ' Any order (compare lists ignoring order)'),
            !p.supported && el('p', { class: 'hint' },
                'This problem has an input format the generated harness doesn\'t cover (class design or an unusual type). ' +
                'Read stdin yourself; examples are still checked, stress testing is off.'));
    }

    function render() {
        if (!state.problem) { app.replaceChildren(status() || el('p', { class: 'status' }, 'Loading…')); return; }
        const parts = [header(state.problem), toolbar(), status(), state.busy ? null : results(), state.busy ? null : stress(),
            testsSection(),
            el('details', { class: 'statement' }, el('summary', {}, 'Problem statement'), el('pre', {}, state.problem.statement))];
        app.replaceChildren(...parts.filter(Boolean));  // replaceChildren would print null as text
    }

    window.addEventListener('message', (event) => {
        const m = event.data;
        switch (m.type) {
            case 'problem': state.problem = m.problem; state.tests = m.tests; state.error = null; break;
            case 'busy': state.busy = { kind: m.kind }; state.error = null; break;
            case 'idle': state.busy = null; break;
            case 'results': state.results = m.result; state.stress = null; state.lang = m.lang; break;
            case 'stressResult': state.stress = m.result; state.results = null; state.lang = m.lang; break;
            case 'error': state.error = m.message; break;
        }
        render();
    });

    render();
    vscode.postMessage({ type: 'ready' });
}());
