""" A model of a migration in CFME

"""
import attr
from navmazing import NavigateToAttribute, NavigateToSibling
from cfme.modeling.base import BaseCollection, BaseEntity, parent_of_type
from cfme.utils.appliance.implementations.ui import navigator, CFMENavigateStep, navigate_to
from cfme.utils.wait import wait_for
from widgetastic.widget import View
from views import InfrastructureMappingView


@attr.s
class InfrastructureMapping(BaseEntity):
    """Class representing v2v infrastructure mappings"""
    category = 'migration'
    string_name = 'Migration'


@attr.s
class InfrastructureMappingCollection(BaseCollection):
    """Collection object for Migration mapping object"""
    ENTITY = InfrastructureMapping


@navigator.register(InfrastructureMappingCollection, 'All')
class All(CFMENavigateStep):
    VIEW = InfrastructureMappingView
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self):
        self.prerequisite_view.navigation.select('Compute', 'Migration', 'Infrastructure Mappings')

    def resetter(self):
        """Reset the view"""
        self.view.browser.refresh()


