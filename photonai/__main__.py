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


def _replace_key(d, key, value):
    d = d.copy()
    d[key] = value
    return d


def _dedupe_schema(schema, names):
    if type(schema) == list:
        # enum
        return [_dedupe_schema(e, names) for e in schema]
    elif type(schema) == dict:
        if schema['type'] == 'array':
            return _replace_key(schema, 'items',
                                _dedupe_schema(schema['items'], names))
        elif schema['type'] == 'map':
            return _replace_key(schema, 'values',
                                _dedupe_schema(schema['values'], names))
        elif schema['type'] == 'record':
            # only support qualified names everywhere - simpler!
            name = '%s.%s' % (schema['namespace'], schema['name'])
            if name in names:
                return name
            else:
                schema = schema.copy()
                schema['fields'] = [
                    _replace_key(
                        f, 'type', _dedupe_schema(f['type'], names))
                    for f in schema['fields']]
                names[name] = schema
                return schema
        else:
            raise ValueError('Unexpected type %s' % schema['type'])
    else:
        return schema


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
@click.option('--time-limit', default=60.0,
              help='hard limit on the simulation time for a draw')
def run(bots, out, map, step_duration, seed, force, repeat_bots, time_limit):
    '''Run a single competitive game with some bots, and save the log.
    '''
    import copy
    # foo = copy.deepcopy(schema.STEP)
    # repo = fastavro._schema.SCHEMA_DEFS.copy()
    # fastavro._schema.populate_schema_defs(foo, repo)
    print("------------------------------------------------------------")
    print(schema.STEP)
    print("------------------------------------------------------------")
    print(_dedupe_schema(schema.STEP, {}))
    print("------------------------------------------------------------")

    if (not force) and os.path.exists(out):
        raise click.ClickException(
            'Output file "%s" already exists - delete to proceed' % out)

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

    with open(out, 'wb') as f:
        try:
            writer = fastavro.writer.Writer(f,
                                            _dedupe_schema(schema.STEP, {}),
                                            codec='deflate')
            for step in steps:
                writer.write(step)
        except game.Stop as stop:
            sys.stderr.write('%s\n' % stop)
            print(json.dumps(None
                             if stop.winner is None else
                             stop.winner['name']))
        finally:
            writer.flush()


sys.argv[0] = 'photonai'
run()
