#!/usr/bin/env python3
"""Add display-only KiCad library models to a scratch copy of the PCBA."""

import argparse
from pathlib import Path

import pcbnew


MODEL_BY_REFERENCE = {
    "D3": "Diode_SMD.3dshapes/D_SOD-323.step",
    "D4": "Diode_SMD.3dshapes/D_SOD-323F.step",
    "FB1": "Inductor_SMD.3dshapes/L_0603_1608Metric.step",
    "FB2": "Inductor_SMD.3dshapes/L_0603_1608Metric.step",
    "IC1": "Package_DFN_QFN.3dshapes/QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm.step",
    "IC4": "Package_LGA.3dshapes/LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y.step",
    "L0": "LED_SMD.3dshapes/LED_0603_1608Metric.step",
    "L1": "Inductor_SMD.3dshapes/L_APV_ANR5045.step",
    "CHG0": "LED_SMD.3dshapes/LED_0603_1608Metric.step",
    "Q1": "Package_TO_SOT_SMD.3dshapes/SOT-23.step",
    "Q2": "Package_TO_SOT_SMD.3dshapes/SOT-23.step",
    "Q4": "Package_TO_SOT_SMD.3dshapes/SOT-23.step",
    "R27": "Resistor_SMD.3dshapes/R_0805_2012Metric.step",
    "U1": "Package_SON.3dshapes/Winbond_USON-8-1EP_3x2mm_P0.5mm_EP0.2x1.6mm.step",
    "U2": "Package_TO_SOT_SMD.3dshapes/SOT-23-5.step",
    "U3": "Package_TO_SOT_SMD.3dshapes/SOT-23-5.step",
    "U4": "Package_DFN_QFN.3dshapes/TQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.step",
    "U5": "Package_TO_SOT_SMD.3dshapes/SOT-563.step",
    "U6": "Package_SON.3dshapes/WSON-6_1.5x1.5mm_P0.5mm.step",
    "X6": "Connector_USB.3dshapes/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step",
    "Y1": "Crystal.3dshapes/Crystal_SMD_Abracon_ABM8G-4Pin_3.2x2.5mm.step",
}

USB_OFFSET_MM = (0.0, 1.205, 0.0)


def model_for_reference(reference: str, footprint_id: str) -> str | None:
    if reference in MODEL_BY_REFERENCE:
        return MODEL_BY_REFERENCE[reference]
    if reference == "CHG_EN0":
        return None  # Solder jumper, not a component body.
    if reference.startswith("C"):
        if reference in {"C1", "C4", "C5", "C19", "C20", "C26", "C27", "C28"}:
            return "Capacitor_SMD.3dshapes/C_0805_2012Metric.step"
        return "Capacitor_SMD.3dshapes/C_0402_1005Metric.step"
    if reference.startswith("R"):
        return "Resistor_SMD.3dshapes/R_0402_1005Metric.step"
    if footprint_id == "Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal":
        return None  # The source board already has this model.
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    model_root = args.model_root.resolve()
    if source == output:
        raise SystemExit("Refusing to overwrite the source PCB")
    if not source.is_file():
        raise SystemExit(f"Source PCB does not exist: {source}")
    if not model_root.is_dir():
        raise SystemExit(f"KiCad 3D model directory does not exist: {model_root}")

    board = pcbnew.LoadBoard(str(source))
    added: list[tuple[str, str]] = []
    skipped: list[str] = []
    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        footprint_id = footprint.GetFPIDAsString()
        if footprint.IsDNP():
            skipped.append(reference)
            continue
        relative_model = model_for_reference(reference, footprint_id)
        if not relative_model:
            if not list(footprint.Models()):
                skipped.append(reference)
            continue

        model_path = model_root / relative_model
        if not model_path.is_file():
            raise SystemExit(f"Missing model for {reference}: {model_path}")
        model = pcbnew.FP_3DMODEL()
        model.m_Filename = model_path.as_posix()
        offset = USB_OFFSET_MM if reference == "X6" else (0.0, 0.0, 0.0)
        model.m_Offset = pcbnew.VECTOR3D(*offset)
        footprint.Add3DModel(model)
        added.append((reference, relative_model))

    output.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.SaveBoard(str(output), board):
        raise SystemExit(f"Could not save preview PCB: {output}")

    print(f"Saved scratch visualization PCB: {output}")
    print(f"Added {len(added)} library models to: {', '.join(ref for ref, _ in added)}")
    print(f"Left unmodeled, without changing footprint geometry: {', '.join(sorted(skipped))}")


if __name__ == "__main__":
    main()
