# Copyright (c) 2021 Microsoft Open Technologies, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
#    THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR
#    CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
#    LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
#    FOR A PARTICULAR PURPOSE, MERCHANTABILITY OR NON-INFRINGEMENT.
#
#    See the Apache Version 2.0 License for specific language governing
#    permissions and limitations under the License.
#
#    Microsoft would like to thank the following companies for their review and
#    assistance with these files: Intel Corporation, Mellanox Technologies Ltd,
#    Dell Products, L.P., Facebook, Inc., Marvell International Ltd.
#
#

from sai_test_base import T0TestBase
from sai_thrift.sai_headers import *
from ptf import config
from ptf.testutils import *
from ptf.thriftutils import *
from sai_utils import *


class L2_Port_Forwarding_Test(T0TestBase):
    """
    Verify the basic fdb forwarding.
    Segment should be forwarding to the correlated port bases on the FDB table.
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)

    def runTest(self):
        """
        Test fdb forwarding
        """
        try:
            print("FDB basic forwarding test.")
            for index in range(2, 9):
                print("L2 Forwarding from {} to port: {}".format(
                    self.dev_port_list[1],
                    self.dev_port_list[index]))
                pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[index],
                                        eth_src=self.local_server_mac_list[1],
                                        vlan_vid=10,
                                        ip_id=101,
                                        ip_ttl=64)

                send_packet(self, self.dev_port_list[1], pkt)
                verify_packet(self, pkt, self.dev_port_list[index])
        finally:
            pass

    def tearDown(self):
        """
        Test the basic tearDown process
        """
        sai_thrift_flush_fdb_entries(
            self.client, entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_ALL)


class VlanPortLearnDisableTest(T0TestBase):
    """
    Verify if MAC addresses are not learned on the port when bridge port learning is disabled
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        unknown_mac1 = "00:01:01:99:99:99"
        unknown_mac2 = "00:01:02:99:99:99"
        self.pkt = simple_udp_packet(eth_dst=unknown_mac2,
                                    eth_src=unknown_mac1,
                                    pktlen=100)
        self.chck_pkt = simple_udp_packet(eth_dst=unknown_mac1,
                                    eth_src=unknown_mac2,
                                    pktlen=100)
        sai_thrift_flush_fdb_entries(
            self.client, entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_ALL)
        sai_thrift_set_vlan_attribute(
            self.client, self.vlans[10].vlan_oid, learn_disable=True)

    def runTest(self):
        print("VlanPortLearnDisableTest")

        attr = sai_thrift_get_switch_attribute(
            self.client, available_fdb_entry=True)
        current_fdb_entry = attr["available_fdb_entry"]

        send_packet(self, 1, self.pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [self.pkt], [self.dev_port_list[2:9]])

        send_packet(self, 2, self.chck_pkt)
        verify_packet(self, self.chck_pkt, self.dev_port_list[1])
        verify_each_packet_on_multiple_port_lists(
            self, [self.chck_pkt], [self.dev_port_list[3:9]])

        self.assertEqual(attr["available_fdb_entry"] - current_fdb_entry, 0)
        print("Verification complete")


    def tearDown(self):
        sai_thrift_flush_fdb_entries(
            self.client, entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_ALL)

        # restore initial VLAN Learning state
        sai_thrift_set_vlan_attribute(
            self.client, self.vlans[10].vlan_oid, learn_disable=False)


