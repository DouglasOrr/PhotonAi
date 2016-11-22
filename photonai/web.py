from flask_assets import Bundle, Environment
from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('player.html')


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
    app.run(host='0.0.0.0', debug=True,
            extra_files=["photonai/templates/player.html"])
