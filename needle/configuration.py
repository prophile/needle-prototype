import yaml
import logging

from .kpi import KPI
from .metrics import METRIC_FAMILIES
from .experiment import Experiment, Branch, UserClass

logger = logging.getLogger(__name__)


class Configuration:
    def __init__(self, path):
        self.path = path
        logger.info("Loading configuration from %s", self.path)
        logger.debug("Getting defaults")
        self.defaults = self._load_yaml('defaults.yaml')
        self.site_areas = set()

        logger.debug("Loading experiments")
        self._load_experiments()

        logger.debug("Loading KPIs")
        self._load_kpis()

    def _load_kpis(self):
        source = self._load_yaml('kpis.yaml')

        self.kpis = {}

        for name, kpi in source['kpis'].items():
            metric = METRIC_FAMILIES[kpi['metric']](kpi['prior'])

            self.kpis[name] = KPI(
                name=kpi['name'],
                description=kpi['description'],
                metric=metric,
                sql=kpi['sql'],
            )

        self.connection_string = source['connection']

        self.get_users_sql = source['get-users']

    def _load_experiments(self):
        source = self._load_yaml('experiments.yaml')

        self.experiments = []

        for experiment in source['experiments']:
            experiment_name = experiment['name']
            logger.info("Loading experiment %r", experiment_name)

            branches = []

            for branch in experiment['branches']:
                branches.append(Branch(
                    name=branch['name'],
                    fraction=branch['fraction'],
                    parameters=branch['parameters'],
                ))

            if not any(x.name == 'control' for x in branches):
                logger.error(
                    "Experiment %s defines no control branch",
                    experiment_name,
                )
                raise ValueError("No branch in %s" % experiment_name)

            if sum(x.fraction for x in branches) > 1:
                logger.error(
                    "Experiment %s defines superunity coverage",
                    experiment_name,
                )
                raise ValueError("Superunity coverage in %s" % experiment_name)

            site_area = experiment['site-area']

            self.experiments.append(Experiment(
                name=experiment_name,
                description=experiment.get('description', ""),
                confidence=experiment.get('confidence', 0.95),
                site_area=site_area,
                user_class=UserClass(experiment.get('user-class', 'both')),
                start_date=experiment['start-date'],
                branches=branches,
                primary_kpi=experiment['kpi'],
                minimum_change=experiment['minimum-change'],
                secondary_kpis=(),
            ))

            self.site_areas.add(site_area)

    def _load_yaml(self, filename):
        path = self.path / filename

        try:
            with path.open('r', encoding='utf-8') as f:
                return yaml.load(f)
        except IOError:
            logger.error("Could not load %s", filename)
            raise
