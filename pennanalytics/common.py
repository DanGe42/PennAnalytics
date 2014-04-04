# link: bytes received/sent since last tick, bytes received/sent % bandwidth
#   since last tick, bytes receieved/sent % bandwidth cumulative average
# node: capacity, bytes received/sent since last tick

import collections
import config
import math
import time


class NetworkLink(object):

    MAX_QUEUE_LENGTH = 2

    def __init__(self, remote_sys_name, capacity, bytes_recv=0, bytes_sent=0):
        self.remote_sys_name = remote_sys_name
        self.capacity = capacity
        self.bytes_recv_hist = collections.deque(maxlen=NetworkLink.MAX_QUEUE_LENGTH)
        self.bytes_sent_hist = collections.deque(maxlen=NetworkLink.MAX_QUEUE_LENGTH)
        self.bytes_recv_hist.appendleft(bytes_recv)
        self.bytes_sent_hist.appendleft(bytes_sent)
        self.requests = 1
        self.input_util_avg = 0.0
        self.output_util_avg = 0.0

    @property
    def bytes_recv(self):
        return self.bytes_recv_hist[0]

    @property
    def bytes_sent(self):
        return self.bytes_sent_hist[0]

    @property
    def bytes_transferred(self):
        return self.bytes_recv_hist[0] + self.bytes_sent_hist[0]

    def __repr__(self):
        return "NetworkLink(remote_sys_name=%s, capacity=%d, bytes_recv=%d, bytes_sent=%d)" % \
               (self.remote_sys_name, self.capacity, self.bytes_recv, self.bytes_sent)

    def bytes_recv_delta(self):
        return self.bytes_recv_hist[0] - self.bytes_recv_hist[1]

    def bytes_sent_delta(self):
        return self.bytes_sent_hist[0] - self.bytes_sent_hist[1]

    # TODO: remove time interval hard codes
    def input_utilization(self):
        return float(self.bytes_recv_delta() * 8) / (config.query_interval_seconds * self.capacity)

    def output_utilization(self):
        return float(self.bytes_sent_delta() * 8) / (config.query_interval_seconds * self.capacity)

    def update(self, bytes_recv, bytes_sent):
        self.requests += 1
        if bytes_recv < self.bytes_recv_hist[0]:
            bytes_recv += 2 ** 32 + bytes_recv
        if bytes_sent < self.bytes_sent_hist[0]:
            bytes_sent += 2 ** 32 + bytes_sent

        self.bytes_recv_hist.appendleft(bytes_recv)
        self.bytes_sent_hist.appendleft(bytes_sent)

        if self.requests >= 2:
            self.input_util_avg += (self.input_utilization() - self.input_util_avg) / (
                self.requests - 1)
            self.output_util_avg += (self.output_utilization() - self.output_util_avg) / (
                self.requests - 1)

    def serialize(self):
        return {
            "remote_sys_name": self.remote_sys_name,
            "capacity": self.capacity,
            "stats": {
                "bytes_recv_last_interval": self.bytes_recv_delta(),
                "bytes_sent_last_interval": self.bytes_sent_delta(),
                "bytes_recv_moving_average": "%.3f" % self.input_util_avg,
                "bytes_sent_moving_average": "%.3f" % self.output_util_avg,
                "upload_utilization": "%.3f" % self.output_utilization(),
                "download_utilization": "%.3f" % self.input_utilization()
            }
        }


class NetworkNode(dict):

    def __init__(self, sys_name, physical_addr):
        super(NetworkNode, self).__init__()
        self._sys_name = sys_name
        self.physical_addr = physical_addr

    @property
    def sys_name(self):
        return self._sys_name

    def __repr__(self):
        return "NetworkNode('%s', %s)" % (self.sys_name, super(NetworkNode, self).__repr__())

    def add_remote(self, port, remote_sys_name, capacity):
        self[port] = NetworkLink(remote_sys_name, capacity, 0, 0)

    def update_remote(self, port, bytes_recv, bytes_sent):
        self[port].update(bytes_recv, bytes_sent)

    def total_capacity(self):
        return sum(link.capacity for link in self.itervalues())

    def total_bytes_received(self):
        return sum(link.bytes_recv for link in self.itervalues())

    def total_bytes_sent(self):
        return sum(link.bytes_sent for link in self.itervalues())

    def total_bytes_received_delta(self):
        return sum(link.bytes_recv_delta() for link in self.itervalues())

    def total_bytes_sent_delta(self):
        return sum(link.bytes_sent_delta() for link in self.itervalues())

    def serialize(self, timestamp=None):
        timestamp = timestamp or int(math.floor(time.time()))
        return {
            "name": self.sys_name,
            "timestamp": timestamp,
            "links": {port: link.serialize() for port, link in self.iteritems()}
        }
