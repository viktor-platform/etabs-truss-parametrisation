import matplotlib.pyplot as plt


def plot_3d_structure(nodes: dict, lines: dict) -> None:
    """
    Plots a 3D structure of nodes and lines.

    Args:
        nodes (dict): A dictionary of node objects with keys as node IDs and values as dicts with 'x', 'y', 'z' coordinates.
        lines (dict): A dictionary of line objects with keys as line IDs and values as dicts with 'nodeI' and 'nodeJ' referring to node IDs.
    """
    # Create a 3D plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    # Plot the nodes
    for node in nodes.values():
        ax.scatter(node["x"], node["y"], node["z"], color="blue")
        ax.text(node["x"], node["y"], node["z"], f"{node['id']}", color="red")

    # Plot the lines between the nodes
    for line in lines.values():
        nodeI = nodes[line["nodeI"]]
        nodeJ = nodes[line["nodeJ"]]
        ax.plot([nodeI["x"], nodeJ["x"]], [nodeI["y"], nodeJ["y"]], [nodeI["z"], nodeJ["z"]], color="black")

    # Set labels
    ax.set_xlabel("X axis")
    ax.set_ylabel("Y axis")
    ax.set_zlabel("Z axis")

    # Show the plot
    plt.show()
