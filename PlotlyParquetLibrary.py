"""Robot Framework keywords for comparing Plotly HTML tables to Parquet datasets."""
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import math
import re

import pandas as pd
from robot.api.deco import keyword


def column_name(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def canonical(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.date().isoformat() if isinstance(value, (datetime, pd.Timestamp)) and value.hour == value.minute == value.second == 0 else value.isoformat()
    if isinstance(value, str):
        value = value.strip()
        if value.lower() in {"", "null", "none", "nan"}:
            return None
        if re.fullmatch(r"\d{4}-\d\d-\d\d(?:[ T]00:00:00(?:\.0+)?)?", value):
            return value[:10]
    if isinstance(value, (int, float, Decimal)) or (isinstance(value, str) and re.fullmatch(r"[-+]?\d+(\.\d+)?", value)):
        try:
            number = Decimal(str(value))
            if number.is_finite():
                return str(number.normalize())
        except InvalidOperation:
            pass
    return str(value)


class PlotlyParquetLibrary:
    @keyword("Compare Plotly Data To Parquet")
    def compare_plotly_data_to_parquet(self, plotly_headers, plotly_rows, parquet_path, sample_limit=10):
        directory = Path(parquet_path)
        if not directory.exists():
            raise AssertionError(f"Parquet path not found: {directory}")
        df = pd.read_parquet(directory, engine="pyarrow")
        # Filter by visit_date: October 13–19, 2026
        start_date = pd.Timestamp("2026-10-13")
        end_date = pd.Timestamp("2026-10-19")

        df["visit_date"] = pd.to_datetime(
            df["visit_date"], errors="raise"
        )

        df = df[
            (df["visit_date"] >= start_date)
            & (df["visit_date"] < end_date + pd.Timedelta(days=1))
            ].copy()

        print(f"Filtered Parquet rows: {len(df)}")

        headers = [column_name(v) for v in plotly_headers]
        source_headers = [column_name(v) for v in df.columns]
        if len(headers) != len(set(headers)) or len(source_headers) != len(set(source_headers)):
            raise AssertionError("Duplicate column names after normalization")

        rename_map = {"avg_time_spent": "average_time_spent"}
        parquet_df = df.rename(columns=rename_map).drop(columns=["partition_date"], errors="ignore")
        source_headers = [column_name(v) for v in parquet_df.columns]
        if len(source_headers) != len(set(source_headers)):
            raise AssertionError("Duplicate Parquet columns after mapping")
        if set(headers) != set(source_headers):
            raise AssertionError(
                f"Column mismatch. HTML: {sorted(headers)}; Parquet: {sorted(source_headers)}. "
                "If the source contains extra columns or differently named aggregates, define explicit mapping."
            )
        if any(len(row) != len(headers) for row in plotly_rows):
            raise AssertionError("HTML row width does not match headers")
        parquet_df.columns = source_headers
        actual = Counter(tuple(canonical(v) for v in row) for row in plotly_rows)
        expected = Counter(
            tuple(canonical(v) for v in row)
            for row in parquet_df[headers].itertuples(index=False, name=None)
        )
        missing_in_html = expected - actual
        extra_in_html = actual - expected
        if missing_in_html or extra_in_html:
            def examples(items):
                return [dict(zip(headers, row), occurrences=count) for row, count in list(items.items())[:int(sample_limit)]]
            raise AssertionError(
                f"Data mismatch. HTML rows={sum(actual.values())}, Parquet rows={sum(expected.values())}.\n"
                f"Missing in HTML: {sum(missing_in_html.values())}, samples: {examples(missing_in_html)}\n"
                f"Extra in HTML: {sum(extra_in_html.values())}, samples: {examples(extra_in_html)}"
            )
        print(f"PASS: HTML and Parquet match: {sum(actual.values())} rows, {len(headers)} columns")
