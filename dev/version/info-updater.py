#!/usr/bin/env python
import sys, os
from collections import OrderedDict
sys.path.append(os.getcwd())
from dev.api.source import SourceImporter
from dev.tools.pretty import pprint_dict
from dev.metadata import PACKAGE_GENERIC_INFO, PACKAGE_SPECIFIC_INFO

info_file_template = """\
# auto-generated by dev/version/info-updater.py
# using metadata from dev/metadata.py

SETUP_INFO = %(setup_info)s
"""

# instanciate our source import system and activate it.
importer = SourceImporter({ 'walt.common': './common/walt/common' })
importer.activate()
from walt.common.versions import API_VERSIONING, UPLOAD

# generate info.py in each pypi package directory
versions_info = dict(
    upload = UPLOAD,
    cs_api = API_VERSIONING['CS'][0],
    ns_api = API_VERSIONING['NS'][0]
)

for package_name, package_specific in PACKAGE_SPECIFIC_INFO.items():
    setup_info = OrderedDict()
    setup_info.update(name = package_name)
    version = package_specific['version_str'] % versions_info
    setup_info.update(version = version)
    install_requires = [ requirement % versions_info \
        for requirement in package_specific['requires'] ]
    setup_info.update(install_requires = install_requires)
    setup_info.update(sorted(PACKAGE_GENERIC_INFO.items()))
    setup_info.update(sorted(package_specific['setup'].items()))
    new_info_file = info_file_template % dict(
        setup_info = pprint_dict(setup_info)
    )
    with open("%(subdir)s/walt/%(subdir)s/info.py" % package_specific, 'w') as f:
        f.write(new_info_file)
