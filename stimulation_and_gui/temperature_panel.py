from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QToolButton,
                               QVBoxLayout, QWidget)
from PySide6.QtCore import QTimer

from stimulation_controller import StimulationController

class TemperaturePanel(QWidget):
    def __init__(self, stimulator_controller = StimulationController):
        super().__init__()
        self.stimulator_controller = stimulator_controller
        self.temp_update_timer = QTimer(self)
        self.temp_update_timer.timeout.connect(self.update_temp_display)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.status_label = QLabel("Current Temperature: Not Available")
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        self.start_button = QToolButton()
        self.start_button.setText("Start Measuring")
        button_layout.addWidget(self.start_button)
        self.start_button.clicked.connect(self.start_clicked)

    def start_clicked(self):
        if (self.start_button.text() == "Start Measuring"):
            self.stimulator_controller.start_measuring_temp()
            self.start_button.setText("Stop Measuring")
            self.temp_update_timer.start(1000)
        else:
            self.stimulator_controller.stop_measuring_temp()
            self.status_label.setText("Current Temperature: Not Available")
            self.start_button.setText("Start Measuring")
            self.temp_update_timer.stop()

    def update_temp_display(self):
        try:
            if self.stimulator_controller.is_connected():
                temp = self.stimulator_controller._driver.current_temp
                current_label = self.status_label.text()[21:].strip()
                if temp != current_label:
                    self.status_label.setText(f"Current Temperature: {temp} °C")
            else:
                self.status_label.setText("Current Temperature: Not Available")
                self.start_button.setText("Start Measuring")
                self.temp_update_timer.stop()
        except:
            self.status_label.setText("Current Temperature: Not Available")
            self.start_button.setText("Start Measuring")
            self.temp_update_timer.stop()
