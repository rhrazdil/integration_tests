from cfme.common import Taggable
from cfme.fixtures import pytest_selenium as sel
from cfme.web_ui import toolbar as tb
from cfme.web_ui.menu import nav

from . import list_tbl, mon_btn, pol_btn

nav.add_branch(
    'containers_pods',
    {
        'containers_pod':
        [
            lambda ctx: list_tbl.select_row_by_cells(
                {'Name': ctx['pod'].name, 'Provider': ctx['provider'].name}),
            {
                'containers_pod_edit_tags':
                lambda _: pol_btn('Edit Tags'),
            }
        ],
        'containers_pod_detail':
        [
            lambda ctx: list_tbl.click_row_by_cells(
                {'Name': ctx['pod'].name, 'Provider': ctx['provider'].name}),
            {
                'containers_pod_timelines_detail':
                lambda _: mon_btn('Timelines'),
                'containers_pod_edit_tags_detail':
                lambda _: pol_btn('Edit Tags'),
            }
        ]
    }
)


class Pod(Taggable):

    def __init__(self, name, provider):
        self.name = name
        self.provider = provider

    def load_details(self, refresh=False):
        if not self._on_detail_page():
            self.navigate(detail=True)
        elif refresh:
            tb.refresh()

    def navigate(self, detail=True):
        if detail is True:
            if not self._on_detail_page():
                sel.force_navigate('containers_pod_detail',
                    context={'pod': self, 'provider': self.provider})
        else:
            sel.force_navigate('containers_pod',
                context={'pod': self, 'provider': self.provider})
