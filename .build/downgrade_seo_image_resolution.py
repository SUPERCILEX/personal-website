import os
import re

from shared import site_dir, removeprefix, downgrade_image

assets_url = 'https://alexsaveau.dev/assets/'


def main():
    for subdir, dirs, files in os.walk(site_dir):
        for file in files:
            if file.endswith('.html'):
                handle_file(os.path.join(subdir, file))


def handle_file(file: str):
    with open(file, 'r+') as f:
        contents = f.read()
        new_contents = contents
        found = set()

        for match in re.finditer(assets_url, contents):
            url = contents[match.start():contents.index('"', match.start())]
            if url in found:
                continue
            found.add(url)

            path = removeprefix(url, assets_url)
            if path.startswith('resized/'):
                continue

            downgraded = downgrade_image(path, max_resolution=800, extension='jpg')
            downgraded = assets_url + removeprefix(downgraded, 'assets/')

            print(f'Downgrading {url} to {downgraded} in {file}')
            new_contents = new_contents.replace(url, downgraded)

        f.seek(0)
        f.write(new_contents)


if __name__ == '__main__':
    main()
