"""Insert the loader shim into Godot's exported index.html; write page.html and local.html."""
import os
import re

SHIM = '''<script>
// The engine ships gzip-compressed and the game data under a web-safe name; map Godot's
// requests onto them and unpack the engine as it loads.
(function () {
	const realFetch = window.fetch.bind(window);
	window.fetch = function (input, init) {
		const url = typeof input === 'string' ? input : input.url;
		if (/index\\.wasm(\\?|$)/.test(url)) {
			return realFetch('engine.gz.wasm', init).then((r) => {
				if (!r.ok) return r;
				const body = r.body.pipeThrough(new DecompressionStream('gzip'));
				return new Response(body, { status: 200, headers: { 'Content-Type': 'application/wasm' } });
			});
		}
		if (/index\\.pck(\\?|$)/.test(url)) {
			// The game data comes in numbered parts, joined into one stream.
			const parts = [];
			for (let i = 0; i < PCK_PARTS; i++) parts.push('game.pck.' + String(i).padStart(2, '0') + '.wasm');
			const stream = new ReadableStream({
				async start(controller) {
					for (const name of parts) {
						const r = await realFetch(name, init);
						if (!r.ok) { controller.error(new Error('missing ' + name)); return; }
						const reader = r.body.getReader();
						for (;;) {
							const { done, value } = await reader.read();
							if (done) break;
							controller.enqueue(value);
						}
					}
					controller.close();
				},
			});
			return Promise.resolve(new Response(stream, { status: 200, headers: { 'Content-Type': 'application/octet-stream' } }));
		}
		return realFetch(input, init);
	};
})();
</script>
		<script src="index.js"></script>'''

import os
SHIM = SHIM.replace('(function () {', '(function () {\n\tconst PCK_PARTS = %d;' % int(os.environ.get('PCK_PARTS', '1')), 1)
s = open('index.html').read()
s = s.replace('<script src="index.js"></script>', SHIM, 1)
# The game's own loading screen in place of the engine's logo: its name, how far along, and
# what the wait is (the first visit fetches about 200 MB; the browser keeps it after).
LOADING_CSS = '''
#status { background: radial-gradient(ellipse at 50% 40%, #1a1410 0%, #070605 70%) !important; font-family: Georgia, 'Times New Roman', serif; color: #e9dcc3; }
#status-splash { position: static !important; margin: 0 !important; text-align: center; padding: 0 24px; }
#status-splash .over { font-size: clamp(10px, 1.4vw, 15px); letter-spacing: 0.28em; color: #b08a4a; }
#status-splash .name { font-size: clamp(40px, 9vw, 104px); letter-spacing: 0.06em; margin: 0.12em 0 0.08em; text-shadow: 0 0 40px rgba(232, 176, 92, 0.25); }
#status-splash .rule { width: min(420px, 60vw); height: 1px; margin: 0 auto 1.2em; background: linear-gradient(90deg, transparent, #b08a4a, transparent); }
#status-splash .what { font-style: italic; font-size: clamp(13px, 1.7vw, 18px); color: #cbbd9f; min-height: 1.4em; }
#status-splash .hint { font-size: clamp(11px, 1.3vw, 14px); color: #8f8572; margin-top: 0.6em; }
#status-progress { position: static !important; display: block; appearance: none; -webkit-appearance: none; width: min(420px, 60vw) !important; height: 4px; margin: 1.6em auto 0 !important; border: 0; background: #2a231b; border-radius: 2px; overflow: hidden; }
#status-progress::-webkit-progress-bar { background: #2a231b; }
#status-progress::-webkit-progress-value { background: linear-gradient(90deg, #8a6a34, #e8b05c); }
#status-progress::-moz-progress-bar { background: #e8b05c; }
#status-notice { margin-top: 1.5em !important; font-family: Georgia, serif !important; }
'''
LOADING_HTML = '''<div id="status-splash">
				<div class="over">TEN THOUSAND YEARS AFTER THE AWAKENING</div>
				<div class="name">WILDLINE</div>
				<div class="rule"></div>
				<div class="what" id="status-what">Waking the field</div>
				<div class="hint" id="status-hint">The first visit is the long one: a few minutes on a slow line.</div>
			</div>'''
LOADING_JS = '''<script>
// Say how far along the load is, in words and megabytes, under the game's name.
(function () {
	const bar = document.getElementById('status-progress');
	const what = document.getElementById('status-what');
	if (!bar || !what) return;
	const started = Date.now();
	const tick = setInterval(function () {
		if (!document.getElementById('status')) { clearInterval(tick); return; }
		const v = Number(bar.getAttribute('value')), m = Number(bar.getAttribute('max'));
		if (m > 0 && v >= 0) {
			const pct = Math.min(100, Math.floor(100 * v / m));
			what.textContent = pct >= 100 ? 'Raising the platform' : 'Bringing the world down the line: ' + pct + '% (' + Math.round(v / 1e6) + ' of ' + Math.round(m / 1e6) + ' MB)';
		} else if (Date.now() - started > 4000) {
			what.textContent = 'Raising the platform';
		}
	}, 250);
})();
</script>'''
size_mb = int(round((os.path.getsize('index.pck') + os.path.getsize('engine.gz.wasm')) / 1e6 / 10.0) * 10)
assert '<img id="status-splash" src="index.png" alt="">' in s and '</style>' in s
s = s.replace('<img id="status-splash" src="index.png" alt="">', LOADING_HTML.replace('SIZE_MB', str(size_mb)), 1)
s = s.replace('</style>', LOADING_CSS + '</style>', 1)
s = s.replace('<script src="index.js"></script>', LOADING_JS + '\n\t\t<script src="index.js"></script>', 1)
open('local.html', 'w').write(s)
p = re.sub(r'<!DOCTYPE html>\s*<html[^>]*>\s*<head>\s*', '', s)
p = p.replace('<meta charset="utf-8">', '').replace('<meta name="viewport" content="width=device-width, user-scalable=no, initial-scale=1.0">', '')
p = re.sub(r'</head>\s*<body>', '', p)
p = re.sub(r'</body>\s*</html>\s*$', '', p)
p = p.replace('html, body, #canvas {', 'html { color-scheme: dark; }\nhtml, body, #canvas {', 1)
open('page.html', 'w').write(p.strip() + '\n')
