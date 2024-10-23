from app.components import Truss,Columns,create_joists
from app.model import Model
from app.clean_model import clean_model

# Create Truss and Columns
x_bay_width = 10000
y_bay_width = 10000
columns_height = 6000
n_diagonals = 8
truss_depth = 500
joist_n_diags = 2 * n_diagonals

truss1 = Truss(
    height=truss_depth, width=x_bay_width, n_diagonals=n_diagonals, xo=0, yo=0, zo=columns_height, plane="xz",component_name= "Truss"
)
truss2 = Truss(
    height=truss_depth, width=y_bay_width, n_diagonals=n_diagonals, xo=0, yo=0, zo=columns_height, plane="yz",component_name= "Truss"
)
truss3 = Truss(
    height=truss_depth, width=y_bay_width, n_diagonals=n_diagonals, xo=x_bay_width, yo=0, zo=columns_height, plane="yz",component_name= "Truss"
)
truss4 = Truss(
    height=truss_depth, width=x_bay_width, n_diagonals=n_diagonals, xo=0, yo=y_bay_width, zo=columns_height, plane="xz",component_name= "Truss"
)
column1 = Columns(height=columns_height, xo=0, yo=0, zo=0, nodes_id=1, lines_id=1,component_name="Column")
column2 = Columns(height=columns_height, xo=x_bay_width, yo=0, zo=0, nodes_id=1, lines_id=1,component_name="Column")
column3 = Columns(height=columns_height, xo=0, yo=y_bay_width, zo=0, nodes_id=1, lines_id=1,component_name="Column")
column4 = Columns(height=columns_height, xo=x_bay_width, yo=y_bay_width, zo=0, nodes_id=1, lines_id=1,component_name="Column")

components = [truss1, column1, column2, truss2, truss3, column4, column3, truss4]

joist_list = create_joists(ref_truss=truss1 , width=y_bay_width,n_diagonal=joist_n_diags)
components.extend(joist_list)

model = Model(components=components)
model.build()
# Clean repeated nodes
nodes, lines = clean_model(Nodes=model.nodes, Lines=model.lines)

print(lines)