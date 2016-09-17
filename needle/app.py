import json
import aiohttp.web
import asyncio
import logging
import dateutil.parser
import functools
import concurrent.futures
import pkg_resources

from .experiment import user_experiments


logger = logging.getLogger(__name__)


current_results = {}


def get_configuration(request):
    from .configuration import Configuration  # Lazy-load
    return Configuration(request.app['root'])


def send_static_file(path, mimetype='text/html', cache=True, headers={}):
    file_data = pkg_resources.resource_string('needle', path)

    if cache:
        headers = {
            **headers,
            'Cache-Control': 'max-age: 600',
        }

    return aiohttp.web.Response(
        status=200,
        content_type=mimetype,
        body=file_data,
        headers=headers,
    )


async def site_root(request):
    return send_static_file('templates/index.html')


async def experiments(request):
    return aiohttp.web.Response(
        status=200,
        headers={
            'Cache-Control': 'max-age: 60',
            'Link': '</>; rel=index',
        },
        content_type='application/json',
        body=json.dumps(current_results, indent=2).encode('utf-8'),
    )


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
        headers={
            'Cache-Control': 'max-age: 60',
            'Link': '</>; rel=index',
        },
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
    app.router.add_route('GET', '/experiments', experiments)
    app['root'] = root
    return app


def bg_run_reports(path):
    from .report import run_all_reports  # Lazy load
    from .configuration import Configuration  # Lazy-load
    import logging
    logging.basicConfig(level=logging.DEBUG)
    config = Configuration(path)
    return run_all_reports(config)


def bg_reports_task(loop, path):
    executor = concurrent.futures.ProcessPoolExecutor()
    future = loop.run_in_executor(executor, bg_run_reports, path)

    def done_a_thing(x):
        current_results.update(x.result())
        loop.call_later(30, bg_reports_task, loop, path)
    future.add_done_callback(done_a_thing)


def run(root, *, host='::', port=1212, debug=False):
    app = get_app(root, debug=debug)

    loop = asyncio.get_event_loop()

    server = loop.create_server(
        app.make_handler(),
        host,
        port,
    )
    loop.run_until_complete(server)

    loop.call_soon(bg_reports_task, loop, root)

    loop.run_forever()
