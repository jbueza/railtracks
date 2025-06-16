from collections import namedtuple

from requestcompletion.state.node import NodeForest
from requestcompletion.state.request import RequestForest, RequestTemplate

from typing import List, Tuple

NodeRequestForestTuple = namedtuple("NodeRequestForestTuple", ["node_forest", "request_forest"])


def create_sub_state_info(
    node_forest: NodeForest,
    request_forest: RequestForest,
    parent_ids: str | List[str],
) -> Tuple[NodeForest, RequestForest]:
    valid_requests = {}
    node_ids = []
    for parent_id in (
            parent_ids if isinstance(parent_ids, list) else [parent_ids]
    ):
        source_id = request_forest[parent_id].sink_id
        requests_to_add = RequestTemplate.all_downstream(request_forest.heap().values(), source_id) + [request_forest[parent_id]]
        for r in requests_to_add:
            assert r.identifier not in valid_requests, "There should not be any duplicate entries"
            assert r.sink_id not in node_ids, "There should not be any duplicate node IDs"
            valid_requests[r.identifier] = r
            node_ids.append(r.sink_id)


    r_f = RequestForest(
        request_heap=valid_requests
    )

    n_f = NodeForest(
        node_heap={nid: node_forest[nid] for nid in node_ids if nid in node_forest.heap()}
    )


    return NodeRequestForestTuple(
        node_forest=n_f,
        request_forest=r_f
    )

