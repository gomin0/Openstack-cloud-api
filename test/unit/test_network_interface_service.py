import pytest

from common.exception.floating_ip_exception import FloatingIpAlreadyAttachedToNetworkInterfaceException, \
    FloatingIpNotFoundException, FloatingIpNotAttachedToNetworkInterfaceException
from common.exception.network_interface_exception import NetworkInterfaceNotFoundException, \
    NetworkInterfaceAccessPermissionDeniedException
from test.util.factory import create_floating_ip_stub, create_network_interface_stub


async def test_attach_floating_ip_to_server_success(
    mock_session,
    mock_async_client,
    network_interface_service,
    mock_floating_ip_repository,
    mock_network_interface_repository,
    mock_neutron_client,
    mock_compensation_manager
):
    # given
    network_interface_id = 1
    project_id = 1
    keystone_token = "token"

    floating_ip = create_floating_ip_stub(project_id=project_id)
    network_interface = create_network_interface_stub(project_id=project_id)

    mock_floating_ip_repository.find_by_id.return_value = floating_ip
    mock_network_interface_repository.find_by_id.return_value = network_interface

    # when
    await network_interface_service.attach_floating_ip_to_server(
        compensating_tx=mock_compensation_manager,
        session=mock_session,
        client=mock_async_client,
        keystone_token=keystone_token,
        project_id=project_id,
        floating_ip_id=floating_ip.id,
        network_interface_id=network_interface_id,
    )

    # then
    mock_network_interface_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        network_interface_id=network_interface_id,
        with_relations=False,
        with_deleted=False
    )
    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip.id,
        with_relations=False,
        with_deleted=False
    )
    mock_neutron_client.attach_floating_ip_to_server.assert_called_once_with(
        client=mock_async_client,
        keystone_token=keystone_token,
        floating_ip_openstack_id=floating_ip.openstack_id,
        port_id=network_interface.openstack_id
    )


async def test_attach_floating_ip_to_server_fail_network_interface_not_found(
    mock_session,
    mock_async_client,
    network_interface_service,
    mock_floating_ip_repository,
    mock_network_interface_repository,
    mock_compensation_manager
):
    # given
    network_interface_id = 1
    floating_ip_id = 1
    project_id = 1
    keystone_token = "token"

    mock_network_interface_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(NetworkInterfaceNotFoundException):
        await network_interface_service.attach_floating_ip_to_server(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token=keystone_token,
            project_id=project_id,
            floating_ip_id=floating_ip_id,
            network_interface_id=network_interface_id,
        )

    mock_network_interface_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        network_interface_id=network_interface_id,
        with_relations=False,
        with_deleted=False
    )


async def test_attach_floating_ip_to_server_fail_access_permission_denied(
    mock_session,
    mock_async_client,
    network_interface_service,
    mock_floating_ip_repository,
    mock_network_interface_repository,
    mock_compensation_manager
):
    # given
    network_interface_id = 1
    floating_ip_id = 1
    project1_id = 1
    project2_id = 2
    keystone_token = "token"

    network_interface = create_network_interface_stub(project_id=project1_id)
    mock_network_interface_repository.find_by_id.return_value = network_interface

    # when & then
    with pytest.raises(NetworkInterfaceAccessPermissionDeniedException):
        await network_interface_service.attach_floating_ip_to_server(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token=keystone_token,
            project_id=project2_id,
            floating_ip_id=floating_ip_id,
            network_interface_id=network_interface_id,
        )

    mock_network_interface_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        network_interface_id=network_interface_id,
        with_relations=False,
        with_deleted=False
    )


async def test_attach_floating_ip_to_server_fail_floating_ip_not_found(
    mock_session,
    mock_async_client,
    network_interface_service,
    mock_floating_ip_repository,
    mock_network_interface_repository,
    mock_compensation_manager
):
    # given
    network_interface_id = 1
    floating_ip_id = 1
    project_id = 1
    keystone_token = "token"
    network_interface = create_network_interface_stub(project_id=project_id)

    mock_network_interface_repository.find_by_id.return_value = network_interface
    mock_floating_ip_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(FloatingIpNotFoundException):
        await network_interface_service.attach_floating_ip_to_server(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token=keystone_token,
            project_id=project_id,
            floating_ip_id=floating_ip_id,
            network_interface_id=network_interface_id,
        )

    mock_network_interface_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        network_interface_id=network_interface_id,
        with_relations=False,
        with_deleted=False
    )
    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip_id,
        with_relations=False,
        with_deleted=False
    )


