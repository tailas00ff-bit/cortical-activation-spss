---
name: cortical-activation-spss
description: Use when processing Tailas fNIRS cortical activation beta_1 .mat files from E:\皮层激活 into SPSS-ready ROI Excel files, then running mixed repeated-measures GLM outputs with profile plots for Tai Chi or balance tasks.
---

# Cortical Activation SPSS

## Overview

Use this skill for the proven cortical activation pipeline: copy `Oxy\beta_1` `.mat` files, merge 48 channels into 8 predefined ROIs, build SPSS wide-format Excel, then run SPSS repeated-measures GLM with `Group` as between-subject factor and task condition as within-subject factor.

Do not run statistics when the user only asks to organize Excel/CSV. Do not modify or delete source files under `E:\皮层激活` unless explicitly requested.

## Core Context

Subject groups:

| Group | Meaning | Subjects |
|---|---|---|
| 1 | 老手组 | LIHONGJUAN, LISHUQIN, LIUXIANZHANG, ZHANGJIEQING |
| 2 | 新手组 | CHENGJINGHUA, LIUZHAOLIN, ZHANGYAN, ZHAOCHUNYAN |

Task folders:

| Task | Source task code | Conditions | Typical staging/output |
|---|---:|---|---|
| 太极拳任务 | `result\2` | `LOU -> TC1`, `DAO -> TC2`, `YUN -> TC3` | `TCC1`, `TCC2`, `TCC3` |
| 平衡任务 | `result\1` | `SZ`, `SB` | `BLL1`, `BLL2`, `BLL3` |

ROI channel map from the user screenshot:

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
   - Source pattern: `E:\皮层激活\<老手|新手>\<subject>\result\<task_code>\<condition>\Oxy\beta_1\*.mat`
   - Preserve group, subject, condition, `Oxy\beta_1` folders in the staging directory.
   - Verify expected counts before proceeding: Tai Chi = 24 files, balance = 16 files.

2. Build ROI Excel:
   - Use `scripts/build_roi_excel.py` on the staging directory.
   - Output one workbook with sheets `SPSS_Wide`, `ROI_Map`, `Check_Log`, `Long_Format_Backup`.
   - `SPSS_Wide` must be one row per subject, first columns `ID`, `Group`, then variables like `lPFC_TC1`, `lPFC_TC2`, `lPFC_TC3` or `lPFC_SZ`, `lPFC_SB`.
   - ROI values are the mean of available non-exception channels. Treat NaN and nonzero `exception_channel` as missing.

3. Run SPSS only when requested:
   - Use `scripts/run_spss_roi_batch.py`.
   - Analyze each ROI separately.
   - Use `GLM <ROI_condition_columns> BY Group`.
   - Use `/WSFACTOR=CONDITION <n> Polynomial`.
   - Always include `/PLOT=PROFILE(Group*CONDITION)` so the output has the profile plot.
   - Save one `.spv` per ROI.

4. Verify before reporting:
   - Excel check: 8 rows, group counts `{1:4, 2:4}`, expected condition columns, no unexpected missing ROI cells unless explained.
   - SPSS check: every `.spv` exists, is not suspiciously small, contains only the ROI's condition variables, has chart entries, and has no command error text.

## Command Examples

Tai Chi ROI Excel from already-copied files:

```powershell
python .\cortical-activation-spss\scripts\build_roi_excel.py `
  --source-root "C:\Users\Tailas\Desktop\TCC1" `
  --output-xlsx "C:\Users\Tailas\Desktop\TCC2\SPSS_TC_CorticalActivation_ROI_wide.xlsx" `
  --conditions "LOU:TC1" "DAO:TC2" "YUN:TC3"
```

Balance ROI Excel from already-copied files:

```powershell
python .\cortical-activation-spss\scripts\build_roi_excel.py `
  --source-root "C:\Users\Tailas\Desktop\BLL1" `
  --output-xlsx "C:\Users\Tailas\Desktop\BLL2\SPSS_BL_CorticalActivation_ROI_wide.xlsx" `
  --conditions "SZ:SZ" "SB:SB"
```

Run SPSS ROI outputs with plots:

```powershell
python .\cortical-activation-spss\scripts\run_spss_roi_batch.py `
  --source-xlsx "C:\Users\Tailas\Desktop\BLL2\SPSS_BL_CorticalActivation_ROI_wide.xlsx" `
  --output-dir "C:\Users\Tailas\Desktop\BLL3" `
  --conditions SZ SB `
  --prefix BLCA
```

## Common Mistakes

- Do not treat ROIs or channels as subjects. Subjects are the 8 people.
- Do not pool all ROIs into one SPSS model. Run one model per ROI.
- Do not forget the profile plot. The SPSS syntax must include `/PLOT=PROFILE(Group*CONDITION)`.
- Do not run stats from the channel-level Excel after the user asks to merge channels into ROIs.
- Do not overwrite or delete raw files under `E:\皮层激活`; copying to staging folders is the safe operation.

## References

Read `references/project-conventions.md` when the exact task mapping, folder conventions, or validation checklist needs to be refreshed.
