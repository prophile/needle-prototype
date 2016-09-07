import flask
import pkg_resources

app = flask.Flask('needle')


@app.route('/')
def bees():
    return flask.send_file(
        pkg_resources.resource_stream('needle', 'index.html'),
        mimetype='text/html',
        conditional=True,
        cache_timeout=30,
    )
