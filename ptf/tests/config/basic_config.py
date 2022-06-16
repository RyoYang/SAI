import os
import time
import sys
import inspect

from config.constant import *

from sai_thrift.sai_adapter import *

class BasicT0Config(object):
    """
    Class use to make all the basic configurations.
    """

    def config_meta_port(self, test):
        """
        Default configuation, with metadata and ports configurations.
        """
        self.get_port_list(test)     
        self.turn_up_and_check_ports(test)  
        self.get_port_list(test)        
        self.get_default_1q_bridge(test)
        self.get_default_vlan(test)
        self.remove_vlan_member(test)
        self.remove_bridge_port(test)
        self.create_bridge_port(test)
        self.create_host_intf(test)
        self.turn_on_port_admin_state(test)
        #test.set_port_serdes()


    def start_switch(self, test):
        """
        Start switch and wait seconds for a warm up.
        """
        switch_init_wait = 1

        test.switch_id = sai_thrift_create_switch(
            test.client, init_switch=True, src_mac_address=ROUTER_MAC)
        test.assertEqual(test.status(), SAI_STATUS_SUCCESS)

        print("Waiting for switch to get ready, {} seconds ...".format(switch_init_wait))
        time.sleep(switch_init_wait)


    def get_port_list(self, test):
        """
        Set the class variable port_list.

        Output variable:
            test.port_list
        """
        port_list = sai_thrift_object_list_t(count=100)
        p_list = sai_thrift_get_switch_attribute(
            test.client, port_list=port_list)
        test.port_list = p_list['port_list'].idlist


    def get_default_1q_bridge(self, test):
        """
        Get defaule 1Q bridge.

        Output variables:
            test.default_1q_bridge_id
        """
        print("Get default 1Q bridge...")
        def_attr = sai_thrift_get_switch_attribute(
            test.client, default_1q_bridge_id=True)
        test.default_1q_bridge_id = def_attr['default_1q_bridge_id']


    def get_default_vlan(self, test):
        """
        Get defaule vlan.

        Output variables:
            test.default_vlan_id
        """
        print("Get default vlan...")
        def_attr = sai_thrift_get_switch_attribute(
            test.client, default_vlan_id=True)
        test.default_vlan_id = def_attr['default_vlan_id']


    def remove_vlan_member(self, test):
        """
        Remove vlan member when init the environment.
        """
        print("Remove vlan and members...")
        vlan_member_list = sai_thrift_object_list_t(count=100)
        mbr_list = sai_thrift_get_vlan_attribute(
            test.client, test.default_vlan_id, member_list=vlan_member_list)
        vlan_members = mbr_list['SAI_VLAN_ATTR_MEMBER_LIST'].idlist

        for member in vlan_members:
            sai_thrift_remove_vlan_member(test.client, vlan_member_oid=member)
        test.assertEqual(test.status(), SAI_STATUS_SUCCESS)


    def remove_bridge_port(self, test):
        """
        Remove bridge ports.
        """
        print("Remove bridge ports...")
        bridge_port_list = sai_thrift_object_list_t(count=100)
        bp_list = sai_thrift_get_bridge_attribute(
            test.client, test.default_1q_bridge_id, port_list=bridge_port_list)
        bp_ports = bp_list['port_list'].idlist
        for port in bp_ports:
            sai_thrift_remove_bridge_port(test.client, port)
        test.assertEqual(test.status(), SAI_STATUS_SUCCESS)

    def create_host_intf(self, test):
        """
        Craete host interface.
        Steps:
         1. create host table entry
         2. create host interface trap
         3. set host interface base on the port_config.int (this file contains the lanes, name and index information.)

        Output variables:
            test.host_intf_table_id
            test.ports_config
            test.port_to_hostif_map
            test.hostifs
        """
        print("Create Host intfs...")
        test.host_intf_table_id = sai_thrift_create_hostif_table_entry(
            test.client, type=SAI_HOSTIF_TABLE_ENTRY_TYPE_WILDCARD,
            channel_type=SAI_HOSTIF_TABLE_ENTRY_CHANNEL_TYPE_NETDEV_PHYSICAL_PORT)
        attr = sai_thrift_get_switch_attribute(test.client, default_trap_group=True)
        test.default_trap_group = attr['default_trap_group']
        sai_thrift_create_hostif_trap(
            test.client, trap_type=SAI_HOSTIF_TRAP_TYPE_TTL_ERROR, packet_action=SAI_PACKET_ACTION_TRAP,
            trap_group=test.default_trap_group, trap_priority=0)

        test.ports_config = test.parsePortConfig(
            test.test_params['port_config_ini'])
        test.port_to_hostif_map = {}
        test.hostif_list = []
        for i, _ in enumerate(test.port_list):
            try:
                setattr(self, 'port%s' % i, test.port_list[i])
                hostif = sai_thrift_create_hostif(
                    test.client, 
                    type=SAI_HOSTIF_TYPE_NETDEV,
                    obj_id=test.port_list[i],
                    name=test.ports_config[i]['name'])
                setattr(self, 'host_if%s' % i, hostif)
                test.port_to_hostif_map[i]=hostif
                sai_thrift_set_hostif_attribute(test.client, hostif_oid=hostif, oper_status=False)
                test.hostif_list.append(hostif)
            except BaseException as e:
                print("Cannot create hostif, error : {}".format(e))


    def create_bridge_port(self, test):
        """
        Create bridge ports base on port_list.
        """
        test.bridge_port_list = []
        for i, _ in enumerate(test.port_list):
            port_bp = sai_thrift_create_bridge_port(
                test.client,
                bridge_id=test.default_1q_bridge_id,
                port_id=test.port_list[i],
                type=SAI_BRIDGE_PORT_TYPE_PORT,
                admin_state=True)
            test.bridge_port_list.append(port_bp)


    def turn_on_port_admin_state(self, test):
        """
        Turn on port admin state
        """
        print("Set port...")
        for i, port in enumerate(test.port_list):
            sai_thrift_set_port_attribute(
                test.client, port_oid=port, mtu=PORT_MTU, admin_state=True)


    def set_port_serdes(self, test):
        """
        Set prot Serdes.
        """     
        print("Recreate Port serdes...")
        for i, port in enumerate(test.port_list):
            sai_thrift_set_port_attribute(
                test.client, port_oid=port, mtu=PORT_MTU, admin_state=True)


    def turn_up_and_check_ports(self, test):
        '''
        Method to turn up the ports.
        In case some device not init the port after start the switch.
        Needs the following class attributes:
            self.port_list - list of all active port objects
        '''

        #For brcm devices, need to init and setup the ports at once after start the switch.
        retries = 10
        for port_id in test.port_list:
            try:
                sai_thrift_set_port_attribute(
                    test.client, port_oid=port_id, admin_state=True)
            except BaseException as e:
                print("Cannot setup port admin state, error {}".format(e))

        for num_of_tries in range(retries):
            all_ports_are_up = True
            time.sleep(2)
            for port_id in test.port_list:
                port_attr = sai_thrift_get_port_attribute(
                    test.client, port_id, oper_status=True)
                if port_attr['oper_status'] != SAI_PORT_OPER_STATUS_UP:
                    all_ports_are_up = False
                    time.sleep(1)
                    print("port is down: {}".format(port_attr['oper_status']))
            if all_ports_are_up:
                break
        if not all_ports_are_up:
            print("Not all the ports are up after {} rounds of retries.".format(retries))
