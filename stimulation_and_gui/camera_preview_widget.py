import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy


class CameraPreviewWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setText("Camera Preview")
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.setMinimumSize(50, 50)

    def updateFrame(self, frame: np.ndarray):
        if frame is not None:
            height, width = frame.shape[:2]
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGBA)
            else:
                if frame.shape[2] == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                elif frame.shape[2] == 4:
                    pass
            # has to use RGBA due to a bug in PySide6. Image width buffer size must be aligned to 4 bytes
            img = QImage(frame.data, width, height, QImage.Format.Format_RGBA8888)
            self.setPixmap(QPixmap.fromImage(img).scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio))
