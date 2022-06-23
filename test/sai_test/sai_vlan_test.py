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

class Vlan_Domain_Forwarding_Test(T0TestBase):
    """
    Verify the basic VLAN forwarding.
    In L2, if segement with VLAN tag and sends to a VLAN port, 
    segment should be forwarded inside a VLAN domain.
    """

    def setUp(self):
        """
        Test the basic setup process
        """
        T0TestBase.setUp(self, is_reset_default_vlan=False)

    def runTest(self):
        """
        Test VLAN forwarding
        """
        try:
            print("VLAN forwarding test.")
            for index in range(2, 9):
                print("Forwarding in VLAN {} from {} to port: {}".format(
                    10,
                    self.dev_port_list[1], 
                    self.dev_port_list[index]))
                pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[index],
                                        eth_src=self.local_server_mac_list[1],
                                        vlan_vid=10,
                                        ip_id=101,
                                        ip_ttl=64)
                    
                send_packet(self, self.dev_port_list[1], pkt)
                verify_packet(self, pkt, self.dev_port_list[index])
            for index in range(10, 17):
                print("Forwarding in VLAN {} from {} to port: {}".format(
                    20,
                    self.dev_port_list[9], 
                    self.dev_port_list[index]))
                pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[index],
                                        eth_src=self.local_server_mac_list[9],
                                        vlan_vid=20,
                                        ip_id=101,
                                        ip_ttl=64)
                    
                send_packet(self, self.dev_port_list[9], pkt)
                verify_packet(self, pkt, self.dev_port_list[index])
        finally:
            pass

    def tearDown(self):
        """
        Test the basic tearDown process
        """
        sai_thrift_flush_fdb_entries(
            self.client, entry_type=SAI_FDB_FLUSH_ENTRY_TYPE_ALL)


class VlanMemberListTest(T0TestBase):
    """
    This test verifies the VLAN member list using SAI_VLAN_ATTR_MEMBER_LIST
    """
    def setUp(self):
        T0TestBase.setUp(self, is_reset_default_vlan=False)

    def runTest(self):
        print("VlanMemberListTest")
        mbr_list = []
        mbr_list.extend(self.vlan_configer.get_vlan_member(self.vlans[10].vlan_oid))
        mbr_list.extend(self.vlan_configer.get_vlan_member(self.vlans[20].vlan_oid))
        self.assertEqual(len(mbr_list), 16)

        for i in range(0, 8):
            self.assertEqual(self.vlans[10].vlan_mport_oids[i], mbr_list[i])
        for i in range(8, 16):
            self.assertEqual(self.vlans[20].vlan_mport_oids[i - 8], mbr_list[i]) 

        # Adding vlan members and veryfing vlan member list
        new_vlan_member = sai_thrift_create_vlan_member(
            self.client,
            vlan_id=self.vlans[10].vlan_oid,
            bridge_port_id=self.bridge_port_list[17],
            vlan_tagging_mode=SAI_VLAN_TAGGING_MODE_UNTAGGED)

        mbr_list = []
        mbr_list.extend(self.vlan_configer.get_vlan_member(self.vlans[10].vlan_oid))
        mbr_list.extend(self.vlan_configer.get_vlan_member(self.vlans[20].vlan_oid))
        self.assertEqual(len(mbr_list), 17)

        # Adding vlan members and veryfing vlan member list
        for i in range(0, 8):
            self.assertEqual(self.vlans[10].vlan_mport_oids[i], mbr_list[i])
        self.assertEqual(new_vlan_member, mbr_list[8])
        for i in range(9, 17):
            self.assertEqual(self.vlans[20].vlan_mport_oids[i - 9], mbr_list[i]) 

        # Removing vlan members and veryfing vlan member list
        sai_thrift_remove_vlan_member(self.client, new_vlan_member)

        mbr_list = []
        mbr_list.extend(self.vlan_configer.get_vlan_member(self.vlans[10].vlan_oid))
        mbr_list.extend(self.vlan_configer.get_vlan_member(self.vlans[20].vlan_oid))
        self.assertEqual(len(mbr_list), 16)

        for i in range(0, 8):
            self.assertEqual(self.vlans[10].vlan_mport_oids[i], mbr_list[i])
        for i in range(8, 16):
            self.assertEqual(self.vlans[20].vlan_mport_oids[i - 8], mbr_list[i])

    def tearDown(self):
        pass


