from collections import deque


class MemoryQueue:
    def __init__(self, maxlen=100):
        self.queue = deque(maxlen=maxlen)

    def push(self, data):

        return self.queue.append(data)

    def peek(self):
        if self.queue:
            return self.queue[0]
        return None


    def pop(self):
        if self.queue:
            return self.queue.popleft()
        return None

    def size(self):
        return len(self.queue)

    def is_empty(self):
        return True if len(self.queue) == 0 else False

    def clear(self):
        self.queue.clear()

    def get_queue(self):
        return self.queue
