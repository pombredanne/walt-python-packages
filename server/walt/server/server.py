#!/usr/bin/env python

import uuid
from walt.common.evloop import EventLoop
from walt.common.tcp import TCPServer
from walt.common.constants import WALT_SERVER_TCP_PORT
from walt.server.images.manager import NodeImageManager
from walt.server.devices.manager import DevicesManager
from walt.server.db import ServerDB
from walt.server.logs import LogsManager
from walt.server.network.dhcpd import DHCPServer
from walt.server.interactive import InteractionManager
from walt.server.blocking import BlockingTasksManager
from walt.server.nodes.manager import NodesManager
from walt.server.mydocker import DockerClient
from walt.server.tools import format_sentence_about_nodes

class Server(object):

    def __init__(self):
        self.ev_loop = EventLoop()
        self.db = ServerDB()
        self.docker = DockerClient()
        self.blocking = BlockingTasksManager()
        self.devices = DevicesManager(self.db)
        self.dhcpd = DHCPServer(self.db)
        self.images = NodeImageManager(self.db, self.blocking, self.dhcpd, self.docker)
        self.tcp_server = TCPServer(WALT_SERVER_TCP_PORT)
        self.logs = LogsManager(self.db, self.tcp_server, self.blocking)
        self.interaction = InteractionManager(\
                        self.tcp_server, self.ev_loop)
        self.nodes = NodesManager(  db = self.db,
                                    tcp_server = self.tcp_server,
                                    blocking = self.blocking,
                                    images = self.images.store,
                                    dhcpd = self.dhcpd,
                                    docker = self.docker,
                                    devices = self.devices)
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
        self.devices.rescan()
        # re-update dhcp with any new device discovered
        self.dhcpd.update()
        # mount images needed
        self.images.update()

    def cleanup(self):
        self.images.cleanup()
        self.blocking.cleanup()

    def set_image(self, requester, node_set, image_tag, warn_unreachable):
        nodes = self.nodes.parse_node_set(requester, node_set)
        if nodes == None:
            return # error already reported
        nodes_ok, nodes_ko = self.nodes.filter_on_connectivity( \
                            requester, nodes, warn_unreachable)
        macs = [ n.mac for n in nodes_ok ]
        if self.images.set_image(requester, macs, image_tag):
            requester.stdout.write(format_sentence_about_nodes(
                '%s will now boot ' + image_tag + '.' ,
                [n.name for n in nodes_ok]) + '\n')

    def rename_device(self, requester, old_name, new_name):
        self.devices.rename(requester, old_name, new_name)
        self.dhcpd.update()

    def device_rescan(self, requester):
        self.devices.rescan(requester)
        self.dhcpd.update()

    def forget_device(self, device_name):
        self.db.forget_device(device_name)
        self.dhcpd.update()

