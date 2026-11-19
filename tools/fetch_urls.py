"""Downloads files into this repo, and reports what's on web pages.

Run by .github/workflows/fetch-urls.yml when tools/fetch-urls.json changes:
  {"files": [{"url": "...", "to": "games/x/game.swf"}],
   "pages": ["https://..."]}
files are saved where "to" says. For each page, its og:image and every link
to a game file (.swf, .html, .zip, .js, .data, .wasm, images) are printed in
the run's log, to find where a game's files are.
"""
import html, json, os, re, urllib.parse, urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/126 Safari/537.36"}

def get(url, referer=None):
    h = dict(HEADERS)
    if referer: h["Referer"] = referer
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120) as r:
        return r.read()

cfg = json.load(open("tools/fetch-urls.json"))
for f in cfg.get("files", []):
    try:
        data = get(f["url"], f.get("referer"))
        os.makedirs(os.path.dirname(f["to"]) or ".", exist_ok=True)
        open(f["to"], "wb").write(data)
        print(f"OK   {len(data):>10,}  {f['to']}  <- {f['url']}")
    except Exception as e:
        print(f"FAIL {f['url']}: {e}")
for p in cfg.get("pages", []):
    print("\n== " + p)
    try:
        text = html.unescape(get(p).decode("utf8", "replace")).replace("\\/", "/")
    except Exception as e:
        print("FAIL", e); continue
    for m in re.findall(r'<meta[^>]+(?:property|name)="(?:og:image|twitter:image)"[^>]*>', text):
        print("  meta:", m)
    seen = set()
    for u in re.findall(r'''["'(]((?:https?:)?//[^"'()\s<>]+|[^"'()\s<>:]+)["')]''', text):
        if re.search(r"\.(swf|zip|html?|js|data|wasm|png|jpe?g|gif|webp)(\?|$)", u, re.I) and u not in seen:
            seen.add(u)
            print("  link:", urllib.parse.urljoin(p, u))
