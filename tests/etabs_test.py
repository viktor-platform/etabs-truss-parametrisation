import comtypes.client
import pythoncom
import json
from pathlib import Path
import json
from app.run_etabs import create_etabs_model, start_etabs

def create_frame_data(length, height):
    nodes = {
        1:{"node_id": 1, "x": 0, "y": 0, "z": 0},
        2:{"node_id": 2, "x": 0, "y": length, "z": 0},
        3:{"node_id": 3, "x": 0, "y": 0, "z": height},
        4:{"node_id": 4, "x": 0, "y": length, "z": height},
        5:{"node_id": 5, "x": length, "y": 0, "z": 0},
        6:{"node_id": 6, "x": length, "y": length, "z": 0},
        7:{"node_id": 7, "x": length, "y": 0, "z": height},
        8:{"node_id": 8, "x": length, "y": length, "z": height},
    }
    lines = {
        1:{"line_id": 1, "node_i": 1, "node_j": 3},
        2:{"line_id": 2, "node_i": 2, "node_j": 4},
        3:{"line_id": 3, "node_i": 3, "node_j": 4},
        4:{"line_id": 4, "node_i": 6, "node_j": 8},
        5:{"line_id": 5, "node_i": 5, "node_j": 7},
        6:{"line_id": 6, "node_i": 3, "node_j": 7},
        7:{"line_id": 7, "node_i": 4, "node_j": 8},
        8:{"line_id": 8, "node_i": 7, "node_j": 8},
    }

    input_json = Path.cwd() / "inputs.json"
    with open(input_json,"w") as jsonfile:
        data = {"nodes":nodes,
                "lines":lines,
                "nodes_with_load":[3,4,7,8],
                "load_magnitud": 1000}
        json.dump(data, jsonfile) 

    return nodes, lines


def test_etabs_model():
    create_frame_data()
    
    input_json = Path.cwd() / "inputs.json"
    with open(input_json) as jsonfile:
        data = json.load(jsonfile)

    EtabsObject, EtabsEngine =  start_etabs()
    deformations = create_etabs_model(EtabsObject=EtabsObject,data=data)
    isinstance(deformations,dict)

