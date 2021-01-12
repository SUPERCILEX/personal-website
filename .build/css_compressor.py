import os
import sys
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from subprocess import check_call, PIPE, STDOUT
from typing import List

from shared import site_dir

css_file = 'build/css/styles.css'
css_marker = '<css-inline-location-marker></css-inline-location-marker>'

uncss = '.build/node_modules/.bin/uncss'
csso = '.build/node_modules/.bin/csso'


def main(prod: bool):
    pool = ThreadPoolExecutor()
    tasks: List[Future] = []

    with open(css_file) as f:
        css = f.read()

    for root, subdirs, files in os.walk(site_dir):
        for file in files:
            if file.endswith('.html'):
                if prod:
                    tasks.append(pool.submit(compress, css, root, file))
                else:
                    tasks.append(pool.submit(inline_into_html, css, os.path.join(root, file)))

    for task in tasks:
        task.result()


def compress(css: str, parent: str, file: str):
    tmp_css_file = file + '.csstmp'
    tmp_css_path = os.path.join(parent, tmp_css_file)
    with open(tmp_css_path, 'w') as f:
        f.write(css)

    check_call([
        uncss,
        '--stylesheets',
        tmp_css_file,
        '--output',
        tmp_css_path,
        os.path.join(parent, file),
    ], stdout=PIPE, stderr=STDOUT, timeout=90)

    check_call([
        csso,
        '--input',
        tmp_css_path,
        '--output',
        tmp_css_path,
    ], stdout=PIPE, stderr=STDOUT, timeout=90)

    with open(tmp_css_path) as f:
        inline_into_html(f.read(), os.path.join(parent, file))
    os.remove(tmp_css_path)


def inline_into_html(css: str, path: str):
    with open(path, 'r+') as f:
        html = f.read()
        html = html.replace(css_marker, f'<style>{css}</style>')

        f.seek(0)
        f.write(html)


if __name__ == '__main__':
    main(sys.argv[1] == 'production')
