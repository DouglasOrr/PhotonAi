import click
import os
import sys
import fastavro.writer
import json
import numpy as np
from . import maps, schema, game, bot


_project_path = os.path.abspath(os.path.join(__file__, '../..'))


def _load_bot(path):
    return bot.SubprocessBot(
        ['env', 'PYTHONPATH=%s' % _project_path, 'python', path],
        stderr=sys.stderr)


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


def _write_avro(out, data, schema_):
    '''Write an avro file, careful to flush after terminating with an exception.
    '''
    with open(out, 'wb') as f:
        writer = fastavro.writer.Writer(f, schema_, codec='deflate')
        try:
            for datum in data:
                writer.write(datum)
        finally:
            writer.flush()


def _write_json(out, data):
    '''Write a jsonlines file.
    '''
    with open(out, 'w') as f:
        for datum in data:
            f.write(json.dumps(datum) + '\n')


def _infer_format(path):
    '''Try to guess if we're writing an Avro file or a jsonlines file
    (eagerly falls back to jsonlines).
    '''
    if path.endswith('avro'):
        return 'avro'
    else:
        return 'json'


@click.command()
@click.argument('bots', nargs=-1, type=click.Path(dir_okay=False, exists=True))
@click.argument('out', type=click.Path(writable=True))
@click.option('--format', type=click.Choice(('json', 'avro')), default=None,
              help='output file format')
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
@click.option('--time-limit', default=60.0,
              help='hard limit on the simulation time for a draw')
def run(bots, out, format, map,
        step_duration, seed, force, repeat_bots, time_limit):
    '''Run a single competitive game with some bots, and save the log.
    '''
    if (not force) and os.path.exists(out):
        raise click.ClickException(
            'Output file "%s" already exists - delete to proceed' % out)

    format = format or _infer_format(out)

    random = np.random.RandomState(seed)
    map = getattr(maps, map).Map(random.randint(2 ** 32))
    bots = [(dict(name=path, version=0), _load_bot(path))
            for path in bots
            for _ in range(repeat_bots)]
    random.shuffle(bots)

    steps = game.run_game(
        map_spec=map,
        controller_bots=bots,
        stop=_stop_condition(len(bots), time_limit),
        step_duration=step_duration)

    try:
        if format == 'avro':
            _write_avro(out, steps, schema.STEP)
        elif format == 'json':
            _write_json(out, steps)
        else:
            raise click.ArgumentException(
                'Unknown format "%s" (expected {json avro})' % format)
    except game.Stop as stop:
        sys.stderr.write('%s\n' % stop)
        click.echo(json.dumps(None
                              if stop.winner is None else
                              stop.winner['name']))


sys.argv[0] = 'photonai'
run()
