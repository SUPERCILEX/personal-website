import os
from html.parser import HTMLParser

from shared import site_dir, site_url

config_file = 'build/_redirects'


def main():
    with open(config_file, "a") as output:
        for subdir, dirs, files in os.walk(site_dir):
            for file in files:
                if file.endswith('.html'):
                    handle_file(os.path.join(subdir, file), output)


def handle_file(file: str, output):
    with open(file) as f:
        contents: str = f.read()
        if 'http-equiv="refresh"' in contents:
            from_path: str = file.replace(site_dir, '', 1).replace('/index.html', '', 1)
            parser = RedirectLinkExtractor(file, from_path, output)
            parser.feed(contents)


class RedirectLinkExtractor(HTMLParser):
    def __init__(self, input_file: str, from_path: str, output):
        super().__init__()
        self.input_file = input_file
        self.from_path = from_path
        self.output = output

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            (attr_name, url) = attrs[0]
            if attr_name != 'href':
                raise attr_name

            if url.startswith(site_url):
                url = '/' + url.split('://')[1].split('/', 1)[1]
            self.output.write(f'{self.from_path} {url} 302\n')

            os.remove(self.input_file)


if __name__ == '__main__':
    main()
