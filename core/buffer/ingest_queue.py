from collections import deque

class CoreBuffer:
    def __init__(self, max_size=100):
        self.queue = deque(maxlen=max_size)

    def add_metric(self, metric):
        self.queue.append(metric)
        return True

    def get_metric(self):
        if not self.queue:
            return None
        return self.queue.popleft()

    def clear_queue(self):
        if self.queue.clear():
            return True
        return False

    def size(self):
        if not self.queue:
            return 0
        return len(self.queue)
