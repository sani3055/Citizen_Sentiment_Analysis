"""Print the expected row count for the configured case-normalized 311 query."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.socrata_client import SocrataClient


rsat = pd.read_parquet("data/raw/rsat_raw.parquet")
services = {str(value).upper() for value in rsat["complaint_type"].value_counts().head(20).index}
quoted = ", ".join("'" + value.replace("'", "''") + "'" for value in services)
where = (
    "status = 'Closed' AND closed_date IS NOT NULL "
    "AND created_date >= '2023-01-01T00:00:00.000' "
    "AND created_date <= '2024-12-31T23:59:59.999' "
    "AND borough in ('BRONX','BROOKLYN','MANHATTAN','QUEENS','STATEN ISLAND') "
    f"AND upper(complaint_type) in ({quoted})"
)
client = SocrataClient("https://data.cityofnewyork.us/resource/erm2-nwe9.json")
print(client.fetch_count(where))
