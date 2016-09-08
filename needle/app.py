import flask
import pkg_resources

app = flask.Flask('needle')


def mark_cached(response, time=600):
    response.add_etag()
    response.make_conditional(flask.request)

    response.headers['Cache-Control'] = 'max-age: %d' % time


def send_static_file(path, mimetype='text/html'):
    file_data = pkg_resources.resource_string('needle', 'static/index.html')

    response = flask.Response(
        status=200,
        mimetype=mimetype,
    )
    response.set_data(file_data)

    mark_cached(response)

    return response


@app.route('/')
def root():
    return send_static_file('static/index.html')
