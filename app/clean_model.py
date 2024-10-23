from collections import defaultdict


def clean_model(Nodes: dict, Lines: dict) -> tuple[dict, dict]:
    """Deletes duplicated nodes"""
    # Create a mapping from coordinates to node IDs
    coord_to_nodes = defaultdict(list)
    for node_id, attrs in Nodes.items():
        coord = (attrs["x"], attrs["y"], attrs["z"])
        coord_to_nodes[coord].append(node_id)

    # Identify duplicates: coordinates with more than one node ID
    duplicates = {coord: ids for coord, ids in coord_to_nodes.items() if len(ids) > 1}

    node_replacements = {}
    for coord, ids in duplicates.items():
        kept_node = min(ids)  # Choose the node with the smallest ID to keep
        for duplicate_node in ids:
            if duplicate_node != kept_node:
                node_replacements[duplicate_node] = kept_node

    # Update Lines to replace deleted Nodes with Kept Nodes
    for line in Lines.values():
        if line["nodeI"] in node_replacements:
            line["nodeI"] = node_replacements[line["nodeI"]]
        if line["nodeJ"] in node_replacements:
            line["nodeJ"] = node_replacements[line["nodeJ"]]

    # Remove duplicate Nodes
    for dup_node in node_replacements.keys():
        del Nodes[dup_node]

    return Nodes, Lines
