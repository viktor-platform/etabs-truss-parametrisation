import json
import viktor as vkt

from io import BytesIO
from pathlib import Path
from textwrap import dedent

from viktor.core import File
from viktor.external.generic import GenericAnalysis

from app.structure import generate_model
from app.optimization import plot_displacement_vs_truss_depth, calculate_variants, generate_variants, mass_co2_from_model
from app.visualization import render_frame_elements, create_load_arrow
from app.visualization import sections_db

SF = 20
COLOR_BY = "component"
COLUMN_HEIGHT = 6000
color_dict = {
    "Truss": vkt.Material(color=vkt.Color(r=255, g=105, b=180)),  # Bright Pastel Pink
    "Column": vkt.Material(color=vkt.Color(r=100, g=200, b=250)),  # Bright Pastel Blue
    "Joist": vkt.Material(color=vkt.Color(r=255, g=220, b=130)),  # Bright Pastel Yellow
}
section_dict = {"Truss": 150, "Column": 300, "Joist": 100}


class Parametrization(vkt.Parametrization):
    step_1 = vkt.Step("Create Model", views=["create_render"])
    step_1.text = vkt.Text(
        dedent(
            """
            # Truss Optimization App

            This app allows you to create parametric models in ETABS to optimize structural parameters, such as truss depth or the number of secondary beams. It also displays the deformation for the optimal model and compares the results between models.
            """
        )
    )
    step_1.title = vkt.Text("## Initial Parameters")
    step_1.x_bay_width = vkt.NumberField("X Bay Width [mm]", min=2000, default=8000)
    step_1.y_bay_width = vkt.NumberField("Y Bay Width [mm]", min=2000, default=14000)
    step_1.n_joist = vkt.NumberField("Number of Joist", min=1.5, default=6)
    step_1.truss_depth = vkt.NumberField("Truss: Depth [mm]", min=300, default=600)
    step_1.joist_n_diags = vkt.NumberField("Joist: Number of Diagonals", min=5, default=8)
    step_1.area_load = vkt.NumberField("Area Load [kN/m2]", min=1.5, max=7, default=5)
    step_1.section = vkt.OptionField("Cross Section", options= list(sections_db.keys()), default =list(sections_db.keys())[0]) 

    step_2 = vkt.Step("Run Analysis", views=["run_model"], width=30)

    step_3 = vkt.Step("Optimize", width=40)
    step_3.txt_tile = vkt.Text("# Optimization Settings")
    step_3.allowable_disp = vkt.NumberField("Allowable Displacement (mm)", default=100)
    step_3.suptitle1 = vkt.Text("## Number Of Joist")
    step_3.min_jst = vkt.NumberField("Min", default=5)
    step_3.max_jst = vkt.NumberField("Max", default=8)
    step_3.delta_jst = vkt.NumberField("Step size", default=1)

    step_3.suptitle2 = vkt.Text("## Truss Depth")
    step_3.min_truss = vkt.NumberField("Min (mm)", default=600)
    step_3.max_truss = vkt.NumberField("Max (mm)", default=1200)
    step_3.delta_truss = vkt.NumberField("Step size (mm)", default=200)

    step_3.suptitle3 = vkt.Text("## Number of Variants")
    step_3.total_variants = vkt.OutputField("Total Number of Variants", value=calculate_variants)
    step_3.lb = vkt.LineBreak()
    step_3.button = vkt.OptimizationButton("Optimize", method="optimal_curve", longpoll=True)


