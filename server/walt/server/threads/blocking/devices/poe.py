from walt.server.tools import to_named_tuple

def nodes_set_poe(server, nodes, poe_status):
    # nodes were transformed to dict to be pickle-able
    nodes = [to_named_tuple(n) for n in nodes]
    # update poe on relevant switch ports
    return server.topology.nodes_set_poe(nodes, poe_status)