class BPPortLearnDisableTest(T0TestBase):
    """
    Verify if MAC addresses are not learned on the port when VLAN port learning is disabled
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        unknown_mac1 = "00:01:01:99:99:99"
        unknown_mac2 = "00:01:02:99:99:99"
        self.pkt = simple_udp_packet(eth_dst=unknown_mac2,
                                    eth_src=unknown_mac1,
                                    pktlen=100)
        self.chck_pkt = simple_udp_packet(eth_dst=unknown_mac1,
                                    eth_src=unknown_mac2,
                                    pktlen=100)
        sai_thrift_flush_fdb_entries(
            self.client, entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_ALL)

        status = sai_thrift_set_bridge_port_attribute(
            self.client,
            self.bridge_port_list[1],
            fdb_learning_mode=SAI_BRIDGE_PORT_FDB_LEARNING_MODE_DISABLE)
        self.assertEqual(status, SAI_STATUS_SUCCESS)

    def runTest(self):
        print("VlanPortLearnDisableTest")

        attr = sai_thrift_get_switch_attribute(
            self.client, available_fdb_entry=True)
        current_fdb_entry = attr["available_fdb_entry"]

        send_packet(self, 1, self.pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [self.pkt], [self.dev_port_list[2:9]])

        send_packet(self, 2, self.chck_pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [self.chck_pkt, self.chck_pkt], [[self.dev_port_list[1]], [self.dev_port_list[3:9]]])

        self.assertEqual(attr["available_fdb_entry"] - current_fdb_entry, 0)
        print("Verification complete")


    def tearDown(self):
        sai_thrift_flush_fdb_entries(
            self.client, entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_ALL)

        # restore initial bridge port Learning state
        status = sai_thrift_set_bridge_port_attribute(
            self.client,
            self.bridge_port_list[1],
            fdb_learning_mode=SAI_BRIDGE_PORT_FDB_LEARNING_MODE_HW)


class NoBPPortNoLearnTest(T0TestBase):
    """
    Verify if MAC addresses are not learned on the port when bridge port was removed from that port
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        unknown_mac1 = "00:01:01:99:99:99"
        unknown_mac2 = "00:01:02:99:99:99"
        self.pkt = simple_udp_packet(eth_dst=unknown_mac2,
                                    eth_src=unknown_mac1,
                                    pktlen=100)
        self.chck_pkt = simple_udp_packet(eth_dst=unknown_mac1,
                                    eth_src=unknown_mac2,
                                    pktlen=100)
        sai_thrift_flush_fdb_entries(
            self.client, entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_ALL)

        status = sai_thrift_remove_bridge_port(self.client, self.port_list[1])
        self.assertEqual(status, SAI_STATUS_SUCCESS)


    def runTest(self):
        print("NoBPPortNoLearnTest")

        attr = sai_thrift_get_switch_attribute(
            self.client, available_fdb_entry=True)
        current_fdb_entry = attr["available_fdb_entry"]

        send_packet(self, 1, self.pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [self.pkt], [self.dev_port_list[2:9]])

        send_packet(self, 2, self.chck_pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [self.chck_pkt, self.chck_pkt], [[self.dev_port_list[1]], [self.dev_port_list[3:9]]])

        self.assertEqual(attr["available_fdb_entry"] - current_fdb_entry, 0)
        print("Verification complete")


    def tearDown(self):
        sai_thrift_flush_fdb_entries(
            self.client, entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_ALL)

        # restore initial bridge port
        self.bridge_port_list[1] = sai_thrift_create_bridge_port(
            self.client,
            bridge_id=self.default_1q_bridge_id,
            port_id=self.port_list[1],
            type=SAI_BRIDGE_PORT_TYPE_PORT,
            admin_state=True)


