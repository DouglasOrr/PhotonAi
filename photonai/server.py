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
    return flask.render_template('layout.html')  # TODO


@app.route('/history')
def history():
    return flask.render_template('layout.html')  # TODO


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


@app.route('/player')
def player():
    return flask.render_template('player.html')


@app.route('/replay/<name>')
def replay(name):
    replay_file = flask.safe_join(app.config['REPLAY_FOLDER'],
                                  '%s.avro' % name)

    with open(replay_file, 'rb') as f:
        return flask.json.jsonify(list(fastavro.reader(f)))


DEFAULT_CONFIG = dict(
    port=5000,
    debug=True,
    db=None,
    replay_folder=None,
)


@click.command('server')
@click.option('-c', '--config', type=click.Path(exists=True, dir_okay=False))
def cli(config):
    '''Start a server to upload bots & show tournament results.
    '''
    config = photonai.config.load(DEFAULT_CONFIG, config)
    app.config['DATABASE'] = config['db']
    app.config['REPLAY_FOLDER'] = config['replay_folder']

    app.run(host='0.0.0.0',
            port=config['port'],
            debug=config['debug'],
            extra_files=os.listdir('photonai/templates'))


if __name__ == '__main__':
    cli()
