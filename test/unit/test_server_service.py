import pytest

from common.application.server.response import ServerResponse
from common.domain.enum import SortOrder
from common.domain.network_interface.entity import NetworkInterface
from common.domain.project.entity import Project
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption
from common.exception.server_exception import ServerNotFoundException, ServerAccessPermissionDeniedException, \
    ServerUpdatePermissionDeniedException, ServerNameDuplicateException
from test.util.factory import create_server_stub, create_volume, create_project, create_server
from test.util.random import random_int, random_string


async def test_find_servers_details_success(
    mock_session,
    mock_async_client,
    mock_server_repository,
    server_service
):
    # given
    project = Project(id=1, name="project", openstack_id="pos", domain_id=1)
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
            server_id=1,
            project_id=project.id,
            volumes=[volume1],
            network_interfaces=[network_interface1],
            security_groups=[]
        ),
        create_server_stub(
            server_id=2,
            project_id=project.id,
            volumes=[volume2],
            network_interfaces=[network_interface2],
            security_groups=[]
        ),
    ]
    mock_server_repository.find_all_by_project_id.return_value = mock_servers

    # when
    response = await server_service.find_servers_details(
        session=mock_session,
        id_=None,
        ids_contain=None,
        ids_exclude=None,
        name_eq=None,
        name_like=None,
        sort_by=ServerSortOption.CREATED_AT,
        order=SortOrder.ASC,
        project_id=project.id,
    )

    # then
    mock_server_repository.find_all_by_project_id.assert_called_once_with(
        session=mock_session,
        project_id=project.id,
        id_=None,
        ids_contain=None,
        ids_exclude=None,
        name_eq=None,
        name_like=None,
        sort_by=ServerSortOption.CREATED_AT,
        order=SortOrder.ASC,
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
        server_id=server_id,
        project_id=project.id,
        volumes=[volume],
        network_interfaces=[network_interface],
        security_groups=[]
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
        server_id=server_id,
        project_id=2,
        volumes=[volume],
        network_interfaces=[network_interface],
        security_groups=[],
    )
    mock_server_repository.find_by_id.return_value = mock_server

    # when & then
    with pytest.raises(ServerAccessPermissionDeniedException):
        await server_service.get_server_detail(
            session=mock_session,
            server_id=server_id,
            project_id=project_id
        )

    mock_server_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        server_id=server_id,
        with_relations=True
    )


async def test_update_server_info_success(mock_session, mock_server_repository, server_service):
    # given
    new_name: str = "new_name"
    new_description: str = "new_description"
    server: Server = create_server()
    mock_server_repository.find_by_id.return_value = server
    mock_server_repository.exists_by_project_and_name.return_value = False

    # when
    result: ServerResponse = await server_service.update_server_info(
        session=mock_session,
        current_project_id=server.project_id,
        server_id=server.id,
        name=new_name,
        description=new_description,
    )

    # then
    mock_server_repository.find_by_id.assert_called_once()
    mock_server_repository.exists_by_project_and_name.assert_called_once()
    assert result.id == server.id
    assert result.name == new_name
    assert result.description == new_description


async def test_update_server_info_fail_server_not_found(mock_session, mock_server_repository, server_service):
    # given
    mock_server_repository.find_by_id.return_value = None

    # when and then
    with pytest.raises(ServerNotFoundException):
        await server_service.update_server_info(
            session=mock_session,
            current_project_id=random_int(),
            server_id=random_int(),
            name=random_string(),
            description=random_string(),
        )
    mock_server_repository.find_by_id.assert_called_once()


async def test_update_server_info_fail_when_requester_has_not_update_permission(
    mock_session,
    mock_server_repository,
    server_service
):
    # given
    project_id = 1
    requesting_project_id = 2
    new_name: str = "new_name"
    new_description: str = "new_description"
    server: Server = create_server(project_id=project_id)
    mock_server_repository.find_by_id.return_value = server

    # when and then
    with pytest.raises(ServerUpdatePermissionDeniedException):
        await server_service.update_server_info(
            session=mock_session,
            current_project_id=requesting_project_id,
            server_id=server.id,
            name=new_name,
            description=new_description,
        )
    mock_server_repository.find_by_id.assert_called_once()

async def test_update_server_info_fail_new_name_is_duplicated(mock_session, mock_server_repository, server_service):
    # given
    new_name: str = "new_name"
    new_description: str = "new_description"
    server: Server = create_server()
    mock_server_repository.find_by_id.return_value = server
    mock_server_repository.exists_by_project_and_name.return_value = True

    # when and then
    with pytest.raises(ServerNameDuplicateException):
        await server_service.update_server_info(
            session=mock_session,
            current_project_id=server.project_id,
            server_id=server.id,
            name=new_name,
            description=new_description,
        )
    mock_server_repository.find_by_id.assert_called_once()
    mock_server_repository.exists_by_project_and_name.assert_called_once()