class NewVlanmemberLearnTest(T0TestBase):
    """
    Verify if MAC addresses are learned on the new add vlan member
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        unknown_mac1 = "00:01:01:99:99:99"
        self.pkt1 = simple_udp_packet(eth_dst=self.local_server_mac_list[1],
                                    eth_src=unknown_mac1,
                                    pktlen=100)
        self.pkt2 = simple_udp_packet(eth_dst=unknown_mac1,
                                    eth_src=self.local_server_mac_list[1],
                                    pktlen=100)
        self.new_vlan10_member = sai_thrift_create_vlan_member(self.client,
            vlan_id=self.vlans[10].vlan_oid,
            bridge_port_id=self.bridge_port_list[24],
            vlan_tagging_mode=vlan_tagging_mode)

        sai_thrift_set_port_attribute(
            self.client, self.port_list[24], port_vlan_id=10)
        self.assertEqual(status, SAI_STATUS_SUCCESS)


    def runTest(self):
        print("NewVlanmemberLearnTest")
        attr = sai_thrift_get_switch_attribute(
            self.client, available_fdb_entry=True)
        current_fdb_entry = attr["available_fdb_entry"]

        send_packet(self, 24, self.pkt1)
        verify_packet(self, self.pkt1, self.dev_port_list[1])

        send_packet(self, 1, self.chck_pkt2)
        verify_packet(self, self.pkt2, self.dev_port_list[24])
       
        self.assertEqual(attr["available_fdb_entry"] - current_fdb_entry, 1)
        print("Verification complete")


    def tearDown(self):
        pass


class RemoveVlanmemberLearnTest(T0TestBase):
    """
    Verify no MAC addresses are learned on the removed vlan member
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        unknown_mac1 = "00:01:01:99:99:99"
        self.pkt1 = simple_udp_packet(eth_dst=self.local_server_mac_list[1],
                                    eth_src=unknown_mac1,
                                    vlan_vid=10,
                                    pktlen=100)
        self.pkt2 = simple_udp_packet(eth_dst=unknown_mac1,
                                    eth_src=self.local_server_mac_list[1],
                                    vlan_vid=10,
                                    pktlen=100)

        sai_thrift_set_port_attribute(
            self.client, self.port_list[24], port_vlan_id=0)
        self.assertEqual(status, SAI_STATUS_SUCCESS)


    def runTest(self):
        print("RemoveVlanmemberLearnTest")
        attr = sai_thrift_get_switch_attribute(
            self.client, available_fdb_entry=True)
        current_fdb_entry = attr["available_fdb_entry"]

        send_packet(self, 2, self.pkt1)
        verify_no_other_packets(self)

        send_packet(self, 1, self.chck_pkt2)
        verify_packet(self, self.pkt2, self.dev_port_list[2:9])
       
        self.assertEqual(attr["available_fdb_entry"] - current_fdb_entry, 0)
        print("Verification complete")


    def tearDown(self):
        pass


class InvalidateVlanmemberNoLearnTest(T0TestBase):
    """
    Verify no MAC addresses are learned on the removed vlan member
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        unknown_mac1 = "00:01:01:99:99:99"
        self.pkt1 = simple_udp_packet(eth_dst=self.local_server_mac_list[1],
                                    eth_src=unknown_mac1,
                                    vlan_vid=11,
                                    pktlen=100)
        self.pkt2 = simple_udp_packet(eth_dst=unknown_mac1,
                                    eth_src=self.local_server_mac_list[1],
                                    vlan_vid=11,
                                    pktlen=100)
        self.assertEqual(status, SAI_STATUS_SUCCESS)


    def runTest(self):
        print("RemoveVlanmemberLearnTest")
        attr = sai_thrift_get_switch_attribute(
            self.client, available_fdb_entry=True)
        current_fdb_entry = attr["available_fdb_entry"]

        send_packet(self, 2, self.pkt1)
        verify_no_other_packets(self)

        send_packet(self, 1, self.chck_pkt2)
        verify_no_other_packets(self)
       
        self.assertEqual(attr["available_fdb_entry"] - current_fdb_entry, 0)
        print("Verification complete")


    def tearDown(self):
        pass


class BroadcastNoLearnTest(T0TestBase):
    """
    Verify no MAC addresses are learned on the removed vlan member
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        bcast_mac = "ff:ff:ff:ff:ff:ff"
        self.pkt1 = simple_udp_packet(eth_src=bcast_mac,
                                    pktlen=100)

        self.pkt2 = simple_udp_packet(eth_dst=bcast_mac,
                                    pktlen=100)

        sai_thrift_set_port_attribute(
            self.client, self.port_list[24], port_vlan_id=0)
        self.assertEqual(status, SAI_STATUS_SUCCESS)


    def runTest(self):
        print("BroadcastNoLearnTest")
        attr = sai_thrift_get_switch_attribute(
            self.client, available_fdb_entry=True)
        current_fdb_entry = attr["available_fdb_entry"]

        send_packet(self, 2, self.pkt1)
        verify_no_other_packets(self)

        send_packet(self, 1, self.chck_pkt2)
        verify_packet(self, self.pkt2, self.dev_port_list[2:9])
       
        self.assertEqual(attr["available_fdb_entry"] - current_fdb_entry, 0)
        print("Verification complete")


    def tearDown(self):
        pass


