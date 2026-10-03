
import os
import threading
import queue
import time
from typing import Optional
from serial import Serial
from serial.tools import list_ports

from data_provider import DataProvider
from stimulator_driver import StimulatorDriver


"""
Used to control the Arduino based stimulator.

The stimulator is controlled over a serial connection and this module provides
methods to connect to, disconnect from, and send commands to the stimulator.

The stimulator has two main actions:

- Turn the LED light strip on and off.
- Start and stop measuring temperature.

Remember to call `disconnect` when you are done with the controller. It keeps an
internal thread that reads from the Arduino, if `disconnect` is not called the
thread will not stop.
"""

class StimulationController:
    def __init__(self) -> None:
        self._driver = StimulatorDriver()

        self._data_provider = DataProvider({'tia': ['current']})

        self._reading_thread = None

    def list_ports(self) -> list[str]:
        return self._driver.scan_port()
    
    def connect(self, port: str) -> None:
        self._driver.connect(port)
        print("Connected to:", port)

        self._reading_thread = threading.Thread(target=self._reading_thread_main)
        self._reading_thread.start()

    def disconnect(self) -> None:
        if self._driver and self._driver.is_connected():
            try:
                self.stop_measuring_temp()
                self.turn_led_strip_on_end()
            except Exception as e:
                print("Cleanup error:", e)

        self._driver.disconnect()
        print("Disconnected")

        if self._reading_thread is not None:
            self._reading_thread.join()
            self._reading_thread = None

    def is_connected(self) -> bool:
        return self._driver.is_connected()
    
    def _reading_thread_main(self) -> None:
        while True:
            if self._driver is None or not self._driver.is_connected():
                break
            try:
                self._data_provider.push_stream_data("tia", [self._driver.tia_values[0] / 1000])
            except (ValueError, UnicodeDecodeError):
                pass
            time.sleep(0.01)

    ## Rachel added
    def turn_led_strip_on(self):
        command = b'1'
        self._driver.ser.write(command)
        with open(os.path.join(self._driver._record_dir_name, f"{self._driver._record_time_str}.txt"), "a") as f:
            f.write(f"Command sent to Arduino for LED to be turned on, {time.time()}\n")

    def turn_led_strip_on_end(self):
        command = b'0'
        self._driver.ser.write(command)
        with open(os.path.join(self._driver._record_dir_name, f"{self._driver._record_time_str}.txt"), "a") as f:
            f.write(f"Command sent to Arduino for LED to be turned on, {time.time()}\n")

    def start_measuring_temp(self):
        command = b'2'
        self._driver.ser.write(command)
        if self._driver.record_temp:
            try:
                with open(os.path.join(self._driver._record_dir_name, f"{self._driver._record_time_str}_temperature_data.csv"), "a") as f1:
                    f1.write(f"Started recording temperature data, {time.time()}\n")
            except:
                print("Start recording video to record temperature data.")
 
    def stop_measuring_temp(self):
        command = b'3'
        self._driver.ser.write(command)
        if self._driver.record_temp:
            try:
                with open(os.path.join(self._driver._record_dir_name, f"{self._driver._record_time_str}_temperature_data.csv"), "a") as f1:
                    f1.write(f"Stopped recording temperature data, {time.time()}\n")
            except:
                pass
        

if __name__ == "__main__":
    controller = StimulationController()
    controller.connect("/dev/ttyUSB0")
    time.sleep(3)
    controller.set_voltage(10)
    time.sleep(3)
    controller.trigger_pulse(100)
    time.sleep(3)
    controller.disconnect()
