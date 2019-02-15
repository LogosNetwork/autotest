import unittest

from utils import LogosRpc, LogosRPCError


class TestRequests(unittest.TestCase):

    def __init__(self, ip_dicts):
        super().__init__()
        self.nodes = {i: LogosRpc(ip_dict['PublicIpAddress']) for i, ip_dict in enumerate(ip_dicts)}

    def setUp(self):
        pass

    def test_(self):
        pass

