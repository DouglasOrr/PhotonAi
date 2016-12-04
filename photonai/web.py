import os
import fastavro
import flask
import io
import click
import yaml


app = flask.Flask(__name__)

SETTINGS = dict(
    replay_folder=os.path.abspath(
        os.path.join(__file__, '../static/.tmp/replays')),
    db=None
)


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

    SETTINGS['db'].upload(full_name, ai_file)

    return flask.redirect('/leaderboard')


@app.route('/player')
def player():
    return flask.render_template('player.html')


@app.route('/replay/<name>')
def replay(name):
    replay_file = flask.safe_join(SETTINGS['replay_folder'], '%s.avro' % name)

    with open(replay_file, 'rb') as f:
        return flask.json.jsonify(list(fastavro.reader(f)))


DEFAULT_CONFIG = dict(
    port=5000,
    debug=True,
)


@click.command()
@click.option('-c', '--config', type=click.Path(exists=True, dir_okay=False))
def cli(config):
    config_values = DEFAULT_CONFIG.copy()
    if config is not None:
        with open(config, 'r') as f:
            config_values.update(yaml.load(f.read()))

    if 'db' in config_values:
        import photonai.db
        SETTINGS['db'] = photonai.db.Session(**config_values['db'])

    app.run(host='0.0.0.0',
            port=config_values['port'],
            debug=config_values['debug'],
            extra_files=os.listdir('photonai/templates'))


if __name__ == '__main__':
    cli()
