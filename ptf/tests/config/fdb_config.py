import os
from platform import mac_ver
import time
import sys
import inspect

from config.constant import *
from sai_thrift.sai_adapter import *
from sai_base_utils import * # pylint: disable=wildcard-import; lgtm[py/polluting-import]

class FdbT0Config(object):
    """
    Class use to make all the fdb configurations.
    """
    def config_fdb(self, test):
        """
         Config fdb according to config_t0.md in sai-ptf test plan
        """
        print("Create fdb config...")
        test.port0_mac_list = generate_mac_address_list(FDB_MAC_PREFIX, 99, 0, 0, 0)
        self.create_fdb_entries(test, test.port0_mac_list, 0, SAI_FDB_ENTRY_TYPE_STATIC)

        test.vlan10_mac_list = generate_mac_address_list(FDB_MAC_PREFIX, 99, 1, 1, 8)
        self.create_fdb_entries(test, test.vlan10_mac_list, 1, SAI_FDB_ENTRY_TYPE_STATIC)

        test.vlan20_mac_list = generate_mac_address_list(FDB_MAC_PREFIX, 99, 2, 9, 16)
        self.create_fdb_entries(test, test.vlan20_mac_list, 9, SAI_FDB_ENTRY_TYPE_STATIC)


    def create_fdb_entries(self, test, mac_list, port_start_index, type, vlan_oid=None):
        """
         Create fdb entries 
        """
        for index, mac in enumerate(mac_list):
            port_index = index + port_start_index
            fdb_entry = sai_thrift_fdb_entry_t(
                switch_id=test.switch_id, 
                mac_address= mac, 
                bv_id=vlan_oid)
            sai_thrift_create_fdb_entry(
                test.client,
                fdb_entry,
                type=type,
                bridge_port_id=test.bridge_port_list[port_index],
                packet_action=SAI_PACKET_ACTION_FORWARD)
