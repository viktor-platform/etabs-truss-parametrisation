from app.components.components import Truss, Columns, create_joists
from app.components.model import Model
from app.components.clean_model import clean_model, get_nodes_by_z
from tests.utils import plot_3d_structure

# Create Truss and Columns
x_bay_width = 8000
y_bay_width = 15000
columns_height = 6000
n_diagonals = 7
truss_depth = 600
joist_n_diags = 8

truss1 = Truss(height=truss_depth, width=x_bay_width, n_diagonals=n_diagonals, xo=0, yo=0, zo=columns_height, plane="xz")
truss2 = Truss(height=truss_depth, width=y_bay_width, n_diagonals=n_diagonals, xo=0, yo=0, zo=columns_height, plane="yz")
truss3 = Truss(height=truss_depth, width=y_bay_width, n_diagonals=n_diagonals, xo=x_bay_width, yo=0, zo=columns_height, plane="yz")
truss4 = Truss(height=truss_depth, width=x_bay_width, n_diagonals=n_diagonals, xo=0, yo=y_bay_width, zo=columns_height, plane="xz")
column1 = Columns(height=columns_height, xo=0, yo=0, zo=0, nodes_id=1, lines_id=1)
column2 = Columns(height=columns_height, xo=x_bay_width, yo=0, zo=0, nodes_id=1, lines_id=1)
column3 = Columns(height=columns_height, xo=0, yo=y_bay_width, zo=0, nodes_id=1, lines_id=1)
column4 = Columns(height=columns_height, xo=x_bay_width, yo=y_bay_width, zo=0, nodes_id=1, lines_id=1)

components = [truss1, column1, column2, truss2, truss3, column4, column3, truss4]

joist_list = create_joists(ref_truss=truss1, height=truss_depth, width=y_bay_width, n_diagonal=joist_n_diags)
components.extend(joist_list)

model = Model(components=components)
model.build()
# Clean repeated nodes
nodes, lines = clean_model(Nodes=model.nodes, Lines=model.lines)
nodes_with_load = get_nodes_by_z(nodes, columns_height)
print(f"{nodes_with_load=},Number_of_nodes = {len(nodes_with_load)}")
plot_3d_structure(nodes, lines)
