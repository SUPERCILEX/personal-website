#!/usr/bin/env python3
import os

import click
from dotenv import load_dotenv

load_dotenv()


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv:
            return rv

        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])

        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


@click.group(cls=AliasedGroup, context_settings={'help_option_names': ['-h', '--help']})
def cli():
    """
    The site CLI provides common utilities in one unified place.
    """

    pass


@click.option('--prod', '--production', '-p', is_flag=True, default=False,
              help='Builds the site under a production environment.')
@click.option('--drafts/--no-drafts', is_flag=True, default=True,
              help='Include draft and future posts.')
@click.option('--fast/--no-fast', is_flag=True, default=True,
              help='Don\'t render the full site to speed up build times.')
@click.option('--live', '-l', is_flag=True, default=False,
              help='Serve on a live staging instance.')
@click.option('--expires', default='1d',
              help='Staging channel expiration. Only used when --live is set.')
@click.option('--profile', is_flag=True, default=False,
              help='Profile Jekyll build performance.')
@cli.command()
def serve(prod, drafts, fast, live, expires, profile):
    """
    Deploy the site.
    """

    env = ''
    if prod:
        env += ' JEKYLL_ENV=production'
    if not live:
        env += ' SERVED_LOCALLY=true'

    args = '--future --drafts' if drafts else ''
    if fast:
        args += ' --limit-posts 3 --config "_config.yml,_config_dev.yml"'
    if profile:
        args += ' --profile'

    if live:
        os.system(f'{env} bundle exec jekyll build {args}')

        os.system('.build/node_modules/.bin/firebase '
                  f'hosting:channel:deploy -e {expires} '
                  '$(git branch --show-current)')
    else:
        os.system(f'{env} bundle exec jekyll serve {args} --livereload --open-url')


if __name__ == "__main__":
    cli()
