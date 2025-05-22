from datetime import datetime, timezone

import pytest

from common.application.volume.response import VolumeResponse, VolumeDetailResponse
from common.application.volume.service import VolumeService
from common.domain.enum import SortOrder
from common.domain.volume.dto import OsVolumeDto
from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus, VolumeSortOption
from common.exception.volume_exception import (
    VolumeNameDuplicateException, VolumeNotFoundException, VolumeDeletePermissionDeniedException,
    VolumeAlreadyDeletedException, VolumeStatusInvalidForDeletionException, AttachedVolumeDeletionException,
    VolumeUpdatePermissionDeniedException, VolumeDeletionFailedException, VolumeStatusInvalidForResizingException,
    VolumeResizeNotAllowedException, VolumeResizingFailedException, VolumeAccessPermissionDeniedException
)
from test.util.factory import create_volume, create_volume_stub
from test.util.random import random_string, random_int


async def test_find_volume_details_success(mock_session, mock_volume_repository, volume_service):
    # given
    project_id: int = random_int()
    expected_result: list[Volume] = [create_volume_stub(project_id=project_id)]
    mock_volume_repository.find_all_by_project.return_value = expected_result

    # when
    actual_result = await volume_service.find_volume_details(
        session=mock_session,
        current_project_id=project_id,
        sort_by=VolumeSortOption.NAME,
        sort_order=SortOrder.DESC,
    )

    # then
    mock_volume_repository.find_all_by_project.assert_called_once()
    assert len(expected_result) == len(actual_result)


async def test_get_volume_detail_success(mock_session, mock_volume_repository, volume_service):
    # given
    project_id: int = random_int()
    volume_id: int = random_int()
    expected_result: Volume = create_volume_stub(volume_id=volume_id, project_id=project_id)
    mock_volume_repository.find_by_id.return_value = expected_result

    # when
    actual_result: VolumeDetailResponse = await volume_service.get_volume_detail(
        session=mock_session,
        current_project_id=project_id,
        volume_id=volume_id,
    )

    # then
    mock_volume_repository.find_by_id.assert_called_once()
    assert actual_result.id == expected_result.id


