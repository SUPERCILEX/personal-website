import os
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from subprocess import check_call, PIPE
from typing import List

from shared import site_dir, site_url

html_minifier = '.build/node_modules/.bin/html-minifier'
served_locally = os.environ.get('SERVED_LOCALLY', '') == 'true'


def main():
    pool = ThreadPoolExecutor()
    tasks: List[Future] = []

    for root, _, files in os.walk(site_dir):
        for file in files:
            if file.endswith('.html'):
                tasks.append(pool.submit(compress, root, file))

    for task in tasks:
        task.result()


def compress(parent: str, file: str):
    path = os.path.join(parent, file)
    maybe_trailing_slash = '/' if served_locally else ''
    base_url = \
        site_url + '/' + parent.removeprefix('build').removeprefix('/') + maybe_trailing_slash

    check_call([
        html_minifier, path,
        '--output', path,
        '--collapse-boolean-attributes',
        '--collapse-whitespace',
        '--decode-entities',
        '--minify-css', '{"level":"2"}',
        '--minify-js', 'true',
        '--minify-urls', base_url,
        '--remove-attribute-quotes',
        '--remove-comments',
        '--remove-empty-attributes',
        '--remove-optional-tags',
        '--remove-redundant-attributes',
        '--remove-script-type-attributes',
        '--remove-style-link-type-attributes',
        '--sort-attributes',
        '--sort-class-name',
        '--use-short-doctype',
    ], stdout=PIPE, timeout=90)


if __name__ == '__main__':
    main()
