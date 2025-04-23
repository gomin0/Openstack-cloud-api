import pytest

from application.security_group.response import SecurityGroupDetailsResponse, SecurityGroupDetailResponse
from domain.project.entity import Project
from exception.security_group_exception import SecurityGroupNotFoundException, SecurityGroupAccessDeniedException
from test.util.factory import create_security_group_stub


async def test_find_security_groups_success(
    mock_session,
    mock_async_client,
    mock_security_group_repository,
    mock_neutron_client,
    security_group_service
):
    # given
    security_group_id = 1
    project = Project(id=1, name="project", openstack_id="pos", domain_id=1)
    mock_security_group_repository.find_all_by_project_id.return_value = [
        create_security_group_stub(security_group_id=security_group_id)
    ]
    mock_neutron_client.get_security_group_rules_in_project.return_value = []

    # when
    result = await security_group_service.find_security_groups_details(
        session=mock_session,
        client=mock_async_client,
        project_id=project.id,
        project_openstack_id=project.openstack_id,
        keystone_token="token",
    )

    # then
    assert len(result.security_groups) == 1
    assert isinstance(result, SecurityGroupDetailsResponse)
    mock_security_group_repository.find_all_by_project_id.assert_called_once()
    mock_neutron_client.get_security_group_rules_in_project.assert_called_once()


async def test_get_security_group_success(
    mock_session,
    mock_async_client,
    mock_security_group_repository,
    mock_neutron_client,
    security_group_service
):
    # given
    security_group_id = 1
    security_group_openstack_id = "sgos"
    token = "token"
    security_group = create_security_group_stub(
        security_group_id=security_group_id,
        openstack_id=security_group_openstack_id,
        project_id=1
    )
    mock_security_group_repository.find_by_id.return_value = security_group
    mock_neutron_client.get_security_group_rules_in_security_group.return_value = []

    # when
    result = await security_group_service.get_security_group(
        session=mock_session,
        client=mock_async_client,
        project_id=1,
        security_group_id=1,
        keystone_token=token
    )

    # then
    assert isinstance(result, SecurityGroupDetailResponse)
    assert result.id == security_group_id
    assert result.rules == []
    mock_security_group_repository.find_by_id.assert_called_once()
    mock_neutron_client.get_security_group_rules_in_security_group.assert_called_once_with(
        client=mock_async_client,
        keystone_token=token,
        security_group_openstack_id=security_group_openstack_id
    )


async def test_get_security_group_not_found(
    mock_session,
    mock_async_client,
    mock_security_group_repository,
    security_group_service
):
    # given
    mock_security_group_repository.find_by_id.return_value = None

    # when / then
    with pytest.raises(SecurityGroupNotFoundException):
        await security_group_service.get_security_group(
            session=mock_session,
            client=mock_async_client,
            project_id=1,
            security_group_id=1,
            keystone_token="token"
        )

    mock_security_group_repository.find_by_id.assert_called_once()


async def test_get_security_group_fail_access_denied(
    mock_session,
    mock_async_client,
    mock_security_group_repository,
    security_group_service
):
    # given
    security_group = create_security_group_stub(
        security_group_id=1,
        project_id=2
    )
    mock_security_group_repository.find_by_id.return_value = security_group

    # when & then
    with pytest.raises(SecurityGroupAccessDeniedException):
        await security_group_service.get_security_group(
            session=mock_session,
            client=mock_async_client,
            project_id=1,
            security_group_id=1,
            keystone_token="token"
        )

    mock_security_group_repository.find_by_id.assert_called_once()
