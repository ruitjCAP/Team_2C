import json
import xml.etree.ElementTree as ET
from pathlib import Path
import pm4py


BPMN_NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"
}


def safe_attr(el, key, default=None):
    return el.attrib.get(key, default)


def parse_bpmn_lanes_and_participants(bpmn_path: str):
    """
    Parse lane/pool-related information directly from BPMN XML.
    This is the reliable way to get lanes from BPMN.
    """
    tree = ET.parse(bpmn_path)
    root = tree.getroot()

    # Processes
    processes = []
    for proc in root.findall("bpmn:process", BPMN_NS):
        processes.append({
            "id": safe_attr(proc, "id"),
            "name": safe_attr(proc, "name", "")
        })

    # Collaboration / participants (pools)
    collaborations = []
    participants = []
    for collab in root.findall("bpmn:collaboration", BPMN_NS):
        collab_id = safe_attr(collab, "id")
        collaborations.append({"id": collab_id})

        for part in collab.findall("bpmn:participant", BPMN_NS):
            participants.append({
                "id": safe_attr(part, "id"),
                "name": safe_attr(part, "name", ""),
                "processRef": safe_attr(part, "processRef"),
                "collaboration_id": collab_id
            })

    # Lanes
    lanes = []
    lane_to_nodes = {}
    node_to_lane = {}

    for proc in root.findall("bpmn:process", BPMN_NS):
        proc_id = safe_attr(proc, "id")

        for lane_set in proc.findall(".//bpmn:laneSet", BPMN_NS):
            lane_set_id = safe_attr(lane_set, "id")

            for lane in lane_set.findall("bpmn:lane", BPMN_NS):
                lane_id = safe_attr(lane, "id")
                lane_name = safe_attr(lane, "name", "")

                flow_node_refs = [
                    (ref.text or "").strip()
                    for ref in lane.findall("bpmn:flowNodeRef", BPMN_NS)
                    if (ref.text or "").strip()
                ]

                lanes.append({
                    "id": lane_id,
                    "name": lane_name,
                    "process_id": proc_id,
                    "lane_set_id": lane_set_id,
                    "flow_node_refs": flow_node_refs
                })

                lane_to_nodes[lane_id] = flow_node_refs

                # if a node appears in nested lanes, keep all assignments
                for node_id in flow_node_refs:
                    node_to_lane.setdefault(node_id, []).append(lane_id)

    return {
        "processes": processes,
        "collaborations": collaborations,
        "participants": participants,
        "lanes": lanes,
        "lane_to_nodes": lane_to_nodes,
        "node_to_lane": node_to_lane
    }


def extract_bpmn_graph_with_pm4py(bpmn_path: str):
    """
    Extract structural BPMN graph info with PM4Py:
    nodes, flows, types, names, connectivity.
    """
    bpmn_graph = pm4py.read_bpmn(bpmn_path)

    nodes = []
    flows = []

    # PM4Py BPMN model exposes nodes and flows
    for n in sorted(list(bpmn_graph.get_nodes()), key=lambda x: x.get_id()):
        node_type = n.__class__.__name__
        in_arcs = getattr(n, "in_arcs", [])
        out_arcs = getattr(n, "out_arcs", [])

        nodes.append({
            "id": n.get_id(),
            "name": n.get_name(),
            "type": node_type,
            "process": n.get_process(),
            "in_degree": len(in_arcs),
            "out_degree": len(out_arcs)
        })

    for f in sorted(list(bpmn_graph.get_flows()), key=lambda x: x.get_id()):
        flow_type = f.__class__.__name__
        flows.append({
            "id": f.get_id(),
            "name": f.get_name(),
            "type": flow_type,
            "source_id": f.get_source().get_id(),
            "target_id": f.get_target().get_id(),
            "process": f.get_process()
        })

    return {
        "bpmn_name": bpmn_graph.get_name(),
        "process_id": bpmn_graph.get_process_id(),
        "nodes": nodes,
        "flows": flows
    }


def export_bpmn_analytics_json(bpmn_path: str, output_json_path: str):
    graph_info = extract_bpmn_graph_with_pm4py(bpmn_path)
    xml_info = parse_bpmn_lanes_and_participants(bpmn_path)

    result = {
        "model_info": {
            "source_bpmn": str(Path(bpmn_path).resolve()),
            "bpmn_name": graph_info["bpmn_name"],
            "main_process_id": graph_info["process_id"],
            "num_nodes": len(graph_info["nodes"]),
            "num_flows": len(graph_info["flows"]),
            "num_participants": len(xml_info["participants"]),
            "num_lanes": len(xml_info["lanes"])
        },
        "nodes": graph_info["nodes"],
        "flows": graph_info["flows"],
        "processes": xml_info["processes"],
        "collaborations": xml_info["collaborations"],
        "participants": xml_info["participants"],
        "lanes": xml_info["lanes"],
        "lane_to_nodes": xml_info["lane_to_nodes"],
        "node_to_lane": xml_info["node_to_lane"]
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result



export_bpmn_analytics_json("AS-ISnew.bpmn", "bpmn_analytics.json")
print("Saved bpmn_analytics.json")
