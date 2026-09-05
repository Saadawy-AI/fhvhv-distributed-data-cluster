"""Merge the twelve 2025 FHVHV Parquet files without loading them all in memory."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


DATA_DIR = Path("data")
OUTPUT = DATA_DIR / "fhvhv_tripdata_2025.parquet"
TEMP_OUTPUT = DATA_DIR / "fhvhv_tripdata_2025.partial.parquet"
FILES = sorted(DATA_DIR.glob("fhvhv_tripdata_2025-*.parquet"))
BATCH_SIZE = 262_144


def main() -> None:
    if len(FILES) != 12:
        raise RuntimeError(f"Expected 12 monthly files, found {len(FILES)}")
    if OUTPUT.exists() or TEMP_OUTPUT.exists():
        raise RuntimeError(f"Refusing to overwrite existing output: {OUTPUT}")

    schema = pq.ParquetFile(FILES[0]).schema_arrow
    for source in FILES[1:]:
        if pq.ParquetFile(source).schema_arrow != schema:
            raise RuntimeError(f"Schema differs: {source}")

    rows_written = 0
    with pq.ParquetWriter(TEMP_OUTPUT, schema, compression="snappy") as writer:
        for source in FILES:
            source_rows = 0
            for batch in pq.ParquetFile(source).iter_batches(batch_size=BATCH_SIZE):
                writer.write_table(pa.Table.from_batches([batch], schema=schema))
                source_rows += batch.num_rows
            rows_written += source_rows
            print(f"Merged {source.name}: {source_rows:,} rows", flush=True)

    TEMP_OUTPUT.replace(OUTPUT)
    print(f"Created {OUTPUT} with {rows_written:,} rows", flush=True)


if __name__ == "__main__":
    main()
