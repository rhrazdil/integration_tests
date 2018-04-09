import fauxfactory
import pytest

from cfme.cloud.provider.openstack import OpenStackProvider
from cfme.utils.appliance.implementations.ui import navigate_to
from cfme.utils.update import update
from cfme.utils.wait import wait_for


pytestmark = [
    pytest.mark.provider([OpenStackProvider]),
    pytest.mark.usefixtures("setup_provider"),
    pytest.mark.ignore_stream("5.8")
]


def test_network_router_crud(appliance, provider):
    """Test crud of sdn router."""
    router_collection = appliance.collections.network_routers
    test_name = "test_router_{}".format(fauxfactory.gen_alphanumeric(6))
    net_manager = "{} Network Manager".format(provider.name)
    router = router_collection.create(test_name, provider, "admin", net_manager)
    assert router.exists
    new_test_name = "{}_changed".format(test_name)
    with update(router):
        router.name = new_test_name
    view = navigate_to(router, 'Details')
    assert view.title == new_test_name
    assert net_manager == view.entities.relationships.get_text_of("Network Manager")
    router.delete()
    wait_for(lambda: not router.exists, delay=50, num_sec=500)


def test_cancel_adding_router(appliance, provider):
    """Test uncompleted adding router."""
    router_collection = appliance.collections.network_routers
    test_name = "test_router_{}".format(fauxfactory.gen_alphanumeric(6))
    view = navigate_to(router_collection, 'Add')
    view.router_name.fill(test_name)
    view.cancel.click()
    network_router = router_collection.instantiate(name=test_name)
    assert not network_router.exists


def test_cloud_network_crud(provider, appliance, options):
    """Test adding cloud network in ui."""
    test_name = "test_network_{}".format(fauxfactory.gen_alphanumeric(6))
    net_manager = "{} Network Manager".format(provider.name)
    collection = appliance.collections.cloud_networks
    network = collection.create(test_name, "admin", provider, net_manager, "VLAN",
                                is_external=True, is_shared=True)
    assert network.exists
    new_test_name = "{}_changed".format(test_name)
    with update(network):
        network.name = new_test_name
    view = navigate_to(network, 'Details')
    assert view.title == new_test_name
    assert net_manager == view.entities.relationships.get_text_of("Network Manager")
    network.delete()
    assert not network.exists


@pytest.mark.parametrize("ip_version", [("4", "192.168.23.0/24"),
                                        ("6", "2001:db6::/64")])
def test_subnet_crud(provider, appliance, ip_version):
    """Test adding subnet in ui."""
    test_name = "test_subnet_{}".format(fauxfactory.gen_alphanumeric(6))
    net_manager = "{} Network Manager".format(provider.name)
    collection = appliance.collections.network_subnets
    subnet = collection.create(test_name, "admin", provider, net_manager, "private", ip_version)
    assert subnet.exists
    new_test_name = "{}_changed".format(test_name)
    with update(subnet):
        subnet.name = new_test_name
    view = navigate_to(subnet, 'Details')
    assert view.title == new_test_name
    assert net_manager == view.entities.relationships.get_text_of("Network Manager")
    subnet.delete()
    assert not subnet.exists


def test_adding_security_group(provider, appliance):
    """Test adding security group in ui."""
    test_name = "test_sec_group_{}".format(fauxfactory.gen_alphanumeric(6))
    description = "test of adding new security group"
    network_manager = "{} Network Manager".format(provider.name)
    collection = appliance.collections.network_security_groups
    security_group = collection.create(name=test_name, network_manager=network_manager,
                                       description=description, provider=provider,
                                       tenant="admin")
    assert security_group.exists
    view = navigate_to(security_group, 'Details')
    assert network_manager == view.entities.relationships.get_text_of("Network Manager")
    security_group.delete()
    wait_for(lambda: not security_group.exists, delay=50, num_sec=500)


def test_adding_floating_ip(provider, appliance):
    """Test adding floating ip in ui"""
    testing_ip = "10.8.58.190"
    network_manager = "{} Network Manager".format(provider.name)

    collection = appliance.collections.network_floating_ips
    view = navigate_to(collection, 'All')
    view.paginator.set_items_per_page(100)
    current_addresses = [ip.address for ip in collection.all()]

    floating_ip = collection.create(address=testing_ip, tenant="admin",
                                    net_manager=network_manager, provider=provider,
                                    ext_network="public")

    provider.refresh_provider_relationships()
    wait_for(provider.is_refreshed, func_kwargs=dict(refresh_delta=10), timeout=600)

    view = navigate_to(collection, 'All')
    view.paginator.set_items_per_page(100)
    wait_for(lambda: len(collection.all()) > len(current_addresses), delay=50, num_sec=500,
             fail_func=provider.appliance.server.browser.refresh)
    item = [ip for ip in collection.all() if ip.address not in current_addresses]
    assert len(item) == 1
    floating_ip.address = item[0].address

    view = navigate_to(floating_ip, 'Details')
    assert network_manager == view.entities.relationships.get_text_of("Network Manager")
    view.toolbar.configuration.item_select('Delete this Floating IP', handle_alert=True)

    current_addresses = [ip.address for ip in collection.all()]
    provider.refresh_provider_relationships()
    wait_for(provider.is_refreshed, func_kwargs=dict(refresh_delta=10), timeout=600)
    wait_for(lambda: len(collection.all()) < len(current_addresses), delay=50, num_sec=500,
             fail_func=provider.appliance.server.browser.refresh)
