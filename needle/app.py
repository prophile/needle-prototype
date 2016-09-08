import flask
import dateutil.parser
import functools
import pkg_resources

from .experiment import user_experiment


app = flask.Flask('needle')


@functools.lru_cache(maxsize=1)
def get_configuration():
    from .configuration import Configuration  # Lazy-load
    return Configuration(app.config['ROOT'])


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

    config = get_configuration()

    experiment, branch = user_experiment(
        user_id=user_id,
        signup_date=signup_date,
        site_area=site_area,
        experiments=config.experiments,
    )

    if branch is not None:
        experiment_parameters = {
            'debug-experiment': experiment.name,
            'debug-branch': branch.name,
            **branch.parameters,
        }
    else:
        experiment_parameters = {
            'debug-experiment': None,
            'debug-branch': None,
        }

    response = flask.jsonify({
        'user-id': user_id,
        **config.defaults,
        **experiment_parameters,
    })
    mark_cached(response, time=60)
    return response
