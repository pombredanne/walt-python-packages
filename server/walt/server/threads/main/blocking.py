from walt.common.thread import RPCThreadConnector
from walt.common.apilink import AttrCallRunner, AttrCallAggregator

class BlockingTasksManager(RPCThreadConnector):
    def session(self, requester):
        # we will receive:
        # service.<func>(rpc_context, <args...>)
        # and we must forward the call as:
        # requester.<func>(<args...>)
        # the following code handles this forwarding
        # and removal of the 'rpc_context' parameter.
        runner = AttrCallRunner(requester)
        def forward_to_requester(attr, args, kwargs):
            return runner.do(attr, args[1:], kwargs)
        service = AttrCallAggregator(forward_to_requester)
        return self.local_service(service)

    def clone_image(self, requester, result_cb, *args, **kwargs):
        self.session(requester).async.clone_image(*args, **kwargs).then(result_cb)

    def search_image(self, requester, result_cb, *args, **kwargs):
        self.session(requester).async.search_image(*args, **kwargs).then(result_cb)

    def publish_image(self, requester, result_cb, *args, **kwargs):
        self.session(requester).async.publish_image(*args, **kwargs).then(result_cb)


