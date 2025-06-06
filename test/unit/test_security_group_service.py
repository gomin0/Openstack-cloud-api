import pytest

from common.application.security_group.response import SecurityGroupDetailsResponse, SecurityGroupDetailResponse
from common.domain.project.entity import Project
from common.domain.security_group.dto import SecurityGroupRuleDTO, CreateSecurityGroupRuleDTO, SecurityGroupDTO, \
    UpdateSecurityGroupRuleDTO
from common.domain.security_group.enum import SecurityGroupRuleDirection, SecurityGroupRuleEtherType
from common.exception.security_group_exception import (
    SecurityGroupNotFoundException,
    SecurityGroupAccessDeniedException,
    SecurityGroupNameDuplicatedException,
    SecurityGroupUpdatePermissionDeniedException,
    SecurityGroupDeletePermissionDeniedException,
    AttachedSecurityGroupDeletionException

)
from test.util.factory import create_security_group_stub


async def test_find_security_groups_success(
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
            ether_type=SecurityGroupRuleEtherType.IPv4,
            direction=SecurityGroupRuleDirection.INGRESS,
            port_range_min=22,
            port_range_max=22,
            remote_ip_prefix="0.0.0.0/0",
        )
    ]

    # when
    result = await security_group_service.find_security_groups_details(
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
            ether_type=SecurityGroupRuleEtherType.IPv4,
            direction=SecurityGroupRuleDirection.INGRESS,
            port_range_min=22,
            port_range_max=22,
            remote_ip_prefix="0.0.0.0/0",
        )
    ]

    # when
    result = await security_group_service.get_security_group_detail(
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
        keystone_token=token,
        security_group_openstack_id=security_group_openstack_id
    )


async def test_get_security_group_not_found(
    mock_security_group_repository,
    security_group_service
):
    # given
    mock_security_group_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(SecurityGroupNotFoundException):
        await security_group_service.get_security_group_detail(
            project_id=1,
            security_group_id=1,
            keystone_token="token"
        )

    mock_security_group_repository.find_by_id.assert_called_once()


async def test_get_security_group_fail_access_denied(
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
            project_id=1,
            security_group_id=1,
            keystone_token="token"
        )

    mock_security_group_repository.find_by_id.assert_called_once()


async def test_create_security_group_success(
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
            ether_type=SecurityGroupRuleEtherType.IPv4,
            port_range_min=22,
            port_range_max=22,
            remote_ip_prefix="0.0.0.0/0"
        )
    ]

    # when
    result = await security_group_service.create_security_group(
        compensating_tx=mock_compensation_manager,
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
            keystone_token="token",
            project_id=1,
            name="sg",
            description="desc",
            rules=[]
        )

    mock_security_group_repository.exists_by_project_and_name.assert_called_once_with(
        project_id=1,
        name="sg"
    )


async def test_update_security_group_success(
    mock_security_group_repository,
    mock_neutron_client,
    security_group_service,
    mock_compensation_manager
):
    # given
    security_group = create_security_group_stub(security_group_id=1, name="old", description="desc", project_id=1)
    mock_security_group_repository.find_by_id.return_value = security_group
    mock_security_group_repository.exists_by_project_and_name.return_value = False
    mock_neutron_client.get_security_group_rules_in_security_group.return_value = [
        {
            "id": "sgos",
            "direction": "egress",
            "protocol": "tcp",
            "port_range_min": 80,
            "port_range_max": 80,
            "remote_ip_prefix": "0.0.0.0/0"
        }
    ]
    mock_neutron_client.create_security_group_rules.return_value = [
        SecurityGroupRuleDTO(
            openstack_id="newsgos",
            security_group_openstack_id="sgos",
            protocol="tcp",
            ether_type=SecurityGroupRuleEtherType.IPv4,
            direction=SecurityGroupRuleDirection.EGRESS,
            port_range_min=22,
            port_range_max=22,
            remote_ip_prefix="0.0.0.0/0"
        )
    ]

    rules = [UpdateSecurityGroupRuleDTO(
        direction=SecurityGroupRuleDirection.EGRESS,
        protocol="tcp",
        ether_type=SecurityGroupRuleEtherType.IPv4,
        port_range_min=22,
        port_range_max=22,
        remote_ip_prefix="0.0.0.0/0"
    )]

    # when
    result = await security_group_service.update_security_group_detail(
        compensating_tx=mock_compensation_manager,
        keystone_token="token",
        project_id=1,
        security_group_id=1,
        name="new",
        description="new",
        rules=rules
    )

    # then
    assert result.name == "new"
    assert result.description == "new"
    mock_security_group_repository.find_by_id.assert_called_once()


