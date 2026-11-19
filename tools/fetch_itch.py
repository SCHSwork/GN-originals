"""Copies a free HTML5 game from its itch.io page into games/<slug>/.

Run by .github/workflows/fetch-itch.yml when tools/itch-fetch.json changes:
  {"url": "https://someone.itch.io/game", "slug": "game"}
Downloads the game's files (index.html and everything it loads, found by
following file names in the HTML, scripts and JSON) and the page's cover
picture to covers/<slug>.<ext>. Prints what it got.
"""
import html, json, os, re, sys, urllib.parse, urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/126 Safari/537.36"}
TEXT = (".html", ".htm", ".js", ".json", ".css")
REF = re.compile(r"""["'`(]([A-Za-z0-9_\-./ %]+\.(?:js|json|unityweb|data|wasm|mem|css|png|jpe?g|gif|ico|gz|br|txt|xml|mp3|ogg|wav|unity3d|bundle|pck))["'`)?]""", re.I)

def get(url, referer=None):
    h = dict(HEADERS)
    if referer: h["Referer"] = referer
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120) as r:
        return r.read()

cfg = json.load(open("tools/itch-fetch.json"))
page_url, slug = cfg["url"], cfg["slug"]
page = get(page_url).decode("utf8", "replace")

def save_cover():
    # The page's cover picture (og:image, attributes in either order)
    og = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', page) or re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', page)
    if not og:
        print("No cover picture on the page"); return
    img = html.unescape(og.group(1))
    ext = os.path.splitext(urllib.parse.urlparse(img).path)[1].lower() or ".png"
    os.makedirs("covers", exist_ok=True)
    open(f"covers/{slug}{ext}", "wb").write(get(img))
    print("Cover:", img, "->", f"covers/{slug}{ext}")

# {"coverOnly": true}: just the cover, leaving a game that's already here alone
if cfg.get("coverOnly"):
    save_cover(); sys.exit(0)
m = re.search(r'https?:(?:\\?/){2}html(?:-classic)?\.itch\.zone(?:\\?/)html(?:\\?/)\d+(?:\\?/)[^"\'<>\s&]*?index\.html', html.unescape(page))
if not m:
    sys.exit("No HTML5 game found on the page")
start = m.group(0).replace("\\/", "/")
base = start.rsplit("/", 1)[0] + "/"
print("Game:", start)
out = os.path.join("games", slug)
os.makedirs(out, exist_ok=True)

seen, queue, got = set(), [start], []
while queue:
    url = queue.pop(0)
    if url in seen or not url.startswith(base):
        continue
    seen.add(url)
    try:
        data = get(url, page_url)
    except Exception:
        if url == start: raise
        continue
    rel = urllib.parse.unquote(url[len(base):].split("?")[0])
    dest = os.path.join(out, rel)
    os.makedirs(os.path.dirname(dest) or out, exist_ok=True)
    open(dest, "wb").write(data)
    got.append((rel, len(data)))
    if rel.lower().endswith(TEXT):
        text = data.decode("utf8", "replace")
        here = url.rsplit("/", 1)[0] + "/"
        for ref in set(REF.findall(text)):
            ref = ref.strip()
            if ref.startswith(("http:", "https:", "//")): continue
            for cand in {urllib.parse.urljoin(here, ref.lstrip("/")), urllib.parse.urljoin(base, ref.lstrip("/")), urllib.parse.urljoin(base, "Build/" + ref.lstrip("/"))}:
                if cand not in seen: queue.append(cand)

for rel, n in sorted(got):
    print(f"  {n:>10,}  {rel}")
print(f"{len(got)} files, {sum(n for _, n in got) / 1e6:.1f} MB")

save_cover()
open(os.path.join(out, ".itch-source.txt"), "w").write(f"{page_url}\n{start}\n")
