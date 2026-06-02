---
name: cortical-activation-spss
description: Use when processing fNIRS cortical activation beta_1 .mat files into ROI-level SPSS-ready Excel files, then running mixed repeated-measures GLM outputs with profile plots for Tai Chi, balance, or similar repeated-measures tasks.
---

# Cortical Activation SPSS

## Overview

Use this skill for a reusable fNIRS cortical activation pipeline: copy `Oxy\beta_1` `.mat` files into a staging folder, merge 48 channels into 8 predefined ROIs, build SPSS wide-format Excel, then run SPSS repeated-measures GLM with `Group` as between-subject factor and task condition as within-subject factor.

Do not run statistics when the user only asks to organize Excel/CSV. Do not modify or delete raw source files unless explicitly requested.

## Data Model

The SPSS-ready wide table should contain:

| Column type | Meaning |
|---|---|
| `ID` | anonymized subject ID |
| `Group` | between-subject group code, usually `1` and `2` |
| `<ROI>_<Condition>` | ROI mean beta value for one repeated-measures condition |

Example balance variables:

- `lPFC_SZ`, `lPFC_SB`
- `rSMA_SZ`, `rSMA_SB`

Example Tai Chi variables:

- `lPFC_TC1`, `lPFC_TC2`, `lPFC_TC3`
- `rSMA_TC1`, `rSMA_TC2`, `rSMA_TC3`

## ROI Channel Map

Use this fixed ROI map unless the user provides a revised map:

| ROI | Channels |
|---|---|
| lPFC | 8 9 11 22 20 23 10 |
| rPFC | 3 5 6 7 17 19 21 |
| lM1 | 30 31 44 |
| rM1 | 15 16 42 |
| lS1 | 33 32 |
| rS1 | 34 35 |
| lSMA | 13 14 27 43 |
| rSMA | 2 28 29 45 |

## Workflow

1. Copy raw files only:
   - Source pattern should resemble `<raw_root>\<group_folder>\<subject>\result\<task_code>\<condition>\Oxy\beta_1\*.mat`.
   - Preserve group, subject, condition, and `Oxy\beta_1` folders in a staging directory.
   - Verify the expected file count before proceeding.

2. Build ROI Excel:
   - Use `scripts/build_roi_excel.py`.
   - Provide subject IDs through `--group1` and `--group2`.
   - Output one workbook with sheets `SPSS_Wide`, `ROI_Map`, `Check_Log`, `Long_Format_Backup`.
   - ROI values are the mean of available non-exception channels. Treat NaN and nonzero `exception_channel` as missing.

3. Run SPSS only when requested:
   - Use `scripts/run_spss_roi_batch.py`.
   - Analyze each ROI separately.
   - Use `GLM <ROI_condition_columns> BY Group`.
   - Use `/WSFACTOR=CONDITION <n> Polynomial`.
   - Always include `/PLOT=PROFILE(Group*CONDITION)` so the output has the profile plot.
   - Save one `.spv` per ROI.

4. Verify before reporting:
   - Excel check: expected subject count, group counts, condition columns, and no unexplained missing ROI cells.
   - SPSS check: every `.spv` exists, is not suspiciously small, contains only the ROI's condition variables, has chart entries, and has no command error text.

## Command Examples

Tai Chi-style ROI Excel from already-copied files:

```powershell
python .\scripts\build_roi_excel.py `
  --source-root "C:\path\to\staging\TCC1" `
  --output-xlsx "C:\path\to\output\SPSS_TC_CorticalActivation_ROI_wide.xlsx" `
  --conditions "LOU:TC1" "DAO:TC2" "YUN:TC3" `
  --group1 Expert01 Expert02 Expert03 Expert04 `
  --group2 Novice01 Novice02 Novice03 Novice04
```

Balance-style ROI Excel from already-copied files:

```powershell
python .\scripts\build_roi_excel.py `
  --source-root "C:\path\to\staging\BLL1" `
  --output-xlsx "C:\path\to\output\SPSS_BL_CorticalActivation_ROI_wide.xlsx" `
  --conditions "SZ:SZ" "SB:SB" `
  --group1 Expert01 Expert02 Expert03 Expert04 `
  --group2 Novice01 Novice02 Novice03 Novice04
```

Run SPSS ROI outputs with plots:

```powershell
python .\scripts\run_spss_roi_batch.py `
  --source-xlsx "C:\path\to\output\SPSS_BL_CorticalActivation_ROI_wide.xlsx" `
  --output-dir "C:\path\to\SPSS_outputs" `
  --conditions SZ SB `
  --prefix BLCA
```

## Common Mistakes

- Do not treat ROIs or channels as subjects. Subjects are rows in `SPSS_Wide`.
- Do not pool all ROIs into one SPSS model. Run one model per ROI.
- Do not forget the profile plot. The SPSS syntax must include `/PLOT=PROFILE(Group*CONDITION)`.
- Do not run stats from a channel-level Excel after the user asks to merge channels into ROIs.
- Do not overwrite or delete raw files. Copy to staging folders first.

## References

Read `references/project-conventions.md` when the folder conventions, ROI map, SPSS model, or validation checklist needs to be refreshed.
