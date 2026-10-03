import abc
import dataclasses
import enum
from typing import Any, Callable, Optional, Union

from PySide6.QtWidgets import QWidget


class ProcessorConfigType(enum.Enum):
    INT = enum.auto()
    FLOAT = enum.auto()
    CHOICE = enum.auto()
    SLIDER = enum.auto()
    BOOL = enum.auto()


@dataclasses.dataclass
class ProcessorConfigMeta:
    name: str
    conf_type: ProcessorConfigType
    min: Union[int, float] = 0
    max: Union[int, float] = 100
    default: Union[int, float, bool] = 0
    choices: list[str] = dataclasses.field(default_factory=list)


class Processor(abc.ABC):
    def __init__(self) -> None:
        super().__init__()

        self._channel_callbacks: dict[str, set[Callable[[str, object], None]]] = {}
        self._channel_values: dict[str, object] = {}
        self.config_params: dict[str, Any] = {}

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def list_channels(self) -> list[str]:
        pass

    def get_channel(self, name: str) -> Optional[object]:
        return self._channel_values.get(name, None)

    def add_channel_listener(self, name: str, callback: Callable[[str, object], None]):
        """Add a listener for a channel. If name is empty str, listen to all channels."""
        if name not in self._channel_callbacks:
            self._channel_callbacks[name] = set()
        self._channel_callbacks[name].add(callback)

    def remove_channel_listener(self, name: str, callback: Callable[[str, object], None]):
        if name in self._channel_callbacks:
            try:
                self._channel_callbacks[name].remove(callback)
            except KeyError:
                pass

    def push_channel(self, name: str, value: object):
        self._channel_values[name] = value
        if name in self._channel_callbacks:
            for callback in self._channel_callbacks[name]:
                try:
                    callback(name, value)
                except Exception as e:
                    print(f"Failed to call callback:{type(e)}, {e}")
                    print(f"Callback: {callback}")
                    print(f"Name: {name}")

        if "" in self._channel_callbacks:
            for callback in self._channel_callbacks[""]:
                try:
                    callback(name, value)
                except Exception as e:
                    print(f"Failed to call callback:{type(e)}, {e}")
                    print(f"Callback: {callback}")
                    print(f"Name: {name}")

    @abc.abstractmethod
    def get_preview(self) -> Optional[object]:
        pass

    @abc.abstractmethod
    def get_fps(self) -> float:
        pass

    @abc.abstractmethod
    def get_config_meta(self) -> list[ProcessorConfigMeta | tuple[ProcessorConfigMeta]]:
        pass

    def get_config(self, name: str) -> object:
        return self.config_params.get(name, None)

    def set_config(self, name: str, value: object):
        self.config_params[name] = value

    def get_custom_widget(self) -> Optional[QWidget]:
        """return a custom widget for the processor panel if needed"""
        return None
