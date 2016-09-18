import enum
import decimal
import hashlib
import datetime
import textwrap

@enum.unique
class UserClass(enum.Enum):
    EXISTING = 'existing'
    NEW = 'new'
    BOTH = 'both'


class Experiment:
    __slots__ = (
        'name',
        'description',
        'confidence',
        'site_area',
        'user_class',
        'start_date',
        'branches',
        'primary_kpi',
        'minimum_change',
        'secondary_kpis',
        'results',
    )

    def __init__(
        self,
        name,
        *,
        description='',
        confidence=0.95,
        site_area,
        user_class=UserClass.BOTH,
        start_date,
        branches,
        primary_kpi,
        minimum_change,
        secondary_kpis=()
    ):
        self.name = name
        self.description = description
        self.confidence = confidence
        self.site_area = site_area
        self.user_class = user_class
        self.start_date = start_date
        self.branches = branches
        self.primary_kpi = primary_kpi
        self.minimum_change = minimum_change
        self.secondary_kpis = secondary_kpis
        self.results = None

    def __repr__(self):
        return textwrap.dedent('''
        Experiment(
            name=%r,
            description=%r,
            confidence=%r,
            site_area=%r,
            user_class=%r,
            start_date=%r,
            branches=%r,
            primary_kpi=%r,
            minimum_change=%r,
            secondary_kpis=%r,
            results=%r,
        )''' % (
            self.name,
            self.description,
            self.confidence,
            self.site_area,
            self.user_class,
            self.start_date,
            self.branches,
            self.primary_kpi,
            self.minimum_change,
            self.secondary_kpis,
            self.results,
        )).strip()

    def __str__(self):
        if self.is_concluded:
            status = "concluded"
        elif self.is_in_progress:
            status = "in progress"
        else:
            status = "upcoming"

        return "<Experiment %r (%s)>" % (
            self.name,
            status,
        )

    @property
    def is_concluded(self):
        return self.results is not None

    @property
    def is_in_progress(self):
        return self.start_date <= datetime.date.today() and not self.is_concluded


class Branch:
    __slots__ = ('name', 'fraction', 'parameters')

    def __init__(self, name, *, fraction, parameters):
        self.name = name
        self.fraction = fraction
        self.parameters = parameters

    def __repr__(self):
        return 'Branch(name=%r, fraction=%r, parameters=%r)' % (
            self.name,
            self.fraction,
            self.parameters,
        )


def split_by_site_area(site_area, experiments):
    relevant_experiments = sorted((
        x
        for x in experiments
        if x.site_area == site_area
        and x.is_in_progress
    ), key=lambda x: x.start_date)

    split_point = 0

    # Done as a list rather than a generator due to exceptions needing to be
    # thrown later rather than yielding some elements first.

    splits = []

    for experiment in relevant_experiments:
        for branch in experiment.branches:
            split_point += branch.fraction
            splits.append((split_point, experiment, branch))

    if split_point > 1:
        raise RuntimeError(
            "Superunity experiment coverage in site area %r" % site_area,
        )

    return splits


def user_valid_for_experiment(signup_date, experiment):
    if (
        experiment.user_class == UserClass.EXISTING and
        signup_date >= experiment.start_date
    ):
        return False

    if (
        experiment.user_class == UserClass.NEW and
        signup_date < experiment.start_date
    ):
        return False

    return True


def user_experiments(user_id, signup_date, configuration):
    for site_area in configuration.site_areas:
        user_split = split_by_site_area(
            site_area,
            configuration.experiments,
        )

        hash_base = ('%s/%s' % (
            user_id,
            site_area,
        )).encode('utf-8')

        user_hash = int.from_bytes(
            hashlib.sha256(hash_base).digest(),
            byteorder='big',
        )
        precision = 2 ** 256

        user_hash /= precision

        for fraction, experiment, branch in user_split:
            if user_hash <= fraction:
                # User is in this group, verify validity

                if user_valid_for_experiment(signup_date, experiment):
                    yield experiment, branch

                break
