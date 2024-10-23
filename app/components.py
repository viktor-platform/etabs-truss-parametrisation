from pydantic import BaseModel, Field
from typing import Literal


class Node(BaseModel):
    id: int | None
    x: float
    y: float
    z: float


class NodeList(BaseModel):
    node_list: list[Node] = Field(default=[])

    def add_node(self, new_node: Node) -> None:
        self.node_list.append(new_node)

    def add_node_list(self, new_node_list: list[Node]) -> None:
        self.node_list.extend(new_node_list)

    def serialize(self) -> dict:
        return {node.id: node.model_dump() for node in self.node_list if node.id is not None}


class Line(BaseModel):
    id: int
    nodeI: int
    nodeJ: int
    component: str | None = Field(default= None)


class LineList(BaseModel):
    line_list: list[Line] = Field(default=[])

    def add_lines(self, new_line: Line) -> None:
        self.line_list.append(new_line)

    def add_line_list(self, new_line_list: list[Line]) -> None:
        self.line_list.extend(new_line_list)

    def serialize(self) -> dict:
        return {line.id: line.model_dump() for line in self.line_list}


Plane = Literal["xz", "yz"]


class Truss:
    def __init__(
        self,
        height: float,
        width: float,
        n_diagonals: int,
        xo: float,
        yo: float,
        zo: float,
        plane: Plane,
        lines_id: int = 0,
        nodes_id: int = 0,
        component_name: str | None = None
    ) -> None:
        self.height = height
        self.width = width
        self.n_diagonals = n_diagonals

        self.xo = xo
        self.yo = yo
        self.zo = zo

        self.plane = plane

        self.nodes = NodeList()
        self.lines = LineList()

        self.lines_id = lines_id
        self.nodes_id = nodes_id

        self.joist_nodes = []
        self.component_name = component_name

    def set_nodes_id(self, node_id: int):
        self.nodes_id = node_id

    def set_lines_id(self, lines_id: int):
        self.lines_id = lines_id

    def gen_node_tag(self) -> int:
        self.nodes_id = self.nodes_id + 1
        return self.nodes_id

    def gen_line_tag(self) -> int:
        self.lines_id = self.lines_id + 1
        return self.lines_id

    def get_line_id(self) -> int:
        return self.lines_id

    def get_nodes_id(self) -> int:
        return self.nodes_id

    def get_joist_node_tag(self) -> list[int]:
        return self.joist_nodes

    def create_chord_nodes(self, width: int, xo: float, yo: float, zo: float, plane: Plane) -> NodeList:
        nNodes = self.n_diagonals + 1
        delta = width / (nNodes - 1)

        if plane == "xz":
            chord_nodes = [Node(id=self.gen_node_tag(), x=xo + dx * delta, y=yo, z=zo) for dx in range(nNodes)]
            self.nodes.add_node_list(new_node_list=chord_nodes)

        if plane == "yz":
            chord_nodes = [Node(id=self.gen_node_tag(), x=xo, y=yo + dx * delta, z=zo) for dx in range(nNodes)]
            self.nodes.add_node_list(new_node_list=chord_nodes)

        return chord_nodes

    def connect_chord_lines(self, chord_nodes: list[Node]) -> list[Line]:
        line_list = [
            Line(
                id=self.gen_line_tag(),
                nodeI=chord_nodes[i].id,
                nodeJ=chord_nodes[i + 1].id,
                component = self.component_name
            )
            for i in range(len(chord_nodes) - 1)
        ]
        self.lines.add_line_list(line_list)
        return line_list

    def create_diagonals(self, top_chord_ids: list[int], bottom_chord_ids: list[int]) -> None:
        if self.n_diagonals % 2 == 0:
            # Shortest way to get the right nodes
            required_st1_ids = top_chord_ids[::2]
            required_st2_ids = bottom_chord_ids[1:-1:2]

            tags_st1 = sorted([required_st1_ids[0]] + [required_st1_ids[-1]] + required_st1_ids[1:-1] * 2)
            tags_st2 = sorted(required_st2_ids[:] * 2)

            for tag_st1, tag_st2 in zip(tags_st1, tags_st2):
                self.lines.add_lines(Line(id=self.gen_line_tag(), nodeI=tag_st1, nodeJ=tag_st2,component=self.component_name))
        else:
            # Shortest way to get the right nodes
            required_st1_ids = top_chord_ids[:-1:2]
            required_st2_ids = bottom_chord_ids[1::2]

            tags_st1 = sorted([required_st1_ids[0]] + required_st1_ids[1:] * 2)
            tags_st2 = sorted([required_st2_ids[-1]] + required_st2_ids[:-1] * 2)

            for tag_st1, tag_st2 in zip(tags_st1, tags_st2):
                self.lines.add_lines(Line(id=self.gen_line_tag(), nodeI=tag_st1, nodeJ=tag_st2,component=self.component_name))

    def create(self) -> tuple[dict[int, Node], dict[int, Line]]:
        bottom_chord_nodes = self.create_chord_nodes(
            width=self.width, xo=self.xo, yo=self.yo, zo=self.zo - self.height, plane=self.plane
        )

        self.connect_chord_lines(chord_nodes=bottom_chord_nodes)

        top_chord_nodes = self.create_chord_nodes(
            width=self.width,
            xo=self.xo,
            yo=self.yo,
            zo=self.zo,
            plane=self.plane,
        )

        self.connect_chord_lines(chord_nodes=top_chord_nodes)

        top_chord_tags = [node.id for node in top_chord_nodes]
        bottom_chord_tags = [node.id for node in bottom_chord_nodes]

        self.joist_nodes = top_chord_tags[1:-1:1]

        self.create_diagonals(top_chord_ids=top_chord_tags, bottom_chord_ids=bottom_chord_tags)

        return self.nodes.serialize(), self.lines.serialize()