async def test_attach_floating_ip_to_server_fail_already_attached(
    mock_session,
    mock_async_client,
    network_interface_service,
    mock_floating_ip_repository,
    mock_network_interface_repository,
    mock_compensation_manager
):
    # given
    network_interface_id = 1
    floating_ip_id = 1
    project_id = 1
    keystone_token = "token"

    network_interface = create_network_interface_stub(project_id=project_id)
    floating_ip = create_floating_ip_stub(project_id=project_id, network_interface=network_interface)

    mock_network_interface_repository.find_by_id.return_value = network_interface
    mock_floating_ip_repository.find_by_id.return_value = floating_ip

    with pytest.raises(FloatingIpAlreadyAttachedToNetworkInterfaceException):
        await network_interface_service.attach_floating_ip_to_server(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token=keystone_token,
            project_id=project_id,
            floating_ip_id=floating_ip_id,
            network_interface_id=network_interface_id,
        )

    mock_network_interface_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        network_interface_id=network_interface_id,
        with_relations=False,
        with_deleted=False
    )
    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip_id,
        with_relations=False,
        with_deleted=False
    )


async def test_detach_floating_ip_from_server_success(
    mock_session,
    mock_async_client,
    network_interface_service,
    mock_floating_ip_repository,
    mock_network_interface_repository,
    mock_neutron_client,
    mock_compensation_manager
):
    # given
    floating_ip_id = 1
    project_id = 1
    keystone_token = "token"

    network_interface = create_network_interface_stub(project_id=project_id)
    floating_ip = create_floating_ip_stub(project_id=project_id, network_interface=network_interface)

    floating_ip.network_interface_id = network_interface.id

    mock_floating_ip_repository.find_by_id.return_value = floating_ip
    mock_network_interface_repository.find_by_id.return_value = network_interface

    # when
    await network_interface_service.detach_floating_ip_from_server(
        compensating_tx=mock_compensation_manager,
        session=mock_session,
        client=mock_async_client,
        keystone_token=keystone_token,
        project_id=project_id,
        floating_ip_id=floating_ip_id,
    )

    # then
    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip_id,
        with_relations=False,
        with_deleted=False
    )
    mock_neutron_client.detach_floating_ip_from_server.assert_called_once_with(
        client=mock_async_client,
        keystone_token=keystone_token,
        floating_ip_openstack_id=floating_ip.openstack_id,
    )


async def test_detach_floating_ip_from_server_fail_floating_ip_not_found(
    mock_session,
    mock_async_client,
    network_interface_service,
    mock_floating_ip_repository,
    mock_network_interface_repository,
    mock_compensation_manager
):
    # given
    floating_ip_id = 1
    project_id = 1
    keystone_token = "token"

    mock_floating_ip_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(FloatingIpNotFoundException):
        await network_interface_service.detach_floating_ip_from_server(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token=keystone_token,
            project_id=project_id,
            floating_ip_id=floating_ip_id,
        )

    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip_id,
        with_relations=False,
        with_deleted=False
    )


async def test_detach_floating_ip_from_server_fail_not_attached(
    mock_session,
    mock_async_client,
    network_interface_service,
    mock_floating_ip_repository,
    mock_network_interface_repository,
    mock_compensation_manager
):
    # given
    floating_ip_id = 1
    project_id = 1
    keystone_token = "valid-token"

    network_interface = create_network_interface_stub(project_id=project_id)
    floating_ip = create_floating_ip_stub(project_id=project_id)

    mock_floating_ip_repository.find_by_id.return_value = floating_ip

    # when & then
    with pytest.raises(FloatingIpNotAttachedToNetworkInterfaceException):
        await network_interface_service.detach_floating_ip_from_server(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token=keystone_token,
            project_id=project_id,
            floating_ip_id=floating_ip_id,
        )

    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip_id,
        with_relations=False,
        with_deleted=False
    )
