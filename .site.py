#!/bin/python3
import os
import uuid

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


@click.option('--drafts/--no-drafts', is_flag=True, default=True,
              help='Include draft and future posts.')
@click.option('--fast/--no-fast', is_flag=True, default=True,
              help='Don\'t render the full site to speed up build times.')
@click.option('--live', '-l', is_flag=True, default=False,
              help='Serve on a live staging instance.')
@click.option('--expires', default='1d',
              help='Staging channel expiration. Only used when --live is set.')
@cli.command()
def serve(drafts, fast, live, expires):
    """
    Deploy the site.
    """

    args = '--future --drafts' if drafts else ''

    if live:
        os.system(f'JEKYLL_ENV=production bundle exec jekyll build {args}')
        # Run twice for image gen
        os.system(f'JEKYLL_ENV=production bundle exec jekyll build {args}')

        os.system(f'firebase hosting:channel:deploy -e {expires} {uuid.uuid1()}')
    else:
        if fast:
            args += ' --limit-posts 3 --config "_config.yml,_config_dev.yml"'

        os.system(f'bundle exec jekyll serve {args} --livereload')


if __name__ == "__main__":
    cli()
