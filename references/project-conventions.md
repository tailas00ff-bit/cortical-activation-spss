# Project Conventions

## Source Layout

Raw cortical activation files live under:

`E:\皮层激活\<老手|新手>\<SUBJECT>\result\<TASK_CODE>\<ACTION>\Oxy\beta_1\*.mat`

Each `.mat` should contain `indexdata` with fields including:

- `indexdata.index`: 48 channel beta values
- `indexdata.exception_channel`: channel exclusion flags
- `indexdata.nch`: expected `48`
- `indexdata.signal_type`: expected `Oxy`
- `indexdata.beta_name`: usually the action label

## Subject and Group Coding

Group 1, 老手组:

- LIHONGJUAN
- LISHUQIN
- LIUXIANZHANG
- ZHANGJIEQING

Group 2, 新手组:

- CHENGJINGHUA
- LIUZHAOLIN
- ZHANGYAN
- ZHAOCHUNYAN

## Task Mapping

Tai Chi cortical activation:

- source task folder: `result\2`
- actions: `LOU`, `DAO`, `YUN`
- SPSS labels: `TC1`, `TC2`, `TC3`
- expected copied file count: `8 * 3 = 24`

Balance cortical activation:

- source task folder: `result\1`
- actions: `SZ`, `SB`
- SPSS labels: `SZ`, `SB`
- expected copied file count: `8 * 2 = 16`

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
- Example balance ROI: `lPFC_SZ lPFC_SB`
- Example Tai Chi ROI: `lPFC_TC1 lPFC_TC2 lPFC_TC3`

Required syntax options:

```spss
/PRINT=DESCRIPTIVE ETASQ HOMOGENEITY
/PLOT=PROFILE(Group*CONDITION)
/WSDESIGN=CONDITION
/DESIGN=Group
```

For 2-condition balance data, Mauchly sphericity is not meaningful because sphericity is automatically satisfied with two levels. For 3-condition Tai Chi data, inspect Mauchly and use Greenhouse-Geisser if needed.
