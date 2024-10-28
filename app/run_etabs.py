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
        json.dump([nodes, lines], jsonfile) 

    return nodes, lines


def create_etabs_model():
    program_path = r"C:\Program Files\Computers and Structures\ETABS 22\ETABS.exe"
    pythoncom.CoInitialize()
    helper = comtypes.client.CreateObject("ETABSv1.Helper")
    helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
    EtabsEngine = helper.CreateObject(program_path)
    EtabsEngine.ApplicationStart()
    EtabsObject = EtabsEngine.SapModel
    EtabsObject.InitializeNewModel(9)
    EtabsObject.File.NewBlank()

    input_json = Path.cwd() / "inputs.json"
    with open(input_json) as jsonfile:
        data = json.load(jsonfile)
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
    for section_name, section_props in sections.items():
        ret = EtabsObject.PropFrame.SetTube(
            Name=section_name,
            MatProp=material_name,
            T3=section_props["depth"],
            T2=section_props["depth"],
            Tf=section_props["thickness"],
            Tw=section_props["thickness"]
        )

    for id, line in lines.items():
        point_i = line["node_i"]
        point_j = line["node_j"]
        section_name = line["section"]
        ret, _ = EtabsObject.FrameObj.AddByPoint(
            str(point_i), str(point_j), str(id), section_name, "Global"
        )

    load_pattern_name = 'MyLoadPattern'
    ret = EtabsObject.LoadPatterns.Add(load_pattern_name, 8, 0)
    EtabsObject.SetPresentUnits(9)

    load_magnitude = 1000
    for node_id in nodes_with_load:
        node_name = str(node_id)
        load_values = [0, 0, -load_magnitude, 0, 0, 0]
        ret = EtabsObject.PointObj.SetLoadForce(
            Name=node_name,
            MyName=load_pattern_name,
            Value=load_values,
            Replace=True,
            CSys='Global'
        )

    ret = EtabsObject.Analyze.RunAnalysis()

    ret = EtabsObject.Results.Setup.DeselectAllCasesAndCombosForOutput()
    ret = EtabsObject.Results.Setup.SetCaseSelectedForOutput(load_pattern_name)
    deformations = {}
    for node_id in nodes_with_load:
        node_name = str(node_id)
        ret, number_results, obj, elm, load_case, step_type, step_num, u1, u2, u3, r1, r2, r3 = EtabsObject.Results.JointDispl(
            PointName=node_name,
            ItemType=2
        )
        if number_results > 0:
            deformations[node_name] = u3[0]
        else:
            deformations[node_name] = None

    output = Path.cwd() / "output.json"
    with open(output, "w") as jsonfile:
        json.dump(deformations, jsonfile)

    # ret = EtabsEngine.ApplicationExit(False)
    pythoncom.CoUninitialize()  # Ensure cleanup is performed

    return ret

if __name__ == "__main__":
    create_frame_data(2000, 2000)
    create_etabs_model()


