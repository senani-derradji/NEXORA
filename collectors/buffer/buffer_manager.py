from buffer.memory_queue import MemoryQueue
from buffer.dbs_buffer.disk_queue import DatabaseBuffer
from transport.grpc_client import CoreClient


class BufferManager:
    def __init__(self):
        self.mem = MemoryQueue()
        self.disk = DatabaseBuffer()
        self.client = CoreClient()

    def push_data(self, metric, status):

        if status:
            self.mem.push(metric)
            disk_rows = self.disk.fetch_all_unsent()

            if disk_rows:

                for d in disk_rows:
                    all_sent = True
                    resp = self.client.send_metric(metric=d.payload)

                    if not resp: all_sent = False ; break

                    if all_sent: self.disk.mark_sent(d.id)

                    else: break

        else: self.disk.store_buffer(data=metric)

    def pop_data(self): return self.mem.pop()
