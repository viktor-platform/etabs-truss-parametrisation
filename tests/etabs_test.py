import json
from pathlib import Path
import json
from app.run_etabs_model import create_etabs_model, start_etabs


def create_frame_data(length, height):
    nodes = {
        1: {"id": 1, "x": 0, "y": 0, "z": 0},
        2: {"id": 2, "x": 0, "y": length, "z": 0},
        3: {"id": 3, "x": 0, "y": 0, "z": height},
        4: {"id": 4, "x": 0, "y": length, "z": height},
        5: {"id": 5, "x": length, "y": 0, "z": 0},
        6: {"id": 6, "x": length, "y": length, "z": 0},
        7: {"id": 7, "x": length, "y": 0, "z": height},
        8: {"id": 8, "x": length, "y": length, "z": height},
    }
    lines = {
        1: {"id": 1, "nodeI": 1, "nodeJ": 3},
        2: {"id": 2, "nodeI": 2, "nodeJ": 4},
        3: {"id": 3, "nodeI": 3, "nodeJ": 4},
        4: {"id": 4, "nodeI": 6, "nodeJ": 8},
        5: {"id": 5, "nodeI": 5, "nodeJ": 7},
        6: {"id": 6, "nodeI": 3, "nodeJ": 7},
        7: {"id": 7, "nodeI": 4, "nodeJ": 8},
        8: {"id": 8, "nodeI": 7, "nodeJ": 8},
    }

    input_json = Path.cwd() / "inputs.json"
    with open(input_json, "w") as jsonfile:
        data = {"nodes": nodes, "lines": lines, "supports": [1,2,5,6], "load_magnitud": 1000,"section_name":"SHS65X3","section_props":{"depth": 60.0, "thickness": 3.0, "weight/m":5.66}, "nodes_with_load": [7,8,4,5]}
        json.dump(data, jsonfile)

    return nodes, lines

def test_etabs_model():
    # Generates a json inputs.json
    create_frame_data(length=1000,height=1000)

    input_json = Path.cwd() / "inputs.json"
    with open(input_json) as jsonfile:
        data = json.load(jsonfile)

    EtabsObject, EtabsEngine = start_etabs()
    deformations = create_etabs_model(EtabsObject=EtabsObject, data=data)
    isinstance(deformations, dict)


if __name__ == "__main__":
    test_etabs_model()
