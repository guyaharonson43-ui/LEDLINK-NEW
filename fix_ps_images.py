"""
Replaces Epsilon -ps- schematic images with real product photos.
Visits each product's Epsilon page and finds the non-ps image.
"""
import json, urllib.request, urllib.parse, re, time, sys

PRODUCTS_JSON = 'C:/Users/guy/Downloads/ledlink/products.json'
LOG_FILE      = 'C:/Users/guy/Downloads/ledlink/fix_ps_log.txt'
CHECKPOINT    = 25   # save every N updates

log_f = open(LOG_FILE, 'w', encoding='utf-8')
def log(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))
    log_f.write(msg + '\n')
    log_f.flush()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*',
    'Accept-Language': 'he-IL,he;q=0.9',
}

def fetch_page(url):
    url = urllib.parse.quote(url, safe=':/?=&#%@')
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8', errors='ignore')

def find_real_img(html, current_ps_url):
    """
    Find the best real product photo from Epsilon page HTML.
    Priority:
      1. Any files/catalog image that does NOT contain '-ps-'
      2. Short numeric jpg (3-8 digits)
    """
    all_imgs = re.findall(r'files/catalog/([\w\-\.]+\.(?:png|jpg|jpeg|webp))', html)
    all_imgs = list(dict.fromkeys(all_imgs))  # unique, preserve order

    # Strip current ps image basename for comparison
    cur_base = current_ps_url.split('/')[-1] if current_ps_url else ''

    candidates = []
    for fname in all_imgs:
        if fname == cur_base:
            continue   # skip the current schematic
        if '-ps-' in fname:
            continue   # skip other schematics
        candidates.append(fname)

    if not candidates:
        return None

    # Prefer jpg over png (usually real photo), then shortest name
    jpg_cands = [c for c in candidates if c.lower().endswith('.jpg') or c.lower().endswith('.jpeg')]
    if jpg_cands:
        return 'https://www.epsilonlighting.co.il/files/catalog/' + jpg_cands[0]

    return 'https://www.epsilonlighting.co.il/files/catalog/' + candidates[0]


with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
    products = json.load(f)

# Find products with -ps- images that also have an Epsilon URL to visit
to_fix = [
    (i, p) for i, p in enumerate(products)
    if '-ps-' in (p.get('img') or '')
    and p.get('url', '').startswith('https://www.epsilonlighting.co.il')
]

log(f"Found {len(to_fix)} products with -ps- schematic images to fix")

updated = 0
failed  = 0

for count, (idx, prod) in enumerate(to_fix, 1):
    name = prod.get('name', '')
    url  = prod['url']
    old_img = prod['img']

    try:
        html = fetch_page(url)
        new_img = find_real_img(html, old_img)

        if new_img:
            products[idx]['img'] = new_img
            updated += 1
            log(f"[{count}/{len(to_fix)}] ✓ {name}: {new_img.split('/')[-1]}")
        else:
            failed += 1
            log(f"[{count}/{len(to_fix)}] – {name}: no real image found (kept ps)")

        # Save checkpoint
        if updated % CHECKPOINT == 0:
            with open(PRODUCTS_JSON, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            log(f"  → Checkpoint saved ({updated} updated so far)")

        time.sleep(0.3)   # be polite

    except Exception as e:
        failed += 1
        log(f"[{count}/{len(to_fix)}] ✗ {name}: ERROR {e}")
        time.sleep(1)

# Final save
with open(PRODUCTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

log(f"\nDone: {updated} updated, {failed} failed/unchanged")
log_f.close()
