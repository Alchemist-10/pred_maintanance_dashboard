# Predictive Maintenance Dashboard — Turbofan Fleet

Tableau dashboard for MRO (Maintenance, Repair & Overhaul) analytics using the public **NASA CMAPSS Turbofan Engine Degradation** dataset.

This repo contains:
- A Python data-prep script that converts CMAPSS raw text files into a single dashboard-ready table
- A dashboard spec (failure probability, maintenance schedule heatmap, component health scores)
- Instructions to publish a live, resume-ready link on **Tableau Public**

## Live dashboard (Tableau Public)

- Link: **ADD YOUR TABLEAU PUBLIC LINK HERE**
  - Example: `https://public.tableau.com/views/<workbook>/<dashboard>`

## What the dashboard shows

Build the dashboard in **Tableau** or **Power BI** with these required visuals:

1. **Failure probability**
	- KPI + trend by unit/time (cycle)
	- Uses a near-term horizon (default: probability of failure within 30 cycles)

2. **Maintenance schedule heatmap**
	- Heatmap of `unit` × `cycle` (or binned cycle/time) colored by `maintenance_bucket` or `maintenance_due_in_cycles`
	- Quickly highlights which engines are “due soon”

3. **Component health scores**
	- Health score per engine over time
	- Designed for a simple “green → red” health view

## Dataset

**NASA CMAPSS (Turbofan Engine Degradation Simulation)** is a standard public dataset for predictive maintenance research.

You can download it from NASA’s Prognostics Center of Excellence (PCoE) or other mirrors.

Files you need for this project (subset FD001 by default):
- `train_FD001.txt`
- (optional) `test_FD001.txt`, `RUL_FD001.txt` (not required by the current dashboard pipeline)

Place the raw files here:

`data/raw/cmapss/`

Example:

`data/raw/cmapss/train_FD001.txt`

## Python data pipeline (feeds the dashboard)

The script below reads CMAPSS raw text, engineers dashboard metrics, and writes a flat CSV extract for BI tools.

Output includes:
- `rul` (Remaining Useful Life) for training data
- `failure_probability_30` (heuristic)
- `maintenance_due_in_cycles`, `maintenance_bucket`, `maintenance_flag`
- `component_health_score` (blended score)

### Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Run

```bash
python src/prepare_cmapss.py --dataset-dir data/raw/cmapss --subset FD001 --out data/processed/turbofan_dashboard.csv
```

When it succeeds, you will have:

`data/processed/turbofan_dashboard.csv`

## Build the dashboard (Tableau)

1. Open Tableau Desktop (or Tableau Public app).
2. Connect to a **Text file** → select `data/processed/turbofan_dashboard.csv`.
3. Create these sheets (minimum):
	- **Failure probability**: line chart of `failure_probability_30` over `cycle` (filter by `unit`)
	- **Maintenance heatmap**: heatmap with rows = `unit`, columns = `cycle` (or binned `cycle`), color = `maintenance_bucket` or `maintenance_due_in_cycles`
	- **Component health**: line chart of `component_health_score` over `cycle` (filter by `unit`)
4. Assemble them into a single dashboard named:
	- **Predictive Maintenance Dashboard — Turbofan Fleet**

### Publish to Tableau Public (resume link)

1. Sign in to Tableau Public.
2. `Server → Tableau Public → Save to Tableau Public`.
3. Copy the published URL.
4. Paste it into the **Live dashboard** section at the top of this README.

## Build the dashboard (Power BI)

1. `Get Data → Text/CSV` and choose `data/processed/turbofan_dashboard.csv`.
2. Create:
	- Card for `failure_probability_30`
	- Heatmap-style matrix for maintenance buckets (or conditional formatting on a matrix)
	- Line chart for `component_health_score` over `cycle`

## Repository structure

- `src/prepare_cmapss.py` — Python script that cleans/engineers metrics and exports a single dashboard table
- `data/raw/cmapss/` — (local) raw CMAPSS dataset files
- `data/processed/` — (local) generated dashboard extract(s)
- `dashboard/` — place Tableau workbook (`.twb/.twbx`) or Power BI report (`.pbix`) here
- `screenshots/` — optional screenshots for README / resume

## Notes on metrics

- `failure_probability_30` is a **heuristic** derived from RUL (Remaining Useful Life). It’s intentionally lightweight and easy to explain in interviews.
- `component_health_score` blends:
  - an RUL-normalized score, and
  - a sensor-deviation score versus early-life baseline

If you want a model-based failure probability (recommended for a deeper ML version), replace the heuristic with a trained classifier or a survival model.

## Troubleshooting

- If the script errors with an “unexpected column count”, confirm you are using the original CMAPSS `train_FD00X.txt` files and that they are placed under `data/raw/cmapss/`.
