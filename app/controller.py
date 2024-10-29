import json
import viktor as vkt
import math
from pathlib import Path
from .structure import generate_model

NODE_RADIUS = 40


def export2json(nodes, lines, nodes_with_load, point_load, supports):
    input_json = Path.cwd() / "app" / "inputs.json"
    with open(input_json, "w") as jsonfile:
        data = {
            "nodes": nodes,
            "lines": lines,
            "nodes_with_load": nodes_with_load,
            "load_magnitud": point_load,
            "supports": supports,
        }
        json.dump(data, jsonfile)


class Parametrization(vkt.Parametrization):
    """This class wraps the parameters of the app"""

    # Structure Params
    step_1 = vkt.Step("Create Model", views=["create_render"])

    step_1.x_bay_width = vkt.NumberField("X Bay Width", min=2000, default=8000)
    step_1.y_bay_width = vkt.NumberField("Y Bay Width", min=2000, default=15000)
    step_1.columns_height = vkt.NumberField("Columns Height", min=3000, default=6000)
    step_1.n_joist = vkt.NumberField("Number of Joist", min=3, default=3)
    step_1.truss_depth = vkt.NumberField("Truss Depth", min=300, default=1000)
    step_1.joist_n_diags = vkt.NumberField("Joist Number of Diagonals", min=5, default=8)
    step_1.area_load = vkt.NumberField("Area Load [kn/m2]", min=5, max=7, default=5)

    step_1.text_settings = vkt.Text("## Optimization settings")
    step_1.option = vkt.OptionField("Select Feature", options=["Joist Number", "Truss Depth"], default="Joist Number")
    step_1.n_iteration = vkt.NumberField("Number of Iterations]", min=1, max=5, default=3)
    # step_1.button = vkt.ActionButton("Optimize!", method="optimize")

    step_2 = vkt.Step("Run Analysis", views=["optimize"], width=30)
    step_2.text = vkt.Text("""
## Run the analysis and view the results
To view the deformed building, click on 'Run analysis' in the bottom right 🔄. You can scale the deformation with the 
'Deformation scale factor' below.
    """)
    # step_2.deformation_scale = vkt.NumberField("Deformation scale factor", min=0, max=1e7, default=1000, num_decimals=2)


class Controller(vkt.Controller):
    label = "Structure Controller"
    parametrization = Parametrization

    def create_load_arrow(self, point_node: dict, magnitude: float, direction: str = "z", material=None) -> vkt.Group:
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

    def render_frame_elements(self, lines: dict, nodes: dict, color_dict: dict, section_dict: dict, COLOR_BY: str) -> list:
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
            section_k = vkt.RectangularExtrusion(sec_size, sec_size, line_k, identifier=str(line_id), material=material)
            sections_group.append(section_k)

        return sections_group

    @vkt.GeometryView("3D model", duration_guess=1, x_axis_to_right=True)
    def create_render(self, params, **kwargs):
        nodes, lines, nodes_with_load, supports, point_load = generate_model(
            params.step_1.truss_depth,
            params.step_1.x_bay_width,
            params.step_1.y_bay_width,
            params.step_1.n_joist + 1,
            params.step_1.columns_height,
            params.step_1.joist_n_diags,
            params.step_1.area_load,
        )
        export2json(nodes, lines, nodes_with_load, point_load, supports)
        color_dict = {
            "Truss": vkt.Material(color=vkt.Color(r=255, g=105, b=180)),  # Bright Pastel Pink
            "Column": vkt.Material(color=vkt.Color(r=100, g=200, b=250)),  # Bright Pastel Blue
            "Joist": vkt.Material(color=vkt.Color(r=255, g=220, b=130)),  # Bright Pastel Yellow
        }
        section_dict = {"Truss": 150, "Column": 500, "Joist": 100}
        # Render Structure
        COLOR_BY = "component"
        sections_group = self.render_frame_elements(lines, nodes, color_dict, section_dict, COLOR_BY)

        # Render loads
        load_list = []
        for node_id in nodes_with_load:
            loads_arrow = self.create_load_arrow(
                nodes[node_id], magnitude=point_load, material=vkt.Material(color=vkt.Color(r=255, g=10, b=10), opacity=0.8)
            )
            sections_group.append(loads_arrow)

        return vkt.GeometryResult(geometry=sections_group)

    @vkt.GeometryView("Deformed model", duration_guess=1, x_axis_to_right=True)
    def optimize(self, params, **kwargs):
        if params.step_1.option == "Joist Number":
            n_iterations = params.step_1.n_iteration
            base = params.step_1.n_joist + 1
            delta = 1
            ranges = [0, -1, 1, 2, -2, 3, -3, 4 - 4, 5, -5, 6, -6]
            models = []
            values = []
            for i in ranges[:n_iterations]:
                value = base + i * delta
                if value >= 2 and value not in values:
                    values.append(value)
                    nodes, lines, nodes_with_load, supports, point_load = generate_model(
                        params.step_1.truss_depth,
                        params.step_1.x_bay_width,
                        params.step_1.y_bay_width,
                        value,
                        params.step_1.columns_height,
                        params.step_1.joist_n_diags,
                        params.step_1.area_load,
                    )

                    models.append(
                        {
                            "nodes": nodes,
                            "lines": lines,
                            "nodes_with_load": nodes_with_load,
                            "load_magnitud": point_load,
                            "supports": supports,
                        }
                    )

            input_json = Path.cwd() / "app" / "inputs.json"
            with open(input_json, "w") as jsonfile:
                json.dump(models, jsonfile)

            output_json = Path.cwd() / "app" / "output copy 2.json"
            with open(output_json) as jsonfile:
                data = json.load(jsonfile)

            min_index, min_value = min(enumerate(data), key=lambda x: x[1]["max_defo"][0])

            opt_model = models[min_index]

            sf = 10

            color_dict = {
                "Truss": vkt.Material(color=vkt.Color(r=255, g=105, b=180)),   # Bright Pastel Pink
                "Column": vkt.Material(color=vkt.Color(r=100, g=200, b=250)),  # Bright Pastel Blue
                "Joist": vkt.Material(color=vkt.Color(r=255, g=220, b=130)),   # Bright Pastel Yellow
            }
            for node_id, node_vals in opt_model["nodes"].items():
                defo = sf * data[min_index]["deformations"][str(node_id)]
                opt_model["nodes"][node_id]["z"] = opt_model["nodes"][node_id]["z"] + defo

            COLOR_BY = "component"

            section_dict = {"Truss": 150, "Column": 500, "Joist": 100}

            sections_group = self.render_frame_elements(
                lines=opt_model["lines"], nodes=opt_model["nodes"], color_dict=color_dict, section_dict=section_dict, COLOR_BY=COLOR_BY
            )

        return vkt.GeometryResult(geometry=sections_group)
