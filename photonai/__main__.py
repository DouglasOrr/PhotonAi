import click
import os
import sys
import fastavro.writer
import numpy as np
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
@click.option('-m', '--map', type=click.STRING, default='singleton',
              show_default=True, help='name of a photonai.maps map to use')
@click.option('-s', '--step-duration', type=click.FLOAT, default=0.01,
              show_default=True, help='simulation timestep')
@click.option('--seed', type=click.INT,
              help='random seed to use for map generation')
@click.option('-f', '--force', is_flag=True,
              help='replace the output file automatically')
@click.option('--repeat-bots', default=1,
              help='number of times to repeat the botlist')
def run(bots, out, map, step_duration, seed, force, repeat_bots):
    '''Run a single competitive game with some bots, and save the log.
    '''
    if (not force) and os.path.exists(out):
        raise click.ClickException(
            'Output file "%s" already exists - delete to proceed' % out)

    random = np.random.RandomState(seed)
    seed = random.randint(2 ** 32)

    bots = [_load_bot(bot)
            for bot in bots
            for _ in range(repeat_bots)]
    random.shuffle(bots)

    steps = game.game(
        map_spec=getattr(maps, map).Map(seed),
        controller_bots=bots,
        step_duration=step_duration)

    with open(out, 'wb') as f:
        fastavro.writer.writer(f, schema.STEP, steps, codec='deflate')


sys.argv[0] = 'photonai'
run()
