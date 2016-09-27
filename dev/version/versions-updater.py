#!/usr/bin/env python
import sys, os, subprocess, hashlib
sys.path.append(os.getcwd())
from dev.api.source import SourceImporter
from dev.tools.pretty import pprint_dict

versions_file_template = """\
# auto-generated by dev/version/versions-updater.py

# We handle compatibility between WalT components (Server, client,
# nodes) by using the concept of API (Application Programming
# Interface) version.
# We consider the following 2 API sets:
# * CS = CLIENT-SERVER
# * NS = NODE-SERVER
# An API set between 2 components is the set of functions prototypes
# each of these 2 components exposes to the other. If any of these
# prototypes is modified, we consider the API between these 2
# components has changed, thus the compatibility is broken with
# previous versions of these components.
# For example, a node with NS api version 3 is not compatible
# with an older server which complies with NS api version 2.
# Important note:
# Let's consider that the prototype of the method allowing to make a node
# blink changes. This implies that the server side code, which calls
# this method, also changes, even if the API did not change on the
# server side. This new server will not work correctly with older nodes
# implementing the previous prototype. This example shows that it is
# important to propagate the break in compatibility on both sides of
# the API set.

API_VERSIONING = %(api_versioning)s

UPLOAD = %(upload)s
"""

if len(sys.argv) != 2:
    print 'Usage: %(prog)s <upload_num>' % dict(prog = sys.argv[0])
    sys.exit()

new_upload = int(sys.argv[1])

# instanciate our source import system and activate it.
importer = SourceImporter({ 'walt.common': './common/walt/common' })
importer.activate()
from walt.common.versions import API_VERSIONING as CUR_API_VERSIONING, \
                                 UPLOAD as CUR_UPLOAD
# retrieve API hash using dev/api/explorer.py
# for each API (CS, NS), compare
# with what we had before and increment the api version
# if it changed.
API_LOCATIONS = {
    'CSAPI': [ 'walt.server.threads.main.api.cs', 'walt.client.client' ],
    'NSAPI': [ 'walt.server.threads.main.api.ns', 'walt.node.daemon' ]
}

new_api_versioning = CUR_API_VERSIONING.copy() # for now
if new_upload != CUR_UPLOAD + 1:
    sys.stderr.write('Warning: the current UPLOAD number should have been %d, it was %d. Overwriting anyway.\n' % \
                        (new_upload - 1, CUR_UPLOAD))

for component, module_paths in API_LOCATIONS.items():
    new_api_proto = ''
    for module_path in module_paths:
        new_api_proto += subprocess.check_output(
            [ 'dev/api/explorer.py', module_path ])
    new_api_hash = hashlib.sha224(new_api_proto).hexdigest()
    cur_api_num, cur_api_hash = CUR_API_VERSIONING[component]
    if cur_api_hash != new_api_hash:
        # API of this component as changed, increment api_num
        # and update hash for next time.
        new_api_versioning[component] = (cur_api_num+1, new_api_hash)

new_versions_file = versions_file_template % dict(
    api_versioning = pprint_dict(new_api_versioning),
    upload = new_upload
)

# write updated info in walt/common/versions.py
with open("common/walt/common/versions.py", "w") as f:
    f.write(new_versions_file)

