class Model:
    def __init__(self, components: list) -> None:
        """
        Initialize the model with a list of components (Truss or Columns).
        """
        self.nodes = {}
        self.lines = {}
        self.components = components
        self.nodes_id = 0
        self.lines_id = 0

    def update_nodes_and_lines(self, _nodes: dict, _lines: dict) -> None:
        """
        Merge new nodes and lines (which are dictionaries of dictionaries) into the existing ones.
        """
        self.nodes.update(_nodes)
        self.lines.update(_lines)

    def build(self) -> None:
        """
        Iterate through all the components (Truss, Columns) and execute their create method.
        """
        for component in self.components:
            component.set_nodes_id(self.nodes_id)
            component.set_lines_id(self.lines_id)
            _nodes, _lines = component.create()
            self.update_nodes_and_lines(_nodes, _lines)
            self.lines_id = component.get_line_id()
            self.nodes_id = component.get_nodes_id()
