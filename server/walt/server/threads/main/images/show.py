from walt.server.tools import columnate

MSG_WS_IS_EMPTY="""\
Your working set is empty.
Use 'walt image search [<keyword>]' to search for images
you could build upon.
Then use 'walt image clone <clonable_link>' to clone them
into your working set.
"""

def show(images, username):
    tabular_data = []
    for image in images.itervalues():
        if image.user != username:
            continue
        created_at = image.get_created_at()
        tabular_data.append([
                    image.name,
                    str(image.mounted),
                    created_at if created_at else 'N/A',
                    str(image.ready) ])
    if len(tabular_data) > 0:
        header = [ 'Name', 'Mounted', 'Created', 'Ready' ]
        return columnate(tabular_data, header)
    else:
        return MSG_WS_IS_EMPTY
