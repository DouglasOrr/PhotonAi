import click
import os
import sys
import fastavro.writer
from . import maps, schema, game, bot


_project_path = os.path.abspath(os.path.join(__file__, '../..'))


def _load_bot(path):
    return dict(name=path,
                version=0,
                bot=bot.SubprocessBot(
                    ['env', 'PYTHONPATH=%s' % _project_path,
                     'python', path],
                    stderr=sys.stderr))


@click.command()
@click.argument('bots', nargs=-1, type=click.Path(dir_okay=False, exists=True))
@click.argument('out', type=click.Path(writable=True))
@click.option('-m', '--map', type=click.STRING, default='singleton')
@click.option('-s', '--step-duration', type=click.FLOAT, default=0.1)
def run(bots, out, map, step_duration):
    '''Run a single competitive game with two bots, and save the log.
    '''
    steps = game.game(
        map_spec=getattr(maps, map),
        controller_bots=[_load_bot(bot) for bot in bots],
        step_duration=step_duration)

    with open(out, 'wb') as f:
        fastavro.writer.writer(f, schema.STEP, steps)


run()
