import sys
sys.path.append("..")
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

        self.pkt = simple_udp_packet(eth_dst=self.vlan10_mac_list[1],
                   eth_src=self.vlan10_mac_list[0])

    def runTest(self):
        """
        Test the basic runTest proecss
        """
        print("Sending packet on port %d, %s -> %s" %
                (self.port_list[1], self.vlan10_mac_list[0], self.vlan10_mac_list[1]))
        try:
            send_packet(self, 1, self.pkt)
            time.sleep(5)
            verify_packet(self, self.pkt, 2)

            print("Verification complete!")
        finally:
            pass

    def tearDown(self):
        """
        Test the basic tearDown proecss
        """
        pass