import abc
from typing import Optional

import numpy as np


class CameraDriver(abc.ABC):
    """
    Defines an abstract camera driver that can be extended by concrete implementations.
    """

    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass

    @abc.abstractmethod
    def is_connected(self) -> bool:
        pass

    @abc.abstractmethod
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a frame from the camera. Returns None if no frame is available.

        Returns a numpy array of a grey scale image.
        """
        pass

    @abc.abstractmethod
    def close(self):
        pass
