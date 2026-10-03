import logging
import queue
import threading
import time
from typing import Optional

import cv2
import numpy as np
from driver.camera_driver import CameraDriver
from processor import Processor, ProcessorConfigMeta
from utils.fps_helper import FPSHelper

logger = logging.getLogger(__name__)


class CameraProcessor(Processor):
    def __init__(self):
        super().__init__()

        self._camera_driver: Optional[CameraDriver] = None
        self._thread: Optional[threading.Thread] = None
        self._thread_stop_event = threading.Event()

        self._processed_frame: Optional[np.ndarray] = None
        self._original_frame: Optional[np.ndarray] = None

        self._target_fps = 150
        self._fps_helper = FPSHelper()

        self._rotate = 0
        self._crop = [0, 0, 0, 0]
        self._exposure = 1.0
        self._offset = 0.0
        self._invert = False
        self._scale = 1.0
        self._flip = False

        # bg subtraction
        self._bg_subtraction_img: Optional[np.ndarray] = None

        # video recording
        self._video_writer_queue = queue.Queue(maxsize=500)
        self._video_writer_thread: Optional[threading.Thread] = None
        self._video_writer: Optional[cv2.VideoWriter] = None
        self._video_writer_lock = threading.Lock()

        ## Rachel added
        self._stop_video_writer = threading.Event()

    def list_channels(self) -> list[str]:
        return [
            "original_frame",
            "processed_frame",
        ]

    def start(self):
        if self._camera_driver is None:
            raise ValueError("Camera driver not set")

        if self.is_running():
            return

        self._thread_stop_event.clear()
        self._thread = threading.Thread(target=self._thread_func)
        self._thread.start()

    def stop(self):
        self.stop_video_recording()
        if self._thread is not None:
            self._thread_stop_event.set()
            self._thread.join()

    def start_video_recording(self, path: str) -> bool:
        if not self.is_running():
            return False
        if self._processed_frame is None:
            return False
        with self._video_writer_lock:
            self._video_writer = cv2.VideoWriter(
                path,
                ## Rachel changed from "FFV1 to XVID"
                cv2.VideoWriter.fourcc(*"MJPG"),
                self._target_fps,
                (self._processed_frame.shape[1], self._processed_frame.shape[0]),
                isColor = False
            )
            # Rachel added line
            self._stop_video_writer.clear()

            self._video_writer_thread = threading.Thread(target=self._video_writer_thread_func)
            self._video_writer_thread.start()
        return True

    def stop_video_recording(self) -> bool:
        ## Rachel added line
        self._stop_video_writer.set()
        
        with self._video_writer_lock:
            if self._video_writer is not None:
                self._video_writer.release()
                self._video_writer = None

        if self._video_writer_thread is not None:
            self._video_writer_thread.join()
            self._video_writer_thread = None

        # clear the queue
        while not self._video_writer_queue.empty():
            self._video_writer_queue.get()
        return True

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def set_camera_driver(self, camera_driver: CameraDriver):
        self._camera_driver = camera_driver

    def get_processed_frame(self) -> Optional[np.ndarray]:
        return self._processed_frame

    def get_original_frame(self) -> Optional[np.ndarray]:
        return self._original_frame

    def get_real_fps(self) -> float:
        return self._fps_helper.get_fps()

    def set_target_fps(self, fps: float):
        self._target_fps = fps

    def get_target_fps(self) -> float:
        return self._target_fps

    def set_crop(self, x_min: int, x_max: int, y_min: int, y_max: int):
        # stop video recording, as resolution changed
        self.stop_video_recording()
        # set new crop
        self._crop = [x_min, x_max, y_min, y_max]

    def set_exposure(self, exposure: float):
        self._exposure = exposure

    def set_offset(self, offset: int):
        self._offset = offset

    def set_invert(self, invert: bool):
        self._invert = invert

    def set_scale(self, scale: float):
        self._scale = scale

    def set_rotate(self, rotate: int):
        self._rotate = rotate

    def set_flip(self, flip: bool):
        self._flip = flip

    def _thread_func(self):
        last_frame_time = time.time()

        while not self._thread_stop_event.is_set():
            if self._camera_driver is None:
                logger.error("Camera driver not set")
                break

            if not self._camera_driver.is_connected():
                logger.error("Camera not connected")
                break

            frame = self._camera_driver.read_frame()
            if frame is None:
                time.sleep(1 / 200)
                continue

            # processing
            # crop
            crop_x_min, crop_x_max, crop_y_min, crop_y_max = self._crop
            crop_y_max = min(crop_y_max, frame.shape[0])
            crop_x_max = min(crop_x_max, frame.shape[1])
            if crop_x_min >= crop_x_max or crop_y_min >= crop_y_max:
                # invalid crop, skip
                cropped_img = frame
            else:
                cropped_img = frame[crop_y_min:crop_y_max, crop_x_min:crop_x_max]

            # flip
            if self._flip:
                cropped_img = cv2.flip(cropped_img, 0)

            # rotate
            if self._rotate == 90:
                cropped_img = cv2.rotate(cropped_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            elif self._rotate == 180:
                cropped_img = cv2.rotate(cropped_img, cv2.ROTATE_180)
            elif self._rotate == 270:
                cropped_img = cv2.rotate(cropped_img, cv2.ROTATE_90_CLOCKWISE)

            # invert
            if self._invert:
                cropped_img = cv2.bitwise_not(cropped_img)

            # scale
            if self._scale != 1.0 and self._scale >= 0.01:
                cropped_img = cv2.resize(
                    cropped_img,
                    (0, 0),
                    fx=self._scale,
                    fy=self._scale,
                    interpolation=cv2.INTER_AREA,
                )

            # exposure and offset
            if self._exposure != 1.0 or self._offset != 0.0:
                cropped_img = np.clip(cropped_img * self._exposure + self._offset, 0, 255).astype(np.uint8)

            # bg subtraction
            bg_img = self._bg_subtraction_img
            if bg_img is not None:
                if bg_img.shape == cropped_img.shape:
                    cropped_img = cv2.subtract(cropped_img, bg_img)

            # update channels
            self._original_frame = np.ascontiguousarray(frame)
            self._processed_frame = np.ascontiguousarray(cropped_img)
            self.push_channel("original_frame", self._original_frame)
            self.push_channel("processed_frame", self._processed_frame)
            # video recording
            if self._video_writer is not None:
                # record_frame = cv2.cvtColor(self._processed_frame, cv2.COLOR_GRAY2BGR)
                if len(self._processed_frame.shape) == 3 and self._processed_frame.shape[2] == 3:
                    # convert RGB/BGR to grayscale
                    record_frame = cv2.cvtColor(self._processed_frame, cv2.COLOR_BGR2GRAY)
                else:
                    # already grayscale
                    record_frame = self._processed_frame

                self._video_writer_queue.put(record_frame)

            # sleep until next frame
            next_frame_time = last_frame_time + 1 / self._target_fps
            current_time = time.time()
            time_to_sleep = next_frame_time - current_time
            if time_to_sleep > 0:
                time.sleep(min(time_to_sleep, 0.5))  # limit sleep to 0.5 seconds max just in case
            elif time_to_sleep < -0.1:
                # lagging more than 0.1 seconds, skip frames
                logger.warning("Lagging more than 0.1 seconds, skipping frames")
                next_frame_time = current_time + 1 / self._target_fps

            self._fps_helper.tick()
            last_frame_time = next_frame_time

    def _video_writer_thread_func(self):
        # while self._video_writer is not None:
        #     if self._video_writer_queue.empty():
        #         time.sleep(0.01)
        #         continue

        #     record_frame = self._video_writer_queue.get()
        #     with self._video_writer_lock:
        #         if self._video_writer is not None:
        #             self._video_writer.write(record_frame)

        ## Rachel added
        while not self._stop_video_writer.is_set():
            try:
                record_frame = self._video_writer_queue.get(timeout=0.1)
            except queue.Empty:
                continue
    
            with self._video_writer_lock:
                if self._video_writer is not None:
                    self._video_writer.write(record_frame)

        print("Video thread stopping")

    def get_preview(self) -> object | None:
        return self.get_channel("processed_frame")

    def get_fps(self) -> float:
        return self._fps_helper.get_fps()

    def get_config_meta(self) -> list[ProcessorConfigMeta]:
        return []