class Controller(vkt.Controller):
    label = "Structure Controller"
    parametrization = Parametrization

    @vkt.GeometryView("3D model", duration_guess=1, x_axis_to_right=True)
    def create_render(self, params, **kwargs) -> vkt.GeometryResult:
        nodes, lines, nodes_with_load, supports, point_load = generate_model(
            params.step_1.truss_depth,
            params.step_1.x_bay_width,
            params.step_1.y_bay_width,
            params.step_1.n_joist + 1,
            COLUMN_HEIGHT,
            params.step_1.joist_n_diags,
            params.step_1.area_load,
        )
        # Render Structure
        selected_section = sections_db[params.step_1.section]["depth"]
        section_dict = {"Truss":selected_section , "Column": 300, "Joist": selected_section}
        sections_group = render_frame_elements(lines, nodes, color_dict, section_dict, COLOR_BY)
        # Render loads
        for node_id in nodes_with_load:
            loads_arrow = create_load_arrow(
                nodes[node_id], magnitude=point_load, material=vkt.Material(color=vkt.Color(r=255, g=10, b=10), opacity=0.8)
            )
            sections_group.append(loads_arrow)

        return vkt.GeometryResult(geometry=sections_group)

    @vkt.GeometryAndDataView("Deformed model", duration_guess=1, x_axis_to_right=True)
    def run_model(self, params, **kwargs) -> vkt.GeometryResult:
        nodes, lines, nodes_with_load, supports, point_load = generate_model(
            params.step_1.truss_depth,
            params.step_1.x_bay_width,
            params.step_1.y_bay_width,
            params.step_1.n_joist + 1,
            COLUMN_HEIGHT,
            params.step_1.joist_n_diags,
            params.step_1.area_load,
        )
        models = []
        models.append(
            {
                "nodes": nodes,
                "lines": lines,
                "nodes_with_load": nodes_with_load,
                "load_magnitud": point_load,
                "supports": supports,
                "section_name": params.step_1.section,
                "section_props": sections_db[params.step_1.section]
            }
        )
        # Run Etabs model with worker
        results_data = self.run_worker(models)
        opt_model = models[0]

        for node_id, _ in opt_model["nodes"].items():
            defo = SF * results_data[0]["deformations"][str(node_id)]
            opt_model["nodes"][node_id]["z"] = opt_model["nodes"][node_id]["z"] + defo

        for line_id, dict_vals in opt_model["lines"].items():
            ni = str(dict_vals["nodeI"])
            nj = str(dict_vals["nodeI"])
            defo_ni = results_data[0]["deformations"][str(ni)]
            defo_nj = results_data[0]["deformations"][str(nj)]
            opt_model["lines"][line_id].update({"deformation": 0.5 * (abs(defo_ni) + abs(defo_nj))})

        max_defo = abs(results_data[0]["max_defo"])
        selected_section = sections_db[params.step_1.section]["depth"]
        section_dict = {"Truss":selected_section , "Column": 300, "Joist": selected_section}
        sections_group = render_frame_elements(
            lines=opt_model["lines"],
            nodes=opt_model["nodes"],
            color_dict=color_dict,
            section_dict=section_dict,
            COLOR_BY=COLOR_BY,
            deformation=True,
            max_defo=max_defo,
        )


        #Data results
        total_mass, element_count, total_co2_emission  = mass_co2_from_model(lines=opt_model["lines"], nodes = opt_model["nodes"], section_name=params.step_1.section, sections_db=sections_db)

        data_result = vkt.DataGroup(
            vkt.DataItem("Output","Model Results", subgroup=vkt.DataGroup(
                    vkt.DataItem("Total mass", total_mass, suffix="kg", number_of_decimals=2),
                    vkt.DataItem("Number of Steel Members", element_count, suffix="-", number_of_decimals=2),
                    vkt.DataItem("Total Co2 Emissions", total_co2_emission, suffix="Co2(kg)", number_of_decimals=2),
                    vkt.DataItem("Max. Displacement", max_defo, suffix="mm", number_of_decimals=3),
                    )
            )
        )

        return vkt.GeometryAndDataResult(sections_group,data_result)

    def optimal_curve(self, params, **kwargs) -> vkt.OptimizationResult:
        variants = generate_variants(params, **kwargs)
        models = []
        co2s = []
        for variant in variants:
            nodes, lines, nodes_with_load, supports, point_load = generate_model(
                variant["truss_depth_value"],
                variant["x_bay_width"],
                variant["y_bay_width"],
                variant["joist_value"],
                COLUMN_HEIGHT,
                variant["joist_n_diags"],
                variant["area_load"],
            )
            models.append(
                {
                "nodes": nodes,
                "lines": lines,
                "nodes_with_load": nodes_with_load,
                "load_magnitud": point_load,
                "supports": supports,
                "section_name": params.step_1.section,
                "section_props": sections_db[params.step_1.section]
            })
            _, _, total_co2_emission  = mass_co2_from_model(lines=lines, nodes = nodes, section_name=params.step_1.section, sections_db=sections_db)
            co2s.append(total_co2_emission)
        # Run multiple models
        results_data = self.run_worker(models=models)
        # Generate optimization result image.
        image_path = plot_displacement_vs_truss_depth(
            model_data=variants, results_data=results_data, allowable_displacement=params.step_3.allowable_disp
        )
        # Generate OptimizationResult: includes images and tables
        results = []
        for model, result,co2 in zip(variants, results_data, co2s,strict=True):
            joist_number = model["joist_value"] - 1
            truss_depth = model["truss_depth_value"]
            max_defo = abs(result["max_defo"])

            params = {"step_1": {"truss_depth": truss_depth, "n_joist": joist_number}}
            results.append(vkt.OptimizationResultElement(params, {"Deformation": round(max_defo, 2),"Emissions (kg Co2)":round(co2,2)}))
        # Pack results
        output_headers = {"Deformation": "Deformation","Emissions (kg Co2)":"Emissions (kg Co2)"}
        return vkt.OptimizationResult(
            results,
            ["step_1.truss_depth", "step_1.n_joist"],
            output_headers=output_headers,
            image=vkt.ImageResult.from_path(image_path),
        )

    def run_worker(self, models: list[dict]) -> list[dict]:
        input_json = json.dumps(models)
        script_path = Path(__file__).parent / "run_etabs_model.py"
        files = [("inputs.json", BytesIO(bytes(input_json, "utf8"))), ("run_etabs_model.py", File.from_path(script_path))]
        generic_analysis = GenericAnalysis(files=files, executable_key="run_etabs", output_filenames=["output.json"])
        generic_analysis.execute(timeout=36000)
        output_file = generic_analysis.get_output_file("output.json", as_file=True)
        results_data = json.loads(output_file.getvalue())
        return results_data
