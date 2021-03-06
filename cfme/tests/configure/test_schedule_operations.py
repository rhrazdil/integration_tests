import fauxfactory
import pytest
import pytz
from dateutil import parser, relativedelta

from cfme.base.ui import BaseLoggedInPage
from cfme.infrastructure.provider.virtualcenter import VMwareProvider
from cfme.markers.env_markers.provider import ONE
from cfme.utils.appliance.implementations.ui import navigate_to
from cfme.utils.wait import wait_for
from cfme.utils.hosts import setup_host_creds
from cfme.utils.update import update

pytestmark = [
    pytest.mark.provider([VMwareProvider], required_fields=['hosts'], selector=ONE, scope='module'),
    pytest.mark.usefixtures("setup_provider")
]

run_types = (
    ['Once', None, None],
    ['Hourly', 'hours', 1],
    ['Daily', 'days', 1],
    ['Weekly', 'weeks', 1],
    ['Monthly', 'months', 1]
)


@pytest.fixture(scope='module')
def host_with_credentials(appliance, provider):
    """ Add credentials to hosts """
    host = provider.hosts.all()[0]
    setup_host_creds(provider, host.name)
    yield host
    setup_host_creds(provider, host.name, remove_creds=True)


@pytest.fixture
def current_server_time(appliance):
    current_time = parser.parse(appliance.ssh_client.run_command('date').output)
    tz_list = appliance.ssh_client.run_command("timedatectl | grep 'Time zone'") \
        .output.strip().split(' ')

    tz_name = tz_list[2]
    tz_num = tz_list[-1][:-1]
    date = current_time.replace(tzinfo=pytz.timezone(tz_name))
    return date, tz_num


def round_min(value, base=5):
    return (0 if int(base * round(float(value) / base)) == 60
            else int(base * round(float(value) / base)))


def test_schedule_crud(appliance, current_server_time):
    current_time, _ = current_server_time
    start_date = current_time + relativedelta.relativedelta(days=2)
    schedule = appliance.collections.system_schedules.create(
        name=fauxfactory.gen_alphanumeric(),
        description=fauxfactory.gen_alphanumeric(),
        start_date=start_date
    )

    view = appliance.browser.create_view(BaseLoggedInPage)
    view.flash.assert_message('Schedule "{}" was saved'.format(schedule.name))
    # test for bz 1569127
    start_date_updated = start_date - relativedelta.relativedelta(days=1)
    updates = {
        'name': fauxfactory.gen_alphanumeric(),
        'description': fauxfactory.gen_alphanumeric(),
    }
    schedule.update(updates, cancel=True)
    view.flash.assert_message(
        'Edit of Schedule "{}" was cancelled by the user'.format(schedule.name))
    schedule.update(updates, reset=True)
    view.flash.assert_message('All changes have been reset')
    with update(schedule):
        schedule.name = fauxfactory.gen_alphanumeric()
        schedule.start_date = start_date_updated
    view.flash.assert_message('Schedule "{}" was saved'.format(schedule.name))
    schedule.delete(cancel=True)
    schedule.delete()
    view.flash.assert_message('Schedule "{}": Delete successful'.format(schedule.description))


def test_schedule_analysis_in_the_past(appliance, current_server_time, request):
    current_time, _ = current_server_time
    past_time = current_time - relativedelta.relativedelta(minutes=5)
    if round_min(past_time.minute) == 0:
        past_time = past_time + relativedelta.relativedelta(hours=1)
        past_time_minute = '0'
    else:
        past_time_minute = str(round_min(past_time.minute))
    schedule = appliance.collections.system_schedules.create(
        name=fauxfactory.gen_alphanumeric(),
        description=fauxfactory.gen_alphanumeric(),
        start_hour=str(past_time.hour),
        start_minute=past_time_minute
    )
    request.addfinalizer(schedule.delete)
    view = appliance.browser.create_view(BaseLoggedInPage)
    assert (
        "Warning: This 'Run Once' timer is in the past and will never"
        " run as currently configured" in [message.text for message in view.flash.messages]
    )


def test_create_multiple_schedules_in_one_timezone(appliance, request):
    schedule_list = []
    request.addfinalizer(lambda: map(lambda item: item.delete(), schedule_list))

    for i in range(6):
        schedule = appliance.collections.system_schedules.create(
            name=fauxfactory.gen_alphanumeric(),
            description=fauxfactory.gen_alphanumeric(),
            time_zone='(GMT-04:00) Atlantic Time (Canada)'
        )
        view = appliance.browser.create_view(BaseLoggedInPage)
        view.flash.assert_message('Schedule "{}" was saved'.format(schedule.name))
        schedule_list.append(schedule)


def test_inactive_schedule(appliance, current_server_time):
    current_time, _ = current_server_time
    start_date = current_time + relativedelta.relativedelta(minutes=5)

    schedule = appliance.collections.system_schedules.create(
        name=fauxfactory.gen_alphanumeric(),
        description=fauxfactory.gen_alphanumeric(),
        start_date=start_date,
        start_hour=str(start_date.hour),
        start_minute=str(round_min(start_date.minute)),

    )
    assert schedule.next_run_date
    schedule.disable()
    assert not schedule.next_run_date


@pytest.mark.parametrize('run_types', run_types, ids=[type[0] for type in run_types])
def test_schedule_timer(appliance, run_types, host_with_credentials, request, current_server_time):

    run_time, time_diff, time_num = run_types
    current_time, tz_num = current_server_time
    start_date = current_time + relativedelta.relativedelta(minutes=5)
    view = navigate_to(appliance.collections.system_schedules, 'Add')
    available_list = view.time_zone.all_options
    # bz is here 1559904
    for tz in available_list:
        if '{}:00'.format(tz_num[0:3]) in tz.text and 'Atlantic Time (Canada)' not in tz.text:
            tz_select = tz.text
            break
    if round_min(start_date.minute) == 0:
        start_date = start_date + relativedelta.relativedelta(minutes=60 - start_date.minute)
        start_date_minute = str(start_date.minute)
    else:
        start_date_minute = str(round_min(start_date.minute))
    schedule = appliance.collections.system_schedules.create(
        name=fauxfactory.gen_alphanumeric(),
        description=fauxfactory.gen_alphanumeric(),
        action_type='Host Analysis',
        filter_level1='A single Host',
        filter_level2=host_with_credentials.name,
        run_type=run_time,
        start_date=start_date,
        time_zone=tz_select,
        start_hour=str(start_date.hour),
        start_minute=start_date_minute,

    )

    @request.addfinalizer
    def _finalize():
        if schedule.exists:
            schedule.delete()

    wait_for(lambda: schedule.last_run_date != '',
             delay=60, timeout="10m", fail_func=appliance.server.browser.refresh,
             message="Scheduled task didn't run in first time")

    if time_diff:
        next_date = parser.parse(schedule.next_run_date)
        up = {time_diff: time_num}
        next_run_date = start_date + relativedelta.relativedelta(minutes=-5, **up)
        appliance.ssh_client.run_command("date {}".format(next_run_date.strftime('%m%d%H%M%Y')))

        wait_for(
            lambda: next_date.strftime('%m%d%H') == parser.parse(
                schedule.last_run_date).strftime('%m%d%H'),
            delay=60, timeout="10m", fail_func=appliance.server.browser.refresh,
            message="Scheduled task didn't run in appropriate time set")
