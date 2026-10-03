from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QGroupBox,
                               QSplitter, QTabWidget, QVBoxLayout,
                               QWidget, QLabel)

from stimulation_controller import (StimulationController)

from camera_panel import CameraPanel
from stimulator_connection_panel import StimulatorConnectionPanel
## Rachel added
from camera_panel import CameraPanel
from camera_processor import CameraProcessor
from temperature_panel import TemperaturePanel


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.stimulator_controller = StimulationController()

        ## Rachel added
        self.camera_processor = CameraProcessor()

        self.setup_ui()
        self.resize(1000, 600)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(layout)

        title_label = QLabel("Light Stimulus Video Recorder")
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)

        title_label.setMaximumHeight(30)
        layout.addWidget(title_label)

        main_splitter = QSplitter()
        layout.addWidget(main_splitter)

        # left panel
        left_panel = QSplitter()
        left_panel.setOrientation(Qt.Orientation.Vertical)
        main_splitter.addWidget(left_panel)

        # device connection panels
        device_connection_group_box = QGroupBox()
        device_connection_group_box.setTitle("Device Connection")
        left_panel.addWidget(device_connection_group_box)

        device_connection_layout = QVBoxLayout()
        device_connection_group_box.setLayout(device_connection_layout)

        device_connection_layout.addWidget(StimulatorConnectionPanel(self.stimulator_controller))
        # device_connection_layout.addWidget(CameraConnectionPanel(self.cam_controller))

        # task panels
        cam_group_box = QGroupBox()
        cam_group_box.setTitle("Camera")
        left_panel.addWidget(cam_group_box)

        cam_layout = QVBoxLayout()
        cam_group_box.setLayout(cam_layout)
        # cam_tab_widget = QTabWidget()
        cam_layout.addWidget(CameraPanel(self.camera_processor, self.stimulator_controller))
        # cam_layout.addWidget(cam_tab_widget)

        # temperature panel
        temp_group_box = QGroupBox()
        temp_group_box.setTitle("Temperature")
        left_panel.addWidget(temp_group_box)

        temp_layout = QVBoxLayout()
        temp_group_box.setLayout(temp_layout)

        temp_layout.addWidget(TemperaturePanel(self.stimulator_controller))

        # default layout stretch
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 3)

        left_panel.setStretchFactor(0, 0)
        left_panel.setStretchFactor(1, 1)

    def closeEvent(self, event):
        self.stimulator_controller.disconnect()
        self.camera_processor.stop()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
