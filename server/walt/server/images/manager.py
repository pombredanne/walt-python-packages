from docker import Client
from walt.server.images.shell import ImageShellSessionStore
from walt.server.images.search import search
from walt.server.images.clone import clone
from walt.server.images.show import show
from walt.server.images.rename import rename
from walt.server.images.remove import remove
from walt.server.images.copy import copy
from walt.server.images.fixowner import fix_owner
from walt.server.images.store import NodeImageStore

# About terminology: See comment about it in image.py.

class NodeImageManager(object):
    def __init__(self, db, blocking_manager, dhcpd, docker):
        self.db = db
        self.blocking = blocking_manager
        self.dhcpd = dhcpd
        self.docker = docker
        self.store = NodeImageStore(self.docker, self.db)
        self.shells = ImageShellSessionStore(self.docker, self.store)
    def update(self):
        self.store.refresh()
        self.store.update_image_mounts()
    def search(self, requester, q, keyword):
        search(q, self.blocking, self.docker, requester, keyword)
    def clone(self, requester, q, clonable_link, force):
        clone(q, self.blocking, self.docker, requester, clonable_link, self.store, force)
    def show(self, username):
        return show(self.store, username)
    def rename(self, requester, image_tag, new_tag):
        rename(self.store, self.docker, requester, image_tag, new_tag)
    def remove(self, requester, image_tag):
        remove(self.store, self.docker, requester, image_tag)
    def copy(self, requester, image_tag, new_tag):
        copy(self.store, self.docker, requester, image_tag, new_tag)
    def fix_owner(self, requester, other_user):
        fix_owner(self.store, self.docker, requester, other_user)
    def cleanup(self):
        # give up image shell sessions
        self.shells.cleanup()
        # un-mount images
        self.store.cleanup()
    def has_image(self, requester, image_tag):
        return self.store.get_user_image_from_tag(requester, image_tag) != None
    def set_image(self, requester, node_mac, image_tag):
        image = self.store.get_user_image_from_tag(requester, image_tag)
        if image:
            self.db.update('nodes', 'mac',
                    mac=node_mac,
                    image=image.fullname)
            self.store.update_image_mounts()
            self.db.commit()
            self.dhcpd.update()
    def create_shell_session(self, requester, image_tag):
        return self.shells.create_session(requester, image_tag)
