/*
 * Check that the gallery shim answers the two endpoints the playground calls.
 *
 *     node site/test_static_shim.mjs
 *
 * Stubs just enough DOM for the shim to load, then drives it the way the
 * playground does: fetch /recipes, then read /run/stream as an SSE body.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const SITE = dirname(fileURLToPath(import.meta.url));

const RUN = {
    events: [
        { type: 'start', recipe: 'demo', t: 0 },
        { type: 'log', text: 'kickoff', t: 0.5 },
        { type: 'complete', output: 'done', t: 9.0 }
    ]
};

// ── Minimal DOM + a fetch that serves our fixtures ────────────────────
const noopEl = () => ({
    textContent: '', innerHTML: '', id: '',
    appendChild() {}, insertBefore() {}, addEventListener() {}
});
globalThis.document = {
    baseURI: 'https://example.test/gallery/',
    head: noopEl(),
    body: { ...noopEl(), firstChild: null },
    createElement: noopEl,
    addEventListener() {}
};
globalThis.window = { fetch: async (url) => served(String(url)) };

let requested = [];
async function served(url) {
    requested.push(url);
    if (url.endsWith('runs/index.json')) return Response.json({ recipes: [{ id: 'demo' }] });
    if (url.endsWith('runs/demo.json')) return Response.json(RUN);
    return new Response('not found', { status: 404 });
}

globalThis.eval(readFileSync(join(SITE, 'static-shim.js'), 'utf8'));
const fetch = window.fetch;

// ── /recipes resolves against the page base, not the server root ──────
const recipes = await (await fetch('/recipes')).json();
assert.deepEqual(recipes.recipes, [{ id: 'demo' }]);
assert.equal(requested.at(-1), 'https://example.test/gallery/runs/index.json',
    'must be page-relative so it works under a /repo-name/ Pages path');

// ── /run/stream replays the recording as SSE ──────────────────────────
async function drain(res) {
    const reader = res.body.getReader(), decoder = new TextDecoder();
    let buffer = '', events = [];
    for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop();
        for (const part of parts) {
            assert.ok(part.startsWith('data: '), `bad SSE frame: ${part}`);
            events.push(JSON.parse(part.slice(6)));
        }
    }
    return events;
}

const started = Date.now();
const res = await fetch('/run/stream', { method: 'POST', body: JSON.stringify({ recipe: 'demo' }) });
assert.equal(res.status, 200);
assert.deepEqual(await drain(res), RUN.events);

// 9s of recorded run must not take 9s to watch, but must not arrive all at once.
const elapsed = Date.now() - started;
assert.ok(elapsed >= 60, `replay was instant (${elapsed}ms) — pacing is broken`);
assert.ok(elapsed < 3000, `replay took ${elapsed}ms — too slow for a landing page`);

// ── A missing recording is a clean 404, not a hang ────────────────────
const missing = await fetch('/run/stream', { method: 'POST', body: JSON.stringify({ recipe: 'nope' }) });
assert.equal(missing.status, 404);
assert.match((await missing.json()).detail, /No recorded run/);

// ── Cancel mid-replay surfaces as AbortError, like the real endpoint ──
const controller = new AbortController();
const aborted = await fetch('/run/stream', {
    method: 'POST', body: JSON.stringify({ recipe: 'demo' }), signal: controller.signal
});
const reader = aborted.body.getReader();
await reader.read();
controller.abort();
await assert.rejects(() => reader.read(), (e) => e.name === 'AbortError');

// ── Anything else falls through untouched ─────────────────────────────
assert.equal((await fetch('/somewhere/else')).status, 404);
assert.equal(requested.at(-1), '/somewhere/else');

console.log('✅ static-shim: routing, replay pacing, 404, abort, passthrough');
