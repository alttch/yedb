#!/usr/bin/env python3

import markdown, jinja2, shutil

from pathlib import Path

build_dir = Path('_build')

build_dir.mkdir(exist_ok=True)

with open('README.md') as fh:
    readme = markdown.markdown(fh.read(),
                               extensions=['markdown.extensions.tables'])

with open('index.j2') as fh:
    tpl = jinja2.Template(fh.read())

(build_dir / 'index.html').write_text(tpl.render(dict(readme=readme)))

shutil.copy('yedb.jpg', build_dir)
