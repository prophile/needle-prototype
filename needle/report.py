import logging
import sqlalchemy

from .metrics import evaluate_metric
from .experiment import user_experiments

logger = logging.getLogger(__name__)


def evaluate_report(experiment, configuration):
    logger.debug("Connecting to DB")
    db_connection = sqlalchemy.create_engine(
        configuration.connection_string,
    )

    users_by_branch = {
        x.name: set()
        for x in experiment.branches
    }

    run_query = db_connection.execute

    logger.debug("Enumerating users")
    for user_id, signup_date in run_query(configuration.get_users_sql):
        for user_experiment, experiment_branch in user_experiments(
            user_id,
            signup_date,
            configuration,
        ):
            if user_experiment == experiment:
                users_by_branch[experiment_branch.name].add(user_id)

    def run_kpi(kpi_name, minimum_effect_size=0):
        kpi = configuration.kpis[kpi_name]

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
            'data': metric_data,
        }

    return {
        'experiment': experiment.name,
        'start_date': experiment.start_date,
        'primary': run_kpi(experiment.primary_kpi),
        'secondaries': [
            run_kpi(x)
            for x in experiment.secondary_kpis
        ],
    }
