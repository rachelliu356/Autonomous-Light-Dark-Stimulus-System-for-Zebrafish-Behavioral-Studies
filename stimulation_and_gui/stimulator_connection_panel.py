from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QToolButton,
                               QVBoxLayout, QWidget)

from stimulation_controller import StimulationController

class StimulatorConnectionPanel(QWidget):
    def __init__(self, stimulator_controller: StimulationController):
        super().__init__()
        self.stimulator_controller = stimulator_controller

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.status_label = QLabel("Arduino (Disconnected)")
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        self.port_combo = QComboBox()
        button_layout.addWidget(self.port_combo)

        refresh_button = QToolButton()
        refresh_button.setText("Refresh")
        button_layout.addWidget(refresh_button)
        refresh_button.clicked.connect(self.refresh_ports)

        connect_button = QToolButton()
        connect_button.setText("Connect")
        button_layout.addWidget(connect_button)
        connect_button.clicked.connect(self.connect_arduino)

        disconnect_button = QToolButton()
        disconnect_button.setText("Disconnect")
        button_layout.addWidget(disconnect_button)
        disconnect_button.clicked.connect(self.disconnect_arduino)

    def refresh_ports(self):
        self.port_combo.clear()
        self.port_combo.addItems(self.stimulator_controller.list_ports())

    def connect_arduino(self):
        if self.stimulator_controller.is_connected():
            print('arduino already connected')
            return
        
        selected_port = self.port_combo.currentText()
        print("Connecting to Arduino")
        try:
            self.stimulator_controller.connect(selected_port)
        except Exception as e:
            print(e)
            print("Failed to connect to arduino")
            return
        self.status_label.setText(f"Arduino (Connected {selected_port})")

    def disconnect_arduino(self):
        print("Disconnecting from Arduino")
        self.stimulator_controller.disconnect()
        self.status_label.setText("Arduino (Disconnected)")