class Columns:
    def __init__(
        self,
        height: float,
        xo: float,
        yo: float,
        zo: float = 0,
        nodes_id: int = 0,
        lines_id: int = 0,
        partition: int = 2,
        component_name: str | None = None
    ) -> None:
        self.xo = xo
        self.yo = yo
        self.zo = zo
        self.partition = partition
        self.height = height
        self.nodes = NodeList()
        self.lines = LineList()

        self.lines_id = lines_id
        self.nodes_id = nodes_id

        self.component_name = component_name

    def set_nodes_id(self, node_id: int):
        self.nodes_id = node_id

    def set_lines_id(self, lines_id: int):
        self.lines_id = lines_id

    def gen_node_tag(self) -> int:
        self.nodes_id = self.nodes_id + 1
        return self.nodes_id

    def gen_line_tag(self) -> int:
        self.lines_id = self.lines_id + 1
        return self.lines_id

    def get_line_id(self) -> int:
        return self.lines_id

    def get_nodes_id(self) -> int:
        return self.nodes_id

    def create(self) -> tuple[dict[int, Node], dict[int, Line]]:
        xo = self.xo
        yo = self.yo
        zo = self.zo
        delta = self.height / self.partition

        column_nodes = [Node(id=self.gen_node_tag(), x=xo, y=yo, z=zo + dz * delta) for dz in range(self.partition + 1)]
        self.nodes.add_node_list(new_node_list=column_nodes)

        line_list = [
            Line(
                id=self.gen_line_tag(),
                nodeI=column_nodes[i].id,
                nodeJ=column_nodes[i + 1].id,
                component=self.component_name
            )
            for i in range(len(column_nodes) - 1)
        ]
        self.lines.add_line_list(line_list)

        return self.nodes.serialize(), self.lines.serialize()


def create_joists(ref_truss: Truss, width: float, n_diagonal: int) -> list[Truss]:
    """Crates joist based on reference truss"""
    joist_list = []
    nodes, lines = ref_truss.create()
    joist_nodes_tags = ref_truss.get_joist_node_tag()
    for joint_tag in joist_nodes_tags:
        node = nodes[joint_tag]
        temp_truss = Truss(
            height=1000, width=width, n_diagonals=n_diagonal, xo=node["x"], yo=node["y"], zo=node["z"], plane="yz",component_name= "Joist"
        )
        joist_list.append(temp_truss)
    return joist_list
