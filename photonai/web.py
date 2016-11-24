from flask_assets import Bundle, Environment
import flask
import os
import fastavro
from flask import Flask, render_template

app = Flask(__name__)

replay_folder = os.path.abspath(
    os.path.join(__file__, '../static/.tmp/replays'))


@app.route('/')
def index():
    return render_template('player.html')


@app.route('/replay/<name>')
def replay(name):
    replay_file = flask.safe_join(replay_folder, '%s.avro' % name)

    with open(replay_file, 'rb') as f:
        return flask.json.jsonify(list(fastavro.reader(f)))


assets = Environment(app)
assets.register(dict(
    player_js=Bundle(
        'js/lib/jquery.js',
        'js/lib/bootstrap.js',
        'js/lib/avsc.js',
        output='gen/player.js'
    ),
    player_css=Bundle(
        'css/lib/bootstrap.css',
        'css/lib/bootstrap-theme.css',
        output='gen/player.css'
    ),
))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000,
            extra_files=['photonai/templates/player.html'])
