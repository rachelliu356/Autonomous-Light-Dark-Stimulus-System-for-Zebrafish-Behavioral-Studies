import os
import time
from typing import Optional

import cv2
from driver import (
    CameraDriver,
    DummyCameraDriver,
    ReplayCameraDriver,
    get_camera_driver,
)
from camera_preview_widget import CameraPreviewWidget
from camera_processor import CameraProcessor
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from stimulation_controller import StimulationController


class CameraPanel(QGroupBox):
    def __init__(self, camera_processor: CameraProcessor, stimulation_controller: StimulationController):
        super().__init__()

        self._camera_processor = camera_processor
        self._camera_driver: Optional[CameraDriver] = None
        self._crop_range = [0, 1920, 0, 1080]

        ## Rachel added
        self._stimulation_controller = stimulation_controller

        self.setup_ui()

        # camera panel update timer
        self._camera_panel_update_timer = QTimer()
        self._camera_panel_update_timer.setInterval(50)
        self._camera_panel_update_timer.timeout.connect(self._update_camera_frame)
        self._camera_panel_update_timer.start()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Source selection
        source_selection_layout = QHBoxLayout()
        layout.addLayout(source_selection_layout)

        source_selection_combo = QComboBox()
        source_selection_combo.addItems(["Select Source", "FLIR Camera", "Replay Video"])
        source_selection_combo.currentTextChanged.connect(self._on_source_selection_changed)
        source_selection_layout.addWidget(source_selection_combo)

        video_selector_button = QPushButton("Select Video")
        video_selector_button.clicked.connect(self._on_select_video_clicked)
        source_selection_layout.addWidget(video_selector_button)

        # Camera Preview
        self._camera_preview = CameraPreviewWidget()
        layout.addWidget(self._camera_preview, 1)

        # Status
        self._camera_status = QLabel("Unavailable")
        layout.addWidget(self._camera_status)

        # Configs
        config_grid = QGridLayout()
        layout.addLayout(config_grid)

        config_grid.addWidget(QLabel("Exposure:"), 0, 0)
        exposure_spin = QDoubleSpinBox()
        exposure_spin.setRange(0, 20)
        exposure_spin.setSingleStep(0.1)
        exposure_spin.valueChanged.connect(self._camera_processor.set_exposure)
        config_grid.addWidget(exposure_spin, 0, 1)

        config_grid.addWidget(QLabel("Offset:"), 0, 2)
        offset_spin = QSpinBox()
        offset_spin.setRange(-255, 255)
        offset_spin.valueChanged.connect(self._camera_processor.set_offset)
        config_grid.addWidget(offset_spin, 0, 3)

        config_grid.addWidget(QLabel("Scale:"), 1, 0)
        scale_spin = QDoubleSpinBox()
        scale_spin.setRange(0, 1)
        scale_spin.setSingleStep(0.1)
        scale_spin.setValue(1)
        scale_spin.valueChanged.connect(self._camera_processor.set_scale)
        config_grid.addWidget(scale_spin, 1, 1)

        config_grid.addWidget(QLabel("FPS:"), 1, 2)
        fps_spin = QSpinBox()
        fps_spin.setRange(1, 160)
        fps_spin.valueChanged.connect(self._camera_processor.set_target_fps)
        config_grid.addWidget(fps_spin, 1, 3)

        invert_check = QCheckBox("Invert")
        invert_check.setChecked(False)
        invert_check.stateChanged.connect(self._camera_processor.set_invert)
        config_grid.addWidget(invert_check, 2, 0)

        flip_check = QCheckBox("Flip")
        flip_check.setChecked(False)
        flip_check.stateChanged.connect(self._camera_processor.set_flip)
        config_grid.addWidget(flip_check, 2, 1)

        rotate_combo = QComboBox()
        rotate_combo.addItems(["Rotate 0", "Rotate 90", "Rotate 180", "Rotate 270"])
        rotate_combo.currentIndexChanged.connect(lambda index: self._camera_processor.set_rotate(index * 90))
        config_grid.addWidget(rotate_combo, 2, 2)

        # Crop
        crop_layout = QVBoxLayout()
        layout.addLayout(crop_layout)

        x_crop_layout = QHBoxLayout()
        crop_layout.addLayout(x_crop_layout)
        x_crop_layout.addWidget(QLabel("X Crop:"))

        self._x_crop_min_spin = QSlider(orientation=Qt.Orientation.Horizontal)
        self._x_crop_min_spin.setRange(0, 1920)
        self._x_crop_min_spin.setSingleStep(1)
        self._x_crop_min_spin.setValue(0)

        def x_crop_min_changed(value):
            self._crop_range[0] = value
            self._camera_processor.set_crop(*self._crop_range)

        self._x_crop_min_spin.valueChanged.connect(x_crop_min_changed)
        x_crop_layout.addWidget(self._x_crop_min_spin)

        self._x_crop_max_spin = QSlider(orientation=Qt.Orientation.Horizontal)
        self._x_crop_max_spin.setRange(0, 1920)
        self._x_crop_max_spin.setSingleStep(1)
        self._x_crop_max_spin.setValue(1920)

        def x_crop_max_changed(value):
            self._crop_range[1] = value
            self._camera_processor.set_crop(*self._crop_range)

        self._x_crop_max_spin.valueChanged.connect(x_crop_max_changed)
        x_crop_layout.addWidget(self._x_crop_max_spin)

        y_crop_layout = QHBoxLayout()
        crop_layout.addLayout(y_crop_layout)
        y_crop_layout.addWidget(QLabel("Y Crop:"))

        self._y_crop_min_spin = QSlider(orientation=Qt.Orientation.Horizontal)
        self._y_crop_min_spin.setRange(0, 1080)
        self._y_crop_min_spin.setSingleStep(1)
        self._y_crop_min_spin.setValue(0)

        def y_crop_min_changed(value):
            self._crop_range[2] = value
            self._camera_processor.set_crop(*self._crop_range)

        self._y_crop_min_spin.valueChanged.connect(y_crop_min_changed)
        y_crop_layout.addWidget(self._y_crop_min_spin)

        self._y_crop_max_spin = QSlider(orientation=Qt.Orientation.Horizontal)
        self._y_crop_max_spin.setRange(0, 1080)
        self._y_crop_max_spin.setSingleStep(1)
        self._y_crop_max_spin.setValue(1080)

        def y_crop_max_changed(value):
            self._crop_range[3] = value
            self._camera_processor.set_crop(*self._crop_range)

        self._y_crop_max_spin.valueChanged.connect(y_crop_max_changed)
        y_crop_layout.addWidget(self._y_crop_max_spin)

        # video recording
        record_layout = QHBoxLayout()
        layout.addLayout(record_layout)

        record_layout.addWidget(QLabel("Video Record:"))

        self._video_record_line_edit = QLineEdit()
        record_layout.addWidget(self._video_record_line_edit)
        _video_record_path_browser_btn = QPushButton("Browse")
        ## Rachel added
        self._is_recording = False

        _video_record_path_browser_btn.clicked.connect(self._on_browse_video_record_path)
        record_layout.addWidget(_video_record_path_browser_btn)
        
        ## Rachel added and changed Record button to push button
        record_layout.addWidget(QLabel("Duration(min):"))
        self._video_duration_spinbox = QSpinBox()
        self._video_duration_spinbox.setMinimum(1)    
        self._video_duration_spinbox.setMaximum(60*48)  ## Max duration is 48 hours
        self._video_duration_spinbox.setValue(60)       
        record_layout.addWidget(self._video_duration_spinbox)
        
        self._video_record_btn = QPushButton("Record")
        self._video_record_btn.clicked.connect(self._toggle_video_record)
        record_layout.addWidget(self._video_record_btn)

        # save image
        save_image_button = QPushButton("Save Image")
        save_image_button.clicked.connect(self._on_save_image)
        layout.addWidget(save_image_button)

        # load or clear bg subtraction image
        layout.addWidget(QLabel("Background Subtraction:"))
        bg_subtract_layout = QHBoxLayout()
        layout.addLayout(bg_subtract_layout)
        _bg_subtract_image_browser_btn = QPushButton("Load")
        _bg_subtract_image_browser_btn.clicked.connect(self._on_load_bg_subtract_image)
        bg_subtract_layout.addWidget(_bg_subtract_image_browser_btn)
        _bg_subtract_image_clear_btn = QPushButton("Clear")
        _bg_subtract_image_clear_btn.clicked.connect(self._on_clear_bg_subtract_image)
        bg_subtract_layout.addWidget(_bg_subtract_image_clear_btn)


    def _on_load_bg_subtract_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", filter="Images (*.png *.jpg)")
        if filename:
            bg_img = cv2.imread(filename)
            if bg_img is None:
                return
            self._camera_processor._bg_subtraction_img = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)

    def _on_clear_bg_subtract_image(self):
        self._camera_processor._bg_subtraction_img = None

    def _on_save_image(self):
        filename, file_type = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG (*.png)")
        if filename == "":
            return
        if not filename.endswith(".png"):
            filename += ".png"
        current_img = self._camera_processor.get_processed_frame()
        if current_img is not None:
            cv2.imwrite(filename, current_img)

    ## Rachel added
    def _toggle_video_record(self):
        #if not self._is_recording:
        if self._video_record_btn.text() == "Record":
            dir_name = self._video_record_line_edit.text()
            if dir_name == "":
                print("No directory selected")
                return
        
            time_str = time.strftime("%Y-%m-%d-%H%M%S")
            self._stimulation_controller._driver.set_record_metadata(dir_name, time_str)
            file_name = os.path.join(dir_name, f"{time_str}.avi")
            start_time = time.time()
            success = self._camera_processor.start_video_recording(file_name)
            if success:
                self._stimulation_controller._driver.record_temp = True
            with open(os.path.join(dir_name, f"{time_str}.txt"), "w") as f:
                f.write(f"Started video recording, {start_time}\n")
                f.write(f"FPS: {self._camera_processor.get_target_fps():.2f}\n")
            self._stimulation_controller.turn_led_strip_on()
        
            if not success:
                print("Failed to start video recording")
                with open(os.path.join(dir_name, f"{time_str}.txt"), "a") as f:
                    f.write(f"Video recording failed.\n")
                return
        
            duration_minutes = self._video_duration_spinbox.value()
        
            print(f"Recording started for {duration_minutes} minutes.")
            self._video_record_btn.setText("Stop Recording")  
            # self._video_record_btn.setEnabled(False)      

            # Automatically stop after duration
            QTimer.singleShot(duration_minutes*60 * 1000, lambda: (
                self._camera_processor.stop_video_recording(),
                self._stimulation_controller.turn_led_strip_on_end(),
                self._video_record_btn.setText("Record"),
                # self._video_record_btn.setEnabled(True),
                self.set_record_temp_false(),
                print("Video recorded.")
            ))
        elif self._video_record_btn.text() == "Stop Recording":
            self._camera_processor.stop_video_recording()
            self._stimulation_controller.turn_led_strip_on_end()
            self._video_record_btn.setText("Record")
            # self._video_record_btn.setEnabled(True)
            self.set_record_temp_false()
            with open(os.path.join(self._stimulation_controller._driver._record_dir_name, f"{self._stimulation_controller._driver._record_time_str}.txt"), "a") as f:
                f.write(f"Video recording stopped, {time.time()}\n")
            print("Video reecording stopped.")

    def set_record_temp_false(self):
        self._stimulation_controller._driver.record_temp = False
        print("Stopped recording temperature")
        
    def set_is_recording_true(self):
        self._is_recording = True

    def set_is_recording_false(self):
        self._is_recording = False

    def _on_browse_video_record_path(self):
        filename = QFileDialog.getExistingDirectory(self, "Choose Directory for Video")
        if filename == "":
            return
        self._video_record_line_edit.setText(filename)

    def _on_source_selection_changed(self, text: str):
        if text == "Select Source":
            source = DummyCameraDriver()
        elif text == "FLIR Camera":
            source = get_camera_driver()
        elif text == "Replay Video":
            source = ReplayCameraDriver()
        else:
            source = DummyCameraDriver()

        self._camera_processor.stop()
        if self._camera_driver is not None:
            self._camera_driver.close()
        self._camera_driver = source
        source.connect()
        self._camera_processor.set_camera_driver(source)
        self._camera_processor.start()

    def _on_select_video_clicked(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video")
        if filename and isinstance(self._camera_driver, ReplayCameraDriver):
            self._camera_processor.stop()
            self._camera_driver.set_video_path(filename)
            self._camera_driver.connect()
            self._camera_processor.start()

    def _update_camera_frame(self):
        processed_frame = self._camera_processor.get_processed_frame()
        if processed_frame is not None:
            self._camera_preview.updateFrame(processed_frame)

        original_frame = self._camera_processor.get_original_frame()
        if original_frame is not None:
            h, w = original_frame.shape[0:2]
            self._camera_status.setText(f"Size: {w}x{h} - FPS: {self._camera_processor.get_real_fps():.2f}")

            self._x_crop_min_spin.setRange(0, w)
            self._x_crop_max_spin.setRange(0, w)
            self._y_crop_min_spin.setRange(0, h)
            self._y_crop_max_spin.setRange(0, h)
