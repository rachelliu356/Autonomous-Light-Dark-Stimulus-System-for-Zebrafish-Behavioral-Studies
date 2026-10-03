import time


class FPSHelper:
    def __init__(self, window_size: int = 20):
        self._window_size = window_size
        self._previous_ticks = []
        self._fps = -1

    def tick(self):
        now = time.time()
        self._previous_ticks.append(now)
        while len(self._previous_ticks) > self._window_size:
            self._previous_ticks.pop(0)

    def get_fps(self) -> float:
        if len(self._previous_ticks) == 0:
            return -1
        delta = self._previous_ticks[-1] - self._previous_ticks[0]
        if delta <= 0:
            return -1
        return len(self._previous_ticks) / delta

    def reset(self):
        self._previous_ticks = []
        self._fps = -1
