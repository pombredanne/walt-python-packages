#!/usr/bin/env python

from walt.common.tools import get_mac_address
from walt.common.nodetypes import get_node_type_from_mac_address
from walt.common.nodetypes import is_a_node_type_name
import snmp, const
from tree import Tree
import walt.server

DEVICE_NAME_NOT_FOUND="""No device with name '%s' found.\n"""

TOPOLOGY_QUERY = """
    SELECT  d1.name as name, d1.type as type, d1.mac as mac,
            d1.ip as ip, d1.reachable as reachable,
            d2.name as switch_name, t.switch_port as switch_port
    FROM devices d1, devices d2, topology t
    WHERE   d1.mac = t.mac and d2.mac = t.switch_mac
    UNION ALL
    SELECT  d1.name as name, d1.type as type, d1.mac as mac,
            d1.ip as ip, d1.reachable as reachable,
            NULL as switch_name, NULL as switch_port
    FROM devices d1, topology t
    WHERE   d1.mac = t.mac and t.switch_mac is null;"""

NODE_LIST_QUERY = """
    SELECT  d.name as name, d.type as type,
            n.image as image,
            d.ip as ip, d.reachable as reachable
    FROM devices d, nodes n
    WHERE   d.mac = n.mac; """

class Topology(object):

    def __init__(self, db):
        self.db = db

    def get_type(self, mac):
        node_type = get_node_type_from_mac_address(mac)
        if node_type != None:
            # this is a node
            return node_type.SHORT_NAME
        elif mac == self.server_mac:
            return 'server'
        else:
            return 'switch'

    def collect_connected_devices(self, host, host_is_a_switch, host_mac):

        # get a SNMP proxy with LLDP feature
        snmp_proxy = snmp.Proxy(host, lldp=True)

        # record neighbors in db and recurse
        for port, neighbor_info in snmp_proxy.lldp.get_neighbors().items():
            ip, mac = neighbor_info['ip'], neighbor_info['mac']
            device_type = self.get_type(mac)
            if host_is_a_switch:
                switch_mac, switch_port = host_mac, port
            else:
                switch_mac, switch_port = None, None
            self.add_device(type=device_type,
                            mac=mac,
                            switch_mac=switch_mac,
                            switch_port=switch_port,
                            ip=ip)
            if device_type == 'switch':
                # recursively discover devices connected to this switch
                self.collect_connected_devices(ip, True, mac)

    def update(self, requester=None):
        # delete some information that will be updated
        self.db.execute('DELETE FROM topology;')
        self.db.execute("""
            UPDATE devices
            SET reachable = 0;""")

        self.server_mac = get_mac_address(const.SERVER_TESTBED_INTERFACE)
        self.collect_connected_devices("localhost", False, self.server_mac)
        self.db.commit()

        if requester != None:
            requester.write_stdout('done.\n')

    def get_device_info(self, requester, device_name, \
                        err_message = DEVICE_NAME_NOT_FOUND):
        device_info = self.db.select_unique("devices", name=device_name)
        if device_info == None and err_message != None:
            requester.write_stderr(err_message % device_name)
        return device_info

    def get_node_info(self, requester, node_name):
        node_info = self.get_device_info(requester, node_name)
        if node_info == None:
            return None # error already reported
        device_type = node_info['type']
        if not is_a_node_type_name(device_type):
            requester.write_stderr('%s is not a node, it is a %s.\n' % \
                                    (node_name, device_type))
            return None
        return node_info

    def get_reachable_node_info(self, requester, node_name, after_rescan = False):
        node_info = self.get_node_info(requester, node_name)
        if node_info == None:
            return None # error already reported
        if node_info['reachable'] == 0:
            if after_rescan:
                requester.write_stderr(
                        'Connot reach %s. The node seems dead or disconnected.\n' % \
                                    node_name)
                return None
            else:
                # rescan, just in case, and retry
                self.update()   # rescan, just in case
                return self.get_reachable_node_info(
                        requester, node_name, after_rescan = True)
        return node_info

    def get_reachable_node_ip(self, requester, node_name):
        node_info = self.get_reachable_node_info(requester, node_name)
        if node_info == None:
            return None # error already reported
        return node_info['ip']

    def get_connectivity_info(self, requester, node_name):
        node_info = self.topology.get_reachable_node_info(requester, node_name)
        if node_info == None:
            return None # error already reported
        node_mac = node_info['mac']
        topology_info = self.db.select_unique("topology", mac=node_mac)
        switch_mac = topology_info['switch_mac']
        switch_port = topology_info['switch_port']
        switch_info = self.db.select_unique("devices", mac=switch_mac)
        return dict(
            switch_ip = switch_info['ip'],
            switch_port = switch_port
        )

    def rename_device(self, requester, old_name, new_name):
        device_info = self.get_device_info(requester, old_name)
        if device_info == None:
            return
        if self.get_device_info(requester, new_name, err_message = None) != None:
            requester.write_stderr("""Failed: a device with name '%s' already exists.\n""" % new_name)
            return
        # all is fine, let's update it
        self.db.update("devices", 'mac', mac = device_info['mac'], name = new_name)
        self.db.commit()

    def generate_device_name(self, **kwargs):
        if kwargs['type'] == 'server':
            return 'walt-server'
        return "%s_%s" %(
            kwargs['type'],
            "".join(kwargs['mac'].split(':')[3:]))

    def add_device(self, **kwargs):
        # if we are there then we can reach this device
        kwargs['reachable'] = 1
        # update device info
        num_rows = self.db.update("devices", 'mac', **kwargs)
        # if no row was updated, this is a new device
        if num_rows == 0:
            # generate a name for this device
            name = self.generate_device_name(**kwargs)
            kwargs['name'] = name
            # insert a new row
            self.db.insert("devices", **kwargs)
            # add node info if relevant
            if is_a_node_type_name(kwargs['type']):
                # unknown nodes boot with the default image
                default_image = walt.server.instance.images.get_default_image()
                self.db.insert("nodes", image=default_image, **kwargs)
        # add topology info
        self.db.insert("topology", **kwargs)

    def printed_as_tree(self):
        t = Tree()
        for device in self.db.execute(TOPOLOGY_QUERY).fetchall():
            name = device['name']
            swport = device['switch_port']
            if swport == None:
                label = name
                # align to 2nd letter of the name
                subtree_offset = 1
            else:
                label = '%d: %s' % (swport, name)
                # align to 2nd letter of the name
                subtree_offset = label.find(' ') + 2
            parent_key = device['switch_name']
            t.add_node( name,   # will be the key in the tree
                        label,
                        subtree_offset=subtree_offset,
                        parent_key = parent_key)
        return t.printed()

    def printed_as_detailed_table(self):
        return self.db.pretty_printed_select(
                    TOPOLOGY_QUERY)

    def list_nodes(self):
        return self.db.pretty_printed_select(
                    NODE_LIST_QUERY)

    def register_node(self, node_ip):
        row = self.db.select_unique("devices", ip=node_ip)
        if row == None or row['reachable'] == 0:
            print 'New node detected.'
            # restart discovery
            self.update()
            # update dhcpd
            walt.server.instance.dhcpd.update()

