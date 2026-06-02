from __future__ import annotations

import argparse
import re
import subprocess
import zipfile
from pathlib import Path

import pandas as pd


ROI_CODES = ["lPFC", "rPFC", "lM1", "rM1", "lS1", "rS1", "lSMA", "rSMA"]


RUNNER_TEMPLATE = r'''
import sys
from pathlib import Path
import SpssClient

syntax_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])

SpssClient.StartClient()
try:
    output_doc = SpssClient.NewOutputDoc()
    output_doc.SetAsDesignatedOutputDoc()
    syntax_doc = SpssClient.NewSyntaxDoc()
    syntax_doc.SetSyntax(syntax_path.read_text(encoding="utf-8"))
    syntax_doc.RunSyntax()
    output_doc = SpssClient.GetDesignatedOutputDoc()
    output_doc.SaveAs(str(output_path))
    output_doc.SetPromptToSave(False)
    syntax_doc.SetPromptToSave(False)
finally:
    SpssClient.StopClient()
print(output_path)
'''


def build_syntax(df: pd.DataFrame, roi: str, conditions: list[str]) -> str:
    value_columns = [f"{roi}_{condition}" for condition in conditions]
    columns = ["ID", "Group", *value_columns]
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise RuntimeError(f"{roi} missing columns: {missing}")

    lines = [
        f"* Auto-generated inline data for {roi}.",
        f"DATA LIST LIST / ID (A64) Group {' '.join(value_columns)}.",
        "BEGIN DATA",
    ]
    for _, row in df[columns].iterrows():
        values = [str(row["ID"]), str(int(row["Group"]))]
        values.extend(format(float(row[column]), ".15g") for column in value_columns)
        lines.append(" ".join(values))

    lines += [
        "END DATA.",
        "EXECUTE.",
        "",
        f"VARIABLE LEVEL Group (NOMINAL) {' '.join(value_columns)} (SCALE).",
        "",
        f"GLM {' '.join(value_columns)} BY Group",
        f"  /WSFACTOR=CONDITION {len(conditions)} Polynomial",
        "  /METHOD=SSTYPE(3)",
        "  /PRINT=DESCRIPTIVE ETASQ HOMOGENEITY",
        "  /PLOT=PROFILE(Group*CONDITION)",
        "  /CRITERIA=ALPHA(.05)",
        "  /WSDESIGN=CONDITION",
        "  /DESIGN=Group.",
    ]
    return "\n".join(lines) + "\n"


def verify_spv(path: Path, roi: str, conditions: list[str]) -> None:
    if not path.exists():
        raise RuntimeError(f"{roi}: missing {path}")
    if path.stat().st_size < 15000:
        raise RuntimeError(f"{roi}: suspiciously small file")
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        payload = b"\n".join(zf.read(name) for name in names if name.endswith((".xml", ".bin")))
        xml_text = "\n".join(zf.read(name).decode("utf-8", "ignore") for name in names if name.endswith(".xml"))
    expected_vars = {f"{roi}_{condition}".encode() for condition in conditions}
    joined = "|".join(re.escape(condition) for condition in conditions)
    found_vars = set(re.findall(fr"[lr][A-Z0-9]+_(?:{joined})".encode(), payload))
    if not expected_vars.issubset(found_vars):
        raise RuntimeError(f"{roi}: missing expected vars {expected_vars - found_vars}")
    if not [name for name in names if "chart" in name.lower()]:
        raise RuntimeError(f"{roi}: missing chart entries")
    if any(token.lower() in xml_text.lower() for token in ["error", "warning #", "command name:"]):
        raise RuntimeError(f"{roi}: SPSS command error text found")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-xlsx", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--conditions", nargs="+", required=True)
    parser.add_argument("--prefix", default="CA")
    parser.add_argument("--spss-python", default=r"D:\SPSS\statisticspython3.bat")
    args = parser.parse_args()

    source_xlsx = Path(args.source_xlsx)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = output_dir / "_syntax"
    work_dir.mkdir(exist_ok=True)

    df = pd.read_excel(source_xlsx, sheet_name="SPSS_Wide")
    if "ID" not in df.columns or "Group" not in df.columns:
        raise RuntimeError("SPSS_Wide must contain ID and Group columns")
    if int(df.isna().sum().sum()) != 0:
        raise RuntimeError("ROI sheet has missing values")

    runner_path = work_dir / "run_one_frontend_spv.py"
    runner_path.write_text(RUNNER_TEMPLATE, encoding="utf-8")

    for roi in ROI_CODES:
        syntax_path = work_dir / f"{roi}_inline.sps"
        output_path = output_dir / f"{args.prefix} {roi}.spv"
        syntax_path.write_text(build_syntax(df, roi, args.conditions), encoding="utf-8")
        subprocess.run([args.spss_python, str(runner_path), str(syntax_path), str(output_path)], check=True)
        verify_spv(output_path, roi, args.conditions)
        print(f"Verified: {output_path}")


if __name__ == "__main__":
    main()