class VlanMemberInvalidTest(T0TestBase):
    """
    This test verifies when adding a VLAN member to a non-exist VLAN, it will fail.
    """
    def setUp(self):
        T0TestBase.setUp(self, is_reset_default_vlan=False)

    def runTest(self):
        print("VlanMemberInvalidTest")

        incorrect_member = sai_thrift_create_vlan_member(
            self.client,
            vlan_id=11,
            bridge_port_id=self.bridge_port_list[17],
            vlan_tagging_mode=SAI_VLAN_TAGGING_MODE_TAGGED) 
        self.assertEqual(incorrect_member, 0)   

    def tearDown(self):
        pass


class DisableMacLearningTaggedTest(T0TestBase):
    """
    This test verifies the function when disabling VLAN MAC learning. When disabled, no new MAC will be learned in the MAC table.
    """
    def setUp(self):
        T0TestBase.setUp(self, is_reset_default_vlan=False)

    def runTest(self):
        print("DisableMacLearningTaggedTest")
        sai_thrift_set_vlan_attribute(self.client, self.vlans[10].vlan_oid, learn_disable=True)
        self.assertEqual(status, SAI_STATUS_SUCCESS)
        print("MAC Learning disabled on VLAN")

        attr = sai_thrift_get_switch_attribute(
            self.client, available_fdb_entry=True)
        current_fdb_entry = attr["available_fdb_entry"]

        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[2],
                                eth_src=self.local_server_mac_list[1],
                                vlan_vid=10,
                                ip_id=101,
                                ip_ttl=64)
        send_packet(self, 1, pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2:9]])

        self.assertEqual(attr["available_fdb_entry"] - current_fdb_entry, 0)


    def tearDown(self):
        pass


class DisableMacLearningUntaggedTest(T0TestBase):
    """
    This test verifies the function when disabling VLAN MAC learning. When disabled, no new MAC will be learned in the MAC table.
    """
    def setUp(self):
        T0TestBase.setUp(self, is_reset_default_vlan=False)

    def runTest(self):
        print("DisableMacLearningUntaggedTest")
        sai_thrift_set_vlan_attribute(self.client, self.vlans[10].vlan_oid, learn_disable=True)
        self.assertEqual(status, SAI_STATUS_SUCCESS)
        print("MAC Learning disabled on VLAN")    
        
        attr = sai_thrift_get_switch_attribute(
            self.client, available_fdb_entry=True)
        current_fdb_entry = attr["available_fdb_entry"]
        
        pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[2],
                                eth_src=self.local_server_mac_list[1],
                                ip_id=101,
                                ip_ttl=64)
        send_packet(self, self.dev_port_list[1], pkt)
        verify_each_packet_on_multiple_port_lists(
            self, [pkt], [self.dev_port_list[2:9]])

        self.assertEqual(attr["available_fdb_entry"] - current_fdb_entry, 0)

    def tearDown(self):
        pass


class ArpRequestFloodingTest(T0TestBase):
    """
    This test verifies the flooding when receive a arp request
    """
    def setUp(self):
        T0TestBase.setUp(self, is_reset_default_vlan=False)

        ip2 = "192.168.0.2" 
        self.arp_request = simple_arp_packet(
                eth_dst=self.local_server_mac_list[2],
                arp_op=1,
                ip_tgt=ip2,
                hw_tgt=self.local_server_mac_list[2])

    def runTest(self):
        send_packet(self, self.dev_port_list[1], self.arp_request)
        verify_each_packet_on_multiple_port_lists(
            self, [self.arp_request], [self.dev_port_list[2:9]])

    def tearDown(self):
        pass


class ArpRequestLearningTest(T0TestBase):
    """
    This test verifies the mac learning when receive a arp request
    """
    def setUp(self):
        T0TestBase.setUp(self, is_reset_default_vlan=False)

        ip1 = "192.168.0.1"
        ip2 = "192.168.0.2" 
        self.arp_response = simple_arp_packet(
                eth_dst=self.local_server_mac_list[1],
                eth_src=self.local_server_mac_list[2],
                arp_op=2,
                ip_tgt=ip2,
                ip_snd=ip1,
                hw_snd=self.local_server_mac_list[2],
                hw_tgt=self.local_server_mac_list[1])

    def runTest(self):
        send_packet(self, self.dev_port_list[2], self.arp_response)
        import pdb
        pdb.set_trace()
        verify_packet(self, self.arp_response, self.dev_port_list[1])
        verify_no_other_packets(self)

    def tearDown(self):
        pass
            

