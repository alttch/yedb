#!/usr/bin/env python3

import markdown, jinja2, shutil

from pathlib import Path
from bleach.linkifier import Linker

build_dir = Path('_build')

build_dir.mkdir(exist_ok=True)

with open('README.md') as fh:
    readme = markdown.markdown(fh.read(),
                               extensions=['markdown.extensions.tables'])

linker = Linker(callbacks=[])
readme = linker.linkify(readme)

with open('index.j2') as fh:
    tpl = jinja2.Template(fh.read())

(build_dir / 'index.html').write_text(tpl.render(dict(readme=readme)))

shutil.copy('yedb.jpg', build_dir)
shutil.copy('bg.png', build_dir)
