'''A web server for viewing tournament results and replays.
'''

import os
import fastavro
import flask
import io
import click
import photonai.config
import photonai.db


app = flask.Flask(__name__)


def get_db():
    db = getattr(flask.g, 'database', None)
    if db is None:
        db = flask.g.database = photonai.db.Session(**app.config['DATABASE'])
    return db


def replay_path(id):
    if app.config['REPLAY_PATH'] is not None:
        path = flask.safe_join(app.config['REPLAY_PATH'], '%d.avro' % id)
        if os.path.exists(path):
            return path


@app.teardown_appcontext
def close_db(exception):
    db = getattr(flask.g, 'database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    return flask.redirect('/leaderboard')


@app.route('/leaderboard')
def leaderboard():
    window = app.config['LEADERBOARD_WINDOW']
    return flask.render_template(
        'leaderboard.html',
        leaderboard=get_db().leaderboard(window),
        leaderboard_window=window
    )


@app.route('/history')
def history():
    n = app.config['HISTORY_LIMIT']
    history = get_db().history(n)
    for d in history:
        d['has_replay'] = replay_path(d['id']) is not None
    return flask.render_template(
        'history.html',
        history=history,
        history_limit=n)


@app.route('/uploader')
def uploader():
    return flask.render_template('uploader.html')


@app.route('/upload', methods=['POST'])
def upload():
    first_name = flask.request.form['first_name']
    last_name = flask.request.form['last_name']
    ai_name = flask.request.form['ai_name']
    full_name = '%s.%s:%s' % (first_name, last_name, ai_name)

    # have to assume we're UTF-8 here
    ai_file = io.TextIOWrapper(
        flask.request.files['ai_file'].stream,
        encoding='utf-8'
    ).read()

    get_db().upload(full_name, ai_file)

    return flask.redirect('/leaderboard')


@app.route('/player', defaults=dict(id=None))
@app.route('/player/<id>')
def player(id):
    return flask.render_template('player.html', game_id=id)


@app.route('/replay/<int:id>')
def replay(id):
    with open(replay_path(id), 'rb') as f:
        return flask.json.jsonify(list(fastavro.reader(f)))


@app.route('/doc/<path:path>')
def doc(path):
    return flask.send_from_directory('static/doc', path)


DEFAULT_CONFIG = dict(
    port=5000,
    debug=True,
    db=None,
    replay_folder=None,
    leaderboard_window=100,
    history_limit=200,
)


@click.command('server')
@click.option('-c', '--config', type=click.Path(exists=True, dir_okay=False))
def cli(config):
    '''Start a server to upload bots & show tournament results.
    '''
    config = photonai.config.load(DEFAULT_CONFIG, config)
    app.config['DATABASE'] = config['db']
    app.config['REPLAY_PATH'] = os.path.abspath(config['replay_folder'])
    app.config['LEADERBOARD_WINDOW'] = config['leaderboard_window']
    app.config['HISTORY_LIMIT'] = config['history_limit']

    if config['debug']:
        # Workzeug
        app.run(host='0.0.0.0',
                port=config['port'],
                debug=True,
                extra_files=os.listdir(os.path.join(
                    os.path.dirname(__file__),
                    'templates')))
    else:
        # gevent
        import gevent.wsgi
        http_server = gevent.wsgi.WSGIServer(('', config['port']), app)
        http_server.serve_forever()


if __name__ == '__main__':
    cli()
