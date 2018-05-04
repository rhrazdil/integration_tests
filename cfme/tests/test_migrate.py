from cfme.utils.appliance.implementations.ui import navigate_to
from cfme.migrations.overview import MigrationsOverview


def test_dummy():
    overview = MigrationsOverview
    view = navigate_to(overview, 'All')
