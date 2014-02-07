from collections import namedtuple

__author__ = 'danielge'

NetworkLink = namedtuple('NetworkLink', ['remote_sys_name', 'capacity', 'stats'])


class NetworkStats(object):
    """ Represents network statistics (e.g. bytes sent/received) for a given link on a
    node.
    """

    def __init__(self, bytes_recv=0, bytes_sent=0):
        self.bytes_recv = bytes_recv
        self.bytes_sent = bytes_sent

    @property
    def bytes_transferred(self):
        return self.bytes_recv + self.bytes_sent


class NetworkNode(dict):
    """ Represents information about a node (i.e. router, switch) on a network. """

    def __init__(self, sys_name):
        super(NetworkNode, self).__init__()
        self._sys_name = sys_name

    @property
    def sys_name(self):
        return self._sys_name

    @property
    def name(self):
        """ Alias for the 'sys_name' property. """
        return self._sys_name

    def total_bytes_recv(self):
        return sum(stats.bytes_recv for _, stats in self.itervalues())

    def total_bytes_sent(self):
        return sum(stats.bytes_sent for _, stats in self.itervalues())

    def total_bytes_transferred(self):
        return sum(stats.bytes_transferred for _, stats in self.itervalues())

    def add_remote(self, port, remote_sys_name, capacity, stats=None):
        self[port] = NetworkLink(
            remote_sys_name=remote_sys_name,
            capacity=capacity,
            stats=stats or NetworkStats(),
        )

    def ports(self):
        return self.keys()

    def iterports(self):
        return self.iterkeys()
