/*
 * Static gallery shim — lets the playground UI run with no backend.
 *
 * The playground touches the server in exactly two places: GET /recipes and
 * POST /run/stream. This patches window.fetch to answer both from the JSON
 * recordings in site/runs/, so GitHub Pages serves the same UI with real,
 * previously-captured agent traces. Loaded before the app script; every other
 * request falls through to the real fetch.
 */
(function () {
    window.__STATIC_GALLERY__ = true;

    // Replay faster than real time, but keep the original rhythm between events.
    var SPEED = 0.25, MIN_GAP_MS = 30, MAX_GAP_MS = 400;

    var realFetch = window.fetch.bind(window);
    var asset = function (path) { return new URL(path, document.baseURI).href; };

    function json(body, status) {
        return new Response(JSON.stringify(body), {
            status: status || 200,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    function replay(events, signal) {
        var encoder = new TextEncoder();
        var i = 0, timer = null;

        return new ReadableStream({
            start: function (controller) {
                function abort() {
                    clearTimeout(timer);
                    controller.error(new DOMException('Aborted', 'AbortError'));
                }
                if (signal) {
                    if (signal.aborted) return abort();
                    signal.addEventListener('abort', abort, { once: true });
                }

                function step() {
                    var event = events[i++];
                    controller.enqueue(encoder.encode('data: ' + JSON.stringify(event) + '\n\n'));
                    if (i >= events.length) return controller.close();

                    var gap = Math.max(0, (events[i].t || 0) - (event.t || 0)) * 1000 * SPEED;
                    timer = setTimeout(step, Math.min(Math.max(gap, MIN_GAP_MS), MAX_GAP_MS));
                }
                step();
            },
            cancel: function () { clearTimeout(timer); }
        });
    }

    window.fetch = function (input, init) {
        var url = String((input && input.url) || input || '');
        init = init || {};

        if (url === '/recipes') {
            return realFetch(asset('runs/index.json'));
        }

        if (url === '/run/stream') {
            var recipe;
            try {
                recipe = JSON.parse(init.body).recipe;
            } catch (e) {
                return Promise.resolve(json({ detail: 'Malformed run request.' }, 400));
            }

            return realFetch(asset('runs/' + recipe + '.json')).then(function (res) {
                if (!res.ok) {
                    return json({ detail: 'No recorded run for "' + recipe + '" yet. Clone the repo to run it live.' }, 404);
                }
                return res.json().then(function (run) {
                    if (!run.events || !run.events.length) {
                        return json({ detail: 'Recording for "' + recipe + '" is empty.' }, 500);
                    }
                    return new Response(replay(run.events, init.signal), {
                        status: 200,
                        headers: { 'Content-Type': 'text/event-stream' }
                    });
                });
            });
        }

        return realFetch(input, init);
    };

    // The playground centres .app-layout with `display:flex` on <body>, so stack
    // the banner above it rather than beside it.
    var style = document.createElement('style');
    style.textContent = [
        'body { flex-direction: column; align-items: center; }',
        '#gallery-banner {',
        '  width: 100%; box-sizing: border-box; padding: 0.7rem 1.5rem;',
        '  background: var(--surface-2); border-bottom: 1px solid var(--border);',
        '  color: var(--text-muted); font-size: 0.85rem; line-height: 1.5; text-align: center;',
        '}',
        '#gallery-banner strong { color: var(--text-color); }',
        '#gallery-banner a { color: var(--primary); text-decoration: none; white-space: nowrap; }',
        '#gallery-banner a:hover { text-decoration: underline; }'
    ].join('\n');
    document.head.appendChild(style);

    // Say plainly what the visitor is looking at.
    document.addEventListener('DOMContentLoaded', function () {
        var banner = document.createElement('div');
        banner.id = 'gallery-banner';
        banner.innerHTML =
            '<strong>Recorded runs.</strong> Every trace below is a real run against ' +
            'Llama 3.1 8B on NVIDIA NIM, captured and replayed here — no server, no API key needed. ' +
            'Inputs are fixed to what was recorded. ' +
            '<a href="https://github.com/Karan-Raj-KR/crewai-recipes#-quickstart">Clone it to run your own →</a>';
        document.body.insertBefore(banner, document.body.firstChild);
    });
})();
