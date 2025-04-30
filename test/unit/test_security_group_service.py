from datetime import datetime, timezone

import pytest

from common.application.security_group.response import SecurityGroupDetailsResponse, SecurityGroupDetailResponse
from common.domain.project.entity import Project
from common.domain.security_group.dto import SecurityGroupRuleDTO, CreateSecurityGroupRuleDTO, SecurityGroupDTO
from common.domain.security_group.enum import SecurityGroupRuleDirection
from common.exception.security_group_exception import SecurityGroupNotFoundException, \
    SecurityGroupAccessDeniedException, SecurityGroupNameDuplicatedException
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
    security_group = create_security_group_stub(security_group_id=security_group_id)
    mock_security_group_repository.find_all_by_project_id.return_value = [security_group]
    mock_neutron_client.find_security_group_rules.return_value = [
        SecurityGroupRuleDTO(
            openstack_id="rule-id",
            security_group_openstack_id=security_group.openstack_id,
            protocol="tcp",
            direction=SecurityGroupRuleDirection.INGRESS,
            port_range_min=22,
            port_range_max=22,
            remote_ip_prefix="0.0.0.0/0",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]

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
    mock_neutron_client.find_security_group_rules.assert_called_once()


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
    mock_neutron_client.find_security_group_rules.return_value = [
        SecurityGroupRuleDTO(
            openstack_id="rule-id",
            security_group_openstack_id=security_group.openstack_id,
            protocol="tcp",
            direction=SecurityGroupRuleDirection.INGRESS,
            port_range_min=22,
            port_range_max=22,
            remote_ip_prefix="0.0.0.0/0",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]

    # when
    result = await security_group_service.get_security_group_detail(
        session=mock_session,
        client=mock_async_client,
        project_id=1,
        security_group_id=1,
        keystone_token=token
    )

    # then
    assert isinstance(result, SecurityGroupDetailResponse)
    assert result.id == security_group_id
    assert len(result.rules) == 1
    mock_security_group_repository.find_by_id.assert_called_once()
    mock_neutron_client.find_security_group_rules.assert_called_once_with(
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

    # when & then
    with pytest.raises(SecurityGroupNotFoundException):
        await security_group_service.get_security_group_detail(
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
        await security_group_service.get_security_group_detail(
            session=mock_session,
            client=mock_async_client,
            project_id=1,
            security_group_id=1,
            keystone_token="token"
        )

    mock_security_group_repository.find_by_id.assert_called_once()


async def test_create_security_group_success(
    mock_session,
    mock_async_client,
    mock_security_group_repository,
    mock_project_repository,
    mock_neutron_client,
    security_group_service,
    mock_compensation_manager
):
    # given
    project_id = 1
    name = "sg"
    security_group = create_security_group_stub(
        security_group_id=1,
        name=name,
        project_id=project_id,
    )

    mock_security_group_repository.exists_by_project_and_name.return_value = False
    mock_neutron_client.create_security_group.return_value = SecurityGroupDTO(
        openstack_id="sgos",
        name=name,
        rules=[],
        description=security_group.description,
    )
    mock_security_group_repository.create.return_value = security_group
    mock_neutron_client.get_security_group_rules.return_value = []

    rules = [
        CreateSecurityGroupRuleDTO(
            direction=SecurityGroupRuleDirection.INGRESS,
            protocol="tcp",
            port_range_min=22,
            port_range_max=22,
            remote_ip_prefix="0.0.0.0/0"
        )
    ]

    # when
    result = await security_group_service.create_security_group(
        compensating_tx=mock_compensation_manager,
        session=mock_session,
        client=mock_async_client,
        keystone_token="token",
        project_id=project_id,
        name=security_group.name,
        description=security_group.description,
        rules=rules
    )

    # then
    assert result.name == name
    assert result.rules == []
    mock_security_group_repository.exists_by_project_and_name.assert_called_once()
    mock_security_group_repository.create.assert_called_once()
    mock_neutron_client.create_security_group.assert_called_once()
    mock_neutron_client.create_security_group_rules.assert_called_once()


async def test_create_security_group_fail_name_duplicated(
    mock_session,
    mock_async_client,
    mock_security_group_repository,
    security_group_service,
    mock_compensation_manager
):
    # given
    mock_security_group_repository.exists_by_project_and_name.return_value = True

    # when & then
    with pytest.raises(SecurityGroupNameDuplicatedException):
        await security_group_service.create_security_group(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token="token",
            project_id=1,
            name="sg",
            description="desc",
            rules=[]
        )

    mock_security_group_repository.exists_by_project_and_name.assert_called_once_with(
        session=mock_session,
        project_id=1,
        name="sg"
    )
