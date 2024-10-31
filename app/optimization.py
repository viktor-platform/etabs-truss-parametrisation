import plotly.graph_objects as go
from plotly.colors import sequential
from pathlib import Path


def calculate_variants(params, **kwargs):
    # Calculate the number of variants for JST
    variants_jst = (params.step_3.max_jst - params.step_3.min_jst) // params.step_3.delta_jst + 1
    # Calculate the number of variants for Truss
    variants_truss = (params.step_3.max_truss - params.step_3.min_truss) // params.step_3.delta_truss + 1
    # Total number of variants
    total_variants = variants_jst * variants_truss
    return total_variants


def generate_variants(params, **kwargs):
    # Generate ranges for joist and truss parameters
    joist_values = list(
        range(int(params.step_3.min_jst), int(params.step_3.max_jst) + int(params.step_3.delta_jst), int(params.step_3.delta_jst))
    )

    truss_values = list(
        range(
            int(params.step_3.min_truss), int(params.step_3.max_truss) + int(params.step_3.delta_truss), int(params.step_3.delta_truss)
        )
    )

    # Generate all combinations of joist and truss values
    variants = []
    for joist_value in joist_values:
        for truss_depth_value in truss_values:
            variant_params = {
                "truss_depth_value": truss_depth_value,
                "joist_value": joist_value + 1,
                "x_bay_width": params.step_1.x_bay_width,
                "y_bay_width": params.step_1.y_bay_width,
                "columns_height": params.step_1.columns_height,
                "joist_n_diags": params.step_1.joist_n_diags,
                "area_load": params.step_1.area_load,
            }
            variants.append(variant_params)

    return variants


def plot_displacement_vs_truss_depth(model_data, results_data, allowable_displacement):
    # Organize data by joist_number
    data_by_joist = {}
    for model, result in zip(model_data, results_data, strict=True):
        joist_number = model["joist_value"] - 1  # Adjust joist_value to joist_number
        truss_depth = model["truss_depth_value"]
        max_defo = abs(result["max_defo"])  # Use absolute value

        if joist_number not in data_by_joist:
            data_by_joist[joist_number] = {"truss_depth": [], "displacement": []}
        data_by_joist[joist_number]["truss_depth"].append(truss_depth)
        data_by_joist[joist_number]["displacement"].append(max_defo)

    # Get shades of blue for each joist_number
    num_joists = len(data_by_joist)
    blues_scale = sequential.Blues[2:]  # Exclude the lightest shades for better distinction

    # Ensure we have enough colors
    if num_joists > len(blues_scale):
        # If there are more joist_numbers than colors in the scale, interpolate colors
        from plotly.colors import sample_colorscale

        blues_scale = [sample_colorscale("Blues", i / (num_joists - 1)) for i in range(num_joists)]
    else:
        blues_scale = blues_scale[-num_joists:]  # Take the darkest 'num_joists' shades

    line_colors = {}
    for idx, joist_number in enumerate(sorted(data_by_joist.keys())):
        line_colors[joist_number] = blues_scale[idx]

    # Initialize figure
    fig = go.Figure()

    # Collect all truss_depths for min_x and max_x
    all_truss_depths = []
    for data in data_by_joist.values():
        all_truss_depths.extend(data["truss_depth"])
    min_x = min(all_truss_depths)
    max_x = max(all_truss_depths)

    # Add traces for each joist_number
    for joist_number in sorted(data_by_joist.keys()):
        truss_depths = data_by_joist[joist_number]["truss_depth"]
        displacements = data_by_joist[joist_number]["displacement"]
        # Sort the data by truss_depths to make the lines look smooth
        sorted_pairs = sorted(zip(truss_depths, displacements, strict=True))
        truss_depths_sorted, displacements_sorted = zip(*sorted_pairs, strict=True)
        # Determine marker colors based on allowable_displacement
        marker_colors = ["red" if disp > allowable_displacement else "green" for disp in displacements_sorted]
        trace = go.Scatter(
            x=truss_depths_sorted,
            y=displacements_sorted,
            mode="lines+markers",
            name=f"Joist Number {joist_number}",
            line=dict(color=line_colors[joist_number]),
            marker=dict(color=marker_colors),
        )
        fig.add_trace(trace)

    # Add horizontal line for allowable_displacement
    fig.add_trace(
        go.Scatter(
            x=[min_x, max_x],
            y=[allowable_displacement, allowable_displacement],
            mode="lines",
            line=dict(color="red", dash="dash"),
            name="Allowable Displacement",
        )
    )

    # Update layout
    fig.update_layout(
        xaxis_title="Truss Depth",
        yaxis_title="Displacement",
        title="Displacement vs Truss Depth",
        legend_title="Joist Number",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(
            x=1.05,
            y=1,
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
        ),
    )
    file_path = Path.cwd() / "app" / "result.png"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(file_path), format="png")

    return file_path
