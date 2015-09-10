#!/usr/bin/env python

import uuid
from walt.common.evloop import EventLoop
from walt.common.tcp import TCPServer
from walt.common.constants import WALT_SERVER_TCP_PORT
from walt.server.images.store import NodeImageStore
from walt.server.platform import Platform
from walt.server.db import ServerDB
from walt.server.logs import LogsManager
from walt.server.network.dhcpd import DHCPServer
from walt.server.interactive import InteractionManager
from walt.server.blocking import BlockingTasksManager

class Server(object):

    def __init__(self):
        self.ev_loop = EventLoop()
        self.db = ServerDB()
        self.blocking = BlockingTasksManager()
        self.platform = Platform(self.db)
        self.images = NodeImageStore(self.db, self.blocking)
        self.dhcpd = DHCPServer(self.db)
        self.tcp_server = TCPServer(WALT_SERVER_TCP_PORT)
        self.logs = LogsManager(self.db, self.tcp_server)
        self.interaction = InteractionManager(\
                        self.tcp_server, self.ev_loop)
        self.tcp_server.join_event_loop(self.ev_loop)
        self.blocking.join_event_loop(self.ev_loop)
        self.db.plan_auto_commit(self.ev_loop)

    def update(self):
        # ensure the dhcp server is running,
        # otherwise the switches may have ip addresses
        # outside the WalT network, and we will not be able
        # to communicate with them when trying to update
        # the topology.
        self.dhcpd.update(force=True)
        # topology exploration
        self.platform.topology.update()
        # update dhcp again for any new device
        self.dhcpd.update()
        # mount images needed
        self.images.update_image_mounts()

    def cleanup(self):
        self.images.cleanup()
        self.blocking.cleanup()

    def set_image(self, requester, node_name, image_tag):
        node_info = self.platform.topology.get_node_info(
                        requester, node_name)
        if node_info == None:
            return # error already reported
        mac = node_info.mac
        self.images.set_image(requester, mac, image_tag)
        self.dhcpd.update()

    def set_default_image(self, requester, image_tag):
        self.images.set_default(requester, image_tag)
        self.dhcpd.update()

    def register_node(self, node_ip):
        self.platform.register_node(node_ip)
        self.dhcpd.update()

    def rename_device(self, requester, old_name, new_name):
        self.platform.rename_device(requester, old_name, new_name)
        self.dhcpd.update()

    def platform_update(self, requester):
        self.platform.update(requester)
        self.dhcpd.update()

    def forget_device(self, device_name):
        self.db.forget_device(device_name)
        self.dhcpd.update()

