import comtypes.client
import pythoncom
import json
from pathlib import Path
import json

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

    with open("inputs.json","w") as jsonfile:
        data = {"nodes":nodes,
                "lines":lines,
                "nodes_with_load":[3,4,7,8],
                "load_magnitud": 1000}
        json.dump(data, jsonfile) 

    return nodes, lines

def start_etabs():
    program_path = r"C:\Program Files\Computers and Structures\ETABS 22\ETABS.exe"
    pythoncom.CoInitialize()
    helper = comtypes.client.CreateObject("ETABSv1.Helper")
    helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
    EtabsEngine = helper.CreateObject(program_path)
    EtabsEngine.ApplicationStart()
    EtabsObject = EtabsEngine.SapModel
    EtabsObject.InitializeNewModel(9)
    EtabsObject.File.NewBlank()
    return EtabsObject,EtabsEngine

def create_etabs_model(EtabsObject, data:dict):
    nodes = data['nodes']
    lines = data['lines']
    nodes_with_load = data['nodes_with_load']

    for id, node in nodes.items():
        ret, _ = EtabsObject.PointObj.AddCartesian(
            node["x"], node["y"], node["z"], " ", str(id)
        )

    sections = {
        "SHS60X3": {
            "depth": 50.0,
            "thickness": 6.0
        },
        "EA70x6": {
            "depth": 70.0,
            "thickness": 6.0
        }
    }

    material_name = "S355"
    MATERIAL_STEEL = 1
    EtabsObject.SetPresentUnits(9)
    ret = EtabsObject.PropMaterial.SetMaterial(material_name, MATERIAL_STEEL)
    ret = EtabsObject.PropMaterial.SetMPIsotropic(material_name, 210000, 0.3, 1.2e-5)

    ret = EtabsObject.PropFrame.SetTube_1(
        "SHS60X3",
        material_name,
        60,
        60,
        3,
        3,
        3,
    )

    for id, line in lines.items():
        point_i = line["nodeI"]
        point_j = line["nodeJ"]
        section_name = "SHS60X3"
        ret, _ = EtabsObject.FrameObj.AddByPoint(
            str(point_i), str(point_j), str(id), section_name, "Global"
        )

    load_pattern_name = 'MyLoadPattern'
    ret = EtabsObject.LoadPatterns.Add(load_pattern_name, 8, 0)
    EtabsObject.SetPresentUnits(9)

    load_magnitude = data["load_magnitud"]
    for node_id in nodes_with_load:
        node_name = str(node_id)
        load_values = [0, 0, -load_magnitude, 0, 0, 0]
        ret = EtabsObject.PointObj.SetLoadForce(
            node_name,
            load_pattern_name,
            load_values,
            True,
            'Global'
        )

    supports = data["supports"]
    for node_id in supports:
        ret = EtabsObject.PointObj.SetRestraint(str(node_id), [1, 1, 1, 1, 1, 1])
    
    EtabsObject.View.RefreshView(0,False)
    file_path = Path.cwd() / "etabsmodel.edb"
    EtabsObject.File.Save(str(file_path))
    EtabsObject.Analyze.RunAnalysis()
    ret = EtabsObject.Analyze.RunAnalysis()

    ret = EtabsObject.Results.Setup.DeselectAllCasesAndCombosForOutput()
    ret = EtabsObject.Results.Setup.SetCaseSelectedForOutput(load_pattern_name)
    deformations = {}
    for node_id in nodes_with_load:
        node_name = str(node_id)
        number_results, obj, elm, load_case, step_type, step_num, u1, u2, u3, r1, r2, r3,ret  = EtabsObject.Results.JointDispl(
                    Name = node_name,
                    ItemTypeElm = 0,
                )
        deformations[node_name] = u3[0]
    
    return deformations

def run_n_times(n=2):
    result_list = []

    input_json = Path.cwd() / "inputs.json"
    with open(input_json) as jsonfile:
        data = json.load(jsonfile)

    EtabsObject,EtabsEngine = start_etabs()
    for _ in range(n):
        results = create_etabs_model(EtabsObject,data)
        result_list.append(results)
        EtabsObject.InitializeNewModel(9)
        EtabsObject.File.NewBlank()

    output = Path.cwd() / "output.json"
    with open(output, "w") as jsonfile:
        json.dump(result_list, jsonfile)

    ret = EtabsEngine.ApplicationExit(False)



    # ret = EtabsEngine.ApplicationExit(False)

    # return ret

if __name__ == "__main__":
    input_json = Path.cwd() / "inputs.json"
    with open(input_json) as jsonfile:
        data = json.load(jsonfile)

    EtabsObject,EtabsEngine = start_etabs()
    results = create_etabs_model(EtabsObject,data)




