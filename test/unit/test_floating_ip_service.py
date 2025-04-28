import pytest

from exception.floating_ip_exception import FloatingNetworkNotFound
from exception.openstack_exception import OpenStackException
from test.util.factory import create_floating_ip_stub


async def test_create_floating_ip_success(
    mock_session,
    mock_async_client,
    mock_floating_ip_repository,
    floating_ip_service,
    mock_compensation_manager
):
    # given
    floating_network_id = "network-id"
    keystone_token = "token"
    project_id = 1

    floating_ip_openstack_id = "openstack-id"
    floating_ip_address = "10.0.0.1"

    floating_ip_service.neutron_client.create_floating_ip.return_value = (
        floating_ip_openstack_id,
        floating_ip_address
    )
    mock_floating_ip_repository.create.return_value = create_floating_ip_stub(
        project_id=project_id,
        floating_ip_id=1,
        address=floating_ip_address
    )

    # when
    result = await floating_ip_service.create_floating_ip(
        compensating_tx=mock_compensation_manager,
        session=mock_session,
        client=mock_async_client,
        project_id=project_id,
        keystone_token=keystone_token,
        floating_network_id=floating_network_id
    )

    # then
    assert result.address == floating_ip_address

    floating_ip_service.neutron_client.create_floating_ip.assert_called_once_with(
        client=mock_async_client,
        floating_network_id=floating_network_id,
        keystone_token=keystone_token
    )
    mock_floating_ip_repository.create.assert_called_once()


async def test_create_floating_ip_fail_network_not_found(
    mock_session,
    mock_async_client,
    mock_floating_ip_repository,
    floating_ip_service,
    mock_compensation_manager
):
    # given
    floating_network_id = "network-id"
    keystone_token = "token"
    project_id = 1

    floating_ip_service.neutron_client.create_floating_ip.side_effect = OpenStackException(
        openstack_status_code=404,
    )

    # when & then
    with pytest.raises(FloatingNetworkNotFound):
        await floating_ip_service.create_floating_ip(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            project_id=project_id,
            keystone_token=keystone_token,
            floating_network_id=floating_network_id
        )

    floating_ip_service.neutron_client.create_floating_ip.assert_called_once_with(
        client=mock_async_client,
        floating_network_id=floating_network_id,
        keystone_token=keystone_token
    )
    mock_floating_ip_repository.create.assert_not_called()
