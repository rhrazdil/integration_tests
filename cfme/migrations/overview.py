""" A model of a migration overview page

"""
from navmazing import NavigateToSibling, NavigateToAttribute
from cfme.utils.appliance.implementations.ui import CFMENavigateStep, navigator
from cfme.utils.appliance import Navigatable
from views import MigrationsOverviewView


class MigrationsOverview(Navigatable):
    pass


@navigator.register(MigrationsOverview, 'All')
class All(CFMENavigateStep):
    VIEW = MigrationsOverviewView
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self):
        self.prerequisite_view.navigation.select('Compute', 'Migration', 'Overview')
