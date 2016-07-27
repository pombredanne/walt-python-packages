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

API_VERSIONING = dict(
    CS = (1, 'bf3a1927c6395ecfb3b075422c391592851e16b44a3a217ad09a3958'),
    NS = (1, 'a9c1c7616dcdaee964da8084a639a7a99b7efa3595d36346333319b7')
)

UPLOAD = 13
