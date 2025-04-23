from application.security_group.response import SecurityGroupDetailsResponse
from domain.project.entity import Project
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
    mock_security_group_repository.find_by_project_id.return_value = [
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
    mock_security_group_repository.find_by_project_id.assert_called_once()
    mock_neutron_client.get_security_group_rules_in_project.assert_called_once()
