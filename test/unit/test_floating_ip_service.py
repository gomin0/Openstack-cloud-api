import pytest

from common.application.floating_ip.response import FloatingIpDetailResponse
from common.domain.enum import SortOrder
from common.domain.floating_ip.dto import FloatingIpDTO
from common.domain.floating_ip.enum import FloatingIpSortOption, FloatingIpStatus
from common.exception.floating_ip_exception import (
    FloatingIpAccessDeniedException,
    FloatingIpNotFoundException,
    AttachedFloatingIpDeletionException,
    FloatingIpDeletePermissionDeniedException,
)
from test.util.factory import create_floating_ip_stub, create_server, create_network_interface


async def test_find_floating_ips_success(mock_session, mock_floating_ip_repository, floating_ip_service):
    # given
    project_id = 1

    floating_ip1 = create_floating_ip_stub(project_id=project_id)
    floating_ip2 = create_floating_ip_stub(project_id=project_id)

    mock_floating_ip_repository.find_all_by_project_id.return_value = [floating_ip1, floating_ip2]

    # when
    result = await floating_ip_service.find_floating_ips_details(
        session=mock_session,
        project_id=project_id,
        sort_by=FloatingIpSortOption.CREATED_AT,
        order=SortOrder.ASC,
        with_deleted=False
    )

    # then
    expected = [
        await FloatingIpDetailResponse.from_entity(floating_ip1),
        await FloatingIpDetailResponse.from_entity(floating_ip2),
    ]

    assert result.floating_ips == expected

    mock_floating_ip_repository.find_all_by_project_id.assert_called_once_with(
        session=mock_session,
        project_id=project_id,
        sort_by=FloatingIpSortOption.CREATED_AT,
        order=SortOrder.ASC,
        with_deleted=False,
        with_relations=True
    )


async def test_get_floating_ip_success(mock_session, mock_floating_ip_repository, floating_ip_service):
    # given
    project_id = 1
    floating_ip = create_floating_ip_stub(project_id=project_id)

    mock_floating_ip_repository.find_by_id.return_value = floating_ip

    # when
    result = await floating_ip_service.get_floating_ip_detail(
        session=mock_session,
        project_id=project_id,
        floating_ip_id=floating_ip.id
    )

    # then
    assert result.id == floating_ip.id

    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip.id,
        with_deleted=False,
        with_relations=True
    )


async def test_get_floating_ip_fail_not_found(mock_session, mock_floating_ip_repository, floating_ip_service):
    # given
    mock_floating_ip_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(FloatingIpNotFoundException):
        await floating_ip_service.get_floating_ip_detail(
            session=mock_session,
            project_id=1,
            floating_ip_id=1
        )

    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=1,
        with_deleted=False,
        with_relations=True
    )


async def test_get_floating_ip_fail_access_denied(mock_session, mock_floating_ip_repository, floating_ip_service):
    # given
    floating_ip = create_floating_ip_stub(project_id=1)
    mock_floating_ip_repository.find_by_id.return_value = floating_ip

    # when & then
    with pytest.raises(FloatingIpAccessDeniedException):
        await floating_ip_service.get_floating_ip_detail(
            session=mock_session,
            project_id=2,
            floating_ip_id=floating_ip.id
        )

    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip.id,
        with_deleted=False,
        with_relations=True
    )


async def test_create_floating_ip_success(
    mock_session,
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

    floating_ip_service.neutron_client.create_floating_ip.return_value = FloatingIpDTO(
        openstack_id=floating_ip_openstack_id,
        status=FloatingIpStatus.DOWN,
        address=floating_ip_address,
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
        project_id=project_id,
        keystone_token=keystone_token,
        floating_network_id=floating_network_id
    )

    # then
    assert result.address == floating_ip_address

    floating_ip_service.neutron_client.create_floating_ip.assert_called_once_with(
        floating_network_id=floating_network_id,
        keystone_token=keystone_token
    )
    mock_floating_ip_repository.create.assert_called_once()


async def test_delete_floating_ip_success(
    mock_session,
    mock_floating_ip_repository,
    mock_neutron_client,
    floating_ip_service
):
    # given
    floating_ip_id = 1
    project_id = 1
    keystone_token = "token"

    floating_ip = create_floating_ip_stub(project_id=project_id)
    mock_floating_ip_repository.find_by_id.return_value = floating_ip
    mock_neutron_client.delete_floating_ip.return_value = None

    # when
    await floating_ip_service.delete_floating_ip(
        session=mock_session,
        project_id=project_id,
        keystone_token=keystone_token,
        floating_ip_id=floating_ip_id,
    )

    # then
    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip_id
    )
    mock_neutron_client.delete_floating_ip.assert_called_once_with(
        keystone_token=keystone_token,
        floating_ip_openstack_id=floating_ip.openstack_id
    )


async def test_delete_floating_ip_fail_not_found(
    mock_session, mock_floating_ip_repository, floating_ip_service
):
    # given
    floating_ip_id = 1
    project_id = 1
    keystone_token = "token"

    mock_floating_ip_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(FloatingIpNotFoundException):
        await floating_ip_service.delete_floating_ip(
            session=mock_session,
            project_id=project_id,
            keystone_token=keystone_token,
            floating_ip_id=floating_ip_id,
        )

    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip_id
    )


async def test_delete_floating_ip_fail_permission_denied(
    mock_session, mock_floating_ip_repository, floating_ip_service
):
    # given
    floating_ip_id = 1
    project_id = 2
    keystone_token = "token"

    floating_ip = create_floating_ip_stub(project_id=1)
    mock_floating_ip_repository.find_by_id.return_value = floating_ip

    # when & then
    with pytest.raises(FloatingIpDeletePermissionDeniedException):
        await floating_ip_service.delete_floating_ip(
            session=mock_session,
            project_id=project_id,
            keystone_token=keystone_token,
            floating_ip_id=floating_ip_id,
        )

    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip_id
    )


async def test_delete_floating_ip_fail_attached(
    mock_session, mock_floating_ip_repository, floating_ip_service
):
    # given
    floating_ip_id = 1
    project_id = 1
    keystone_token = "token"
    server = create_server(project_id=project_id, server_id=1)
    network_interface = create_network_interface(server_id=server.id, project_id=project_id)
    floating_ip = create_floating_ip_stub(project_id=project_id, network_interface=network_interface)

    mock_floating_ip_repository.find_by_id.return_value = floating_ip

    # when & then
    with pytest.raises(AttachedFloatingIpDeletionException):
        await floating_ip_service.delete_floating_ip(
            session=mock_session,
            project_id=project_id,
            keystone_token=keystone_token,
            floating_ip_id=floating_ip_id,
        )

    mock_floating_ip_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        floating_ip_id=floating_ip_id
    )
