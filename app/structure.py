from app.components.components import Truss, Columns, create_joists
from app.components.model import Model
from app.components.clean_model import clean_model, get_nodes_by_z


def generate_model(truss_depth, x_bay_width, y_bay_width, n_diagonals, columns_height, joist_n_diags, area_load):
    truss1 = Truss(
        height=truss_depth,
        width=x_bay_width,
        n_diagonals=n_diagonals,
        xo=0,
        yo=0,
        zo=columns_height,
        plane="xz",
        component_name="Truss",
    )
    truss2 = Truss(
        height=truss_depth,
        width=y_bay_width,
        n_diagonals=joist_n_diags,
        xo=0,
        yo=0,
        zo=columns_height,
        plane="yz",
        component_name="Truss",
    )
    truss3 = Truss(
        height=truss_depth,
        width=y_bay_width,
        n_diagonals=joist_n_diags,
        xo=x_bay_width,
        yo=0,
        zo=columns_height,
        plane="yz",
        component_name="Truss",
    )
    truss4 = Truss(
        height=truss_depth,
        width=x_bay_width,
        n_diagonals=n_diagonals,
        xo=0,
        yo=y_bay_width,
        zo=columns_height,
        plane="xz",
        component_name="Truss",
    )
    column1 = Columns(height=columns_height, xo=0, yo=0, zo=0, nodes_id=1, lines_id=1, component_name="Column")
    column2 = Columns(height=columns_height, xo=x_bay_width, yo=0, zo=0, nodes_id=1, lines_id=1, component_name="Column")
    column3 = Columns(height=columns_height, xo=0, yo=y_bay_width, zo=0, nodes_id=1, lines_id=1, component_name="Column")
    column4 = Columns(
        height=columns_height,
        xo=x_bay_width,
        yo=y_bay_width,
        zo=0,
        nodes_id=1,
        lines_id=1,
        component_name="Column",
    )

    components = [truss1, column1, column2, truss2, truss3, column4, column3, truss4]

    joist_list = create_joists(ref_truss=truss1, height=truss_depth, width=y_bay_width, n_diagonal=joist_n_diags)
    components.extend(joist_list)

    model = Model(components=components)
    model.build()
    # Clean repeated nodes
    nodes, lines = clean_model(Nodes=model.nodes, Lines=model.lines)
    # Nodes with load
    nodes_with_load = get_nodes_by_z(nodes, columns_height)
    # Supports
    supports = get_nodes_by_z(nodes, 0)

    point_load = area_load * 0.001 * (x_bay_width * y_bay_width) / len(nodes_with_load)

    return nodes, lines, nodes_with_load, supports, point_load
