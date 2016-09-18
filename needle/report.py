import logging
import datetime
import sqlalchemy

from .metrics import evaluate_metric
from .experiment import user_experiments

logger = logging.getLogger(__name__)


def run_all_reports(configuration):
    logger.info("Running all reports")
    now = datetime.date.today()

    reports = {}

    for experiment in configuration.experiments:
        if experiment.start_date > now or experiment.results is not None:
            continue

        reports[experiment.name] = evaluate_report(experiment, configuration)

    logger.info("Finished running reports")

    return reports


def get_recommendation(kpi_result):
    non_control_branches = [
        branch
        for branch_name, branch in kpi_result['data'].items()
        if branch_name != 'control'
    ]

    if (
        all(x['p_negative'] < 0.05 for x in non_control_branches) or
        any(x['p_positive'] > 0.95 for x in non_control_branches)
    ):
        return "conclude"

    return "continue"


def evaluate_report(experiment, configuration):
    logging.info("Reporting on %s", experiment.name)
    logger.debug("Connecting to DB")
    db_connection = sqlalchemy.create_engine(
        configuration.connection_string,
    )

    users_by_branch = {
        x.name: set()
        for x in experiment.branches
    }

    def run_query(x, *args, **kwargs):
        return list(db_connection.execute(x, *args, **kwargs))

    logger.debug("Enumerating users")
    for user_id, signup_date in run_query(configuration.get_users_sql):
        for user_experiment, experiment_branch in user_experiments(
            user_id,
            signup_date,
            configuration,
        ):
            if user_experiment == experiment:
                users_by_branch[experiment_branch.name].add(user_id)

    for branch in experiment.branches:
        logger.debug("%s: %d", branch.name, len(users_by_branch[branch.name]))

    def run_kpi(kpi_name, minimum_effect_size=0):
        kpi = configuration.kpis[kpi_name]

        logger.debug("Running KPI %s", kpi.name)

        metric_data = evaluate_metric(
            users_by_branch,
            kpi.metric,
            kpi.sql,
            run_query,
            minimum_effect_size=minimum_effect_size,
        )

        return {
            'kpi': kpi.name,
            'description': kpi.description,
            'model': kpi.metric.name,
            'data': {
                branch: {
                    'p_positive': metrics.p_positive,
                    'p_negative': metrics.p_negative,
                    'sample_size': metrics.sample_size,
                    'posterior': metrics.posterior._asdict(),
                }
                for branch, metrics in metric_data.items()
            },
        }

    primary_kpi_result = run_kpi(experiment.primary_kpi)

    return {
        'experiment': experiment.name,
        'description': experiment.description,
        'start_date': str(experiment.start_date),
        'primary': primary_kpi_result,
        'recommendation': get_recommendation(primary_kpi_result),
        'secondaries': [
            run_kpi(x)
            for x in experiment.secondary_kpis
        ],
    }
