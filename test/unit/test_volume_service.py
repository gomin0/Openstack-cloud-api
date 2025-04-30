import pytest

from common.application.volume.response import VolumeResponse
from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus
from common.exception.volume_exception import (
    VolumeNameDuplicateException, VolumeUpdatePermissionDeniedException, VolumeNotFoundException
)
from test.util.factory import create_volume
from test.util.random import random_string, random_int


async def test_create_volume_success(
    mock_session,
    mock_async_client,
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
        client=mock_async_client,
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
    mock_async_client,
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
            client=mock_async_client,
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
    mock_async_client,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    mock_cinder_client.get_volume_status.return_value = VolumeStatus.AVAILABLE
    mock_volume_repository.find_by_openstack_id.return_value = create_volume()

    # when
    await volume_service.sync_creating_volume_until_available(
        session=mock_session,
        client=mock_async_client,
        keystone_token=random_string(),
        project_openstack_id=random_string(),
        volume_openstack_id=random_string(),
    )

    # then
    mock_cinder_client.get_volume_status.assert_called_once()
    mock_volume_repository.find_by_openstack_id.assert_called_once()


async def test_sync_creating_volume_until_available_fail_when_error_occurred_from_openstack(
    mock_session,
    mock_async_client,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    mock_cinder_client.get_volume_status.return_value = VolumeStatus.ERROR
    mock_volume_repository.find_by_openstack_id.return_value = create_volume()

    # when
    await volume_service.sync_creating_volume_until_available(
        session=mock_session,
        client=mock_async_client,
        keystone_token=random_string(),
        project_openstack_id=random_string(),
        volume_openstack_id=random_string(),
    )

    # then
    mock_cinder_client.get_volume_status.assert_called_once()
    mock_volume_repository.find_by_openstack_id.assert_called_once()


async def test_sync_creating_volume_until_available_fail_when_updated_unexpected_status(
    mock_session,
    mock_async_client,
    mock_volume_repository,
    mock_cinder_client,
    volume_service,
):
    # given
    mock_cinder_client.get_volume_status.return_value = VolumeStatus.DOWNLOADING
    mock_volume_repository.find_by_openstack_id.return_value = create_volume()

    # when
    await volume_service.sync_creating_volume_until_available(
        session=mock_session,
        client=mock_async_client,
        keystone_token=random_string(),
        project_openstack_id=random_string(),
        volume_openstack_id=random_string(),
    )

    # then
    mock_cinder_client.get_volume_status.assert_called_once()
    mock_volume_repository.find_by_openstack_id.assert_called_once()


async def test_sync_creating_volume_until_available_fail_timeout(
    mock_session,
    mock_async_client,
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
        client=mock_async_client,
        keystone_token=random_string(),
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
