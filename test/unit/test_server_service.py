import pytest

from common.domain.network_interface.entity import NetworkInterface
from common.exception.server_exception import ServerNotFoundException, ServerAccessDeniedException
from test.util.factory import create_server_stub, create_volume, create_project


async def test_find_servers_details_success(
    mock_session,
    mock_async_client,
    mock_server_repository,
    server_service
):
    # given
    project = create_project(project_id=1, domain_id=1)
    volume1 = create_volume(
        volume_id=1, project_id=project.id, server_id=1, is_root_volume=True, image_openstack_id="123"
    )
    volume2 = create_volume(
        volume_id=2, project_id=project.id, server_id=2, is_root_volume=True, image_openstack_id="456"
    )
    network_interface1 = NetworkInterface(fixed_ip_address="123")
    network_interface2 = NetworkInterface(fixed_ip_address="456")
    mock_servers = [
        create_server_stub(
            server_id=1, project_id=project.id, volumes=[volume1], network_interfaces=[network_interface1]
        ),
        create_server_stub(
            server_id=2, project_id=project.id, volumes=[volume2], network_interfaces=[network_interface2]
        ),
    ]
    mock_server_repository.find_all_by_project_id.return_value = mock_servers

    # when
    response = await server_service.find_servers_details(
        session=mock_session,
        ids=None,
        is_exclude_ids=False,
        name=None,
        name_like=None,
        sort_by="created_at",
        order="desc",
        project_id=project.id,
    )

    # then
    mock_server_repository.find_all_by_project_id.assert_called_once_with(
        session=mock_session,
        ids=None,
        is_exclude_ids=False,
        name=None,
        name_like=None,
        sort_by="created_at",
        order="desc",
        project_id=project.id,
        with_deleted=False,
        with_relations=True
    )
    assert len(response.servers) == 2


async def test_get_server_detail_success(
    mock_session,
    mock_async_client,
    mock_server_repository,
    server_service
):
    # given
    server_id = 1
    project_id = 1
    project = create_project(project_id=project_id, domain_id=1)
    volume = create_volume(
        volume_id=1, project_id=project.id, server_id=1, is_root_volume=True, image_openstack_id="123"
    )
    network_interface = NetworkInterface(fixed_ip_address="123")
    mock_server = create_server_stub(
        server_id=server_id, project_id=project.id, volumes=[volume], network_interfaces=[network_interface]
    )

    mock_server_repository.find_by_id.return_value = mock_server

    # when
    response = await server_service.get_server_detail(
        session=mock_session,
        server_id=server_id,
        project_id=project_id
    )

    # then
    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        server_id=server_id,
        with_deleted=False,
        with_relations=True
    )
    assert response.id == mock_server.id


async def test_get_server_detail_fail_not_found(
    mock_session,
    mock_async_client,
    mock_server_repository,
    server_service
):
    # given
    server_id = 1
    project_id = 1
    mock_server_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(ServerNotFoundException):
        await server_service.get_server_detail(
            session=mock_session,
            server_id=server_id,
            project_id=project_id
        )

    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        server_id=server_id,
        with_deleted=False,
        with_relations=True
    )


async def test_get_server_detail_fail_access_denied(
    mock_session,
    mock_async_client,
    mock_server_repository,
    server_service
):
    # given
    server_id = 1
    project_id = 1
    volume = create_volume(
        volume_id=1, project_id=2, server_id=1, is_root_volume=True, image_openstack_id="123"
    )
    network_interface = NetworkInterface(fixed_ip_address="123")
    mock_server = create_server_stub(
        server_id=server_id, project_id=2, volumes=[volume], network_interfaces=[network_interface]
    )
    mock_server_repository.find_by_id.return_value = mock_server

    # when & then
    with pytest.raises(ServerAccessDeniedException):
        await server_service.get_server_detail(
            session=mock_session,
            server_id=server_id,
            project_id=project_id
        )

    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        server_id=server_id,
        with_deleted=False,
        with_relations=True
    )
