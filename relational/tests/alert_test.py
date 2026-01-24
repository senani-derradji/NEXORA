from ..operations.devices_ops import DeviceOperations
from ..operations.alerts_ops import AlertOperations
from ..schemas.device_validator import DeviceValidate
from ..schemas.alerts_validator import AlertValidate


def test_create_device_for_alerts(db_session):
    device_ops = DeviceOperations(db=db_session)

    device = device_ops.create_device(DeviceValidate(
        name="Router1",
        ip_address="192.168.1.1",
        device_type="router",
        location="Office",
        status="online",
        group_id=1
    ))

    assert device is not None
    assert device.id == 1
    assert device.name == "Router1"


def test_create_alert_for_device(db_session):
    device_ops = DeviceOperations(db=db_session)
    alert_ops = AlertOperations(db=db_session)

    device = device_ops.create_device(DeviceValidate(
        name="Router1",
        ip_address="192.168.1.1",
        device_type="router",
        location="Office",
        status="online",
        group_id=1
    ))

    alert = alert_ops.create_alert(AlertValidate(
        alert_message="CPU usage high",
        alert_level="high",
        device_id=device.id
    ))

    assert alert is not None
    assert alert.alert_message == "CPU usage high"
    assert alert.device_id == device.id


def test_get_alerts_by_device(db_session):
    device_ops = DeviceOperations(db=db_session)
    alert_ops = AlertOperations(db=db_session)

    device = device_ops.create_device(DeviceValidate(
        name="Router1",
        ip_address="192.168.1.1",
        device_type="router",
        location="Office",
        status="online",
        group_id=1
    ))

    alert_ops.create_alert(AlertValidate(
        alert_message="CPU usage high",
        alert_level="high",
        device_id=device.id
    ))

    alerts = alert_ops.get_alerts_by_device(device.id)

    assert len(alerts) == 1
    assert alerts[0].alert_message == "CPU usage high"
    assert alerts[0].device.name == "Router1"
