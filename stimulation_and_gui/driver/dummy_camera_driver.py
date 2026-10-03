from typing import Optional

import numpy as np

from driver.camera_driver import CameraDriver


class DummyCameraDriver(CameraDriver):
    """
    A dummy implentation of the CameraDriver class that does nothing.
    """

    def connect(self):
        pass

    def disconnect(self):
        pass

    def is_connected(self) -> bool:
        return False

    def read_frame(self) -> Optional[np.ndarray]:
        return None

    def close(self):
        pass
