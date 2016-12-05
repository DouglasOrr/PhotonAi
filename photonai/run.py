'''Utility for running a single game.
'''

import click
import os
import sys
import fastavro.writer
import json
import contextlib
import numpy as np
import photonai.maps
import photonai.bot
import photonai.schema
from . import game


_project_path = os.path.abspath(os.path.join(__file__, '../..'))


def load_bot(path):
    path = os.path.join(os.environ.get('HOST_ROOT'), path)
    return photonai.bot.DockerPythonBot(
        path, 'photonai:latest', stderr=sys.stderr)


def _stop_condition(nbots, time_limit):
    '''Infer the appropriate stop condition from the number of starting bots,
    whether running a pure simulation (0 bots), playground (1 bot), or battle
    (2+ bots).
    '''
    if nbots == 0:
        return game.stop_after(time_limit)
    else:
        return game.stop_when_any(
            (game.stop_when_no_ships()
             if nbots == 1 else
             game.stop_when_one_ship()),
            game.stop_after(time_limit)
        )


class NothingWriter:
    def __call__(self, data):
        # Still have to exhaust the iterator
        for d in data:
            pass


class AvroWriter:
    '''Write results to an Avro file, careful to flush after terminating with
    an exception.
    '''
    def __init__(self, f):
        self.f = f

    def __call__(self, data):
        writer = fastavro.writer.Writer(
            self.f, photonai.schema.STEP, codec='deflate')
        try:
            for datum in data:
                writer.write(datum)
        finally:
            writer.flush()


class JsonWriter:
    '''Write results to a json file.
    '''
    def __init__(self, f):
        self.f = f

    def __call__(self, data):
        for datum in data:
            self.f.write(json.dumps(datum) + '\n')


def run_game(bots, map, writer, seed, time_limit, step_duration):
    '''Run a game (randomly but repeatedly set up based on `seed`).

    bots -- a list of bots as per photonai.game.run_game
    '''
    random = np.random.RandomState(seed)
    map = getattr(photonai.maps, map).Map(random.randint(2 ** 32))
    bots = bots.copy()
    random.shuffle(bots)

    steps = game.run_game(
        map_spec=map,
        controller_bots=bots,
        stop=_stop_condition(len(bots), time_limit),
        step_duration=step_duration)
    try:
        writer(steps)
    except game.Stop as stop:
        return stop
    assert False, 'game ended without raising Stop'


DEFAULT_CONFIG = dict(
    bots=[],
    out=None,
    maps=['singleton'],
    step_duration=0.01,
    seed=None,
    force=False,
    repeat_bots=1,
    time_limit=60.0,
)


@click.command('run')
@click.option('-c', '--config', type=click.Path(exists=True, dir_okay=False),
              help='configuration file specifying any of these options')
@click.option('-b', '--bots', multiple=True,
              type=click.Path(dir_okay=False, exists=True),
              help='paths to Python scripts to use as bots')
@click.option('-o', '--out', type=click.Path(writable=True),
              help='path to save log file for processing')
@click.option('-m', '--maps', type=click.STRING, multiple=True,
              help='names of photonai.maps to select from')
@click.option('-t', '--step-duration', type=click.FLOAT,
              help='simulation timestep')
@click.option('-s', '--seed', type=click.INT,
              help='random seed to use for map generation')
@click.option('-f', '--force', is_flag=True,
              help='replace the output file automatically')
@click.option('-n', '--repeat-bots', default=1,
              help='number of times to repeat the botlist')
@click.option('-l', '--time-limit', default=60.0,
              help='hard limit on the simulation time for a draw')
def cli(config, **args):
    '''Run a single competitive game with some bots, and save the log.
    '''
    config = photonai.config.load(DEFAULT_CONFIG, config, args)
    if len(config['maps']) == 0:
        config['maps'] = DEFAULT_CONFIG['maps']

    if (not config['force']) and (config['out'] is not None) and \
       os.path.exists(config['out']):
        raise click.ClickException(
            'Output file "%s" already exists - delete to proceed' %
            config['out'])

    with contextlib.ExitStack() as stack:
        if config['out'] is None:
            writer = NothingWriter()
        elif config['out'].endswith('avro'):
            writer = AvroWriter(stack.enter_context(open(config['out'], 'wb')))
        else:
            writer = JsonWriter(stack.enter_context(open(config['out'], 'w')))

        bots = [(dict(name=path, version=0),
                 stack.enter_context(load_bot(path)))
                for path in config['bots']
                for _ in range(config['repeat_bots'])]

        map = np.random.RandomState(config['seed']).choice(config['maps'])

        result = run_game(bots=bots, writer=writer, map=map,
                          **photonai.config.select(
                              config,
                              'seed', 'time_limit', 'step_duration'))

        sys.stderr.write('%s\n' % result)
        click.echo(json.dumps(result.winner and result.winner['name']))


if __name__ == '__main__':
    cli()