async def test_update_security_group_fail_not_found(
    mock_security_group_repository,
    security_group_service,
    mock_compensation_manager
):
    # given
    mock_security_group_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(SecurityGroupNotFoundException):
        await security_group_service.update_security_group_detail(
            compensating_tx=mock_compensation_manager,
            keystone_token="token",
            project_id=1,
            security_group_id=1,
            name="name",
            description="desc",
            rules=[]
        )


async def test_update_security_group_fail_access_denied(
    mock_security_group_repository,
    security_group_service,
    mock_compensation_manager
):
    # given
    security_group = create_security_group_stub(security_group_id=1, project_id=2)
    mock_security_group_repository.find_by_id.return_value = security_group

    # when & then
    with pytest.raises(SecurityGroupUpdatePermissionDeniedException):
        await security_group_service.update_security_group_detail(
            compensating_tx=mock_compensation_manager,
            keystone_token="token",
            project_id=1,
            security_group_id=1,
            name="same",
            description="desc",
            rules=[]
        )


async def test_delete_security_group_success(
    mock_security_group_repository,
    mock_network_interface_security_group_repository,
    mock_neutron_client,
    security_group_service
):
    # given
    security_group_id = 1
    project_id = 1
    keystone_token = "token"

    security_group = create_security_group_stub(security_group_id=security_group_id, project_id=project_id)
    mock_security_group_repository.find_by_id.return_value = security_group
    mock_network_interface_security_group_repository.exists_by_security_group.return_value = False

    # when
    await security_group_service.delete_security_group(
        project_id=project_id,
        keystone_token=keystone_token,
        security_group_id=security_group_id,
    )

    # then
    mock_security_group_repository.find_by_id.assert_called_once_with(
        security_group_id=security_group_id
    )
    mock_network_interface_security_group_repository.exists_by_security_group.assert_called_once_with(
        security_group_id=security_group_id
    )
    mock_neutron_client.delete_security_group.assert_called_once_with(
        keystone_token=keystone_token, security_group_openstack_id=security_group.openstack_id
    )


async def test_delete_security_group_fail_not_found(
    mock_security_group_repository,
    security_group_service
):
    # given
    security_group_id = 1
    mock_security_group_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(SecurityGroupNotFoundException):
        await security_group_service.delete_security_group(
            project_id=1,
            keystone_token="token",
            security_group_id=security_group_id,
        )

    mock_security_group_repository.find_by_id.assert_called_once_with(
        security_group_id=security_group_id
    )


async def test_delete_security_group_fail_permission_denied(
    mock_security_group_repository,
    security_group_service
):
    # given
    security_group_id = 1
    security_group = create_security_group_stub(security_group_id=security_group_id, project_id=2)
    mock_security_group_repository.find_by_id.return_value = security_group

    # when & then
    with pytest.raises(SecurityGroupDeletePermissionDeniedException):
        await security_group_service.delete_security_group(
            project_id=1,
            keystone_token="token",
            security_group_id=security_group_id,
        )

    mock_security_group_repository.find_by_id.assert_called_once_with(
        security_group_id=security_group_id
    )


async def test_delete_security_group_fail_server_attached(
    mock_security_group_repository,
    mock_network_interface_security_group_repository,
    security_group_service
):
    # given
    security_group_id = 1
    project_id = 1
    security_group = create_security_group_stub(security_group_id=security_group_id, project_id=project_id)
    mock_security_group_repository.find_by_id.return_value = security_group
    mock_network_interface_security_group_repository.exists_by_security_group.return_value = True

    # when & then
    with pytest.raises(AttachedSecurityGroupDeletionException):
        await security_group_service.delete_security_group(
            project_id=project_id,
            keystone_token="token",
            security_group_id=security_group_id,
        )

    mock_network_interface_security_group_repository.exists_by_security_group.assert_called_once_with(
        security_group_id=security_group_id
    )
    mock_security_group_repository.find_by_id.assert_called_once_with(
        security_group_id=security_group_id
    )
