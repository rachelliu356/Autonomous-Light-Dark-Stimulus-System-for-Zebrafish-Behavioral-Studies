import os
from typing import Optional

import cv2
import numpy as np

from driver.camera_driver import CameraDriver


class ReplayCameraDriver(CameraDriver):
    """
    A camera driver class for replaying a video file frame by frame.
    """

    def __init__(self, video_path: str = ""):
        self._video_path = video_path
        self._cap = None
        self._is_connected = False

    def __del__(self):
        self.close()

    def set_video_path(self, video_path: str):
        self._video_path = video_path

    def connect(self):
        if not os.path.isfile(self._video_path):
            return

        self._cap = cv2.VideoCapture(self._video_path)
        self._is_connected = self._cap.isOpened()

        if not self._is_connected:
            self._cap = None

    def disconnect(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._is_connected = False

    def is_connected(self) -> bool:
        return self._is_connected

    def read_frame(self) -> Optional[np.ndarray]:
        if self._cap is None or not self._is_connected:
            return None
        ret, frame = self._cap.read()
        if not ret:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._cap.read()
            if not ret:
                return None
        # Convert to grayscale
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def close(self):
        self.disconnect()
