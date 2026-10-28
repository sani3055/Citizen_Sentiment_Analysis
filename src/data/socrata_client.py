"""
Socrata API client for paginated retrieval of NYC Open Data datasets.
Supports RSAT (5ijn-vbdv) and NYC 311 Service Requests (erm2-nwe9).
"""

import os
import time
import logging
from typing import Dict, Any, Iterable, List, Optional
import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class SocrataClient:
    """Robust paginated Socrata API client with automatic retries and backoff."""

    def __init__(
        self,
        base_url: str,
        app_token: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 5,
        backoff_factor: float = 1.5,
        page_size: int = 50000,
        sleep_between_pages: float = 0.5,
    ):
        self.base_url = base_url
        self.app_token = app_token
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.page_size = page_size
        self.sleep_between_pages = sleep_between_pages
        self.session = requests.Session()
        if self.app_token:
            self.session.headers.update({"X-App-Token": self.app_token})

    def fetch_page(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch a single page with retries and exponential backoff."""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(self.base_url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait_time = self.backoff_factor ** attempt * 2
                    logger.warning(f"Rate limited (429). Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    logger.warning(
                        f"HTTP {response.status_code}: {response.text[:200]}. Attempt {attempt}/{self.max_retries}"
                    )
                    time.sleep(self.backoff_factor ** attempt)
            except (requests.RequestException, Exception) as exc:
                logger.warning(f"Request error: {exc}. Attempt {attempt}/{self.max_retries}")
                time.sleep(self.backoff_factor ** attempt)

        raise RuntimeError(f"Failed to fetch data from {self.base_url} after {self.max_retries} attempts.")

    def fetch_all(
        self,
        where_clause: Optional[str] = None,
        select_clause: Optional[str] = None,
        order_clause: str = ":id",
        max_records: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Paginates through Socrata endpoint using $limit and $offset.
        Returns accumulated records as a pandas DataFrame.
        """
        all_records = []
        offset = 0

        logger.info(f"Starting fetch from {self.base_url} (where='{where_clause}', limit_per_page={self.page_size})")

        while True:
            params = {
                "$limit": self.page_size,
                "$offset": offset,
            }
            if where_clause:
                params["$where"] = where_clause
            if select_clause:
                params["$select"] = select_clause
            if order_clause:
                params["$order"] = order_clause

            records = self.fetch_page(params)
            num_fetched = len(records)
            all_records.extend(records)
            offset += num_fetched

            logger.info(f"Fetched {num_fetched} rows (total accumulated: {len(all_records):,})")

            if num_fetched < self.page_size:
                logger.info("Reached end of available records.")
                break

            if max_records and len(all_records) >= max_records:
                logger.info(f"Reached specified max_records limit ({max_records:,}).")
                all_records = all_records[:max_records]
                break

            time.sleep(self.sleep_between_pages)

        if not all_records:
            return pd.DataFrame()

        df = pd.DataFrame(all_records)
        logger.info(f"Completed download. Total records: {len(df):,}, Columns: {list(df.columns)}")
        return df

    def fetch_count(self, where_clause: Optional[str] = None) -> int:
        """Return the server-side row count for a filtered Socrata query."""
        params: Dict[str, Any] = {"$select": "count(*) as count"}
        if where_clause:
            params["$where"] = where_clause
        rows = self.fetch_page(params)
        if not rows:
            return 0
        return int(rows[0]["count"])

    def iter_pages(
        self,
        where_clause: Optional[str] = None,
        select_clause: Optional[str] = None,
        order_clause: str = ":id",
        max_records: Optional[int] = None,
    ) -> Iterable[List[Dict[str, Any]]]:
        """Yield stable, ordered pages without accumulating the full result in RAM."""
        offset = 0
        while True:
            limit = self.page_size
            if max_records is not None:
                remaining = max_records - offset
                if remaining <= 0:
                    break
                limit = min(limit, remaining)

            params: Dict[str, Any] = {"$limit": limit, "$offset": offset}
            if where_clause:
                params["$where"] = where_clause
            if select_clause:
                params["$select"] = select_clause
            if order_clause:
                params["$order"] = order_clause

            records = self.fetch_page(params)
            if not records:
                break
            yield records
            offset += len(records)
            logger.info("Fetched %d rows (streamed total: %s)", len(records), f"{offset:,}")
            if len(records) < limit:
                break
            time.sleep(self.sleep_between_pages)

    def fetch_all_to_parquet(
        self,
        output_path: str,
        where_clause: Optional[str] = None,
        select_clause: Optional[str] = None,
        order_clause: str = ":id",
        max_records: Optional[int] = None,
    ) -> int:
        """Stream a complete Socrata result to one Parquet file atomically.

        Every selected column is stored as a nullable string so page-specific
        missing values cannot change the Parquet schema.  The final file is
        installed only after all pages have been written successfully.
        """
        if not select_clause:
            raise ValueError("select_clause is required for deterministic Parquet output")

        columns = [part.strip() for part in select_clause.split(",")]
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        partial_path = output_path + ".part"
        if os.path.exists(partial_path):
            os.remove(partial_path)

        writer = None
        total = 0
        try:
            for records in self.iter_pages(
                where_clause=where_clause,
                select_clause=select_clause,
                order_clause=order_clause,
                max_records=max_records,
            ):
                frame = pd.DataFrame.from_records(records).reindex(columns=columns)
                for column in columns:
                    frame[column] = frame[column].astype("string")
                table = pa.Table.from_pandas(frame, preserve_index=False)
                if writer is None:
                    writer = pq.ParquetWriter(partial_path, table.schema, compression="snappy")
                writer.write_table(table)
                total += len(frame)
        finally:
            if writer is not None:
                writer.close()

        if total == 0:
            if os.path.exists(partial_path):
                os.remove(partial_path)
            raise RuntimeError("Socrata query returned zero rows; refusing to replace the dataset")

        os.replace(partial_path, output_path)
        logger.info("Completed streamed download: %s rows -> %s", f"{total:,}", output_path)
        return total
