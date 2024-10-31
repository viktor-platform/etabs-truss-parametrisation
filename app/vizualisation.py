import math
import numpy as np
import viktor as vkt
import matplotlib.pyplot as plt

from matplotlib.colors import ListedColormap

NODE_RADIUS = 40


def create_load_arrow(point_node: dict, magnitude: float, direction: str = "z", material=None) -> vkt.Group:
    """Function to create a load arrow from a selected node"""
    size_arrow = abs(magnitude / 20)
    scale_point = 1.5
    scale_arrow_line = 7
    # Create points for the origin of the arrow point and line, based on the coordinate of the node with the load
    origin_of_arrow_point = vkt.Point(point_node["x"] - size_arrow - NODE_RADIUS, point_node["y"], point_node["z"])
    origin_of_arrow_line = vkt.Point(origin_of_arrow_point.x - size_arrow, origin_of_arrow_point.y, origin_of_arrow_point.z)

    # Creating the arrow with Viktor Cone and RectangularExtrusion
    arrow_point = vkt.Cone(
        size_arrow / scale_point, size_arrow, origin=origin_of_arrow_point, orientation=vkt.Vector(1, 0, 0), material=material
    )
    arrow_line = vkt.RectangularExtrusion(
        size_arrow / scale_arrow_line,
        size_arrow / scale_arrow_line,
        vkt.Line(origin_of_arrow_line, origin_of_arrow_point),
        material=material,
    )
    arrow = vkt.Group([arrow_point, arrow_line])
    # Rotate the arrow if the direction is not 'x' or if the magnitude is negative
    if direction == "z":
        vector = vkt.Vector(0, 1, 0)
        arrow.rotate(0.5 * math.pi, vector, point=vkt.Point(x=point_node["x"], y=point_node["y"], z=point_node["z"]))
    if magnitude < 0:
        arrow.rotate(math.pi, vector, point=vkt.Point(x=point_node["x"], y=point_node["y"], z=point_node["z"]))

    return arrow


def render_frame_elements(
    lines: dict,
    nodes: dict,
    color_dict: dict,
    section_dict: dict,
    COLOR_BY: str,
    deformation: bool = False,
    max_defo: float | None = None,
) -> list:
    sections_group = []
    rendered_sphere = set()
    for line_id, dict_vals in lines.items():
        node_id_i = dict_vals["nodeI"]
        node_id_j = dict_vals["nodeJ"]

        node_i = nodes[node_id_i]
        node_j = nodes[node_id_j]

        point_i = vkt.Point(node_i["x"], node_i["y"], node_i["z"])
        point_j = vkt.Point(node_j["x"], node_j["y"], node_j["z"])

        # To Do: This can be simplified
        if not node_id_i in rendered_sphere:
            sphere_k = vkt.Sphere(point_i, radius=NODE_RADIUS, material=None, identifier=str(node_id_i))
            sections_group.append(sphere_k)
            rendered_sphere.add(node_id_i)

        if not node_id_j in rendered_sphere:
            sphere_k = vkt.Sphere(point_j, radius=NODE_RADIUS, material=None, identifier=str(node_id_j))
            sections_group.append(sphere_k)
            rendered_sphere.add(node_id_j)

        line_k = vkt.Line(point_i, point_j)
        material = color_dict[dict_vals[COLOR_BY]]
        sec_size = section_dict[dict_vals[COLOR_BY]]
        if deformation:
            def_val = dict_vals["deformation"]
            r, g, b = get_color_from_displacement(def_val, max_defo)
            material = vkt.Material(color=vkt.Color(r=r, g=g, b=b))
        section_k = vkt.RectangularExtrusion(sec_size, sec_size, line_k, identifier=str(line_id), material=material)
        sections_group.append(section_k)

    return sections_group


def get_color_from_displacement(displacement: float, max_displacement: float, partitions: int = 30):
    # Normalize the displacement value
    normalized_displacement = displacement / max_displacement if max_displacement != 0 else 0
    # Generate a colormap with the specified number of partitions
    base_cmap = plt.get_cmap("jet")
    discrete_cmap = ListedColormap(base_cmap(np.linspace(0, 1, partitions)))
    # Get the RGB color from the discrete colormap
    rgb_color = discrete_cmap(normalized_displacement)[:3]  # Exclude alpha channel
    return tuple(int(x * 255) for x in rgb_color)
