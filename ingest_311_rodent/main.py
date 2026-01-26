import os
import json
import time
from datetime import datetime
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from sodapy import Socrata


SOCRATA_HOST = "data.cityofnewyork.us"
SOCRATA_DATASET_ID = "DATASET_ID"
CHUNK_SIZE = 5000
ORDER_BY_FIELD = "created_date"
SOCRATA_WHERE_CLAUSE = ""

SOCRATA_APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN")


BQ_PROJECT_ID = "GCP_PROJECT"
BQ_DATASET_ID = "BIGQUERY_DATASET"
BQ_TABLE_ID = "BIGQUERY_TABLE"

bq_client = bigquery.Client(project=BQ_PROJECT_ID)


CORE_BQ_SCHEMA = [
    SchemaField("created_date", "TIMESTAMP"),
    SchemaField("agency", "STRING"),
    SchemaField("agency_name", "STRING"),
    SchemaField("complaint_type", "STRING"),
    SchemaField("descriptor", "STRING"),
    SchemaField("location_type", "STRING"),
    SchemaField("address_type", "STRING"),
    SchemaField("city", "STRING"),
    SchemaField("borough", "STRING"),
    SchemaField("latitude", "FLOAT"),
    SchemaField("longitude", "FLOAT"),
]



def clean_record(record):
    cleaned = {}

    for key, value in record.items():

        # remove Socrata metadata
        if key.startswith(":") or key in ["location"] or "__computed_region" in key:
            continue

        clean_key = (
            key.lower()
            .replace(":", "_")
            .replace("@", "_")
            .replace(" ", "_")
        )

        if value == "":
            cleaned[clean_key] = None
        else:
            cleaned[clean_key] = value

        # ZIP fix
        if "zip" in clean_key and cleaned.get(clean_key) is not None:
            cleaned[clean_key] = str(cleaned[clean_key])

        # TIMESTAMP fix
        if clean_key == "created_date" and value:
            try:
                cleaned[clean_key] = value.replace("T", " ")
            except:
                cleaned[clean_key] = None

    return cleaned



def get_current_offset():
    query = f"""
        SELECT COUNT(*) AS count
        FROM `{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}`
    """
    try:
        result = list(bq_client.query(query).result())[0]
        return result.count
    except Exception:
        return 0


def update_bq_schema_if_needed(table_ref, data):
    try:
        table = bq_client.get_table(table_ref)
        current_fields = {field.name for field in table.schema}

        incoming_fields = set()
        for row in data:
            incoming_fields.update(row.keys())

        new_fields = incoming_fields - current_fields
        if not new_fields:
            return False

        new_schema = list(table.schema)
        for f in sorted(new_fields):
            new_schema.append(
                SchemaField(f, "STRING", description="Auto-added")
            )

        table.schema = new_schema
        bq_client.update_table(table, ["schema"])
        print(f"Updated schema with fields: {new_fields}")
        return True

    except Exception as e:
        print(f"Schema update error: {e}")
        return False


def load_data_to_bigquery(cleaned_data):
    table_ref = bigquery.TableReference(
        bigquery.DatasetReference(BQ_PROJECT_ID, BQ_DATASET_ID),
        BQ_TABLE_ID,
    )

    # Ensure dataset exists
    try:
        bq_client.get_dataset(BQ_DATASET_ID)
    except:
        dataset = bigquery.Dataset(f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}")
        bq_client.create_dataset(dataset)

    # Ensure table exists
    try:
        bq_client.get_table(table_ref)
    except:
        table = bigquery.Table(table_ref, schema=CORE_BQ_SCHEMA)
        bq_client.create_table(table)
        print("Created table")

    # Update schema (if needed)
    schema_updated = update_bq_schema_if_needed(table_ref, cleaned_data)

    # Insert with retries
    retries = 3
    for i in range(retries):
        errors = bq_client.insert_rows_json(table_ref, cleaned_data)

        if not errors:
            print(f"Inserted {len(cleaned_data)} rows.")
            return True

        print("Insert error:", errors)
        time.sleep(4)

    return False


def ingest_socrata_data(request):
    print("Starting ingestion:", datetime.now())

    offset = get_current_offset()
    print(f"Current offset = {offset}")

    # Socrata Client
    client = Socrata(
        SOCRATA_HOST,
        SOCRATA_APP_TOKEN,
        timeout=300,
    )

    params = {
        "$limit": CHUNK_SIZE,
        "$offset": offset,
        "$order": f"{ORDER_BY_FIELD} ASC",
    }

    if SOCRATA_WHERE_CLAUSE:
        params["$where"] = SOCRATA_WHERE_CLAUSE

    print("Fetching with params:", params)

    try:
        data = client.get(SOCRATA_DATASET_ID, **params)
    except Exception as e:
        return (f"API error: {e}", 500)

    client.close()

    if not data:
        print("No new rows. Up to date.")
        return ("No new data", 200)

    print(f"Fetched {len(data)} rows")

    cleaned = [clean_record(r) for r in data]

    success = load_data_to_bigquery(cleaned)

    if not success:
        return ("Failed loading to BigQuery", 500)

    print("Ingestion complete")
    return ("Success", 200)
