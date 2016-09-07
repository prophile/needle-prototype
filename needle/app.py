import flask
import pkg_resources

app = flask.Flask('needle')


def send_static_file(path, mimetype='text/html'):
    file_data = pkg_resources.resource_string('needle', 'static/index.html')

    response = flask.Response(
        status=200,
        mimetype=mimetype,
    )

    response.set_data(file_data)

    response.add_etag()
    response.make_conditional(flask.request)

    response.headers['Cache-Control'] = 'max-age: 30'

    return response


@app.route('/')
def bees():
    return send_static_file('static/index.html')