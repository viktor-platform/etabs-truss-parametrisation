from app.components import Truss,Columns,create_joists
from app.model import Model
from app.clean_model import clean_model,get_nodes_by_z
import viktor as vkt
import math

NODE_RADIUS = 40

class Parametrization(vkt.Parametrization):
    ''' This class wraps the parameters of the app'''
    # Structure Params
    text_building = vkt.Text('## Structure Geometry')
    
    x_bay_width = vkt.NumberField('X Bay Width', min=2000, default=8000)
    y_bay_width = vkt.NumberField('Y Bay Width', min=2000, default=10000)
    columns_height = vkt.NumberField('Columns Height', min=3000, default=6000)
    n_diagonals = vkt.NumberField('Number of Joist', min=3, default=8)
    truss_depth = vkt.NumberField('Truss Depth', min=300, default=1000)
    joist_n_diags = vkt.NumberField('Joist Number of Diagonals', min=5, default=14)
    area_load = vkt.NumberField('Area Load [kn/m2]', min=5,max=7, default=5)



class Controller(vkt.Controller):
    ''' This class renders, creates the geometry and the sap2000 model'''
    label = 'Structure Controller'
    parametrization = Parametrization

    def create_load_arrow(self, point_node: dict, magnitude: float, direction: str = "z", material=None) -> vkt.Group:
        """Function to create a load arrow from a selected node"""
        size_arrow = abs(magnitude / 20)
        scale_point = 1.5
        scale_arrow_line = 7

        # Create points for the origin of the arrow point and line, based on the coordinate of the node with the load
        origin_of_arrow_point = vkt.Point(point_node["x"] - size_arrow - NODE_RADIUS, point_node["y"],
                                      point_node["z"])
        origin_of_arrow_line = vkt.Point(origin_of_arrow_point.x - size_arrow, origin_of_arrow_point.y,
                                     origin_of_arrow_point.z)

        # Creating the arrow with Viktor Cone and RectangularExtrusion
        arrow_point = vkt.Cone(size_arrow / scale_point, size_arrow, origin=origin_of_arrow_point,
                           orientation=vkt.Vector(1, 0, 0),
                           material=material)
        arrow_line = vkt.RectangularExtrusion(size_arrow / scale_arrow_line, size_arrow / scale_arrow_line,
                                          vkt.Line(origin_of_arrow_line, origin_of_arrow_point),
                                          material=material)

        arrow = vkt.Group([arrow_point, arrow_line])

        # Rotate the arrow if the direction is not 'x' or if the magnitude is negative
        if direction == "z":
            vector = vkt.Vector(0, 1, 0)
            arrow.rotate(0.5 * math.pi, vector, point=point_node)
        if magnitude < 0:
            arrow.rotate(math.pi, vector, point=point_node)

        return arrow


    @vkt.GeometryView("3D model", duration_guess=1, x_axis_to_right=True)
    def create_render(self, params, **kwargs):
        truss1 = Truss(
            height=params.truss_depth, width=params.x_bay_width, n_diagonals=params.n_diagonals, xo=0, yo=0, zo=params.columns_height, plane="xz",component_name= "Truss"
        )
        truss2 = Truss(
            height=params.truss_depth, width=params.y_bay_width, n_diagonals=params.n_diagonals, xo=0, yo=0, zo=params.columns_height, plane="yz",component_name= "Truss"
        )
        truss3 = Truss(
            height=params.truss_depth, width=params.y_bay_width, n_diagonals=params.n_diagonals, xo=params.x_bay_width, yo=0, zo=params.columns_height, plane="yz",component_name= "Truss"
        )
        truss4 = Truss(
            height=params.truss_depth, width=params.x_bay_width, n_diagonals=params.n_diagonals, xo=0, yo=params.y_bay_width, zo=params.columns_height, plane="xz",component_name= "Truss"
        )
        column1 = Columns(height=params.columns_height, xo=0, yo=0, zo=0, nodes_id=1, lines_id=1,component_name="Column")
        column2 = Columns(height=params.columns_height, xo=params.x_bay_width, yo=0, zo=0, nodes_id=1, lines_id=1,component_name="Column")
        column3 = Columns(height=params.columns_height, xo=0, yo=params.y_bay_width, zo=0, nodes_id=1, lines_id=1,component_name="Column")
        column4 = Columns(height=params.columns_height, xo=params.x_bay_width, yo=params.y_bay_width, zo=0, nodes_id=1, lines_id=1,component_name="Column")

        components = [truss1, column1, column2, truss2, truss3, column4, column3, truss4]

        joist_list = create_joists(ref_truss=truss1 , width=params.y_bay_width,n_diagonal=params.joist_n_diags)
        components.extend(joist_list)

        model = Model(components=components)
        model.build()
        # Clean repeated nodes
        nodes, lines = clean_model(Nodes=model.nodes, Lines=model.lines)
        # Nodes with load
        nodes_with_load = get_nodes_by_z(nodes,params.columns_height)
        point_load = params.area_load*0.001*(params.x_bay_width * params.y_bay_width)/len(nodes_with_load)


        color_dict = {
            "Truss": vkt.Material(color=vkt.Color(r=255, g=105, b=180)),  # Bright Pastel Pink
            "Column": vkt.Material(color=vkt.Color(r=100, g=200, b=250)),  # Bright Pastel Blue
            "Joist": vkt.Material(color=vkt.Color(r=255, g=220, b=130)),  # Bright Pastel Yellow
        }

        section_dict = {
        "Truss":150,
        "Column":500,
        "Joist":100,

        }
        # Render Structure
        sections_group = []
        rendered_sphere = set()
        for line_id, dict_vals in lines.items():

            node_id_i = dict_vals["nodeI"]
            node_id_j = dict_vals["nodeJ"]

            node_i = nodes[node_id_i]
            node_j = nodes[node_id_j]

            point_i = vkt.Point(node_i["x"],
                            node_i["y"],
                            node_i["z"])

            point_j = vkt.Point(node_j["x"],
                            node_j["y"],
                            node_j["z"])
            
            # To Do: This can be simplified 
            if not node_id_i in rendered_sphere:
                sphere_k = vkt.Sphere(point_i, radius=NODE_RADIUS,material=None, identifier= str(node_id_i))
                sections_group.append(sphere_k)
                rendered_sphere.add(node_id_i)

            if not node_id_j in rendered_sphere:
                sphere_k = vkt.Sphere(point_j , radius=NODE_RADIUS, material= None,  identifier= str(node_id_j))
                sections_group.append(sphere_k)
                rendered_sphere.add(node_id_j)

            line_k = vkt.Line(point_i, point_j)
            material = color_dict[dict_vals["component"]]
            sec_size = section_dict[dict_vals["component"]]
            section_k = vkt.RectangularExtrusion(sec_size, sec_size, line_k, identifier=str(line_id), material = color_dict[dict_vals["component"]])
            sections_group.append(section_k)
        
        #Render loads

        return vkt.GeometryResult(geometry=sections_group)
