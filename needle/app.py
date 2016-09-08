import flask
import dateutil.parser
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


@app.route('/', methods=('GET',))
def root():
    return send_static_file('static/index.html')


@app.route('/user', methods=('GET',))
def lookup_user():
    try:
        user_id = int(flask.request.args['user-id'])
        signup_date = dateutil.parser.parse(
            flask.request.args['user-signup-date'],
        )
        site_area = flask.request.args['site-area']
    except (ValueError, KeyError):
        flask.abort(400)

    response = flask.jsonify({
        'user-id': user_id,
    })
    mark_cached(response, time=60)
    return response
