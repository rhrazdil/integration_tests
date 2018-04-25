"""
Test that VM can be provisioned to virtual network create in RHV OVN.
Test case definition in polarion: https://polarion.engineering.redhat.com/polarion/#/project/RHEVM3/wiki/CFME/4_2_cfme_ovn
Feature page: https://www.ovirt.org/blog/2016/11/ovirt-provider-ovn/
ManageIQ integration: https://www.ovirt.org/develop/release-management/features/network/manageiq_ovn/
"""

import fauxfactory
import pytest

from cfme import test_requirements
from cfme.infrastructure.provider.rhevm import RHEVMProvider
from cfme.utils.wait import wait_for
from cfme.common.vm import VM
from widgetastic.utils import partial_match
from cfme.provisioning import do_vm_provisioning

pytestmark = [
    pytest.mark.provider([RHEVMProvider],
                         required_fields=[['provisioning', 'template'],
                                          ['provisioning', 'host'],
                                          ['provisioning', 'datastore']],
                         scope="module"
                         ),
    pytest.mark.usefixtures("setup_provider"),
    pytest.mark.ignore_stream("5.8"),
    test_requirements.provision,
]


@pytest.fixture(scope='function')
def network(provider, appliance):
    """Test adding cloud network in ui."""
    test_name = "test_network_{}".format(fauxfactory.gen_alphanumeric(6))
    net_manager = "{} Network Manager".format(provider.name)
    collection = appliance.collections.network_providers
    network_provider = collection.instantiate(
        name=net_manager)
    collection = appliance.collections.cloud_networks
    network = collection.create(test_name, "tenant", network_provider, net_manager,"None")
    return network


def test_provision_from_template(appliance, setup_provider, provider,
                                 vm_name, request, provisioning, network):
    """ Tests provisioning from a template

    Metadata:
        test_flag: provision
        suite: infra_provisioning
        rbac:
            roles:
                default:
                evmgroup-super_administrator:
                evmgroup-administrator:
                evmgroup-operator: NoSuchElementException
                evmgroup-auditor: NoSuchElementException
    """

    template = provisioning['template']

    request.addfinalizer(
        lambda: VM.factory(vm_name, provider).cleanup_on_provider())

    provisioning_data = {
        'catalog': {
            'vm_name': vm_name
        },
        'environment': {
            'vm_name': vm_name,
            'automatic_placement': True
        },
        'network': {
            'vlan': partial_match(network.name)
        }
    }

    wait_for(
        do_vm_provisioning,
        [appliance, template, provider, vm_name, provisioning_data, request],
        {'num_sec': 900, 'return_result': True, 'smtp_test': False},
        handle_exception=True,
        delay=50,
        num_sec=900,
        fail_func=provider.appliance.server.browser.refresh
    )