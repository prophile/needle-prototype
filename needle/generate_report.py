import math
import scipy.stats
import logging
import sqlalchemy

from . import metrics
from .experiment import user_experiments, Tail


logger = logging.getLogger(__name__)


def difference_probabilities(control_dist, test_dist, minimum_effect):
    """
    Computes the probability that a sample from the test distribution is less
    than / greater than a sample from the control distribution by at least
    the minimum_effect size, assuming a normal approximation to both.
    """
    mean_diff_above = test_dist.mean() - (control_dist.mean() + minimum_effect)
    mean_diff_below = test_dist.mean() - (control_dist.mean() - minimum_effect)
    var_diff = control_dist.var() + test_dist.var()
    prob_test_below = 1 - scipy.stats.norm().cdf(
        mean_diff_below / math.sqrt(var_diff),
    )
    prob_test_above = 1 - scipy.stats.norm().cdf(
        -mean_diff_above / math.sqrt(var_diff),
    )
    return prob_test_below, prob_test_above


def generate_report(experiment, configuration):
    logger.info("Generating report on experiment %r", experiment.name)

    db = sqlalchemy.create_engine(
        configuration._tmp_metric_config['connection'],
    )

    logger.debug("Indexing all users")
    users_by_branch = {x: set() for x in experiment.branches}

    for user_id, join_date in db.execute(
        configuration._tmp_metric_config['get-users'],
    ):
        experiments = user_experiments(user_id, join_date, configuration)

        for user_experiment, user_branch in experiments:
            if user_experiment.name == experiment.name:
                users_by_branch[user_branch].add(user_id)

    for branch, branch_users in users_by_branch.items():
        logger.debug(
            "In branch %r: %d users",
            branch.name,
            len(branch_users),
        )

    primary_metric_config = configuration._tmp_metric_config['metrics'][
        experiment.primary_metric
    ]
    logger.debug("Evaluating %s", primary_metric_config['name'])

    evaluator = getattr(metrics, primary_metric_config['type'])

    stats_by_branch = {}

    for branch, branch_users in users_by_branch.items():
        logger.debug("branch %r", branch.name)
        posterior, samples = evaluator(
            primary_metric_config['sql'],
            db,
            tuple(branch_users),
            primary_metric_config['prior'],
        )
        logger.debug(
            " => %d samples, posterior mean=%f median=%f std=%f 95CR=%s",
            samples,
            posterior.mean(),
            posterior.median(),
            posterior.std(),
            posterior.interval(0.95),
        )
        stats_by_branch[branch] = posterior

    for branch, stats in stats_by_branch.items():
        if branch.name == 'control':
            control_posterior = stats

    # Forgive the frequentism
    logger.debug("Computing Bayesian difference probabilities")

    for branch, stats in stats_by_branch.items():
        if branch.name == 'control':
            continue

        prob_below, prob_above = difference_probabilities(
            control_posterior,
            stats,
            experiment.minimum_change,
        )

        if experiment.tail == Tail.LESS:
            prob_success = prob_below
            prob_failed = prob_above
        elif experiment.tail == Tail.GREATER:
            prob_success = prob_above
            prob_failed = prob_below
        else:
            prob_success = prob_below + prob_above
            prob_failed = 0

        if prob_success > experiment.confidence:
            logger.info("*** Experiment is positive")
        elif prob_failed > experiment.confidence:
            logger.info("*** Experiment is negative")

        logger.debug(
            "Branch %r p+ve=%f p-ve=%f",
            branch.name,
            prob_success,
            prob_failed,
        )
