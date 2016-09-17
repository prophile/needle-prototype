import math
import numpy
import scipy.stats
import collections


DistributionDescription = collections.namedtuple('DistributionDescription', (
    'mean',
    'std',
    'skewness',
    'percentiles',
))


def describe_scipy_distribution(distribution):
    mean, var, skew = distribution.stats('mvs')

    ppf = distribution.ppf

    return DistributionDescription(
        mean=float(mean),
        std=numpy.sqrt(var),
        skewness=float(skew),
        percentiles=tuple(
            float(ppf(x / 100))
            for x in range(101)
        ),
    )


def describe_empirical_distribution(data):
    mean = numpy.mean(data)
    std = numpy.std(data)
    skew = scipy.stats.skew(data)

    return DistributionDescription(
        mean=mean,
        std=std,
        skewness=skew,
        percentiles=tuple(
            numpy.percentile(data, x)
            for x in range(101)
        ),
    )


class Metric(object):
    name = NotImplemented

    def __init__(self, prior):
        pass

    def evaluate(self, user_ids, sql, run_query):
        samples = self.get_samples(user_ids, sql, run_query)

        return self.analyse_samples(samples), len(samples)

    def get_samples(self, user_ids, sql, run_query):
        return numpy.array([
            x
            for (x,) in run_query(
                sql,
                users=user_ids,
            )
        ])

    def analyse_samples(self, samples):
        raise NotImplementedError("Must implement `analyse_samples`")


class BernoulliMetric(Metric):
    name = "Bernoulli"

    def __init__(self, prior):
        self.prior_alpha = prior['alpha']
        self.prior_beta = prior['beta']

    def analyse_samples(self, samples):
        counts = collections.Counter(samples.astype(bool))

        return describe_scipy_distribution(scipy.stats.beta(
            self.prior_alpha + counts[True],
            self.prior_beta + counts[False],
        ))


class BootstrapMetric(Metric):
    NBOOTSTRAPS = 10000

    def __init__(self, prior):
        self.seed_samples = prior

    def analyse_samples(self, samples):
        sample_db = numpy.append(samples, self.seed_samples)

        bootstraps = numpy.array([
            self.statistic(numpy.random.choice(
                sample_db,
                len(sample_db),
                replace=True,
            ))
            for x in range(self.NBOOTSTRAPS)
        ])

        return describe_empirical_distribution(bootstraps)

    def statistic(self, data):
        raise NotImplementedError("Must implement `statistic`")


class MedianBootstrapMetric(BootstrapMetric):
    name = "Median (bootstrap)"

    def statistic(self, data):
        return numpy.median(data.astype(float))


METRIC_FAMILIES = {
    'bernoulli': BernoulliMetric,
    'median_bootstrap': MedianBootstrapMetric,
}


BranchEvaluation = collections.namedtuple('BranchEvaluation', (
    'posterior',
    'sample_size',
    'p_positive',
    'p_negative',
))


def calculate_prob_improvement(
    reference,
    test,
    minimum_effect_size=0,
):
    # Assume a normal approximation here
    minimum_effect_negative_tail = minimum_effect_size < 0
    minimum_effect_size = abs(minimum_effect_size)

    mean_diff_above = test.mean - (reference.mean + minimum_effect_size)
    mean_diff_below = test.mean - (reference.mean - minimum_effect_size)

    std_diff = math.hypot(reference.std, test.std)

    prob_test_below = 1 - scipy.stats.norm.cdf(
        mean_diff_below / std_diff,
    )
    prob_test_above = 1 - scipy.stats.norm.cdf(
        -mean_diff_above / std_diff,
    )

    if minimum_effect_negative_tail:
        return prob_test_below, prob_test_above
    else:
        return prob_test_above, prob_test_below


def evaluate_metric(
    branches,
    metric,
    sql,
    run_query,
    minimum_effect_size=0,  # Positive for > tail, negative for < tail
    control_branch='control',
):
    # Branches are a dict of branch names to user ID tuples.
    # 2 stage: first calculate all branches, the annotate with p_positive and
    # p_negative.

    # Stage 1: Metric evaluation
    def describe_branch(users):
        posterior, samples = metric.evaluate(tuple(users), sql, run_query)
        return BranchEvaluation(
            posterior=posterior,
            sample_size=samples,
            p_positive=None,
            p_negative=None,
        )

    results = {
        branch_id: describe_branch(branch_users)
        for branch_id, branch_users in branches.items()
    }

    # Stage 2: improvement annotations
    control_posterior = results[control_branch].posterior

    for branch in branches:
        if branch == control_branch:
            continue

        branch_posterior = results[branch].posterior

        p_positive, p_negative = calculate_prob_improvement(
            control_posterior,
            branch_posterior,
            minimum_effect_size,
        )

        results[branch] = results[branch]._replace(
            p_positive=p_positive,
            p_negative=p_negative,
        )

    return results
