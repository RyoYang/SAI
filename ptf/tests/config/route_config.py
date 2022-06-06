import os
import time
import sys
import inspect

from config.constant import *
from sai_thrift.sai_adapter import *
from sai_base_utils import * # pylint: disable=wildcard-import; lgtm[py/polluting-import]

class RouteT0Config(object):
    """
    Class use to make all the route configurations.
    """

    def create_default_route(self, test):
        
        self.create_default_route_intf(test)
        self.create_default_v4_v6_route_entry(test)
        self.create_local_v6_route(test)


    def create_default_route_intf(self, test):
        """
        Create default route interface on loop back interface.

        Output variables:
            test.default_vrf
            test.lpbk_intf
        """
        print("Create loop back interface...")
        attr = sai_thrift_get_switch_attribute(test.client, default_virtual_router_id=True)
        test.default_vrf = attr['default_virtual_router_id']
        test.assertNotEqual(test.default_vrf, 0)
        test.lpbk_intf = sai_thrift_create_router_interface(
            test.client, type=SAI_ROUTER_INTERFACE_TYPE_LOOPBACK,
            virtual_router_id=test.default_vrf)
        test.assertEqual(test.status(), SAI_STATUS_SUCCESS)

    def create_default_v4_v6_route_entry(self, test):
        """
        Create default v4 and v6 route entry.

        Output variable:
            test.default_ipv6_route_entry
            test.default_ipv4_route_entry
        """
        print("Create default v4 & v6 route entry...")
        v6_default = sai_thrift_ip_prefix_t(
            addr_family=1, addr=sai_thrift_ip_addr_t(ip6=DEFAULT_IP_V6_PREFIX),
            mask=sai_thrift_ip_addr_t(ip6=DEFAULT_IP_V6_PREFIX))
        entry = sai_thrift_route_entry_t(
            vr_id=test.default_vrf,
            destination=v6_default,
            switch_id=test.switch_id)
        test.default_ipv6_route_entry = sai_thrift_create_route_entry(
            test.client, route_entry=entry, packet_action=SAI_PACKET_ACTION_DROP)
        test.assertEqual(test.status(), SAI_STATUS_SUCCESS)
        entry = sai_thrift_route_entry_t(
            vr_id=test.default_vrf,
            destination=sai_ipprefix(DEFAULT_IP_V4_PREFIX),
            switch_id=test.switch_id)
        test.default_ipv4_route_entry = sai_thrift_create_route_entry(
            test.client, route_entry=entry, packet_action=SAI_PACKET_ACTION_DROP)
        test.assertEqual(test.status(), SAI_STATUS_SUCCESS)


    def create_local_v6_route(self, test):
        """
        Create local v6 route base on the configuration of the actual switch.

        Output variable:
            test.local_10v6_route_entry
            test.local_128v6_route_entry
        """
        #Todo make the v6 prefix from actual device config.

        print("Create Local V6 route...")
        entry = sai_thrift_route_entry_t(
            vr_id=test.default_vrf,
            destination=sai_ipprefix(LOCAL_IP_10V6_PREFIX),
            switch_id=test.switch_id)
        test.local_10v6_route_entry = sai_thrift_create_route_entry(
            test.client, route_entry=entry, packet_action=SAI_PACKET_ACTION_FORWARD)
        test.assertEqual(test.status(), SAI_STATUS_SUCCESS)
        entry = sai_thrift_route_entry_t(
            vr_id=test.default_vrf,
            destination=sai_ipprefix(LOCAL_IP_128V6_PREFIX),
            switch_id=test.switch_id)
        test.local_128v6_route_entry = sai_thrift_create_route_entry(
            test.client, route_entry=entry, packet_action=SAI_PACKET_ACTION_FORWARD)
        test.assertEqual(test.status(), SAI_STATUS_SUCCESS)