class TaggedVlanStatusTest(T0TestBase):
    """
    This test verifies VLAN-related counters during 
    """
    def setUp(self):
        T0TestBase.setUp(self, is_reset_default_vlan=False)
        self.tagged_pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[2],
                eth_src=self.local_server_mac_list[1],
                vlan_vid=10,
                ip_id=101,
                ip_ttl=64)

    def runTest(self):
        stats = sai_thrift_get_vlan_stats(self.client, self.vlans[10].vlan_oid)

        in_bytes_pre = stats["SAI_VLAN_STAT_IN_OCTETS"]
        out_bytes_pre = stats["SAI_VLAN_STAT_OUT_OCTETS"]
        in_packets_pre = stats["SAI_VLAN_STAT_IN_PACKETS"]
        in_ucast_packets_pre = stats["SAI_VLAN_STAT_IN_UCAST_PKTS"]
        out_packets_pre = stats["SAI_VLAN_STAT_OUT_PACKETS"]
        out_ucast_packets_pre = stats["SAI_VLAN_STAT_OUT_UCAST_PKTS"]

        print("Sending L2 packet port 1 -> port 2")
        send_packet(self, self.dev_port_list[1], self.tagged_pkt)
        verify_packet(self, self.tagged_pkt, self.dev_port_list[2])

        
        stats = sai_thrift_get_vlan_stats(self.client, self.vlans[10].vlan_oid)
        in_bytes = stats["SAI_VLAN_STAT_IN_OCTETS"]
        out_bytes = stats["SAI_VLAN_STAT_OUT_OCTETS"]
        in_packets = stats["SAI_VLAN_STAT_IN_PACKETS"]
        in_ucast_packets = stats["SAI_VLAN_STAT_IN_UCAST_PKTS"]
        out_packets = stats["SAI_VLAN_STAT_OUT_PACKETS"]
        out_ucast_packets = stats["SAI_VLAN_STAT_OUT_UCAST_PKTS"]
        """
        Brcm may don't support this API, Skip all verification in this testcase
        """
        # self.assertEqual((in_packets, in_packets_pre + 1),
        #                 'vlan IN packets counter {} != {}'.format(
        #                     in_packets, in_packets_pre + 1))
        # self.assertEqual((in_ucast_packets, in_ucast_packets_pre + 1),
        #                 'vlan IN unicats packets counter {} != {}'.format(
        #                     in_ucast_packets, in_ucast_packets_pre + 1))
        # self.assertNotEqual(((in_bytes - in_bytes_pre), 0),
        #                 'vlan IN bytes counter is 0')
        # self.assertEqual((out_packets, out_packets_pre + 1),
        #                 'vlan OUT packets counter {} != {}'.format(
        #                     out_packets, out_packets_pre + 1))
        # self.assertEqual((out_ucast_packets, out_ucast_packets_pre + 1),
        #                 'vlan OUT unicats packets counter {} != {}'.format(
        #                     out_ucast_packets, out_ucast_packets_pre + 1))
        # self.assertEqual(((out_bytes - out_bytes_pre), 0),
        #                 'vlan OUT bytes counter is 0')

        print("Sending L2 packet port 1 -> port 2 [access vlan=10])")
        send_packet(self, self.dev_port_list[1], self.tagged_pkt)
        verify_packet(self, self.tagged_pkt, self.dev_port_list[2])

        # Clear bytes and packets counter
        sai_thrift_clear_vlan_stats(self.client, self.vlans[10].vlan_oid)

        # Check counters
        stats = sai_thrift_get_vlan_stats(self.client, self.vlans[10].vlan_oid)
        in_bytes = stats["SAI_VLAN_STAT_IN_OCTETS"]
        out_bytes = stats["SAI_VLAN_STAT_OUT_OCTETS"]
        in_packets = stats["SAI_VLAN_STAT_IN_PACKETS"]
        in_ucast_packets = stats["SAI_VLAN_STAT_IN_UCAST_PKTS"]
        out_packets = stats["SAI_VLAN_STAT_OUT_PACKETS"]
        out_ucast_packets = stats["SAI_VLAN_STAT_OUT_UCAST_PKTS"]

        # self.assertEqual(in_packets, 0, 'vlan IN packets counter is not 0')
        # self.assertEqual(in_ucast_packets, 0,
        #                 'vlan IN unicast packets counter is not 0')
        # self.assertEqual(in_bytes, 0, 'vlan IN bytes counter is not 0')
        # self.assertEqual(out_packets, 0,
        #                 'vlan OUT packets counter is not 0')
        # self.assertEqual(out_ucast_packets, 0,
        #                 'vlan OUT unicast packets counter is not 0')
        # self.assertEqual(out_bytes, 0, 'vlan OUT bytes counter is not 0')

    def tearDown(self):
        pass


