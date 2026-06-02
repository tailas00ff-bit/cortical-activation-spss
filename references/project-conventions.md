# Project Conventions

## Source Layout

Raw cortical activation files usually live under a structure like:

`<raw_root>\<group_folder>\<SUBJECT>\result\<TASK_CODE>\<ACTION>\Oxy\beta_1\*.mat`

Each `.mat` should contain `indexdata` with fields including:

- `indexdata.index`: 48 channel beta values
- `indexdata.exception_channel`: channel exclusion flags
- `indexdata.nch`: expected `48`
- `indexdata.signal_type`: expected `Oxy`
- `indexdata.beta_name`: usually the action label

## Subject and Group Coding

Use anonymized subject IDs for shared or public repositories.

Example:

| Group | Meaning | Example IDs |
|---|---|---|
| 1 | expert or experienced group | Expert01, Expert02, Expert03, Expert04 |
| 2 | novice or comparison group | Novice01, Novice02, Novice03, Novice04 |

The scripts accept subject IDs through `--group1` and `--group2`, so real names do not need to be stored in this repository.

## Task Mapping

Tai Chi-style cortical activation:

- source task folder example: `result\2`
- source actions example: `LOU`, `DAO`, `YUN`
- SPSS labels example: `TC1`, `TC2`, `TC3`
- expected copied file count for 8 subjects and 3 conditions: `8 * 3 = 24`

Balance-style cortical activation:

- source task folder example: `result\1`
- source actions example: `SZ`, `SB`
- SPSS labels example: `SZ`, `SB`
- expected copied file count for 8 subjects and 2 conditions: `8 * 2 = 16`

## ROI Merge Rules

Use these fixed ROIs:

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

Average only non-missing, non-exception channels. If all channels inside an ROI are missing or excluded, leave that ROI value blank and report it.

## SPSS Model

For each ROI, run one mixed repeated-measures GLM:

- Between-subject factor: `Group`
- Within-subject factor: `CONDITION`
- Within levels: condition columns for that ROI
- Example 2-condition ROI: `lPFC_SZ lPFC_SB`
- Example 3-condition ROI: `lPFC_TC1 lPFC_TC2 lPFC_TC3`

Required syntax options:

```spss
/PRINT=DESCRIPTIVE ETASQ HOMOGENEITY
/PLOT=PROFILE(Group*CONDITION)
/WSDESIGN=CONDITION
/DESIGN=Group
```

For 2-condition data, Mauchly sphericity is not meaningful because sphericity is automatically satisfied with two levels. For 3-condition data, inspect Mauchly and use Greenhouse-Geisser if needed.
