# Autonomous-Light-Dark-Stimulus-System-for-Zebrafish-Behavioral-Studies

A custom-built light-dark stimulus system for enabling automated behavioural study experiments on juvenile zebrafish. The system uses an Arduino microcontroller to support automatic LED control and water temperature monitoring, and a PySide6 Python GUI for customizable video recording and automatic data acquisition. The complete system architecture consists of the software application, electronic system, and Arduino firmware.

## System Architecture
### Software Application
A PySide6 software application with two main device paths: a camera/video recording path and an Arduino-based stimulation path. 

#### GUI Design:
```
stimulation_and_gui
  └─ main.py
      └─ MainWindow
          ├─ StimulatorConnectionPanel ── StimulationController ── StimulatorDriver
          ├─ CameraPanel ──────────────── CameraProcessor ── CameraDriver
          │     └─ CameraPreviewWidget
          └─ TemperaturePanel ─────────── StimulationController
```
The Python-based GUI enables customizable experiments and video capture. The UI panels call into controller or processor objects that handle device access and background work.

#### Camera Path
- ```camera_panel.py``` enables customizable video recording. Allows the user choose a camera source, adjust image settings, view frames, save images, and record video. Displays camera preview via ```camera_preview_widget.py``` and refreshes the preview periodically using a Qt timer. 
- ```camera_processor.py``` handles frame processing. Reads frames on a worker thread and applies crop, flip, rotation, inversion, scaling, exposure/offset, and optional background subtraction. Publishes original and processed frames through the defined channel interface.
- The ```driver``` folder provides a way for the applications to connect to the camera source and retrieve image frames. It contains a shared ```CameraDriver``` class in ```camera_driver.py``` and three driver implementations:
  - ```flir_camera_driver.py``` allows the application to connect to the Forward Looking Infrared (FLIR) camera. Finds the available camera, initializes it for continuous acquisition, and begins video capturing. Uses FLIR’s PySpin/Spinnaker API.
  - ```replay_camera_driver.py``` enables video replay. Opens a video file with OpenCV.
  - ```dummy_camera_driver.py``` is an empty/default source implementation.

#### Stimulation Path
- ```stimulator_connection_panel.py``` handles port selection and controls connection to the Arduino.
- ```temperature_panel.py``` allows user to manually start and stop temperature measurement and displays the current reading in the UI.
- ```stimulation_controller.py``` is responsible for experiment/stimulation control: connecting to the Arduino, sending LED and temperature measurement commands, and reading stimulation data. It communicates the raw serial data to the stimulator driver for parsing.
- ```stimulator_driver.py``` parses incoming serial data to track stimulus application and temperature sensor values.

### Electronic System
A custom-designed electronic circuit architecture that integrates an Arduino microcontroller with external hardware peripherals to autonomously regulate and monitor environmental variables during experiments. 
#### Key Components
- **Arduino Uno microcontroller**: main hardware control unit, drives light stimulus application and collects temperature data from thermocouple
- **5V LED Strip**: delivers controlled light and dark stimulus to the zebrafish
- **Thermocouple Type-K Glass Braid Insulated - K**: monitors water temperature fluctuations
- **Thermocouple Amplifier MAX31855**: amplifies the weak thermocouple signals for data acquisition
- **30N06 MOSFET**: enables LED control via the Arduino's GPIO pin
- **Resistors**: current limiting and voltage division

### Firmware
An Arduino Uno microcontroller programmed to automatically apply and remove the light stimulus over a precise time interval set by the user. The program also continuously collects water temperature data and stimulus application timestamps over the entire experimental run, and sends the data to the software application over the Serial port for aggregation. 
