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
#Todo make those two parameters from input
LOCAL_IP_128V6_PREFIX = 'fe80::f68e:38ff:fe16:bc75/128'
LOCAL_IP_10V6_PREFIX = 'fe80::/10'
PORT_MTU=9122
NAT_ZONE_ID = 0

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


    def config_meta_port(self):
        """
        Default configuation, with metadata and ports configurations.
        """
        self.get_port_list()
        self.create_default_route_intf()
        self.get_default_1q_bridge()
        self.get_default_vlan()
        self.remove_vlan_member()
        self.remove_bridge_port()
        self.create_default_v4_v6_route_entry()
        self.create_local_v6_route()
        self.create_host_intf()
        self.turn_on_port_admin_state()
        #self.set_port_serdes()
        self.config_vlan()


    def start_switch(self):
        """
        Start switch and wait seconds for a warm up.
        """
        switch_init_wait = 1

        self.switch_id = sai_thrift_create_switch(
            self.client, init_switch=True, src_mac_address=ROUTER_MAC)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

        print("Waiting for switch to get ready, {} seconds ...".format(switch_init_wait))
        time.sleep(switch_init_wait)


    def get_port_list(self):
        """
        Set the class variable port_list.
        
        Output variable:
            self.port_list
        """
        port_list = sai_thrift_object_list_t(count=100)
        p_list = sai_thrift_get_switch_attribute(
            self.client, port_list=port_list)
        self.port_list = p_list['port_list'].idlist


    def create_default_route_intf(self):
        """
        Create default route interface on loop back interface.

        Output variables:
            self.default_vrf
            self.lpbk_intf
        """
        print("Create loop back interface...")
        attr = sai_thrift_get_switch_attribute(self.client, default_virtual_router_id=True)
        self.default_vrf = attr['default_virtual_router_id']
        self.assertNotEqual(self.default_vrf, 0)
        self.lpbk_intf = sai_thrift_create_router_interface(
            self.client, type=SAI_ROUTER_INTERFACE_TYPE_LOOPBACK,
            virtual_router_id=self.default_vrf)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)

    
    def get_default_1q_bridge(self):
        """
        Get defaule 1Q bridge.

        Output variables:
            self.default_1q_bridge_id
        """
        print("Get default 1Q bridge...")
        def_attr = sai_thrift_get_switch_attribute(
            self.client, default_1q_bridge_id=True)
        self.default_1q_bridge_id = def_attr['default_1q_bridge_id']


    def get_default_vlan(self):
        """
        Get defaule vlan.

        Output variables:
            self.default_vlan_id
        """
        print("Get default vlan...")
        def_attr = sai_thrift_get_switch_attribute(
            self.client, default_vlan_id=True)
        self.default_vlan_id = def_attr['default_vlan_id']

    
    def remove_vlan_member(self):
        """
        Remove vlan member when init the environment.
        """
        print("Remove vlan and members...")
        vlan_member_list = sai_thrift_object_list_t(count=100)
        mbr_list = sai_thrift_get_vlan_attribute(
            self.client, self.default_vlan_id, member_list=vlan_member_list)
        vlan_members = mbr_list['SAI_VLAN_ATTR_MEMBER_LIST'].idlist

        for member in vlan_members:
            sai_thrift_remove_vlan_member(self.client, vlan_member_oid=member)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)


    def remove_bridge_port(self):
        """
        Remove bridge ports.
        """
        print("Remove bridge ports...")
        bridge_port_list = sai_thrift_object_list_t(count=100)
        bp_list = sai_thrift_get_bridge_attribute(
            self.client, self.default_1q_bridge_id, port_list=bridge_port_list)
        bp_ports = bp_list['port_list'].idlist
        for port in bp_ports:
            sai_thrift_remove_bridge_port(self.client, port)
        self.assertEqual(self.status(), SAI_STATUS_SUCCESS)


    def create_default_v4_v6_route_entry(self):
        """
        Create default v4 and v6 route entry.

        Output variable:
            self.default_ipv6_route_entry
            self.default_ipv4_route_entry
        """
        print("Create default v4 & v6 route entry...")
        v6_default = sai_thrift_ip_prefix_t(
            addr_family=1, addr=sai_thrift_ip_addr_t(ip6=DEFAULT_IP_V6_PREFIX),
            mask=sai_thrift_ip_addr_t(ip6=DEFAULT_IP_V6_PREFIX))
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


    def create_local_v6_route(self):
        """
        Create local v6 route base on the configuration of the actual switch.

        Output variable:
            self.local_10v6_route_entry
            self.local_128v6_route_entry
        """
        #Todo make the v6 prefix from actual device config.

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


    def create_host_intf(self):
        """
        Craete host interface.
        Steps:
         1. create host table entry
         2. create host interface trap
         3. set host interface base on the port_config.int (this file contains the lanes, name and index information.)

        Output variables:
            self.host_intf_table_id
            self.ports_config
            self.port_to_hostif_map
            self.hostifs
        """
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


    def config_vlan(self):
        """
        Default configuation, with Vlan.
        Craete bridge_port and route interface
        Steps:
        """
        VLAN_ID = 1000
        PC_PORT_MTU=9100
        vlan_id = sai_thrift_create_vlan(self.client, vlan_id=VLAN_ID)
        for i in range(3, 24):
            bridge_port_id = sai_thrift_create_bridge_port(self.client,
                    type=SAI_BRIDGE_PORT_TYPE_PORT,
                    port_id=self.port_list[i],
                    admin_state=True,
                    fdb_learning_mode=SAI_BRIDGE_PORT_FDB_LEARNING_MODE_HW)
        
            sai_thrift_set_hostif_attribute(self.client, 
                    hostif_oid=self.hostifs[i], 
                    vlan_tag=SAI_HOSTIF_VLAN_TAG_KEEP)

            self.vlan_member = sai_thrift_create_vlan_member(
                    self.client,
                    vlan_id=vlan_id,
                    bridge_port_id=bridge_port_id,
                    vlan_tagging_mode=SAI_VLAN_TAGGING_MODE_UNTAGGED)

            sai_thrift_set_port_attribute(self.client, 
                    port_oid=self.port_list[i], 
                    port_vlan_id=VLAN_ID)

        rif_id = sai_thrift_create_router_interface(self.client, 
            virtual_router_id=self.default_vrf,
            src_mac_address=ROUTER_MAC,
            type=SAI_ROUTER_INTERFACE_TYPE_PORT,
            mtu=PC_PORT_MTU,
            nat_zone_id=NAT_ZONE_ID)
            
        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix('192.168.0.1/32'),
            switch_id=self.switch_id)

        status = sai_thrift_create_route_entry(
            self.client,
            route_entry=entry, 
            packet_action=SAI_PACKET_ACTION_FORWARD)

        nbr_entry = sai_thrift_neighbor_entry_t(
            rif_id=rif_id,
            ip_address=sai_ipaddress('192.168.7.255'),
            switch_id=self.switch_id
            )

        # status = sai_thrift_create_neighbor_entry(
        #     self.client,
        #     neighbor_entry=nbr_entry,
        #     dst_mac_address="FF:FF:FF:FF:FF:FF"
        #     )

        entry = sai_thrift_route_entry_t(
            vr_id=self.default_vrf,
            destination=sai_ipprefix('fc02:1000::1/128'),
            switch_id=self.switch_id)

        status = sai_thrift_create_route_entry(
            self.client,
            route_entry=entry, 
            packet_action=SAI_PACKET_ACTION_FORWARD)
        self.assertEqual(status, SAI_STATUS_SUCCESS)


    def turn_on_port_admin_state(self):
        """
        Turn on port admin state
        """
        print("Set port...")
        for i, port in enumerate(self.port_list):
            sai_thrift_set_port_attribute(
                self.client, port_oid=port, mtu=PORT_MTU, admin_state=True)


    def set_port_serdes(self):
        """
        Set prot Serdes.
        """     
        print("Recreate Port serdes...")
        for i, port in enumerate(self.port_list):
            sai_thrift_set_port_attribute(
                self.client, port_oid=port, mtu=PORT_MTU, admin_state=True)
