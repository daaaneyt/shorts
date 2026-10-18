"""Assemble the paper-text generator.

  python3 build.py            -> paper-text-generator.html   (standalone: open it in any browser, works offline)
                                 build/artifact.html          (the same page without the document wrapper, for publishing)

Inlines the two fonts as data URIs, so the page has no dependencies.
"""
import base64, os, re, sys
here = os.path.dirname(os.path.abspath(__file__))
rd = lambda p: open(os.path.join(here, p), encoding='utf-8').read()
b64 = lambda p: base64.b64encode(open(os.path.join(here, p), 'rb').read()).decode()

fonts = (
    '@font-face{font-family:"Space Grotesk";font-weight:300 700;font-style:normal;font-display:block;'
    'src:url(data:font/ttf;base64,%s) format("truetype")}\n'
    '@font-face{font-family:"Space Mono";font-weight:700;font-style:normal;font-display:block;'
    'src:url(data:font/ttf;base64,%s) format("truetype")}\n' % (b64('fonts/SpaceGrotesk-Variable.ttf'), b64('fonts/SpaceMono-Bold.ttf')))

fragment = (
    '<title>sub3piece Paper Text</title>\n<style>\n' + fonts + rd('src/app.css') + '</style>\n'
    + rd('src/app.html') + '<script>\n' + rd('src/papertext.js') + '\n</script>\n<script>\n' + rd('src/ui.js') + '\n</script>\n')
assert '</script' not in rd('src/papertext.js') + rd('src/ui.js')

os.makedirs(os.path.join(here, 'build'), exist_ok=True)
open(os.path.join(here, 'build/artifact.html'), 'w', encoding='utf-8').write(fragment)

title = re.search(r'<title>.*?</title>', fragment).group(0)
body = fragment.replace(title + '\n', '', 1)
doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       + title + '\n<style>:root{color-scheme:light}body{margin:0;font:14px system-ui}[hidden]{display:none!important}img{max-width:100%}</style>\n</head>\n<body>\n' + body + '</body>\n</html>\n')
open(os.path.join(here, 'paper-text-generator.html'), 'w', encoding='utf-8').write(doc)
print('paper-text-generator.html %.0f KB; build/artifact.html %.0f KB' % (len(doc) / 1024, len(fragment) / 1024))
