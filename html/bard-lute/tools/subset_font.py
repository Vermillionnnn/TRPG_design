"""Re-embed the body font with exactly the characters the page uses.

bard-lute.html embeds Noto Serif SC (SIL OFL) as a woff2 data URI cut down to
the characters on the page. After adding or changing Chinese text, run this so
new characters are not drawn in a fallback font. It needs network access to
Google Fonts, which serves the subset.

    python3 tools/subset_font.py
"""
import base64
import pathlib
import re
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / 'bard-lute.html'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
FACE = re.compile(r'(@font-face\{font-family:"Noto Serif SC";[^}]*?url\(data:font/woff2;base64,)([A-Za-z0-9+/=]+)(\))')


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA})).read()


page = PAGE.read_text(encoding='utf-8')
match = FACE.search(page)
if not match:
    raise SystemExit('could not find the embedded Noto Serif SC @font-face')
# every non-ASCII character in the page (static text and strings in the script) plus printable ASCII
chars = sorted(set(c for c in page if ord(c) > 126) | set(chr(i) for i in range(32, 127)))
text = urllib.parse.quote(''.join(chars))
css = get(f'https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600&text={text}').decode()
woff2 = get(re.search(r'url\((https://[^)]+)\)', css).group(1))
page = page[:match.start(2)] + base64.b64encode(woff2).decode() + page[match.end(2):]
PAGE.write_text(page, encoding='utf-8')
print(f'embedded {len(chars)} characters: {len(woff2)} bytes of woff2')
