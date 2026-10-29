# Validate Plotly HTML report against Parquet

Put `report.html` and the complete `facility_type_avg_time_spent_per_visit_date/` directory next to the scripts. The directory may contain multiple `.parquet` part-files and partition subfolders.

Install:

```powershell
python -m pip install -r requirements.txt
```

Run:

```powershell
python -m robot compare_report.robot
```

Chrome must be installed. The test loads the Plotly report in Chrome via Selenium and extracts the underlying Plotly table trace, not nonexistent HTML `<table>` tags. It reads the Parquet dataset with pandas/pyarrow, compares names and rows ignoring order, preserving duplicate multiplicity, and prints sample mismatches. No date filtering or implicit column mapping is performed.
