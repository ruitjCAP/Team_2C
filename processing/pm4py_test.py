import json
from collections import deque
from pathlib import Path
import pm4py


def safe_call(obj, method_name, default=None):
    """Call obj.method_name() if it exists, otherwise return default."""
    if hasattr(obj, method_name):
        try:
            return getattr(obj, method_name)()
        except Exception:
            return default
    return default


def safe_attr(obj, attr_name, default=None):
    """Return obj.attr_name if it exists, otherwise default."""
    if hasattr(obj, attr_name):
        try:
            return getattr(obj, attr_name)
        except Exception:
            return default
    return default


def get_obj_id(obj):
    return (
        safe_call(obj, "get_id")
        or safe_attr(obj, "id")
        or None
    )


def get_obj_name(obj):
    return (
        safe_call(obj, "get_name")
        or safe_attr(obj, "name")
        or None
    )


def get_obj_process(obj):
    return (
        safe_call(obj, "get_process")
        or safe_attr(obj, "process")
        or None
    )


def get_in_arcs(node):
    return (
        safe_call(node, "get_in_arcs")
        or safe_attr(node, "in_arcs")
        or []
    )


def get_out_arcs(node):
    return (
        safe_call(node, "get_out_arcs")
        or safe_attr(node, "out_arcs")
        or []
    )


def get_flow_source(flow):
    return (
        safe_call(flow, "get_source")
        or safe_attr(flow, "source")
        or None
    )


def get_flow_target(flow):
    return (
        safe_call(flow, "get_target")
        or safe_attr(flow, "target")
        or None
    )


def extract_bpmn_objects_general(bpmn_graph):
    """
    Extract all BPMN nodes and flows in a generic way.
    This is more general than extracting only data store references.
    """
    nodes = list(bpmn_graph.get_nodes())
    flows = list(bpmn_graph.get_flows())

    nodes_json = []
    for node in sorted(nodes, key=lambda n: ((get_obj_name(n) or ""), (get_obj_id(n) or ""))):
        node_id = get_obj_id(node)
        node_type = node.__class__.__name__

        in_arcs = get_in_arcs(node)
        out_arcs = get_out_arcs(node)

        nodes_json.append({
            "id": node_id,
            "name": get_obj_name(node),
            "type": node_type,
            "process": str(get_obj_process(node)) if get_obj_process(node) is not None else None,
            "incoming_flow_ids": [
                get_obj_id(a) for a in in_arcs if get_obj_id(a) is not None
            ],
            "outgoing_flow_ids": [
                get_obj_id(a) for a in out_arcs if get_obj_id(a) is not None
            ],
            "num_incoming_flows": len(in_arcs),
            "num_outgoing_flows": len(out_arcs),
        })

    flows_json = []
    for flow in sorted(flows, key=lambda f: ((get_obj_name(f) or ""), (get_obj_id(f) or ""))):
        src = get_flow_source(flow)
        tgt = get_flow_target(flow)

        flows_json.append({
            "id": get_obj_id(flow),
            "name": get_obj_name(flow),
            "type": flow.__class__.__name__,
            "process": str(get_obj_process(flow)) if get_obj_process(flow) is not None else None,
            "source_id": get_obj_id(src) if src is not None else None,
            "source_name": get_obj_name(src) if src is not None else None,
            "source_type": src.__class__.__name__ if src is not None else None,
            "target_id": get_obj_id(tgt) if tgt is not None else None,
            "target_name": get_obj_name(tgt) if tgt is not None else None,
            "target_type": tgt.__class__.__name__ if tgt is not None else None,
        })

    return {
        "num_nodes": len(nodes_json),
        "num_flows": len(flows_json),
        "nodes": nodes_json,
        "flows": flows_json,
    }

bpmn_graph = pm4py.read_bpmn("AS-ISnew.bpmn")
net, initial_marking, final_marking = pm4py.convert_to_petri_net(bpmn_graph)

bpmn_objects = extract_bpmn_objects_general(bpmn_graph)
output_json_path="export_model.json"
with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(bpmn_objects, f, indent=2, ensure_ascii=False)
