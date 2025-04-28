from application.floating_ip.response import FloatingIpDetailResponse
from domain.enum import SortOrder
from domain.floating_ip.enum import FloatingIpSortOption
from test.util.factory import create_floating_ip_stub


async def test_find_floating_ips(mock_session, mock_floating_ip_repository, floating_ip_service):
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
