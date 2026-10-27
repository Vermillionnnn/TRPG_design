"""Build the standalone release page from the artifact source.

The artifact source (bard-lute.html) is page content only: the artifact
viewer wraps it in a document with a doctype, a viewport and a small reset.
A copy sent on its own needs that wrapper itself, so this script adds it.

    python3 tools/build_release.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'bard-lute.html'
OUT = ROOT / 'bard-lute-release.html'

src = SRC.read_text(encoding='utf-8')
title = re.search(r'<title>(.*?)</title>', src).group(1)
style = re.search(r'<style>.*?</style>', src, re.S).group(0)
body = src[src.index(style) + len(style):].strip()

# the same reset the artifact viewer puts around the page
RESET = """<style>
:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0;font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
img{max-width:100%}
[hidden]{display:none!important}
</style>"""

page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="仿中世纪湿壁画：精灵吟游诗人在篝火旁弹鲁特琴，可以听《绿袖子》《斯卡布罗集市》《春天来临》三首老歌、自己弹，或玩慢速的落键音游。">
<title>{title}</title>
{RESET}
{style}
</head>
<body>
{body}
</body>
</html>
"""
OUT.write_text(page, encoding='utf-8')
print(f'wrote {OUT.name}: {len(page.encode("utf-8"))} bytes')
