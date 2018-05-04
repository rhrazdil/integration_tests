from cfme.base.login import BaseLoggedInPage
from widgetastic.widget import View
# from widgetastic_manageiq import Button
from widgetastic_patternfly import Button


class MigrationsOverviewView(BaseLoggedInPage):
    mapping = Button('Create Infrastructure Mapping')
    plan = Button('Create Migration Plan')

    @property
    def is_displayed(self):
        return self.navigation.currently_selected == ['Compute', 'Migration', 'Overview']


class InfrastructureMappingView(View):
    pass

