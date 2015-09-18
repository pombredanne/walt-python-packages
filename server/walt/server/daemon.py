#!/usr/bin/env python

import rpyc, sys
import walt.server as server
from walt.server.network import setup
from walt.server.tools import AutoCleaner
from walt.common.daemon import WalTDaemon
from walt.common.constants import           \
                 WALT_SERVER_DAEMON_PORT,   \
                 WALT_NODE_DAEMON_PORT

WALT_SERVER_DAEMON_VERSION = 0.1

class ClientMirroringService(rpyc.Service):
    services_per_node = {}

    def on_connect(self):
        node_id = id(self._conn.root)
        self._node_id = node_id
        ClientMirroringService.services_per_node[node_id] = self

    def on_disconnect(self):
        del ClientMirroringService.services_per_node[self._node_id]

    def __del__(self):
        self._client = None

    def register_client(self, client):
        self._client = client

    @staticmethod
    def link_node_to_client(node, client):
        service = ClientMirroringService.services_per_node[id(node)]
        service.register_client(client)

    # forward all other method accesses to self._client
    def __getattr__(self, attr_name):
        return getattr(self._client, attr_name)

class ServerToNodeLink:
    def __init__(self, ip_address, client = None):
        self.node_ip = ip_address
        self.client = client

    def __enter__(self):
        if self.client:
            self.conn = rpyc.connect(self.node_ip, WALT_NODE_DAEMON_PORT,
                            service = ClientMirroringService)
            node_service = self.conn.root
            ClientMirroringService.link_node_to_client(node_service, self.client)
        else:
            self.conn = rpyc.connect(self.node_ip, WALT_NODE_DAEMON_PORT)
        return self.conn.root

    def __exit__(self, type, value, traceback):
        self.conn.close()

class PlatformService(rpyc.Service):
    ALIASES=("WalT_Platform",)

    def __init__(self, *args, **kwargs):
        rpyc.Service.__init__(self, *args, **kwargs)
        self.server = server.instance
        self.images = server.instance.images
        self.devices = server.instance.devices
        self.nodes = server.instance.nodes

    def on_connect(self):
        self._client = self._conn.root

    def on_disconnect(self):
        self._client = None

    def exposed_device_rescan(self):
        self.server.device_rescan(self._client)

    def exposed_device_show(self, details=False):
        return self.devices.show(details)

    def exposed_show_nodes(self, show_all):
        return self.nodes.show(self._client, show_all)

    def exposed_get_reachable_node_ip(self, node_name):
        return self.nodes.get_reachable_node_ip(
                        self._client, node_name)

    def exposed_get_device_ip(self, device_name):
        return self.devices.get_device_ip(
                        self._client, device_name)

    def exposed_get_node_ip(self, node_name):
        return self.nodes.get_node_ip(
                        self._client, node_name)

    def exposed_blink(self, node_name, blink_status):
        node_ip = self.nodes.get_reachable_node_ip(
                        self._client, node_name)
        if node_ip == None:
            return False # error was already reported
        with ServerToNodeLink(node_ip, self._client) as node_service:
            node_service.blink(blink_status)
        return True

    def exposed_poweroff(self, node_name):
        return self.nodes.setpower(self._client, node_name, False)

    def exposed_poweron(self, node_name):
        return self.nodes.setpower(self._client, node_name, True)

    def exposed_rename(self, old_name, new_name):
        self.server.rename_device(self._client, old_name, new_name)

    def exposed_has_image(self, image_tag):
        return self.images.has_image(self._client, image_tag)

    def exposed_set_image(self, node_name, image_tag):
        self.server.set_image(self._client, node_name, image_tag)

    def exposed_check_device_exists(self, device_name):
        return self.devices.get_device_info(
                        self._client, device_name) != None

    def exposed_is_disconnected(self, device_name):
        return self.devices.topology.is_disconnected(device_name)

    def exposed_count_logs(self, device_name):
        return self.server.db.count_logs(device_name)

    def exposed_forget(self, device_name):
        self.server.forget_device(device_name)

    def exposed_fix_image_owner(self, other_user):
        return self.images.fix_owner(self._client, other_user)

    def exposed_search_images(self, q, keyword):
        self.images.search(self._client, q, keyword)

    def exposed_clone_image(self, q, clonable_link, force=False):
        self.images.clone(self._client, q, clonable_link, force)

    def exposed_show_images(self):
        return self.images.show(self._client.username)

    def exposed_create_image_shell_session(self, image_tag):
        return self.images.create_shell_session(self._client, image_tag)

    def exposed_remove_image(self, image_tag):
        self.images.remove(self._client, image_tag)

    def exposed_rename_image(self, image_tag, new_tag):
        self.images.rename(self._client, image_tag, new_tag)

    def exposed_copy_image(self, image_tag, new_tag):
        self.images.copy(self._client, image_tag, new_tag)

class WalTServerDaemon(WalTDaemon):
    """WalT (wireless testbed) server daemon."""
    VERSION = WALT_SERVER_DAEMON_VERSION

    def getParameters(self):
        return dict(
                service_cl = PlatformService,
                port = WALT_SERVER_DAEMON_PORT,
                ev_loop = server.instance.ev_loop)

def run():
    if setup.setup_needed():
        setup.setup()
    with AutoCleaner(server.Server) as server.instance:
        server.instance.update()
        WalTServerDaemon.run()

if __name__ == "__main__":
    run()

