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

"""
This file contains class for brcm specified functions.
"""
import pdb
from socket import AddressFamily
from platform_helper.common_sai_helper import * # pylint: disable=wildcard-import; lgtm[py/polluting-import]

DEFAULT_IP_V4_PREFIX = '0.0.0.0/0'
DEFAULT_IP_V6_PREFIX = '0000:0000:0000:0000:0000:0000:0000:0000'
LOCAL_IP_128V6_PREFIX = 'fe80::f68e:38ff:fe16:bc75/128'
LOCAL_IP_10V6_PREFIX = 'fe80::/10'
PORT_MTU=9122
class BrcmT0SaiHelper(CommonSaiHelper):
    """
    This class contains broadcom(brcm) specified functions for the platform setup and test context configuration.
    """

    platform = 'brcm'
    role_config = 't0'

    def normal_setup(self):
        """
        Normal setup
        """
        print("BrcmT0SaiHelper::normal_setup")
        self.start_switch()
        self.config_meta_port()
        self.config_portchannel()


    def config_meta_port(self):
        """
        Default configuation, with metadata and ports configurations.
        """

        port_list = sai_thrift_object_list_t(count=100)
        p_list = sai_thrift_get_switch_attribute(
            self.client, port_list=port_list)
        self.port_list = p_list['port_list'].idlist
        

        print("Create loop back interface...")
        attr = sai_thrift_get_switch_attribute(self.client, default_virtual_router_id=True)
        self.default_vrf = attr['default_virtual_router_id']
        self.assertNotEqual(self.default_vrf, 0)
        self.lpbk_intf = sai_thrift_create_router_interface(
            self.client, type=SAI_ROUTER_INTERFACE_TYPE_LOOPBACK,
            virtual_router_id=self.default_vrf)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        print("Get default 1Q bridge...")
        def_attr = sai_thrift_get_switch_attribute(
            self.client, default_1q_bridge_id=True, default_vlan_id=True)
        self.default_1q_bridge_id = def_attr['default_1q_bridge_id']
        self.default_vlan_id = def_attr['default_vlan_id'] 


        print("Remove vlan and members...")
        vlan_member_list = sai_thrift_object_list_t(count=100)
        mbr_list = sai_thrift_get_vlan_attribute(
            self.client, self.default_vlan_id, member_list=vlan_member_list)
        vlan_members = mbr_list['SAI_VLAN_ATTR_MEMBER_LIST'].idlist
        count = mbr_list['SAI_VLAN_ATTR_MEMBER_LIST'].count

        for member in vlan_members:
            sai_thrift_remove_vlan_member(self.client, vlan_member_oid=member)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        print("Remove bridge ports...")
        bridge_port_list = sai_thrift_object_list_t(count=100)
        bp_list = sai_thrift_get_bridge_attribute(
            self.client, self.default_1q_bridge_id, port_list=bridge_port_list)
        bp_ports = bp_list['port_list'].idlist
        for port in bp_ports:
            sai_thrift_remove_bridge_port(self.client, port)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        print("Create default v4 & v6 route entry...")
        v6_default = sai_thrift_ip_prefix_t(
            addr_family=1, addr=sai_thrift_ip_addr_t(ip6='0000:0000:0000:0000:0000:0000:0000:0000'), 
            mask=sai_thrift_ip_addr_t(ip6='0000:0000:0000:0000:0000:0000:0000:0000'))
        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=v6_default,
            switch_id=self.switch_id)
        self.default_ipv6_route_entry = sai_thrift_create_route_entry(
            self.client, route_entry=entry, packet_action=SAI_PACKET_ACTION_DROP)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)
        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(DEFAULT_IP_V4_PREFIX),
            switch_id=self.switch_id)
        self.default_ipv4_route_entry = sai_thrift_create_route_entry(
            self.client, route_entry=entry, packet_action=SAI_PACKET_ACTION_DROP)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        print("Create Local V6 route...")
        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(LOCAL_IP_10V6_PREFIX),
            switch_id=self.switch_id)
        self.local_10v6_route_entry = sai_thrift_create_route_entry(
            self.client, route_entry=entry, packet_action=SAI_PACKET_ACTION_FORWARD)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)
        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(LOCAL_IP_128V6_PREFIX),
            switch_id=self.switch_id)
        self.local_128v6_route_entry = sai_thrift_create_route_entry(
            self.client, route_entry=entry, packet_action=SAI_PACKET_ACTION_FORWARD)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        print("Create Host intfs...")
        self.host_intf_table_id = sai_thrift_create_hostif_table_entry(
            self.client, type=SAI_HOSTIF_TABLE_ENTRY_TYPE_WILDCARD,
            channel_type=SAI_HOSTIF_TABLE_ENTRY_CHANNEL_TYPE_NETDEV_PHYSICAL_PORT)
        attr = sai_thrift_get_switch_attribute(self.client, default_trap_group=True)
        self.default_trap_group = attr['default_trap_group']
        sai_thrift_create_hostif_trap(
            self.client, trap_type=SAI_HOSTIF_TRAP_TYPE_TTL_ERROR, packet_action=SAI_PACKET_ACTION_TRAP,
            trap_group=self.default_trap_group, trap_priority=0)

        self.ports_config = self.parsePortConfig(
            self.test_params['port_config_ini'])
        self.port_to_hostif_map = {}
        self.hostifs = []
        for i, _ in enumerate(self.port_list):
            try:
                setattr(self, 'port%s' % i, self.port_list[i])
                hostif = sai_thrift_create_hostif(
                    self.client, 
                    type=SAI_HOSTIF_TYPE_NETDEV,
                    obj_id=self.port_list[i],
                    name=self.ports_config[i]['name'])
                setattr(self, 'host_if%s' % i, hostif)
                self.port_to_hostif_map[i]=hostif
                sai_thrift_set_hostif_attribute(self.client, hostif_oid=hostif, oper_status=False)
                self.hostifs.append(hostif)
            except BaseException as e:
                print("Cannot create hostif, error : {}".format(e))

        print("Set port...")
        for i, port in enumerate(self.port_list):
            sai_thrift_set_port_attribute(
                self.client, port_oid=port, mtu=PORT_MTU, admin_state=True)
        
        print("Recreate Port serdes...")
        #for i, port in enumerate(self.port_list):
            #serdes = sai_thrift_get_port_attribute(self.client, port_serdes_id=True)
            #sai_thrift_remove_port_serdes(self.client, serdes)
            #sai_thrift_create_port_serdes(
            #    self.client, port_oid=port, mtu=PORT_MTU, admin_state=True)

    def config_portchannel(self):
        """
        Default configration for Port Channel 
        """
        print("Get Port List...")
        port_list = sai_thrift_object_list_t(count=100)
        p_list = sai_thrift_get_switch_attribute(
            self.client, port_list=port_list)
        self.port_list = p_list['port_list'].idlist

        self.port1 = self.port_list[hw_port1]
        self.port2 = self.port_list[hw_port2]
        self.port3 = self.port_list[hw_port3]
        self.port4 = self.port_list[hw_port4]

        print("Create lag...")
        vlan_id1 = 1
        vlan_id2 = 1000
        self.lag_list = []

        self.lag_id1 = sai_thrift_create_lag(self.client)
        self.lag_id2 = sai_thrift_create_lag(self.client)
        self.lag_id3 = sai_thrift_create_lag(self.client)
        self.lag_id4 = sai_thrift_create_lag(self.client)

        sai_thrift_set_port_attribute(self.client, port_oid=self.port1, port_vlan_id=self.vlan_id1)
        self.lag_member1 = sai_thrift_create_lag_member(
            self.client, 
            lag_id=self.lag_id1, 
            port_id=self.port1,
            egress_disable=True,
            ingress_disable=True)

        sai_thrift_set_port_attribute(self.client, port_oid=self.port2, port_vlan_id=self.vlan_id1)
        self.lag_member2 = sai_thrift_create_lag_member(
            self.client, 
            lag_id=self.lag_id2, 
            port_id=self.port2
            egress_disable=True,
            ingress_disable=True)

        sai_thrift_set_port_attribute(self.client, port_oid=self.port3, port_vlan_id=self.vlan_id1)
        self.lag_member3 = sai_thrift_create_lag_member(
            self.client, 
            lag_id=self.lag_id3, 
            port_id=self.port3
            egress_disable=True,
            ingress_disable=True)

        sai_thrift_set_port_attribute(self.client, port_oid=self.port4, port_vlan_id=self.vlan_id1)
        self.lag_member4 = sai_thrift_create_lag_member(
            self.client, 
            lag_id=self.lag_id4, 
            port_id=self.port4
            egress_disable=True,
            ingress_disable=True)

        PC_IP_32V4_PREFIX1 = '10.0.0.56/32'
        PC_IP_32V4_PREFIX2 = '10.0.0.58/32'
        PC_IP_32V4_PREFIX3 = '10.0.0.60/32'
        PC_IP_32V4_PREFIX4 = '10.0.0.62/32'

        PC_IP_128V6_PREFIX1 = 'fc00::71/128'
        PC_IP_128V6_PREFIX2 = 'fc00::75/128'
        PC_IP_128V6_PREFIX3 = 'fc00::79/128'
        PC_IP_128V6_PREFIX4 = 'fc00::7d/128'
        PC_PORT_MTU = 9100
        NAT_ZONE_ID = 0

        print("Create route...")
        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(LOCAL_IP_10V6_PREFIX),
            switch_id=self.switch_id)
        self.local_10v6_route_entry = sai_thrift_create_route_entry(
            self.client, route_entry=entry, packet_action=SAI_PACKET_ACTION_FORWARD)

        rif_id1 = sai_thrift_create_router_interface(self.client, 
            vr_id=self.default_vrf,
            src_mac_address=ROUTER_MAC,
            type=SAI_ROUTER_INTERFACE_TYPE_PORT,
            mtu=PC_PORT_MTU
            port_id=self.port1,
            nat_zone_id=NAT_ZONE_ID)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(PC_IP_32V4_PREFIX1),
            switch_id=self.switch_id)

        self.pc_32v4_route_entry1 = sai_thrift_create_route_entry(
            self.client,
            route_entry=entry, 
            packet_action=SAI_PACKET_ACTION_FORWARD)

        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(PC_IP_128V6_PREFIX1),
            switch_id=self.switch_id)
        self.pc_128v6_route_entry1 = sai_thrift_create_route_entry(
            self.client,
            route_entry=entry, 
            packet_action=SAI_PACKET_ACTION_FORWARD)

        rif_id2 = sai_thrift_create_router_interface(self.client, 
            vr_id=self.default_vrf,
            src_mac_address=ROUTER_MAC,
            type=SAI_ROUTER_INTERFACE_TYPE_PORT,
            mtu=PC_PORT_MTU
            port_id=self.port2,
            nat_zone_id=NAT_ZONE_ID)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(PC_IP_32V4_PREFIX2),
            switch_id=self.switch_id)

        self.pc_32v4_route_entry2 = sai_thrift_create_route_entry(
            self.client,
            route_entry=entry, 
            packet_action=SAI_PACKET_ACTION_FORWARD)

        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(PC_IP_128V6_PREFIX2),
            switch_id=self.switch_id)
        self.pc_128v6_route_entry2 = sai_thrift_create_route_entry(
            self.client,
            route_entry=entry, 
            packet_action=SAI_PACKET_ACTION_FORWARD)


        rif_id3 = sai_thrift_create_router_interface(self.client, 
            vr_id=self.default_vrf,
            src_mac_address=ROUTER_MAC,
            type=SAI_ROUTER_INTERFACE_TYPE_PORT,
            mtu=PC_PORT_MTU
            port_id=self.port3,
            nat_zone_id=NAT_ZONE_ID)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(PC_IP_32V4_PREFIX3),
            switch_id=self.switch_id)

        self.pc_32v4_route_entry3 = sai_thrift_create_route_entry(
            self.client,
            route_entry=entry, 
            packet_action=SAI_PACKET_ACTION_FORWARD)

        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(PC_IP_128V6_PREFIX3),
            switch_id=self.switch_id)
        self.pc_128v6_route_entry3 = sai_thrift_create_route_entry(
            self.client,
            route_entry=entry, 
            packet_action=SAI_PACKET_ACTION_FORWARD)


        rif_id4 = sai_thrift_create_router_interface(self.client, 
            vr_id=self.default_vrf,
            src_mac_address=ROUTER_MAC,
            type=SAI_ROUTER_INTERFACE_TYPE_PORT,
            mtu=PC_PORT_MTU
            port_id=self.port4,
            nat_zone_id=NAT_ZONE_ID)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(PC_IP_32V4_PREFIX4),
            switch_id=self.switch_id)

        self.pc_32v4_route_entry4 = sai_thrift_create_route_entry(
            self.client,
            route_entry=entry, 
            packet_action=SAI_PACKET_ACTION_FORWARD)

        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix(PC_IP_128V6_PREFIX4),
            switch_id=self.switch_id)
        self.pc_128v6_route_entry4 = sai_thrift_create_route_entry(
            self.client,
            route_entry=entry, 
            packet_action=SAI_PACKET_ACTION_FORWARD)
    

        print("Create policer...")

        print("Set default trap group...")
        def_attr = sai_thrift_get_switch_attribute(
            self.client, default_trap_group=True)
        self.default_trap_group = def_attr['default_trap_group']

        

        POLICER_CBS1 = 600
        POLICER_CIR1 = 600
        POLICER_CBS2 = 6000
        POLICER_CIR2 = 6000

        sai_policer_id1 = sai_thrift_create_policer(self.client,
                            meter_type=SAI_METER_TYPE_PACKETS,
                            mode=SAI_POLICER_MODE_SR_TCM,
                            cbs=POLICER_CBS1,
                            cir=POLICER_CIR1,
                            packet_action=SAI_PACKET_ACTION_DROP)
        sai_thrift_set_hostif_trap_group(self.client, queue=0, policer=self.sai_policer_id1)

        sai_policer_id2 = sai_thrift_create_policer(self.client,
                            meter_type=SAI_METER_TYPE_PACKETS,
                            mode=SAI_POLICER_MODE_SR_TCM,
                            cbs=POLICER_CBS2,
                            cir=POLICER_CIR2,
                            packet_action=SAI_PACKET_ACTION_DROP)

        trap_group_id2 = sai_thrift_create_hostif_trap_group(self.client, queue=4)
        sai_thrift_set_hostif_trap_group(self.client, policer=sai_policer_id2)
        sai_thrift_create_hostif_trap(client=self.client,
            type=SAI_HOSTIF_TRAP_TYPE_BGP,
            trap_group_id=trap_group_id2,
            packet_action=SAI_PACKET_ACTION_TRAP,
            trap_priority=4)

        sai_thrift_create_hostif_trap(client=self.client,
            type=SAI_HOSTIF_TRAP_TYPE_BGPV6,
            trap_group=trap_group_id2,
            packet_action=SAI_PACKET_ACTION_TRAP,
            trap_priority=4)

        sai_thrift_create_hostif_trap(client=self.client,
            type=SAI_HOSTIF_TRAP_TYPE_LACP,
            trap_group=trap_group_id2,
            packet_action=SAI_PACKET_ACTION_TRAP,
            trap_priority=4)
        

        trap_group_id3 = sai_thrift_create_hostif_trap_group(self.client, queue=4)
        sai_policer_id3 = sai_thrift_create_policer(self.client,
                            meter_type=SAI_METER_TYPE_PACKETS,
                            mode=SAI_POLICER_MODE_SR_TCM,
                            cbs=POLICER_CBS1,
                            cir=POLICER_CIR1,
                            packet_action=SAI_PACKET_ACTION_DROP)

        
        sai_thrift_set_hostif_trap_group(self.client, policer=sai_policer_id3)

        sai_thrift_create_hostif_trap(client=self.client,
            type=SAI_HOSTIF_TRAP_TYPE_ARP_REQUEST,
            trap_group_id=trap_group_id3,
            packet_action=SAI_PACKET_ACTION_TRAP,
            trap_priority=4)

        sai_thrift_create_hostif_trap(client=self.client,
            type=SAI_HOSTIF_TRAP_TYPE_ARP_RESPONSE,
            trap_group=trap_group_id3,
            packet_action=SAI_PACKET_ACTION_TRAP,
            trap_priority=4)

        sai_thrift_create_hostif_trap(client=self.client,
            type=SAI_HOSTIF_TRAP_TYPE_IPV6_NEIGHBOR_DISCOVERY,
            trap_group=trap_group_id3,
            packet_action=SAI_PACKET_ACTION_TRAP,
            trap_priority=4)

        trap_group_id4 = sai_thrift_create_hostif_trap_group(self.client, queue=4)

        sai_thrift_create_hostif_trap(client=self.client,
            type=SAI_HOSTIF_TRAP_TYPE_DHCP,
            trap_group_id=trap_group_id4,
            packet_action=SAI_PACKET_ACTION_TRAP,
            trap_priority=4)

        sai_thrift_create_hostif_trap(client=self.client,
            type=SAI_HOSTIF_TRAP_TYPE_DHCPV6,
            trap_group=trap_group_id4,
            packet_action=SAI_PACKET_ACTION_TRAP,
            trap_priority=4)

        sai_thrift_create_hostif_trap(client=self.client,
            type=SAI_HOSTIF_TRAP_TYPE_LLDP,
            trap_group=trap_group_id4,
            packet_action=SAI_PACKET_ACTION_TRAP,
            trap_priority=4)

        sai_thrift_create_hostif_trap(client=self.client,
            type=SAI_HOSTIF_TRAP_TYPE_UDLD,
            trap_group=trap_group_id4,
            packet_action=SAI_PACKET_ACTION_TRAP,
            trap_priority=4)


        print("Disable Lag configration...")
        sai_thrift_set_port_attribute(self.client, port_oid=self.port1, port_vlan_id=self.vlan_id1)
        sai_thrift_set_lag_member(self.client, 
            lag_member=self.lag1_member, 
            egress_disable=False,
            ingress_disable=False)

        nbr_entry = sai_thrift_neighbor_entry_t(
            rif=rif_id1,
            ip='10.0.0.57',
            switch_id=self.switch_id,

            )
        status = sai_thrift_create_neighbor_entry(
            self.client,
            nbr_entry,
            dst_mac_address='02:D9:B8:E2:36:33'
            )

        nexthop = sai_thrift_create_next_hop(
            self.client,
            ip='10.0.0.57',
            router_interface_id=rif_id1,
            type=SAI_NEXT_HOP_TYPE_IP)
        self.assertEqual(status, SAI_STATUS_SUCCESS)

        sai_thrift_set_port_attribute(self.client, port_oid=self.port4, port_vlan_id=self.vlan_id1)
        sai_thrift_set_lag_member(self.client, lag_member=lag_member1, egress_disable=False, ingress_disable=False)

        rif_id2 = sai_thrift_create_router_interface(self.client, 
            vr_id=self.default_vrf,
            src_mac_address=ROUTER_MAC,
            type=SAI_ROUTER_INTERFACE_TYPE_PORT,
            mtu=PC_PORT_MTU
            port_id=self.port2,
            nat_zone_id=NAT_ZONE_ID)
            
        sai_thrift_set_router_interface(self.client, rif=rif_id1, mtu=PC_PORT_MTU)
        sai_thrift_set_router_interface(self.client, rif=rif_id2, mtu=PC_PORT_MTU)
        sai_thrift_set_router_interface(self.client, rif=rif_id3, mtu=PC_PORT_MTU)
        sai_thrift_set_router_interface(self.client, rif=rif_id4, mtu=PC_PORT_MTU)

        sai_thrift_set_lag_member(self.client, lag_member=lag_member2, egress_disable=False, ingress_disable=False)
        sai_thrift_set_lag_member(self.client, lag_member=lag_member3, egress_disable=False, ingress_disable=False)
        sai_thrift_set_lag_member(self.client, lag_member=lag_member4, egress_disable=False, ingress_disable=False)


        nbr_entry = sai_thrift_neighbor_entry_t(
            rif=rif_id2,
            ip='10.0.0.59',
            switch_id=self.switch_id,
            )

        status = sai_thrift_create_neighbor_entry(
            self.client,
            nbr_entry,
            dst_mac_address='32:A3:B0:44:01:DA'
            )

        nexthop = sai_thrift_create_next_hop(
            self.client,
            ip='10.0.0.59',
            router_interface_id=rif_id2,
            type=SAI_NEXT_HOP_TYPE_IP)
        self.assertEqual(status, SAI_STATUS_SUCCESS)


        nbr_entry = sai_thrift_neighbor_entry_t(
            rif=rif_id3,
            ip='10.0.0.61',
            switch_id=self.switch_id,

            )
        status = sai_thrift_create_neighbor_entry(
            self.client,
            nbr_entry,
            dst_mac_address='4E:8E:DF:55:5F:26'
            )

        nexthop = sai_thrift_create_next_hop(
            self.client,
            ip='10.0.0.61',
            router_interface_id=rif_id4,
            type=SAI_NEXT_HOP_TYPE_IP)
        self.assertEqual(status, SAI_STATUS_SUCCESS)

        nbr_entry = sai_thrift_neighbor_entry_t(
            rif=rif_id4,
            ip='10.0.0.63',
            switch_id=self.switch_id,
            )

        status = sai_thrift_create_neighbor_entry(
            self.client,
            nbr_entry,
            dst_mac_address='46:B1:78:24:6A:0E'
            )

        nexthop = sai_thrift_create_next_hop(
            self.client,
            ip='10.0.0.63',
            router_interface_id=rif_id3,
            type=SAI_NEXT_HOP_TYPE_IP)
        self.assertEqual(status, SAI_STATUS_SUCCESS)

        nbr_entry = sai_thrift_neighbor_entry_t(
            rif=rif_id1,
            ip='fc00::72',
            switch_id=self.switch_id,
            )

        status = sai_thrift_create_neighbor_entry(
            self.client,
            nbr_entry,
            dst_mac_address='02:D9:B8:E2:36:33'
            )

        nexthop = sai_thrift_create_next_hop(
            self.client,
            ip='fc00::72',
            router_interface_id=rif_id1,
            type=SAI_NEXT_HOP_TYPE_IP)
        self.assertEqual(status, SAI_STATUS_SUCCESS)



        nbr_entry = sai_thrift_neighbor_entry_t(
            rif=rif_id2,
            ip='fc00::7a',
            switch_id=self.switch_id,

            )
        status = sai_thrift_create_neighbor_entry(
            self.client,
            nbr_entry,
            dst_mac_address='4E:8E:DF:55:5F:26'
            )

        nexthop = sai_thrift_create_next_hop(
            self.client,
            ip='fc00::7a',
            router_interface_id=rif_id2,
            type=SAI_NEXT_HOP_TYPE_IP)
        self.assertEqual(status, SAI_STATUS_SUCCESS)

        nbr_entry = sai_thrift_neighbor_entry_t(
            rif=rif_id4,
            ip='fc00::76',
            switch_id=self.switch_id,
            )

        status = sai_thrift_create_neighbor_entry(
            self.client,
            nbr_entry,
            dst_mac_address='46:B1:78:24:6A:0E'
            )

        nexthop = sai_thrift_create_next_hop(
            self.client,
            ip='fc00::76',
            router_interface_id=rif_id3,
            type=SAI_NEXT_HOP_TYPE_IP)
        self.assertEqual(status, SAI_STATUS_SUCCESS)

        nbr_entry = sai_thrift_neighbor_entry_t(
            rif=rif_id4,
            ip='fc00::7e',
            switch_id=self.switch_id,
            )

        status = sai_thrift_create_neighbor_entry(
            self.client,
            nbr_entry,
            dst_mac_address='46:B1:78:24:6A:0E'
            )

        nexthop = sai_thrift_create_next_hop(
            self.client,
            ip='fc00::7e',
            router_interface_id=rif_id3,
            type=SAI_NEXT_HOP_TYPE_IP)
        self.assertEqual(status, SAI_STATUS_SUCCESS)


    def start_switch(self):
        """
        Start switch and wait seconds for a warm up.
        """
        switch_init_wait = 5

        self.switch_id = sai_thrift_create_switch(
            self.client, init_switch=True, src_mac_address=ROUTER_MAC)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        print("Waiting for switch to get ready, {} seconds ...".format(switch_init_wait))
        #time.sleep(switch_init_wait)