class MulticastNoLearnTest(T0TestBase):
    """
    Verify no MAC addresses are learned on the removed vlan member
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        mcast_mac = "01:00:5e:11:22:33"
        self.pkt1 = simple_udp_packet(eth_src=mcast_mac,
                                    pktlen=100)

        self.pkt2 = simple_udp_packet(eth_dst=mcast_mac,
                                    pktlen=100)

        sai_thrift_set_port_attribute(
            self.client, self.port_list[24], port_vlan_id=0)
        self.assertEqual(status, SAI_STATUS_SUCCESS)


    def runTest(self):
        print("MulticastNoLearnTest")
        attr = sai_thrift_get_switch_attribute(
            self.client, available_fdb_entry=True)
        current_fdb_entry = attr["available_fdb_entry"]

        send_packet(self, 2, self.pkt1)
        verify_no_other_packets(self)

        send_packet(self, 1, self.chck_pkt2)
        verify_packet(self, self.pkt2, self.dev_port_list[2:9])
       
        self.assertEqual(attr["available_fdb_entry"] - current_fdb_entry, 0)
        print("Verification complete")


    def tearDown(self):
        pass


class FdbPortAgingTest(T0TestBase):
    """
    Test fdb Aging on Port
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        # age time used in tests (in sec)
        self.age_time = 10
        status = sai_thrift_set_switch_attribute(self.client,
                                                 fdb_aging_time=self.age_time)
        self.assertEqual(status, SAI_STATUS_SUCCESS)
        sw_attr = sai_thrift_get_switch_attribute(self.client,
                                                  fdb_aging_time=True)
        self.assertEqual(sw_attr["fdb_aging_time"], self.age_time)
        print("Set aging time to {} sec".fomrat(self.age_time))

    def runTest(self):
        unknown_mac1 = "00:01:01:99:99:99"
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[1],
                                eth_src=unknown_mac1,
                                pktlen=100)
        tag_pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[1],
                                    eth_src=unknown_mac1,
                                    dl_vlan_enable=True,
                                    vlan_vid=10,
                                    pktlen=104)
        send_packet(self, 2, tag_pkt)
        verify_packets(self, pkt, [self.dev_port_list[1]])
        time.sleep(1)

        print("Verifying if MAC address was learned")
        pkt = simple_udp_packet(eth_dst=unknown_mac1,
                                eth_src=self.local_server_mac_list[1],
                                pktlen=100)
        tag_pkt = simple_udp_packet(eth_dst=unknown_mac1,
                                    eth_src=self.local_server_mac_list[1],
                                    dl_vlan_enable=True,
                                    vlan_vid=10,
                                    pktlen=104)
        
        send_packet(self, 1, tag_pkt)
        verify_packets(self, pkt, [self.dev_port_list[2]])
        print("\tOK")

        self.saiWaitFdbAge(self.age_time)
        print("Verify if aged MAC address was removed")
        send_packet(self, self.dev_port_list[1], pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2:9]])
        print("\tVerification complete")

    def tearDown(self):
        sai_thrift_flush_fdb_entries(
        self.client, entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_DYNAMIC)


