from cfme.base.login import BaseLoggedInPage
from widgetastic.widget import View
from widgetastic_patternfly import Button


class MigrationsOverviewView(BaseLoggedInPage):
    create_mapping_button = Button('Create Infrastructure Mapping')
    create_plan_button = Button('Create Migration Plan')

    @property
    def is_displayed(self):
        return self.navigation.currently_selected == ['Compute', 'Migration', 'Overview']


class InfrastructureMappingView(View):
    pass

