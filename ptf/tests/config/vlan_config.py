from doctest import testfile
from imghdr import tests
import os
import time
import sys
import inspect

from config.constant import *
from sai_thrift.sai_adapter import *
from sai_base_utils import * # pylint: disable=wildcard-import; lgtm[py/polluting-import]

class VlanT0Config(object):
    """
    Class use to make all the vlan configurations.
    """

    def vlan_config(self, test):
        """
         Config fdb according to config_t0.md in sai-ptf test plan
        """
        print("Create vlan config...")
        test.vlan_list = []
        test.vlan_member_list = []
        test.vlan_rif_list = []
        self.config_vlan(test, [10, 20])
        self.config_vlan_member(test, test.vlan10, 1, 8)
        self.config_vlan_member(test, test.vlan20, 9, 16)
        # self.config_vlan_intf(test, 

    def config_vlan(self, test, vlan_id_list):
        for vlan_id in vlan_id_list:
            vlan_oid = sai_thrift_create_vlan(test.client, vlan_id=vlan_id)
            test.vlan_list.append(vlan_oid)
            setattr(test, 'vlan%s' % (vlan_id), vlan_oid)


    def config_vlan_member(self, test, vlan_oid, port_start, port_end):
        attr = sai_thrift_get_vlan_attribute(test.client, vlan_oid, vlan_id=True)
        vlan_id = attr['vlan_id']
        for port_index in range(port_start, port_end):
            vlan_member = sai_thrift_create_vlan_member(test.client,
                vlan_id = vlan_oid, 
                bridge_port_id=test.bridge_port_list[port_index],
                vlan_tagging_mode=SAI_VLAN_TAGGING_MODE_UNTAGGED)
            test.vlan_member_list.append(vlan_member)
            sai_thrift_set_port_attribute(test.client, test.port_list[port_index], port_vlan_id=vlan_id)


    def create_vlan_interfaces(self, test):
        print("Create vlan interfaces...")
        self.create_vlan_interface(test, vlan_id=self.vlan10, ip_address='192.168.10.1')
        self.create_vlan_interface(test, vlan_id=self.vlan20, ip_address='192.168.20.1')


    def create_vlan_interface(self, test, vlan_oid, ip_address):

        attr = sai_thrift_get_vlan_attribute(self.client, vlan_oid, vlan_id==True)
        vlan_id = attr['vlan_id']

        vlan_rif = sai_thrift_create_router_interface(
            test.client,
            type=SAI_ROUTER_INTERFACE_TYPE_VLAN,
            virtual_router_id=self.default_vrf,
            vlan_id=vlan_oid)
            setattr(test, 'vlan%s_rif' % (vlan_id), vlan_rif)
            vlan_id = None
        test.rif_list.append(vlan_rif)

    
    def create_port_router_interfaces(self):
        print("Create port router interface and neighbor entry ...")
        self.create_vlan_neighbor_entry()
        for i in range(1, 32):
            port_index = i
            if i <= 8:
                self.create_port_router_interface(port_index, '192.168.10.11', '10:00:11:11:11:11')
            elif i <= 16:
                self.create_port_router_interface(port_index, '192.168.20.11', '20:00:11:11:11:11')
            else:
                self.create_port_router_interface(port_index, '192.168.0.17', '00:00:77:77:77:77')


    def create_port_router_interface(self, port_index, ip_address, mac_address):
        rif = sai_thrift_create_router_interface(
        self.client, type=SAI_ROUTER_INTERFACE_TYPE_PORT,
        port_id=self.port_list[port_index], virtual_router_id=self.default_vrf) 
        rifnh = sai_thrift_create_next_hop(
            self.client, ip=sai_ipaddress(ip_address),
            router_interface_id=rif, type=SAI_NEXT_HOP_TYPE_IP)
        neighbor_entry = sai_thrift_neighbor_entry_t(
                rif_id=self.rif, 
                ip_address=sai_ipaddress(ip_address),
                dst_mac_address=mac_address)
        setattr(self, 'nb%s' % (port_index), neighbor_entry)     


    def remove_vlan_members(self, test):
        print("Teardown lags...")
        for vlan_member in test.vlan_member_list:
            sai_thrift_remove_vlan_member(test.client, vlan_member)


    def remove_vlans(self, test):
        print("Teardown lag members...")
        for vlan in test.vlan_list:
            sai_thrift_remove_vlan(test.client, vlan)