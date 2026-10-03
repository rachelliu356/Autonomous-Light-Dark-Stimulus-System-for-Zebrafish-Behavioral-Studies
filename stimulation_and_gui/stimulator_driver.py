import os
import struct
import threading
import time

import serial
import serial.tools.list_ports


class StimulatorDriver:
    def __init__(self):
        self.ser = None
        self.thread = None
        self.tia_values = [0, 0, 0, 0]
        self.extra_ain_values = [0, 0]

        # Rachel added
        self._record_dir_name = None
        self._record_time_str = None
        self.current_temp = -273
        self.record_temp = False
        self.last_checked_time = 0

    def set_record_metadata(self, dir_name, time_str):
        self._record_dir_name = dir_name
        self._record_time_str = time_str

    def connect(self, port):
        if self.is_connected():
            self.disconnect()

        self.ser = serial.Serial(port, 115200)
        time.sleep(2)
        self.thread = threading.Thread(target=self._poll_data)
        self.thread.start()

    def disconnect(self):
        if self.ser is not None:
            self.ser.close()
        self.ser = None

        if self.thread is not None:
            self.thread.join()
        self.thread = None

    def is_connected(self) -> bool:
        return self.ser is not None

    @staticmethod
    def scan_port() -> list[str]:
        ports = list(serial.tools.list_ports.comports())
        return [port.device for port in ports]
    
    def _poll_data(self):
        while self.ser:
            try:
                first_byte = self.ser.read(1)
                if not first_byte:
                    break

                # Check if first byte is ASCII printable (text message)
                if 32 <= first_byte[0] <= 126:
                    text_line = first_byte + self.ser.readline()
                    try:
                        decoded = text_line.decode("utf-8", errors="ignore").strip()
                        if decoded.startswith("TXT:"):
                            # print("Serial received:", decoded[4:].strip())
                            if "TXT: LED turned on" in decoded:
                                with open(os.path.join(self._record_dir_name, f"{self._record_time_str}.txt"), "a") as f:
                                    f.write(f"LED turned on, {time.time()}\n")
                            elif "TXT: LED turned off" in decoded:
                                with open(os.path.join(self._record_dir_name, f"{self._record_time_str}.txt"), "a") as f:
                                    f.write(f"LED turned off, {time.time()}\n")
                            elif "TXT: LED already on" in decoded:
                                with open(os.path.join(self._record_dir_name, f"{self._record_time_str}.txt"), "a") as f:
                                    f.write(f"LED already on\n")
                            elif "TXT: LED already off" in decoded:
                                with open(os.path.join(self._record_dir_name, f"{self._record_time_str}.txt"), "a") as f:
                                    f.write(f"LED already off\n")
                        elif decoded.startswith("TEMP:"):
                            # print(f"Current Temperature: {decoded[5:].strip()} °C")
                            self.current_temp = decoded[5:].strip()
                            current_time = time.time()
                            if self.record_temp and current_time-self.last_checked_time >= 60:
                                try:
                                    with open(os.path.join(self._record_dir_name, f"{self._record_time_str}_temperature_data.csv"), "a") as f1:
                                        f1.write(f"{self.current_temp}, {time.time()}\n")
                                    self.last_checked_time = current_time
                                except:
                                    pass

                    #     else:
                    #         print("Serial received:", decoded)
                    except:
                    #     print("Serial received (undecodable):", text_line)
                        continue
                    continue  # skip to next loop

                # Begin reading full binary packet
                data = first_byte + self.ser.read(13)

                if len(data) != 14:
                    print(f"[Warning] Incomplete packet: received {len(data)} bytes")
                    continue

                unpacked_data = struct.unpack("<BBhhhhhh", data)

                allign_success = False

                if unpacked_data[0] != 0b01010101 or unpacked_data[1] != 0b00000000:
                    print("error header detected, dropping data and auto aligning")

                    for i in range(256):
                        if not self.ser:
                            break
                        try:
                            c = self.ser.read(1)
                        except:
                            # no data, probably disconnected
                            break
                        if c[0] != 0b01010101:
                            continue
                        else:
                            c2 = self.ser.read(1)
                            if c2[0] == 0b00000000:
                                # both headers found, skip next body
                                self.ser.read(2 * 4 + 2 * 2)
                                allign_success = True
                                break

                    if not allign_success:
                        print("failed to align")
                        break

                self.tia_values = unpacked_data[2:6]
                self.extra_ain_values = unpacked_data[6:8]
            except:
                break  # probably disconnected

            

    def __del__(self):
        self.disconnect()



if __name__ == "__main__":
    driver = StimulatorDriver()
    driver.connect("COM3")

    driver.disconnect()
