"""Re-embed the page fonts with exactly the characters the page uses.

scribe-scroll.html embeds two fonts as woff2 data URIs, both SIL OFL and served by Google Fonts:
- Noto Serif SC, cut down to every non-ASCII character in the page plus printable ASCII;
- Fondamento, the chancery hand of the scroll text, cut down to printable ASCII plus the
  middle dot that stands in for faded letters.
After adding or changing Chinese text, run this so new characters are not drawn in a fallback
font. It needs network access to Google Fonts, which serves the subsets.

    python3 html/scribe-scroll/tools/subset_font.py
"""
import base64
import pathlib
import re
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / 'scribe-scroll.html'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
ASCII = set(chr(i) for i in range(32, 127))


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA})).read()


def embed(page, family, query, chars):
    face = re.compile(r'(@font-face\{font-family:"%s";[^}]*?url\(data:font/woff2;base64,)([A-Za-z0-9+/=]+)(\))' % family)
    match = face.search(page)
    if not match:
        raise SystemExit(f'could not find the embedded {family} @font-face')
    text = urllib.parse.quote(''.join(sorted(chars)))
    css = get(f'https://fonts.googleapis.com/css2?family={query}&text={text}').decode()
    woff2 = get(re.search(r'url\((https://[^)]+)\)', css).group(1))
    print(f'{family}: embedded {len(chars)} characters, {len(woff2)} bytes of woff2')
    return page[:match.start(2)] + base64.b64encode(woff2).decode() + page[match.end(2):]


page = PAGE.read_text(encoding='utf-8')
# every non-ASCII character in the page (static text and strings in the script) plus printable ASCII
page = embed(page, 'Noto Serif SC', 'Noto+Serif+SC:wght@400;600', set(c for c in page if ord(c) > 126) | ASCII)
# the spell texts are English; faded letters are drawn as a middle dot
page = embed(page, 'Fondamento', 'Fondamento', ASCII | {'·'})
PAGE.write_text(page, encoding='utf-8')
