import json
import os
from html.parser import HTMLParser

from shared import site_dir

firebase_config_template_file = '.build/firebase-template.json'
firebase_config_file = 'firebase.json'


def main():
    firebase_config = read_firebase_config()
    redirects = []

    for subdir, dirs, files in os.walk(site_dir):
        for file in files:
            if file.endswith('.html'):
                handle_file(os.path.join(subdir, file), redirects)

    write_updated_firebase_config(firebase_config, redirects)


def read_firebase_config() -> dict:
    with open(firebase_config_template_file) as f:
        return json.load(f)


def write_updated_firebase_config(config: dict, redirects: list):
    existing_redirects: list = config['hosting'].get('redirects', [])
    redirects.sort(key=lambda r: r['source'])
    existing_redirects.extend(redirects)
    config['hosting']['redirects'] = existing_redirects

    with open(firebase_config_file, mode='w') as f:
        f.write(json.dumps(config, indent=2))


def handle_file(file: str, redirects: list):
    with open(file) as f:
        contents: str = f.read()
        if 'http-equiv="refresh"' in contents:
            from_path: str = file.replace(site_dir, '', 1).replace('/index.html', '', 1)
            parser = RedirectLinkExtractor(from_path, redirects)
            parser.feed(contents)


class RedirectLinkExtractor(HTMLParser):
    def __init__(self, from_path: str, redirects: list):
        super().__init__()
        self.from_path = from_path
        self.redirects = redirects

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            (attr_name, url) = attrs[0]
            if attr_name != 'href':
                raise attr_name

            if url.startswith('https://alexsaveau.dev'):
                url = '/' + url.split('://')[1].split('/', 1)[1]
            self.redirects.append({
                'source': self.from_path,
                'destination': url,
                'type': 302
            })


if __name__ == '__main__':
    main()
