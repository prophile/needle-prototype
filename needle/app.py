import flask
import dateutil.parser
import functools
import pkg_resources

from .experiment import user_experiments


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
    except (ValueError, KeyError):
        flask.abort(400)

    config = get_configuration()

    experiment_parameters = dict(config.defaults)

    debug_experiments = []

    for experiment, branch in user_experiments(
        user_id=user_id,
        signup_date=signup_date,
        configuration=config,
    ):
        experiment_parameters.update(branch.parameters)
        debug_experiments.append({
            'site-area': experiment.site_area,
            'experiment': experiment.name,
            'branch': branch.name,
        })

    response = flask.jsonify({
        'user-id': user_id,
        'debug-experiments': debug_experiments,
        **experiment_parameters,
    })
    mark_cached(response, time=60)
    return response
