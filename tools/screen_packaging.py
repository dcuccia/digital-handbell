# SPDX-License-Identifier: MIT
"""Generate explicitly hypothetical packaging screens, not fabrication CAD."""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs" / "measurements" / "shell-speaker-inputs.json"


def circle_area(diameter):
    return math.pi * diameter * diameter / 4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assumed-40mm-depth", type=float, required=True,
                        help="Explicit hypothetical depth from lip; the owner has not measured this station.")
    args = parser.parse_args()
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    shell = data["shell"]
    z40 = args.assumed_40mm_depth
    if not 0 < z40 <= shell["bell_body_height"]:
        parser.error("Assumed station must be inside the approximate bell body.")
    d0 = shell["inside_diameter_at_lip"]
    d40 = shell["inside_diameter_at_unspecified_taper_station"]
    slope = (d0-d40)/z40
    speaker = data["speaker_40mm_candidate"]
    frame = speaker["frame_diameter_nominal"] + speaker["frame_diameter_tolerance"]
    depth = speaker["overall_height_nominal"] + speaker["overall_height_tolerance"]
    magnet = speaker["magnet_diameter_nominal"] + speaker["magnet_diameter_tolerance"]
    gap = 2.0
    board_z = depth+gap
    board_station_d = d0-slope*board_z if board_z <= z40 else None
    annuli = []
    for outer, inner in [(64, 43), (66, 43), (68, 43), (66, 45)]:
        annuli.append({
            "outer_diameter_mm": outer,
            "inner_diameter_mm": inner,
            "gross_area_mm2": circle_area(outer)-circle_area(inner),
            "area_equivalent_solid_disk_diameter_mm": math.sqrt(outer*outer-inner*inner),
            "area_after_1mm_allowance_at_both_edges_mm2":
                circle_area(outer-2)-circle_area(inner+2),
            "radial_band_width_mm": (outer-inner)/2,
        })
    result = {
        "status": "Not for fabrication; hypothetical geometry and area only",
        "assumptions": {
            "linear_interpolation_between_lip_and_hypothetical_station": True,
            "assumed_40mm_station_z_mm": z40,
            "actual_40mm_station_z_mm": shell["taper_station_depth_from_lip"],
            "speaker_front_at_lip_plane_for_this_example": True,
            "example_speaker_to_pcb_gap_mm": gap,
            "pcb_thickness_components_grille_cell_cables_not_included": True,
        },
        "speaker_retail_drawing_maxima_mm": {
            "frame_diameter": frame, "overall_height": depth, "magnet_diameter": magnet,
        },
        "latest_plane_depth_before_any_clearance_mm": {
            str(d): (d0-d)/slope for d in [55, 50, 45, 40]
        },
        "example_pcb_plane_z_mm": board_z,
        "interpolated_cavity_diameter_at_example_plane_mm": board_station_d,
        "annular_area_examples": annuli,
        "caveats": [
            "No inference of actual taper shape or extrapolation beyond the hypothetical station.",
            "The 2.7 mm rim dimension is within the 18 mm overall speaker height, not added to it.",
            "Gross annular area does not prove component placement or routability.",
            "A uniform 66/43 mm ring is only 11.5 mm wide: a 15.4 mm-wide S3-MINI body cannot fit wholly in that band.",
            "Near-mouth components have height; fitting the PCB plane alone does not prove component clearance.",
            "Carrier wall, aperture/basket/terminal clearance, thermal paths and antenna keepouts remain unknown.",
        ],
    }
    out = ROOT / "docs" / "measurements" / "packaging-screen.json"
    out.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")

    scale = 4
    origin_x, origin_y = 200, 110
    sx = lambda x: origin_x + scale*x
    sy = lambda z: origin_y + scale*z
    left0, right0 = sx(-d0/2), sx(d0/2)
    left40, right40 = sx(-d40/2), sx(d40/2)
    board_line = ""
    if board_station_d is not None:
        board_line = f'''
        <line x1="{sx(-25)}" y1="{sy(board_z)}" x2="{sx(25)}" y2="{sy(board_z)}" stroke="#b42318" stroke-width="5"/>
        <text x="65" y="326">Example 50 mm PCB at z={board_z:g} mm</text>
        <text x="65" y="348">Interpolated opening: {board_station_d:.1f} mm before clearance</text>'''
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="480" viewBox="0 0 1100 480">
    <rect width="1100" height="480" fill="white"/>
    <g font-family="Arial, sans-serif" font-size="15" fill="#172b4d">
      <text x="25" y="30" font-size="22" font-weight="bold">Packaging sensitivity screen - NOT fabrication CAD</text>
      <text x="25" y="56">The 40 mm station depth is UNMEASURED. This illustration explicitly assumes z={z40:g} mm.</text>
      <text x="65" y="88" font-weight="bold">A. Solid PCB behind speaker</text>
      <path d="M {left0} {origin_y} L {left40} {sy(z40)} M {right0} {origin_y} L {right40} {sy(z40)}"
            stroke="#b7791f" stroke-width="3" stroke-dasharray="7 4" fill="none"/>
      <line x1="{left0}" y1="{origin_y}" x2="{right0}" y2="{origin_y}" stroke="#64748b"/>
      <text x="142" y="104">70 mm lip ID</text>
      <rect x="{sx(-frame/2)}" y="{origin_y}" width="{frame*scale}" height="{depth*scale}"
            fill="#d1fae5" stroke="#047857"/>
      <text x="125" y="138">Speaker envelope</text>
      <text x="127" y="159">{frame:g} x {depth:g} mm</text>
      <text x="65" y="300">Dashed taper is assumed, not measured</text>
{board_line}
      <text x="65" y="375">PCB thickness, components, grille and cell omitted.</text>
      <text x="580" y="88" font-weight="bold">B. Near-mouth annular PCB area</text>
      <circle cx="755" cy="205" r="132" fill="#dbeafe" stroke="#1d4ed8" stroke-width="2"/>
      <circle cx="755" cy="205" r="86" fill="white" stroke="#1d4ed8" stroke-width="2"/>
      <text x="671" y="196">43 mm aperture</text>
      <text x="688" y="219">66 mm outside</text>
      <rect x="856" y="164" width="61.6" height="82" fill="#fee2e2" fill-opacity=".8" stroke="#b42318" stroke-width="2"/>
      <text x="923" y="184">S3-MINI body</text>
      <text x="923" y="207">15.4 x 20.5</text>
      <text x="580" y="365">Gross area: {annuli[1]["gross_area_mm2"]:.0f} mm2; only 11.5 mm radial width.</text>
      <text x="580" y="387">Red rectangle illustrates a fit conflict, not a placement.</text>
      <text x="25" y="432">An offset aperture / wider electronics bay or separate controller location requires a real 3D fit study.</text>
      <text x="25" y="457">Original diagram from owner-reported estimates and retail dimensions; no supplied product image reproduced.</text>
    </g></svg>
'''
    image = ROOT / "docs" / "images" / "packaging-screen.svg"
    image.parent.mkdir(exist_ok=True)
    image.write_text(svg, encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ["caveats", "annular_area_examples"]}, indent=2))
    print(f"Wrote {out.relative_to(ROOT)} and {image.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