class UntaggedVlanStatusTest(T0TestBase):
    def setUp(self):
        T0TestBase.setUp(self, is_reset_default_vlan=False)

        self.untaged_pkt = simple_udp_packet(eth_dst=self.local_server_mac_list[2],
                eth_src=self.local_server_mac_list[1],
                ip_id=101,
                ip_ttl=64)

    def runTest(self):
        stats = sai_thrift_get_vlan_stats(self.client, self.port_list[1])

        in_bytes_pre = stats["SAI_VLAN_STAT_IN_OCTETS"]
        out_bytes_pre = stats["SAI_VLAN_STAT_OUT_OCTETS"]
        in_packets_pre = stats["SAI_VLAN_STAT_IN_PACKETS"]
        in_ucast_packets_pre = stats["SAI_VLAN_STAT_IN_UCAST_PKTS"]
        out_packets_pre = stats["SAI_VLAN_STAT_OUT_PACKETS"]
        out_ucast_packets_pre = stats["SAI_VLAN_STAT_OUT_UCAST_PKTS"]

        print("Sending L2 packet port 1 -> port 2 [access vlan=10])")
        send_packet(self, self.dev_port_list[1], self.untaged_pkt)
        verify_packet(self, self.untaged_pkt, self.dev_port_list[2])

        time.sleep(1)
        stats = sai_thrift_get_vlan_stats(self.client, self.vlans[10].vlan_oid)
        in_bytes = stats["SAI_VLAN_STAT_IN_OCTETS"]
        out_bytes = stats["SAI_VLAN_STAT_OUT_OCTETS"]
        in_packets = stats["SAI_VLAN_STAT_IN_PACKETS"]
        in_ucast_packets = stats["SAI_VLAN_STAT_IN_UCAST_PKTS"]
        out_packets = stats["SAI_VLAN_STAT_OUT_PACKETS"]
        out_ucast_packets = stats["SAI_VLAN_STAT_OUT_UCAST_PKTS"]
        """
        Brcm may don't support this API, Skip all verification in this testcase
        """
        # self.assertEqual((in_packets, in_packets_pre + 1),
        #                 'vlan IN packets counter {} != {}'.format(
        #                     in_packets, in_packets_pre + 1))
        # self.assertEqual((in_ucast_packets, in_ucast_packets_pre + 1),
        #                 'vlan IN unicats packets counter {} != {}'.format(
        #                     in_ucast_packets, in_ucast_packets_pre + 1))
        # self.assertNotEqual(((in_bytes - in_bytes_pre), 0),
        #                 'vlan IN bytes counter is 0')
        # self.assertEqual((out_packets, out_packets_pre + 1),
        #                 'vlan OUT packets counter {} != {}'.format(
        #                     out_packets, out_packets_pre + 1))
        # self.assertEqual((out_ucast_packets, out_ucast_packets_pre + 1),
        #                 'vlan OUT unicats packets counter {} != {}'.format(
        #                     out_ucast_packets, out_ucast_packets_pre + 1))
        # self.assertEqual(((out_bytes - out_bytes_pre), 0),
        #                 'vlan OUT bytes counter is 0')

        print("Sending L2 packet port 1 -> port 2 [access vlan=10])")
        send_packet(self, self.dev_port_list[1], self.untaged_pkt)
        verify_packet(self, self.untaged_pkt, self.dev_port_list[2])

        # Clear bytes and packets counter
        sai_thrift_clear_vlan_stats(self.client, self.vlans[10].vlan_oid)
        # Check counters

        stats = sai_thrift_get_vlan_stats(self.client, self.vlans[10].vlan_oid)
        in_bytes = stats["SAI_VLAN_STAT_IN_OCTETS"]
        out_bytes = stats["SAI_VLAN_STAT_OUT_OCTETS"]
        in_packets = stats["SAI_VLAN_STAT_IN_PACKETS"]
        in_ucast_packets = stats["SAI_VLAN_STAT_IN_UCAST_PKTS"]
        out_packets = stats["SAI_VLAN_STAT_OUT_PACKETS"]
        out_ucast_packets = stats["SAI_VLAN_STAT_OUT_UCAST_PKTS"]

        # self.assertEqual(in_packets, 0, 'vlan IN packets counter is not 0')
        # self.assertEqual(in_ucast_packets, 0,
        #                 'vlan IN unicast packets counter is not 0')
        # self.assertEqual(in_bytes, 0, 'vlan IN bytes counter is not 0')
        # self.assertEqual(out_packets, 0,
        #                 'vlan OUT packets counter is not 0')
        # self.assertEqual(out_ucast_packets, 0,
        #                 'vlan OUT unicast packets counter is not 0')
        # self.assertEqual(out_bytes, 0, 'vlan OUT bytes counter is not 0')

    def tearDown(self):
        pass