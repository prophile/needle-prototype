import json
import aiohttp.web
import logging
import dateutil.parser
import functools
import pkg_resources

from .experiment import user_experiments


logger = logging.getLogger(__name__)


def get_configuration(request):
    from .configuration import Configuration  # Lazy-load
    return Configuration(request.app['root'])


def send_static_file(path, mimetype='text/html'):
    file_data = pkg_resources.resource_string('needle', 'static/index.html')

    headers = {'Cache-Control': 'max-age: 600'}

    return aiohttp.web.Response(
        status=200,
        content_type=mimetype,
        body=file_data,
        headers=headers,
    )


async def site_root(request):
    return send_static_file('static/index.html')


async def lookup_user(request):
    try:
        user_id = int(request.GET['user-id'])
        signup_date = dateutil.parser.parse(
            request.GET['user-signup-date'],
        )
    except (ValueError, KeyError):
        return aiohttp.web.Response(
            status=400,
            content_type='text/plain',
            text="Bad request",
        )

    config = get_configuration(request)

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

    response = {
        'user-id': user_id,
        'debug-experiments': debug_experiments,
        **experiment_parameters,
    }

    return aiohttp.web.Response(
        status=200,
        headers={'Cache-Control': 'max-age: 60'},
        content_type='application/json',
        body=json.dumps(response).encode('utf-8'),
    )


def get_app(root, *, debug=False):
    app = aiohttp.web.Application(
        logger=logger,
        debug=debug,
    )
    app.router.add_route('GET', '/', site_root)
    app.router.add_route('GET', '/user', lookup_user)
    app['root'] = root
    return app


def run(root, *, host='::', port=2121, debug=False):
    app = get_app(root, debug=debug)

    aiohttp.web.run_app(
        app,
        host=host,
        port=port,
    )
