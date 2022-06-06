import os
import time
import sys
import inspect
from threading import Thread

from collections import OrderedDict

from ptf import config
from ptf.base_tests import BaseTest

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from sai_thrift import sai_rpc

import sai_thrift.sai_adapter as adapter
from sai_thrift.sai_adapter import *
from config.basic_config import BasicT0Config
from config.route_config import RouteT0Config
from sai_base_utils import *

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

from sai_base_test import ThriftInterface
from sai_base_test import ThriftInterfaceDataPlane

class SaiT0HelperBase(ThriftInterfaceDataPlane):
    """
    SAI test helper base class without initial switch ports setup

    Set the following class attributes:
        self.default_vlan_id
        self.default_vrf
        self.default_1q_bridge
        self.cpu_port_hdl
        self.active_ports_no - number of active ports
        self.port_list - list of all active port objects
        self.portX objects for all active ports (where X is a port number)
    """

    def setUp(self):
        super(SaiT0HelperBase, self).setUp()
        self.basic_configer = BasicT0Config()
        self.route_configer = RouteT0Config()
        self.getSwitchPorts()
        self.normal_setup()

    def shell(self):
        '''
        Method use to start a sai shell in a thread.
        '''
        def start_shell():
            sai_thrift_set_switch_attribute(self.client, switch_shell_enable=True)
        thread = Thread(target = start_shell)
        thread.start()
   
    def normal_setup(self):
        """
        Normal setup
        """
        print("t0_base_test::normal_setup")
        self.basic_configer.start_switch(self)
        self.basic_configer.config_meta_port(self)
        self.route_configer.create_default_route(self)
    
    def getSwitchPorts(self):
        """
        Get device port numbers
        """
        dev_no = 0
        for _, port, _ in config['interfaces']:
            setattr(self, 'dev_port%d' % dev_no, port)
            dev_no += 1

    def parsePortConfig(self, port_config_file):
        """
        Parse port_config.ini file

        Example of supported format for port_config.ini:
        # name        lanes       alias       index    speed    autoneg   fec
        Ethernet0       0         Ethernet0     1      25000      off     none
        Ethernet1       1         Ethernet1     1      25000      off     none
        Ethernet2       2         Ethernet2     1      25000      off     none
        Ethernet3       3         Ethernet3     1      25000      off     none
        Ethernet4       4         Ethernet4     2      25000      off     none
        Ethernet5       5         Ethernet5     2      25000      off     none
        Ethernet6       6         Ethernet6     2      25000      off     none
        Ethernet7       7         Ethernet7     2      25000      off     none
        Ethernet8       8         Ethernet8     3      25000      off     none
        Ethernet9       9         Ethernet9     3      25000      off     none
        Ethernet10      10        Ethernet10    3      25000      off     none
        Ethernet11      11        Ethernet11    3      25000      off     none
        etc

        Args:
            port_config_file (string): path to port config file

        Returns:
            dict: port configuation from file

        Raises:
            e: exit if file not found
        """
        ports = OrderedDict()
        try:
            index = 0
            with open(port_config_file) as conf:
                for line in conf:
                    if line.startswith('#'):
                        if "name" in line:
                            titles = line.strip('#').split()
                        continue
                    tokens = line.split()
                    if len(tokens) < 2:
                        continue
                    
                    name_index = titles.index('name')
                    name = tokens[name_index]
                    data = {}
                    for i, item in enumerate(tokens):
                        if i == name_index:
                            continue
                        data[titles[i]] = item
                    data['lanes'] = [int(lane)
                                     for lane in data['lanes'].split(',')]
                    data['speed'] = int(data['speed'])
                    data['name'] = name
                    ports[index] = data
                    index = index + 1
            return ports
        except Exception as e:
            raise e

    @staticmethod
    def status():
        """
        Returns the last operation status.

        Returns:
            int: sai call result
        """
        return adapter.status

    @staticmethod
    def saiWaitFdbAge(timeout):
        """
        Wait for fdb entry to ageout

        Args:
            timeout (int): Timeout value in seconds
        """
        print("Waiting for fdb entry to age")
        aging_interval_buffer = 10
        time.sleep(timeout + aging_interval_buffer)
