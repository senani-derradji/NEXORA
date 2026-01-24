from ..operations.devices_ops import DeviceOperations
from ..schemas.device_validator import DeviceValidate


def test_create_device(db_session):
    ops = DeviceOperations(db=db_session)

    device = ops.create_device(DeviceValidate(
        name="Router1",
        ip_address="192.168.1.1",
        device_type="router",
        location="Office",
        status="online",
        group_id=1
    ))

    assert device is not None
    assert device.name == "Router1"
    assert device.ip_address == "192.168.1.1"
    assert device.status == "online"


def test_get_device_by_id(db_session):
    ops = DeviceOperations(db=db_session)

    ops.create_device(DeviceValidate(
        name="Switch1",
        ip_address="10.0.0.1",
        device_type="switch",
        location="Lab",
        status="online",
        group_id=1
    ))

    result = ops.get_device_by_id(1)
    assert result is not None
    assert result.name == "Switch1"

    result_none = ops.get_device_by_id(99)
    assert result_none is None


def test_update_device(db_session):
    ops = DeviceOperations(db=db_session)

    ops.create_device(DeviceValidate(
        name="AP1",
        ip_address="192.168.0.10",
        device_type="router",
        location="Hall",
        status="online",
        group_id=1
    ))

    assert ops.get_device_by_id(1) is not None
    assert ops.get_device_by_id(1).name == "AP1"
    assert ops.get_device_by_id(1).ip_address == "192.168.0.10"
    assert ops.get_device_by_id(1).status == "online"


    updated = ops.update_device(1, DeviceValidate(
        name="AP2",
        ip_address="192.168.0.11",
        device_type="router",
        location="Hall",
        status="offline",
        group_id=2
    ))

    assert updated is not None
    assert updated.name == "AP2"
    assert updated.ip_address == "192.168.0.11"
    assert updated.status == "offline"
    assert updated.group_id == 2


def test_delete_device(db_session):
    ops = DeviceOperations(db=db_session)

    ops.create_device(DeviceValidate(
        name="Firewall1",
        ip_address="172.16.0.1",
        device_type="router",
        location="DC",
        status="online",
        group_id=1
    ))

    deleted = ops.delete_device(1)
    assert deleted is True

    result = ops.get_device_by_id(1)
    assert result is None


def test_get_all_devices(db_session):
    ops = DeviceOperations(db=db_session)

    ops.create_device(DeviceValidate(
        name="D1",
        ip_address="10.0.0.1",
        device_type="router",
        location="A",
        status="online",
        group_id=1
    ))

    assert ops.get_all_devices() is not None
    assert len(ops.get_all_devices()) == 1
    assert ops.get_all_devices()[0].name == "D1"
    assert ops.get_all_devices()[0].ip_address == "10.0.0.1"

    ops.create_device(DeviceValidate(
        name="D2",
        ip_address="10.0.0.2",
        device_type="switch",
        location="B",
        status="online",
        group_id=1
    ))

    devices = ops.get_all_devices()
    assert len(devices) == 2