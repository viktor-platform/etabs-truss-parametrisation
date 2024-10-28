from app.components import Truss,Columns,create_joists
from app.model import Model
from app.clean_model import clean_model
import viktor as vkt

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


class Controller(vkt.Controller):
    ''' This class renders, creates the geometry and the sap2000 model'''
    label = 'Structure Controller'
    parametrization = Parametrization

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
                sphere_k = vkt.Sphere(point_i, radius=40,material=None, identifier= str(node_id_i))
                sections_group.append(sphere_k)
                rendered_sphere.add(node_id_i)

            if not node_id_j in rendered_sphere:
                sphere_k = vkt.Sphere(point_j , radius=40, material= None,  identifier= str(node_id_j))
                sections_group.append(sphere_k)
                rendered_sphere.add(node_id_j)

            line_k = vkt.Line(point_i, point_j)
            material = color_dict[dict_vals["component"]]
            sec_size = section_dict[dict_vals["component"]]
            section_k = vkt.RectangularExtrusion(sec_size, sec_size, line_k, identifier=str(line_id), material = color_dict[dict_vals["component"]])
            sections_group.append(section_k)

        return vkt.GeometryResult(geometry=sections_group)
