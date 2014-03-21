from __future__ import print_function

import collections


class NetworkStats(object):

    def __init__(self, bytes_recv=0, bytes_sent=0):
        self.bytes_recv_hist = collections.deque(maxlen=10)
        self.bytes_sent_hist = collections.deque(maxlen=10)
        self.bytes_recv_hist.appendleft(bytes_recv)
        self.bytes_sent_hist.appendleft(bytes_sent)

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
        return "NetworkStats(bytes_recv=%d, bytes_sent=%d)" \
               % (self.bytes_recv, self.bytes_sent)

    def update(self, bytes_recv, bytes_sent):
        self.bytes_recv_hist.appendleft(bytes_recv)
        self.bytes_sent_hist.appendleft(bytes_sent)

    def serialize(self):
        return {
            "bytes_recv_history": list(self.bytes_recv_hist),
            "bytes_sent_history": list(self.bytes_sent_hist)
        }


class NetworkLink(object):

    def __init__(self, remote_sys_name, capacity, stats):
        self.remote_sys_name = remote_sys_name
        self.capacity = capacity
        self.stats = stats

    def __repr__(self):
        return "NetworkLink(remote_sys_name=%s, capacity=%d, stats=%s)" \
               % (self.remote_sys_name, self.capacity, self.stats)

    def serialize(self):
        return {
            "remote_sys_name": self.remote_sys_name,
            "capacity": self.capacity,
            "stats": self.stats.serialize()
        }


class NetworkNode(dict):

    def __init__(self, sys_name):
        super(NetworkNode, self).__init__()
        self._sys_name = sys_name

    @property
    def sys_name(self):
        return self._sys_name

    def __repr__(self):
        return "NetworkNode('%s', %s)" \
               % (self.sys_name, super(NetworkNode, self).__str__())

    def add_remote(self, port, remote_sys_name, capacity, stats=NetworkStats()):
        self[port] = NetworkLink(remote_sys_name, capacity, stats)

    def update_remote(self, port, bytes_recv, bytes_sent):
        self[port].stats.update(bytes_recv, bytes_sent)

    def capacity(self):
        return sum(link.capacity for link in self.itervalues())

    def total_bytes_received(self):
        return sum(link.stats.bytes_recv for link in self.itervalues())

    def total_bytes_sent(self):
        return sum(link.stats.bytes_sent for link in self.itervalues())

    def total_bytes_transferred(self):
        return sum(link.stats.bytes_transferred for link in self.itervalues())

    def serialize(self):
        return {
            "name": self.sys_name,
            "links": {port: link.serialize() for port, link in self.iteritems()}
        }


if __name__ == "__main__":
    n = NetworkNode("hub")
    n.add_remote(1, "sys1", 100)
    for l in n:
        print(n[l])
