import json
import xml.etree.ElementTree as ET
from pathlib import Path
import pm4py


BPMN_NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"
}


ACTIVITY_TAGS = {
    "task",
    "userTask",
    "serviceTask",
    "scriptTask",
    "manualTask",
    "businessRuleTask",
    "sendTask",
    "receiveTask",
    "callActivity",
    "subProcess"
}


READ_KEYWORDS = {
    "read", "get", "fetch", "load", "query", "select", "retrieve", "lookup"
}

WRITE_KEYWORDS = {
    "write", "save", "update", "insert", "delete", "store", "persist", "create", "upsert"
}


def safe_attr(el, key, default=None):
    return el.attrib.get(key, default)


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def infer_operation_from_name(name: str):
    """
    Heuristic fallback if BPMN does not explicitly model data associations.
    """
    if not name:
        return []

    lowered = name.lower()
    ops = set()

    for kw in READ_KEYWORDS:
        if kw in lowered:
            ops.add("read")

    for kw in WRITE_KEYWORDS:
        if kw in lowered:
            ops.add("write")

    return sorted(list(ops))


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
                    node_to_lane.setdefault(node_id, []).append(lane_name)

    return {
        "processes": processes,
        "collaborations": collaborations,
        "participants": participants,
        "lanes": lanes,
        "lane_to_nodes": lane_to_nodes,
        "node_to_lane": node_to_lane
    }


def parse_bpmn_database_access(bpmn_path: str):
    """
    Extract database read/write relationships from BPMN XML using:
    - dataStore
    - dataStoreReference
    - dataInputAssociation / dataOutputAssociation
    - optional name-based heuristic fallback
    """
    tree = ET.parse(bpmn_path)
    root = tree.getroot()

    # Global data store definitions
    data_stores = []
    data_store_defs = {}

    for ds in root.findall("bpmn:dataStore", BPMN_NS):
        ds_id = safe_attr(ds, "id")
        ds_name = safe_attr(ds, "name", "")
        item_subject_ref = safe_attr(ds, "itemSubjectRef")

        obj = {
            "id": ds_id,
            "name": ds_name,
            "itemSubjectRef": item_subject_ref
        }
        data_stores.append(obj)
        data_store_defs[ds_id] = obj

    # Data store references inside processes
    data_store_references = []
    data_store_ref_map = {}

    for proc in root.findall("bpmn:process", BPMN_NS):
        proc_id = safe_attr(proc, "id")

        for dsr in proc.findall(".//bpmn:dataStoreReference", BPMN_NS):
            dsr_id = safe_attr(dsr, "id")
            dsr_name = safe_attr(dsr, "name", "")
            ds_ref = safe_attr(dsr, "dataStoreRef")

            obj = {
                "id": dsr_id,
                "name": dsr_name,
                "process_id": proc_id,
                "dataStoreRef": ds_ref,
                "dataStore_name": data_store_defs.get(ds_ref, {}).get("name", "")
            }
            data_store_references.append(obj)
            data_store_ref_map[dsr_id] = obj

    # Parse activity-level DB access
    activity_database_access = []

    for proc in root.findall("bpmn:process", BPMN_NS):
        proc_id = safe_attr(proc, "id")

        for el in proc.iter():
            tag_name = local_name(el.tag)
            if tag_name not in ACTIVITY_TAGS:
                continue

            activity_id = safe_attr(el, "id")
            activity_name = safe_attr(el, "name", "") or ""
            documentation_el = el.find("bpmn:documentation", BPMN_NS)
            documentation = (documentation_el.text or "").strip() if documentation_el is not None and documentation_el.text else ""

            reads = []
            writes = []

            # READS: activity consumes data from a data store reference
            for dia in el.findall("bpmn:dataInputAssociation", BPMN_NS):
                source_refs = [
                    (src.text or "").strip()
                    for src in dia.findall("bpmn:sourceRef", BPMN_NS)
                    if (src.text or "").strip()
                ]

                for src_id in source_refs:
                    if src_id in data_store_ref_map:
                        ref_obj = data_store_ref_map[src_id]
                        reads.append({
                            "operation": "read",
                            "data_store_reference_id": ref_obj["id"],
                            "data_store_reference_name": ref_obj["name"],
                            "data_store_id": ref_obj["dataStoreRef"],
                            "data_store_name": ref_obj["dataStore_name"],
                            "detection": "dataInputAssociation"
                        })

            # WRITES: activity outputs data to a data store reference
            for doa in el.findall("bpmn:dataOutputAssociation", BPMN_NS):
                target_ref_el = doa.find("bpmn:targetRef", BPMN_NS)
                if target_ref_el is not None and (target_ref_el.text or "").strip():
                    target_ref = (target_ref_el.text or "").strip()
                    if target_ref in data_store_ref_map:
                        ref_obj = data_store_ref_map[target_ref]
                        writes.append({
                            "operation": "write",
                            "data_store_reference_id": ref_obj["id"],
                            "data_store_reference_name": ref_obj["name"],
                            "data_store_id": ref_obj["dataStoreRef"],
                            "data_store_name": ref_obj["dataStore_name"],
                            "detection": "dataOutputAssociation"
                        })

            # Heuristic fallback from activity name / documentation
            inferred_ops = infer_operation_from_name(activity_name)
            if not inferred_ops and documentation:
                inferred_ops = infer_operation_from_name(documentation)

            heuristic_ops = []
            if inferred_ops and not reads and not writes:
                for op in inferred_ops:
                    heuristic_ops.append({
                        "operation": op,
                        "data_store_reference_id": None,
                        "data_store_reference_name": None,
                        "data_store_id": None,
                        "data_store_name": None,
                        "detection": "name_heuristic"
                    })

            entry = {
                "activity_id": activity_id,
                "activity_name": activity_name,
                "activity_type": tag_name,
                "process_id": proc_id,
                "documentation": documentation,
                "reads": reads,
                "writes": writes,
                "heuristic_operations": heuristic_ops
            }

            if reads or writes or heuristic_ops:
                activity_database_access.append(entry)

    return {
        "data_stores": data_stores,
        "data_store_references": data_store_references,
        "activity_database_access": activity_database_access
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
    db_info = parse_bpmn_database_access(bpmn_path)

    # attach DB access directly to nodes
    db_access_by_activity = {
        item["activity_id"]: item
        for item in db_info["activity_database_access"]
    }

    enriched_nodes = []
    for node in graph_info["nodes"]:
        new_node = dict(node)
        new_node["database_access"] = db_access_by_activity.get(node["id"], None)
        enriched_nodes.append(new_node)

    result = {
        "nodes": enriched_nodes,
        "flows": graph_info["flows"],
        "processes": xml_info["processes"],
        "collaborations": xml_info["collaborations"],
        "participants": xml_info["participants"],
        "lanes": xml_info["lanes"],
        "lane_to_nodes": xml_info["lane_to_nodes"],
        "node_to_lane": xml_info["node_to_lane"],
        "data_stores": db_info["data_stores"],
        "data_store_references": db_info["data_store_references"],
        "activity_database_access": db_info["activity_database_access"]
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result

if __name__ == "__main__":
    export_bpmn_analytics_json("violates.bpmn", "bpmn_analytics_dataStore.json")
    print("Saved bpmn_analytics.json")
