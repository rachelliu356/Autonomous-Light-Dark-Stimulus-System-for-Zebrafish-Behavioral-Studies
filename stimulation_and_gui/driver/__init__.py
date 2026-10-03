from .camera_driver import CameraDriver
from .dummy_camera_driver import DummyCameraDriver
from .replay_camera_driver import ReplayCameraDriver

_flir_camera_available = False

try:
    from .flir_camera_driver import FLIRCameraDriver

    camera_driver_cls = FLIRCameraDriver
    _flir_camera_available = True
except ImportError:
    print("Warning: FLIRCameraDriver cannot be imported. Using a dummy camera driver instead.")
    camera_driver_cls = DummyCameraDriver


def get_camera_driver() -> CameraDriver:
    return camera_driver_cls()


def is_flir_camera_available() -> bool:
    return _flir_camera_available
