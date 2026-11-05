"""Insert the loader shim into Godot's exported index.html; write page.html and local.html."""
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
			return realFetch('game.pck.wasm', init).then((r) => {
				if (!r.ok) return r;
				return new Response(r.body, { status: 200, headers: { 'Content-Type': 'application/octet-stream' } });
			});
		}
		return realFetch(input, init);
	};
})();
</script>
		<script src="index.js"></script>'''

s = open('index.html').read()
s = s.replace('<script src="index.js"></script>', SHIM, 1)
s = s.replace('<title>WILDLINE</title>', '<title>WILDLINE Pulse Room</title>')
open('local.html', 'w').write(s)
p = re.sub(r'<!DOCTYPE html>\s*<html[^>]*>\s*<head>\s*', '', s)
p = p.replace('<meta charset="utf-8">', '').replace('<meta name="viewport" content="width=device-width, user-scalable=no, initial-scale=1.0">', '')
p = re.sub(r'</head>\s*<body>', '', p)
p = re.sub(r'</body>\s*</html>\s*$', '', p)
p = p.replace('html, body, #canvas {', 'html { color-scheme: dark; }\nhtml, body, #canvas {', 1)
open('page.html', 'w').write(p.strip() + '\n')
