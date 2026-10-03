
from typing import Callable


class DataProvider:
    def __init__(self, streams: dict[str, list[str]]):
        self.available_streams = streams
        self.stream_callbacks: list[Callable[[str, list[float]], None]] = []
        self.log_callbacks: list[Callable[[str | dict | list], None]] = []


    def push_stream_data(self, stream_name: str, data: list[float]):
        for callback in self.stream_callbacks:
            callback(stream_name, data)

    def push_log_data(self, data: str | dict | list):
        for callback in self.log_callbacks:
            callback(data)
    

    def add_stream_callback(self, callback: Callable[[str, list[float]], None]):
        if callback not in self.stream_callbacks:
            self.stream_callbacks.append(callback)

    def remove_stream_callback(self, callback: Callable[[str, list[float]], None]):
        try:
            self.stream_callbacks.remove(callback)
        except ValueError:
            pass

    def add_log_callback(self, callback: Callable[[str | dict | list], None]):
        if callback not in self.log_callbacks:
            self.log_callbacks.append(callback)

    def remove_log_callback(self, callback: Callable[[str | dict | list], None]):
        try:
            self.log_callbacks.remove(callback)
        except ValueError:
            pass

