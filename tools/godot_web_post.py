#!/usr/bin/env python3
"""post.py <export_dir> <dest_game_dir> <originals_root> [godot_version]
Makes a Godot 4.6.2 web export fit jsDelivr's 20 MB file limit: the engine
.wasm is shared (gzipped once in games/_godot/4.6.2/), big .pck files are
gzipped, and a small fetch shim unpacks them in the browser."""
import sys, gzip, hashlib, shutil, pathlib, re
src, dst, root = map(pathlib.Path, sys.argv[1:4])
VER = sys.argv[4] if len(sys.argv) > 4 else "4.6.2"
eng_dir = root / "games/_godot" / VER; eng_dir.mkdir(parents=True, exist_ok=True)
wasm = (src / "index.wasm").read_bytes()
h = hashlib.sha256(wasm).hexdigest()[:16]
eng = eng_dir / "godot.wasm.gz"
if not eng.exists():
    eng.write_bytes(gzip.compress(wasm, 9, mtime=0)); (eng_dir / "godot.wasm.sha").write_text(h)
elif (eng_dir / "godot.wasm.sha").read_text().strip() != h:
    sys.exit("engine wasm differs from the shared one")
dst.mkdir(parents=True, exist_ok=True)
for f in src.iterdir():
    if f.name in ("index.wasm",): continue
    shutil.copy(f, dst / f.name)
mapping = {"index.wasm": ["REL/godot.wasm.gz"]}
pck = dst / "index.pck"
if pck.stat().st_size > 15_000_000:
    gz = gzip.compress(pck.read_bytes(), 6, mtime=0); pck.unlink()
    PART = 18_000_000
    if len(gz) <= PART:
        (dst / "index.pck.gz").write_bytes(gz); mapping["index.pck"] = ["index.pck.gz"]
    else:  # jsDelivr serves files up to 20 MB, so split it; the shim joins the parts
        parts = []
        for i in range(0, len(gz), PART):
            name = f"index.pck.gz.{i // PART}"; (dst / name).write_bytes(gz[i:i + PART]); parts.append(name)
        mapping["index.pck"] = parts
depth = len(dst.relative_to(root / "games").parts)
rel = "../" * depth + "_godot/" + VER
js_map = "{" + ",".join(f'"{k}":[' + ",".join(f'"{x.replace("REL", rel)}"' for x in v) + "]" for k, v in mapping.items()) + "}"
shim = ("<script>/* GN Originals: the engine and big data files are stored gzipped (and split if over 18 MB); unpack them here */"
 f"(function(){{var m={js_map},f=window.fetch;"
 "function joined(urls,o){var i=0;return new ReadableStream({pull:function(c){if(i>=urls.length){c.close();return}"
 "return f(new URL(urls[i++],document.baseURI).href,o).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);var rd=r.body.getReader();"
 "function pump(){return rd.read().then(function(x){if(x.done)return;c.enqueue(x.value);return pump()})}return pump()})}})}"
 "window.fetch=function(u,o){var s=String(u&&u.url||u).split('?')[0];"
 "for(var k in m){if(s===k||s.slice(-k.length-1)==='/'+k){var t=k.slice(-5)==='.wasm'?'application/wasm':'application/octet-stream';"
 "return Promise.resolve(new Response(joined(m[k],o).pipeThrough(new DecompressionStream('gzip')),{status:200,headers:{'Content-Type':t}}))}}"
 "return f.apply(this,arguments)}})();</script>")
html = (dst / "index.html").read_text(encoding="utf8")
html = html.replace("<script src=\"index.js\"></script>", shim + "<script src=\"index.js\"></script>", 1) if '<script src="index.js"></script>' in html else html.replace("</head>", shim + "</head>", 1)
# fileSizes in the config are only used for the progress bar; drop them so gz sizes don't confuse it
html = html.replace('"ensureCrossOriginIsolationHeaders":true','"ensureCrossOriginIsolationHeaders":false')
html = re.sub(r'"fileSizes":\{[^}]*\}', '"fileSizes":{}', html)
(dst / "index.html").write_text(html, encoding="utf8")
print("ok", dst, {p.name: p.stat().st_size for p in dst.iterdir()}, "engine.gz", eng.stat().st_size)
