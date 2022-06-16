import os
import time
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
from t0_base_test import SaiT0HelperBase
from sai_thrift.sai_headers import *
from ptf import config
from ptf.base_tests import BaseTest
from ptf import config
from ptf.testutils import *
from ptf.thriftutils import *
import time

class L2FdbForwardingTest(SaiT0HelperBase):
    """
    Verify L2 fdb functionilty
    """
    def setUp(self):
        """
        Test the basic setup proecss
        """
        #this process contains the switch_init process
        SaiT0HelperBase.setUp(self)
        print("Sending L2 packet port 1 -> port 2")

        self.pkt = simple_tcp_packet(eth_dst=self.vlan10_mac_list[1],
                            eth_src=self.vlan10_mac_list[0],
                            ip_dst='172.16.0.1',
                            ip_id=101,
                            ip_ttl=64)
    def runTest(self):
        """
        Test the basic runTest proecss
        """
        print("Sending packet on port %d, %s -> %s" %
                (self.port_list[1], self.vlan10_mac_list[0], self.vlan10_mac_list[1]))
        try:
            send_packet(self, 1, self.pkt)
            verify_packet(self, self.pkt, 2)

            print("Verification complete!")
        finally:
            pass

    def tearDown(self):
        """
        Test the basic tearDown proecss
        """
        pass