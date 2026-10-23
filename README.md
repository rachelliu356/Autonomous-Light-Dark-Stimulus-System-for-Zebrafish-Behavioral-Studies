# Autonomous-Light-Dark-Stimulus-System-for-Zebrafish-Behavioral-Studies

A custom-built light-dark stimulus system for enabling automated behavioural study experiments on juvenile zebrafish. The system uses an Arduino microcontroller to support automatic LED control and water temperature monitoring, and a PySide6 Python GUI for customizable video recording and automatic data acquisition. The complete system architecture consists of the software application, electronic system, and Arduino firmware.

## System Architecture
### Software Application
A PySide6 software application with two main device paths: a camera /video recording path and an Arduino-based stimulation path. 

#### GUI Design:
```
main.py
  └─ MainWindow
      ├─ CameraPanel ──────────────── CameraProcessor ── CameraDriver
      │     └─ CameraPreviewWidget
      ├─ StimulatorConnectionPanel ── StimulationController ── StimulatorDriver
      └─ TemperaturePanel ─────────── StimulationController
```
The Python-based GUI enables customizable experiments and video recording. The GUI panels call into controller or processor objects that handle device access and background work.

#### Camera Path
- ```camera_panel.py``` allows the user choose a camera source, adjust image settings, view frames, save images, and record video. Displays camera preview via ```camera_preview_widget.py``` and refreshes the preview periodically using a Qt timer. 
- ```camera_processor.py``` reads frames on a worker thread and applies crop, flip, rotation, inversion, scaling, exposure/offset, and optional background subtraction. Publishes original and processed frames through the defined channel interface.

#### Stimulation Path


### Electronic System

### Firmware
An Arduino UNO microcontroller programmed to automatically apply and remove the light stimulus over a precise time interval set by the user. The program also continuously collects water temperature data and stimulus application timestamps over the entire experimental run, and sends the data to the software application over the Serial port for aggregation. 
