import numpy
import scipy.stats


def bernoulli(sql, connection, user_ids, prior):
    compound_sql = """
    SELECT
        SUM(sample :: integer) AS successes,
        COUNT(*) AS trials
    FROM (
        %s
    ) AS sq(sample)
    """ % sql

    result = connection.execute(compound_sql, users=user_ids)

    successes, trials = result.fetchone()

    return scipy.stats.beta(
        prior[0] + successes,
        prior[1] + trials - successes,
    ), trials