class FdbPortMoveAfterAgingTest(T0TestBase):
    """
    Test fdb moving after Aging on Port
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        # age time used in tests (in sec)
        self.age_time = 10
        status = sai_thrift_set_switch_attribute(self.client,
                                                 fdb_aging_time=self.age_time)
        self.assertEqual(status, SAI_STATUS_SUCCESS)
        sw_attr = sai_thrift_get_switch_attribute(self.client,
                                                  fdb_aging_time=True)
        self.assertEqual(sw_attr["fdb_aging_time"], self.age_time)
        print("Set aging time to {} sec".fomrat(self.age_time))

    def runTest(self):
        unknown_mac1 = "00:01:01:99:99:99"
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[1],
                                eth_src=unknown_mac1,
                                pktlen=100)
        tag_pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[1],
                                    eth_src=unknown_mac1,
                                    dl_vlan_enable=True,
                                    vlan_vid=10,
                                    pktlen=104)
        send_packet(self, 2, tag_pkt)
        verify_packets(self, pkt, [self.dev_port_list[1]])
        time.sleep(1)

        print("Verifying if MAC address was learned")
        pkt = simple_udp_packet(eth_dst=unknown_mac1,
                                eth_src=self.local_server_mac_list[1],
                                pktlen=100)
        tag_pkt = simple_udp_packet(eth_dst=unknown_mac1,
                                    eth_src=self.local_server_mac_list[1],
                                    dl_vlan_enable=True,
                                    vlan_vid=10,
                                    pktlen=104)
        
        send_packet(self, 1, tag_pkt)
        verify_packets(self, pkt, [self.dev_port_list[2]])
        print("\tOK")

        self.saiWaitFdbAge(self.age_time)

        send_packet(self, 3, tag_pkt)
        verify_packets(self, pkt, [self.dev_port_list[2]])
        time.sleep(1)

        print("Verifying if MAC address was moved")
        pkt = simple_udp_packet(eth_dst=lrn_mac,
                                eth_src=self.vrf_mac,
                                pktlen=100)
        tag_pkt = simple_udp_packet(eth_dst=lrn_mac,
                                    eth_src=self.vrf_mac,
                                    dl_vlan_enable=True,
                                    vlan_vid=self.vlan_id,
                                    pktlen=104)

        self.saiWaitFdbAge(self.age_time)
        print("Verify if aged MAC address was removed")
        send_packet(self, self.dev_port_list[1], pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2:9]])
        print("\tVerification complete")

        print("Verify if aged MAC address was removed")
        send_packet(self, self.dev_port_list[1], pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2:9]])
        print("\tVerification complete")

    def tearDown(self):
        sai_thrift_flush_fdb_entries(
        self.client, entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_DYNAMIC)


class FdbFlushVlanStaticTest(T0TestBase):
    '''
    Verify flushing of static MAC entries by VLAN
    '''

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        sai_thrift_flush_fdb_entries(
            self.client,
            bv_id=self.vlans[10].vlan_oid,
            entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_STATIC)


    def runTest(self):
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[2],
                                pktlen=100)
        send_packet(self, 1, tag_pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2:9]])
        print("\tVerified the flooding happend")
        time.sleep(1)
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[10],
                                pktlen=100)
        send_packet(self, 9, pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[10]])
        print("\tVerified the flooding happend")


        print("\tVerification complete")

    def tearDown(self):
        pass


class FdbFlushPortStaticTest(T0TestBase):
    '''
    Verify flushing of static MAC entries by Port
    '''

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        sai_thrift_flush_fdb_entries(
            self.client,
            bridge_port_id=self.bridge_port_list[1],
            entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_STATIC)


    def runTest(self):
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[1],
                                pktlen=100)
        send_packet(self, 2, tag_pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2:9]])
        print("\tVerified the flooding happend")
        time.sleep(1)
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[9],
                                pktlen=100)
        send_packet(self, 10, pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[9]])
        print("\tVerified the flooding happend")


        print("\tVerification complete")

    def tearDown(self):
        pass


class FdbFlushAllStaticTest(T0TestBase):
    '''
    Verify flushing of static MAC entries by all
    '''

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        sai_thrift_flush_fdb_entries(
            self.client,
            entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_STATIC)


    def runTest(self):
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[2],
            pktlen=100)
        send_packet(self, 1, tag_pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2:9]])
        print("\tVerified the flooding happend")
        time.sleep(1)
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[10],
                                pktlen=100)
        send_packet(self, 9, pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[10]])
        print("\tVerified the flooding happend")


        print("\tVerification complete")

    def tearDown(self):
        pass


class FdbFlushVlanDynamicTest(T0TestBase):
    '''
    Verify flushing of dynamic MAC entries by VLAN
    '''

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        sai_thrift_flush_fdb_entries(
            self.client,
            bv_id=self.vlans[20].vlan_oid,
            entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_STATIC)


    def runTest(self):
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[10],
                                pktlen=100)
        send_packet(self, 9, tag_pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[10:16]])
        print("\tVerified the flooding happend")
        time.sleep(1)
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[2],
                                pktlen=100)
        send_packet(self, 1, pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2]])
        print("\tVerified the flooding happend")


        print("\tVerification complete")

    def tearDown(self):
        pass


class FdbFlushPortDynamicTest(T0TestBase):
    '''
    Verify flushing of dynamic MAC entries by Port
    '''

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        sai_thrift_flush_fdb_entries(
            self.client,
            bridge_port_id=self.bridge_port_list[9],
            entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_STATIC)


    def runTest(self):
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[9],
                                pktlen=100)
        send_packet(self, 10, tag_pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [[self.dev_port_list[9],[self.dev_port_list[11:16]]]])
        print("\tVerified the flooding happend")
        time.sleep(1)
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[1],
                                pktlen=100)
        send_packet(self, 2, pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[1]])
        print("\tVerified the flooding happend")


        print("\tVerification complete")

    def tearDown(self):
        pass


class FdbFlushAllDynamicTest(T0TestBase):
    '''
    Verify flushing of dynamic MAC entries by all
    '''

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        sai_thrift_flush_fdb_entries(
            self.client,
            entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_DYNAMIC)


    def runTest(self):
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[10],
            pktlen=100)
        send_packet(self, 9, tag_pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[10:16]])
        print("\tVerified the flooding happend")
        time.sleep(1)
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[2],
                                pktlen=100)
        send_packet(self, 1, pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2]])
        print("\tVerified the flooding happend")

        print("\tVerification complete")

    def tearDown(self):
        pass


class FdbFlushAllTest(T0TestBase):
    '''
    Verify flushing MAC entries by all
    '''

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        sai_thrift_flush_fdb_entries(
            self.client,
            entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_DYNAMIC)


    def runTest(self):
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[2],
            pktlen=100)
        send_packet(self, 1, tag_pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2:9]])
        print("\tVerified the flooding happend")
        time.sleep(1)
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[10],
                                pktlen=100)
        send_packet(self, 9, pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[10:16]])
        print("\tVerified the flooding happend")

        print("\tVerification complete")

    def tearDown(self):
        pass


class FdbDisableMacMoveDropTest(T0TestBase):
    '''
    Verify if disable MAC move, drop packet with known
    '''

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        sai_thrift_flush_fdb_entries(
            self.client,
            entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_DYNAMIC)


    def runTest(self):
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[2],
            pktlen=100)
        send_packet(self, 1, tag_pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2:9]])
        print("\tVerified the flooding happend")
        time.sleep(1)
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[10],
                                pktlen=100)
        send_packet(self, 9, pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[10:16]])
        print("\tVerified the flooding happend")

        print("\tVerification complete")


    def tearDown(self):
        pass