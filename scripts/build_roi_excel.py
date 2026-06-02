from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.io import loadmat


ROI_CHANNELS = {
    "lPFC": [8, 9, 11, 22, 20, 23, 10],
    "rPFC": [3, 5, 6, 7, 17, 19, 21],
    "lM1": [30, 31, 44],
    "rM1": [15, 16, 42],
    "lS1": [33, 32],
    "rS1": [34, 35],
    "lSMA": [13, 14, 27, 43],
    "rSMA": [2, 28, 29, 45],
}


def parse_condition_map(items: list[str]) -> dict[str, str]:
    mapping = {}
    for item in items:
        if ":" not in item:
            raise ValueError(f"Condition mapping must look like SOURCE:LABEL, got {item!r}")
        source, label = item.split(":", 1)
        mapping[source.upper()] = label
    return mapping


def parse_groups(group1: list[str], group2: list[str]) -> dict[str, int]:
    groups = {subject.upper(): 1 for subject in group1}
    overlap = sorted(set(groups) & {subject.upper() for subject in group2})
    if overlap:
        raise ValueError(f"Subjects cannot appear in both groups: {overlap}")
    groups.update({subject.upper(): 2 for subject in group2})
    if not groups:
        raise ValueError("At least one subject ID is required")
    return groups


def get_field(obj: Any, name: str) -> Any:
    if hasattr(obj, name):
        return getattr(obj, name)
    if isinstance(obj, np.ndarray) and obj.dtype.names and name in obj.dtype.names:
        return obj[name]
    raise KeyError(name)


def as_1d_float(values: Any) -> np.ndarray:
    return np.asarray(values, dtype=float).reshape(-1)


def find_subject_and_condition(
    path: Path,
    condition_map: dict[str, str],
    groups: dict[str, int],
) -> tuple[str, str, str]:
    parts_upper = [part.upper() for part in path.parts]
    subject = next((name for name in groups if name in parts_upper), None)
    source_condition = next((cond for cond in condition_map if cond in parts_upper), None)
    if subject is None or source_condition is None:
        raise ValueError(f"Cannot parse subject/condition from path: {path}")
    return subject, source_condition, condition_map[source_condition]


def read_beta_file(path: Path) -> tuple[np.ndarray, np.ndarray, str, int]:
    mat = loadmat(path, squeeze_me=True, struct_as_record=False)
    if "indexdata" not in mat:
        raise KeyError("indexdata")
    indexdata = mat["indexdata"]
    values = as_1d_float(get_field(indexdata, "index"))
    exception_channel = as_1d_float(get_field(indexdata, "exception_channel"))
    signal_type = str(np.asarray(get_field(indexdata, "signal_type")).reshape(()))
    nch = int(np.asarray(get_field(indexdata, "nch")).reshape(()))
    return values, exception_channel, signal_type, nch


def mean_roi(values: np.ndarray, exception_channel: np.ndarray, channels: list[int]) -> float:
    roi_values = []
    for channel in channels:
        idx = channel - 1
        value = values[idx]
        exception = exception_channel[idx] if idx < len(exception_channel) else 0
        if np.isfinite(value) and exception == 0:
            roi_values.append(value)
    return float(np.mean(roi_values)) if roi_values else np.nan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-xlsx", required=True)
    parser.add_argument("--conditions", required=True, nargs="+", help="SOURCE:LABEL pairs, e.g. LOU:TC1 DAO:TC2 YUN:TC3")
    parser.add_argument("--group1", required=True, nargs="+", help="Subject IDs for Group=1")
    parser.add_argument("--group2", required=True, nargs="+", help="Subject IDs for Group=2")
    args = parser.parse_args()

    source_root = Path(args.source_root)
    output_xlsx = Path(args.output_xlsx)
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    condition_map = parse_condition_map(args.conditions)
    condition_labels = list(condition_map.values())
    groups = parse_groups(args.group1, args.group2)

    mat_files = sorted(source_root.rglob("*.mat"))
    if not mat_files:
        raise FileNotFoundError(f"No .mat files found under {source_root}")

    values_by_subject_condition: dict[tuple[str, str], dict[str, float]] = {}
    check_rows = []
    long_rows = []

    for file_path in mat_files:
        subject, source_condition, condition = find_subject_and_condition(file_path, condition_map, groups)
        problem = ""
        try:
            values, exception_channel, signal_type, nch = read_beta_file(file_path)
            if nch != 48 or len(values) != 48:
                problem = f"Unexpected channel count: nch={nch}, len(index)={len(values)}"
            roi_values = {roi: mean_roi(values, exception_channel, channels) for roi, channels in ROI_CHANNELS.items()}
        except Exception as exc:
            signal_type = ""
            nch = 0
            exception_channel = np.array([])
            roi_values = {roi: np.nan for roi in ROI_CHANNELS}
            problem = f"{type(exc).__name__}: {exc}"

        values_by_subject_condition[(subject, condition)] = roi_values
        missing_roi_count = int(sum(pd.isna(value) for value in roi_values.values()))
        exception_count = int(np.sum(exception_channel != 0)) if len(exception_channel) else np.nan

        check_rows.append({
            "ID": subject,
            "Group": groups[subject],
            "Source_Condition": source_condition,
            "Condition": condition,
            "File_Path": str(file_path),
            "Read_OK": problem == "",
            "Signal_Type": signal_type,
            "NCH": nch,
            "Exception_Channel_Count": exception_count,
            "ROI_Count": len(ROI_CHANNELS),
            "Missing_ROI_Count": missing_roi_count,
            "Problem": problem,
        })
        for roi, value in roi_values.items():
            long_rows.append({"ID": subject, "Group": groups[subject], "Condition": condition, "ROI": roi, "Value": value})

    wide_rows = []
    for subject, group in groups.items():
        row = {"ID": subject, "Group": group}
        for roi in ROI_CHANNELS:
            for condition in condition_labels:
                row[f"{roi}_{condition}"] = values_by_subject_condition.get((subject, condition), {}).get(roi, np.nan)
        wide_rows.append(row)

    wide_df = pd.DataFrame(wide_rows)
    roi_map_df = pd.DataFrame({"ROI": roi, "Channels": " ".join(map(str, channels)), "Channel_Count": len(channels)} for roi, channels in ROI_CHANNELS.items())
    check_df = pd.DataFrame(check_rows).sort_values(["Group", "ID", "Condition"])
    long_df = pd.DataFrame(long_rows).sort_values(["Group", "ID", "Condition", "ROI"])

    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        wide_df.to_excel(writer, sheet_name="SPSS_Wide", index=False)
        roi_map_df.to_excel(writer, sheet_name="ROI_Map", index=False)
        check_df.to_excel(writer, sheet_name="Check_Log", index=False)
        long_df.to_excel(writer, sheet_name="Long_Format_Backup", index=False)

    print(f"Saved: {output_xlsx}")
    print(f"Input .mat files: {len(mat_files)}")
    print(f"SPSS_Wide shape: {wide_df.shape[0]} rows x {wide_df.shape[1]} columns")
    print(f"Problems: {int((check_df['Problem'].fillna('') != '').sum())}")
    print(f"Missing ROI cells: {int(wide_df.drop(columns=['ID', 'Group']).isna().sum().sum())}")


if __name__ == "__main__":
    main()
