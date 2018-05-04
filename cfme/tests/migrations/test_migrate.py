from cfme.utils.appliance.implementations.ui import navigate_to
from cfme.migrations.overview import MigrationsOverview


def test_dummy():
    overview = MigrationsOverview

    view = navigate_to(overview, 'All')
    view.create_mapping_button.click()

    view = navigate_to(overview, 'All')
    view.create_plan_button.click()