async def test_get_volume_detail_fail_not_found(mock_session, mock_volume_repository, volume_service):
    # given
    project_id: int = random_int()
    volume_id: int = random_int()
    mock_volume_repository.find_by_id.return_value = None

    # when and then
    with pytest.raises(VolumeNotFoundException):
        await volume_service.get_volume_detail(
            session=mock_session,
            current_project_id=project_id,
            volume_id=volume_id,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_get_volume_detail_fail_requester_do_not_have_access_permission(mock_session, mock_volume_repository,
                                                                              volume_service):
    # given
    project_id: int = 1
    requesting_project_id: int = 2
    volume_id: int = random_int()
    expected_result: Volume = create_volume_stub(volume_id=volume_id, project_id=project_id)
    mock_volume_repository.find_by_id.return_value = expected_result

    # when and then
    with pytest.raises(VolumeAccessPermissionDeniedException):
        await volume_service.get_volume_detail(
            session=mock_session,
            current_project_id=requesting_project_id,
            volume_id=volume_id,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_create_volume_success(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    name: str = random_string()
    description: str = random_string()
    size: int = random_int(max_val=10)
    volume_type_openstack_id: str = random_string()
    image_openstack_id: str = random_string()
    expected_result: Volume = create_volume(
        name=name,
        description=description,
        size=size,
        volume_type_openstack_id=volume_type_openstack_id,
        image_openstack_id=image_openstack_id,
    )
    mock_volume_repository.exists_by_name_and_project.return_value = False
    mock_volume_repository.create.return_value = expected_result
    mock_cinder_client.create_volume.return_value = "new_volume_openstack_id"

    # when
    actual_result = await volume_service.create_volume(
        session=mock_session,
        keystone_token=random_string(),
        project_id=random_int(),
        project_openstack_id=random_string(),
        name=name,
        description=description,
        size=size,
        volume_type_openstack_id=volume_type_openstack_id,
        image_openstack_id=image_openstack_id,
    )

    # then
    mock_volume_repository.exists_by_name_and_project.assert_called_once()
    mock_cinder_client.create_volume.assert_called_once()
    mock_volume_repository.create.assert_called_once()
    assert actual_result == VolumeResponse.from_entity(expected_result)


async def test_create_volume_fail_when_name_already_exists(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    mock_volume_repository.exists_by_name_and_project.return_value = True

    # when & then
    with pytest.raises(VolumeNameDuplicateException):
        await volume_service.create_volume(
            session=mock_session,
            keystone_token=random_string(),
            project_id=random_int(),
            project_openstack_id=random_string(),
            name=random_string(),
            description=random_string(),
            size=random_int(max_val=10),
            volume_type_openstack_id=random_string(),
            image_openstack_id=random_string(),
        )
    mock_volume_repository.exists_by_name_and_project.assert_called_once()


async def test_sync_creating_volume_until_available_success(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    mock_cinder_client.get_volume_status.return_value = VolumeStatus.AVAILABLE
    mock_volume_repository.find_by_openstack_id.return_value = create_volume()
    VolumeService.SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION = 0
    VolumeService.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION = 3

    # when
    await volume_service.sync_creating_volume_until_available(
        session=mock_session,
        project_openstack_id=random_string(),
        volume_openstack_id=random_string(),
    )

    # then
    mock_cinder_client.get_volume_status.assert_called_once()
    mock_volume_repository.find_by_openstack_id.assert_called_once()


async def test_sync_creating_volume_until_available_fail_when_error_occurred_from_openstack(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    mock_cinder_client.get_volume_status.return_value = VolumeStatus.ERROR
    mock_volume_repository.find_by_openstack_id.return_value = create_volume()
    VolumeService.SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION = 0
    VolumeService.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION = 3

    # when
    await volume_service.sync_creating_volume_until_available(
        session=mock_session,
        project_openstack_id=random_string(),
        volume_openstack_id=random_string(),
    )

    # then
    mock_cinder_client.get_volume_status.assert_called_once()
    mock_volume_repository.find_by_openstack_id.assert_called_once()


async def test_sync_creating_volume_until_available_fail_when_updated_unexpected_status(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    mock_cinder_client.get_volume_status.return_value = VolumeStatus.BACKING_UP
    mock_volume_repository.find_by_openstack_id.return_value = create_volume()
    VolumeService.SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION = 0
    VolumeService.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION = 3

    # when
    await volume_service.sync_creating_volume_until_available(
        session=mock_session,
        project_openstack_id=random_string(),
        volume_openstack_id=random_string(),
    )

    # then
    mock_cinder_client.get_volume_status.assert_called_once()
    mock_volume_repository.find_by_openstack_id.assert_called_once()


async def test_sync_creating_volume_until_available_fail_timeout(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    mock_cinder_client.get_volume_status.return_value = VolumeStatus.CREATING
    volume_service.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION = 3
    volume_service.SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION = 0

    # when
    await volume_service.sync_creating_volume_until_available(
        session=mock_session,
        project_openstack_id=random_string(),
        volume_openstack_id=random_string(),
    )

    # then
    assert mock_cinder_client.get_volume_status.call_count == volume_service.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION
    mock_volume_repository.find_by_openstack_id.assert_called_once()


async def test_update_volume_info_success(mock_session, mock_volume_repository, volume_service):
    # given
    volume_id: int = random_int()
    project_id: int = random_int()
    new_name: str = random_string()
    new_description: str = random_string()
    volume: Volume = create_volume(volume_id=volume_id, project_id=project_id)
    mock_volume_repository.find_by_id.return_value = volume
    mock_volume_repository.exists_by_name_and_project.return_value = False

    # when
    await volume_service.update_volume_info(
        session=mock_session,
        current_project_id=project_id,
        volume_id=volume_id,
        name=new_name,
        description=new_description,
    )

    # then
    mock_volume_repository.find_by_id.assert_called_once()
    mock_volume_repository.exists_by_name_and_project.assert_called_once()
    assert volume.name == new_name
    assert volume.description == new_description


async def test_update_volume_info_fail_volume_not_found(mock_session, mock_volume_repository, volume_service):
    # given
    mock_volume_repository.find_by_id.return_value = None

    # when and then
    with pytest.raises(VolumeNotFoundException):
        await volume_service.update_volume_info(
            session=mock_session,
            current_project_id=random_int(),
            volume_id=random_int(),
            name=random_string(),
            description=random_string(),
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_update_volume_info_fail_when_has_not_permission_to_update_volume(
    mock_session,
    mock_volume_repository,
    volume_service
):
    # given
    volume_id: int = random_int()
    volume_project_id: int = 1
    requesting_project_id: int = 2
    new_name: str = random_string()
    new_description: str = random_string()
    volume: Volume = create_volume(volume_id=volume_id, project_id=volume_project_id)
    mock_volume_repository.find_by_id.return_value = volume

    # when and then
    with pytest.raises(VolumeUpdatePermissionDeniedException):
        await volume_service.update_volume_info(
            session=mock_session,
            current_project_id=requesting_project_id,
            volume_id=volume_id,
            name=new_name,
            description=new_description,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_update_volume_info_fail_when_new_name_is_already_exists(
    mock_session,
    mock_volume_repository,
    volume_service
):
    # given
    volume_id: int = random_int()
    project_id: int = random_int()
    new_name: str = random_string()
    new_description: str = random_string()
    volume: Volume = create_volume(volume_id=volume_id, project_id=project_id)
    mock_volume_repository.find_by_id.return_value = volume
    mock_volume_repository.exists_by_name_and_project.return_value = True

    # when and then
    with pytest.raises(VolumeNameDuplicateException):
        await volume_service.update_volume_info(
            session=mock_session,
            current_project_id=project_id,
            volume_id=volume.id,
            name=new_name,
            description=new_description,
        )
    mock_volume_repository.find_by_id.assert_called_once()
    mock_volume_repository.exists_by_name_and_project.assert_called_once()


async def test_update_volume_size_success(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    new_size: int = 2
    volume: Volume = create_volume(status=VolumeStatus.AVAILABLE, size=1)
    mock_volume_repository.find_by_id.return_value = volume
    mock_cinder_client.extend_volume_size.return_value = None
    mock_cinder_client.get_volume.return_value = OsVolumeDto(
        openstack_id=volume.openstack_id,
        volume_type_name="DEFAULT",
        image_openstack_id=None,
        status=VolumeStatus.AVAILABLE,
        size=new_size
    )

    # when
    result: Volume = await volume_service.update_volume_size(
        session=mock_session,
        keystone_token=random_string(),
        current_project_id=volume.project_id,
        current_project_openstack_id=random_string(),
        volume_id=volume.id,
        new_size=new_size,
    )

    # then
    mock_volume_repository.find_by_id.assert_called_once()
    mock_cinder_client.extend_volume_size.assert_called_once()
    mock_cinder_client.get_volume.assert_called_once()
    assert result.id == volume.id
    assert result.status == VolumeStatus.AVAILABLE
    assert result.size == new_size


async def test_update_volume_size_fail_volume_not_found(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    new_size: int = random_int()
    mock_volume_repository.find_by_id.return_value = None

    # when and then
    with pytest.raises(VolumeNotFoundException):
        await volume_service.update_volume_size(
            session=mock_session,
            keystone_token=random_string(),
            current_project_id=random_int(),
            current_project_openstack_id=random_string(),
            volume_id=random_int(),
            new_size=new_size,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_update_volume_size_fail_update_permission_denied(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    new_size: int = 2
    volume: Volume = create_volume(project_id=1, status=VolumeStatus.AVAILABLE, size=1)
    mock_volume_repository.find_by_id.return_value = volume

    # when and then
    with pytest.raises(VolumeUpdatePermissionDeniedException):
        await volume_service.update_volume_size(
            session=mock_session,
            keystone_token=random_string(),
            current_project_id=2,
            current_project_openstack_id=random_string(),
            volume_id=random_int(),
            new_size=new_size,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_update_volume_size_fail_when_volume_status_is_not_available(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    new_size: int = 2
    volume: Volume = create_volume(status=VolumeStatus.IN_USE, size=1)
    mock_volume_repository.find_by_id.return_value = volume

    # when and then
    with pytest.raises(VolumeStatusInvalidForResizingException):
        await volume_service.update_volume_size(
            session=mock_session,
            keystone_token=random_string(),
            current_project_id=volume.project_id,
            current_project_openstack_id=random_string(),
            volume_id=random_int(),
            new_size=new_size,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_update_volume_size_fail_when_given_invalid_size(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    new_size: int = 1
    volume: Volume = create_volume(status=VolumeStatus.AVAILABLE, size=1)
    mock_volume_repository.find_by_id.return_value = volume

    # when and then
    with pytest.raises(VolumeResizeNotAllowedException):
        await volume_service.update_volume_size(
            session=mock_session,
            keystone_token=random_string(),
            current_project_id=volume.project_id,
            current_project_openstack_id=random_string(),
            volume_id=random_int(),
            new_size=new_size,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_update_volume_size_fail_resize_from_openstack(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    volume_service.MAX_CHECK_ATTEMPTS_FOR_VOLUME_RESIZING = 3
    volume_service.CHECK_INTERVAL_SECONDS_FOR_VOLUME_RESIZING = 0

    new_size: int = 2
    volume: Volume = create_volume(status=VolumeStatus.AVAILABLE, size=1)
    mock_volume_repository.find_by_id.return_value = volume
    mock_cinder_client.extend_volume_size.return_value = None
    mock_cinder_client.get_volume.return_value = OsVolumeDto(
        openstack_id=volume.openstack_id,
        volume_type_name="DEFAULT",
        image_openstack_id=None,
        status=VolumeStatus.EXTENDING,
        size=new_size
    )

    # when and then
    with pytest.raises(VolumeResizingFailedException):
        await volume_service.update_volume_size(
            session=mock_session,
            keystone_token=random_string(),
            current_project_id=volume.project_id,
            current_project_openstack_id=random_string(),
            volume_id=random_int(),
            new_size=new_size,
        )
    mock_volume_repository.find_by_id.assert_called_once()
    mock_cinder_client.extend_volume_size.assert_called_once()
    assert mock_cinder_client.get_volume.call_count == volume_service.MAX_CHECK_ATTEMPTS_FOR_VOLUME_RESIZING


async def test_delete_volume_success(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    project_id: int = random_int()
    volume: Volume = create_volume(project_id=project_id, status=VolumeStatus.AVAILABLE)
    mock_volume_repository.find_by_id.return_value = volume
    mock_cinder_client.delete_volume.return_value = None
    mock_cinder_client.exists_volume.return_value = False

    # when
    await volume_service.delete_volume(
        session=mock_session,
        current_project_id=project_id,
        current_project_openstack_id=random_string(),
        keystone_token=random_string(),
        volume_id=volume.id,
    )

    # then
    mock_volume_repository.find_by_id.assert_called_once()
    mock_cinder_client.delete_volume.assert_called_once()
    mock_cinder_client.exists_volume.assert_called_once()
    assert volume.deleted_at is not None


async def test_delete_volume_fail_volume_not_found(
    mock_session,
    mock_volume_repository,
    volume_service,
):
    # given
    mock_volume_repository.find_by_id.return_value = None

    # when and then
    with pytest.raises(VolumeNotFoundException):
        await volume_service.delete_volume(
            session=mock_session,
            current_project_id=random_int(),
            current_project_openstack_id=random_string(),
            keystone_token=random_string(),
            volume_id=random_int(),
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_delete_volume_fail_when_has_not_permission_to_delete_volume(
    mock_session,
    mock_volume_repository,
    volume_service,
):
    # given
    requesting_project_id: int = 1
    volume: Volume = create_volume(project_id=2, status=VolumeStatus.AVAILABLE)
    mock_volume_repository.find_by_id.return_value = volume

    # when and then
    with pytest.raises(VolumeDeletePermissionDeniedException):
        await volume_service.delete_volume(
            session=mock_session,
            current_project_id=requesting_project_id,
            current_project_openstack_id=random_string(),
            keystone_token=random_string(),
            volume_id=volume.id,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_delete_volume_fail_volume_is_linked_to_server(
    mock_session,
    mock_volume_repository,
    volume_service,
):
    # given
    project_id: int = random_int()
    volume: Volume = create_volume(project_id=project_id, server_id=random_int())
    mock_volume_repository.find_by_id.return_value = volume

    # when and then
    with pytest.raises(AttachedVolumeDeletionException):
        await volume_service.delete_volume(
            session=mock_session,
            current_project_id=project_id,
            current_project_openstack_id=random_string(),
            keystone_token=random_string(),
            volume_id=volume.id,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_delete_volume_fail_volume_status_is_not_deletable(
    mock_session,
    mock_volume_repository,
    volume_service,
):
    # given
    project_id: int = random_int()
    volume: Volume = create_volume(project_id=project_id, status=VolumeStatus.CREATING)
    mock_volume_repository.find_by_id.return_value = volume

    # when and then
    with pytest.raises(VolumeStatusInvalidForDeletionException):
        await volume_service.delete_volume(
            session=mock_session,
            current_project_id=project_id,
            current_project_openstack_id=random_string(),
            keystone_token=random_string(),
            volume_id=volume.id,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_delete_volume_fail_volume_is_already_deleted(
    mock_session,
    mock_volume_repository,
    volume_service,
):
    # given
    project_id: int = random_int()
    volume: Volume = create_volume(
        project_id=project_id,
        status=VolumeStatus.ERROR,
        deleted_at=datetime.now(timezone.utc),
    )
    mock_volume_repository.find_by_id.return_value = volume

    # when and then
    with pytest.raises(VolumeAlreadyDeletedException):
        await volume_service.delete_volume(
            session=mock_session,
            current_project_id=project_id,
            current_project_openstack_id=random_string(),
            keystone_token=random_string(),
            volume_id=volume.id,
        )
    mock_volume_repository.find_by_id.assert_called_once()


async def test_delete_volume_fail_deletion_not_completed(
    mock_session,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    project_id: int = random_int()
    volume: Volume = create_volume(project_id=project_id, status=VolumeStatus.ERROR)
    mock_volume_repository.find_by_id.return_value = volume
    mock_cinder_client.delete_volume.return_value = None
    mock_cinder_client.get_volume.return_value = OsVolumeDto(
        openstack_id=volume.openstack_id,
        volume_type_name=random_string(),
        image_openstack_id=volume.image_openstack_id,
        status=volume.status,
        size=volume.size
    )

    volume_service.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DELETION = 3
    volume_service.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DELETION = 0

    # when and then
    with pytest.raises(VolumeDeletionFailedException):
        await volume_service.delete_volume(
            session=mock_session,
            current_project_id=project_id,
            current_project_openstack_id=random_string(),
            keystone_token=random_string(),
            volume_id=volume.id,
        )
    mock_volume_repository.find_by_id.assert_called_once()
