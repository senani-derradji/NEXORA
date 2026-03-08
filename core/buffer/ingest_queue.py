from collections import deque

class CoreBuffer:
    def __init__(self, max_size=1000):
        self._queue = deque(maxlen=max_size)

    def add_metric(self, metric):
        self._queue.append(metric)
        return True

    def get_metric(self):
        if not self._queue:
            return None
        return self._queue.popleft()

    def clear_queue(self):
        if self._queue.clear():
            return True
        return False

    def size(self):
        if not self._queue:
            return 0
        return len(self._queue)