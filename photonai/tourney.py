'''Background runner for a tournament.
'''

import click
import random
import tempfile
import shutil
import os
import contextlib
import logging
import time

import photonai.config
import photonai.db
import photonai.run


DEFAULT_CONFIG = dict(
    db=None,
    replay_folder=None,
    maps=[
        'empty',
        'singleton',
        'orbital',
        'binary',
    ],
    time_limit=60,
    step_duration=0.01,
)


def load(bot):
    '''Load a bot spec with a 'script' key, and add a 'path' key.
    '''
    f = tempfile.NamedTemporaryFile()
    f.write(bot['script'].encode('utf8'))
    f.flush()
    bot['path'] = f.name
    return f


class NotEnoughBotsError(Exception):
    pass


def run(config):
    with contextlib.ExitStack() as stack:
        db = stack.enter_context(photonai.db.Session(**config['db']))

        # Randomly sample a game to play
        bots = db.sample_bots(2)
        if len(bots) < 2:
            raise NotEnoughBotsError
        bot_a, bot_b = bots
        stack.enter_context(load(bot_a))
        stack.enter_context(load(bot_b))
        map = random.choice(config['maps'])
        seed = random.randint(0, 2 ** 31)

        logging.debug('Playing %s (v%d) vs %s (v%d) on %s (seed %d)',
                      bot_a['name'], bot_a['version'],
                      bot_b['name'], bot_b['version'],
                      map, seed)

        # Play the game
        tmp_out = stack.enter_context(tempfile.NamedTemporaryFile())
        result = photonai.run.run_game(
            bots=[bot_a, bot_b],
            writer=photonai.run.AvroWriter(tmp_out),
            seed=seed,
            map=map,
            time_limit=config['time_limit'],
            step_duration=config['step_duration'])

        logging.debug('Winner %s', result.winner)

        # Save a record
        game_id = db.add_game(
            bot_a=bot_a['id'],
            bot_b=bot_b['id'],
            winner=(result.winner and {
                bot_a['name']: bot_a['id'],
                bot_b['name']: bot_b['id'],
            }[result.winner['name']]),
            map=map,
            seed=seed)

        logging.debug('Game %d: winner %s',
                      game_id, result.winner and result.winner['name'])

        # Save the replay
        if config['replay_folder'] is not None:
            tmp_out.flush()
            dest = os.path.join(config['replay_folder'],
                                '%d.avro' % game_id)
            logging.debug('Saving replay to %s', dest)
            if os.path.exists(dest):
                logging.severe('Replay for game %d already exists!', game_id)
            else:
                shutil.copyfile(tmp_out.name, dest)


@click.command('tourney')
@click.option('-c', '--config', type=click.Path(exists=True, dir_okay=False))
def cli(config):
    '''Start a worker to continuously run tournament games
    in the background.
    '''
    logging.basicConfig(
        format='%(levelname)s\t%(message)s',
        level=logging.DEBUG,
    )

    config = photonai.config.load(DEFAULT_CONFIG, config)
    if config['replay_folder'] is not None and \
       not os.path.exists(config['replay_folder']):
        os.makedirs(config['replay_folder'])

    while True:
        try:
            run(config)
        except NotEnoughBotsError:
            logging.debug('Not enough bots to run a game')
            time.sleep(10)


if __name__ == '__main__':
    cli()
