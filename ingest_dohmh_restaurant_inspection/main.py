import os
import time
from datetime import datetime
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from sodapy import Socrata
from dateutil import parser


SOCRATA_HOST = "data.cityofnewyork.us"
SOCRATA_DATASET_ID = "SOCRATA_DATASET_ID"
CHUNK_SIZE = 5000
ORDER_BY_FIELD = "camis"
SOCRATA_WHERE_CLAUSE = ""

SOCRATA_APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN")

BQ_PROJECT_ID = "GCP_PROJECT"
BQ_DATASET_ID = "BIGQUERY_DATASET"
BQ_TABLE_ID = "BIGQUERY_TABLE"


bq_client = bigquery.Client(project=BQ_PROJECT_ID)



CORE_BQ_SCHEMA = [
    SchemaField("camis", "STRING", description="Unique identifier code for the restaurant (CAMIS ID)"),
    SchemaField("dba", "STRING", description="Doing‑Business-As (restaurant trade name)"),
    SchemaField("boro", "STRING", description="Borough of the restaurant"),
    SchemaField("building", "STRING", description="Building number of the address"),
    SchemaField("street", "STRING", description="Street name of the address"),
    SchemaField("zipcode", "STRING", description="ZIP code of the restaurant’s address"),
    SchemaField("phone", "STRING", description="Phone number of the restaurant"),
    SchemaField("cuisine_description", "STRING", description="Description of the cuisine (e.g., Italian, Chinese)"),
    SchemaField("inspection_date", "TIMESTAMP", description="Date of the inspection; 1/1/1900 means no inspection yet"),
    SchemaField("action", "STRING", description="Actions associated with inspection; e.g., violations cited, no violations, establishment reopened or closed"),
    SchemaField("violation_code", "STRING", description="Violation code associated with inspection"),
    SchemaField("violation_description", "STRING", description="Description of the violation"),
    SchemaField("critical_flag", "STRING", description="Indicator of critical violation; Critical / Not Critical / Not Applicable"),
    SchemaField("score", "FLOAT", description="Total inspection score; lower is better"),
    SchemaField("grade", "STRING", description="Grade associated with the inspection; A, B, C, N, Z, or P"),
    SchemaField("grade_date", "TIMESTAMP", description="Date when the grade was issued"),
]


def clean_record(record):
    cleaned = {}

    for key, value in record.items():
        if key.startswith(":") or "__computed_region" in key:
            continue

        clean_key = key.lower().replace(" ", "").replace(":", "").replace("@", "_")

        if value in ["", None]:
            cleaned[clean_key] = None
        else:
            try:
                if clean_key in ["score"]:
                    cleaned[clean_key] = float(value)
                elif clean_key in ["inspection_date", "grade_date"]:
                    # convert datetime to ISO string
                    dt = parser.parse(value)
                    cleaned[clean_key] = dt.isoformat()
                else:
                    cleaned[clean_key] = str(value)

            except Exception as e:
                print(f"Error cleaning key {clean_key} with value {value}: {e}")
                cleaned[clean_key] = None

        if "zip" in clean_key and cleaned.get(clean_key) is not None:
            cleaned[clean_key] = str(cleaned[clean_key])

    return cleaned


def get_current_offset():
       query = f"SELECT COUNT(*) AS count FROM `{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}`"
    try:
        res = list(bq_client.query(query).result())[0]
        return res.count
    except Exception as e:
        print("Error getting offset, defaulting to 0:", e)
        return 0

def update_bq_schema_if_needed(table_ref, data):
    try:
        table = bq_client.get_table(table_ref)
        existing = {f.name for f in table.schema}
        incoming = set()
        for row in data:
            incoming.update(row.keys())

        new_fields = incoming - existing

        if new_fields:
            print("New fields detected, adding to schema:", new_fields)
            new_schema = list(table.schema)
            for f in sorted(new_fields):
                # Dynamically add the new field as a STRING
                new_schema.append(SchemaField(f, "STRING", description="Dynamically added from Socrata"))

            table.schema = new_schema
            # Update the table's schema in BigQuery
            bq_client.update_table(table, ["schema"])
            return True
        return False
    except Exception as e:
        print("Schema update error:", e)
        return False


def load_data_to_bigquery(data):
    table_ref = bq_client.dataset(BQ_DATASET_ID).table(BQ_TABLE_ID)
    # Print sample rows for debugging
    print("Sample cleaned rows before insertion:")
    for row in data[:5]:
        print(row)

    try:
        bq_client.get_dataset(BQ_DATASET_ID)
    except Exception:
        print("Dataset not found. Creating dataset:", BQ_DATASET_ID)
        bq_client.create_dataset(bigquery.Dataset(f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}"))

    try:
        bq_client.get_table(table_ref)
    except Exception:
        print("Table not found. Creating table with core schema.")
        table = bigquery.Table(table_ref, schema=CORE_BQ_SCHEMA)
        bq_client.create_table(table)

    update_bq_schema_if_needed(table_ref, data)

    for attempt in range(3):
        errors = bq_client.insert_rows_json(table_ref, data)
        if not errors:
            print("Successfully loaded rows:", len(data))
            return True
        print(f"Attempt {attempt+1}: Errors inserting rows:")
        for err in errors:
            print(err)
        time.sleep(5)

    print("Failed to insert after retries")
    return False


def ingest_socrata_data(request):
    print("Starting ingestion at", datetime.now().isoformat())

    if not SOCRATA_APP_TOKEN:
        print("Missing Socrata token")
        return ("Missing Socrata token", 500)

    # Determine where to start fetching data from Socrata
    offset = get_current_offset()
    print("Offset:", offset)

    # Initialize Socrata client
    client = Socrata(SOCRATA_HOST, SOCRATA_APP_TOKEN, timeout=300)
    
    # Socrata API query parameters
    params = {
        "$limit": CHUNK_SIZE,
        "$offset": offset,
        "$order": f"{ORDER_BY_FIELD} ASC",
    }
    if SOCRATA_WHERE_CLAUSE:
        params["$where"] = SOCRATA_WHERE_CLAUSE

    # Fetch data from Socrata
    try:
        print(f"Fetching {CHUNK_SIZE} rows from offset {offset}")
        data = client.get(SOCRATA_DATASET_ID, **params)
    except Exception as e:
        return (f"API fetch error: {e}", 500)
    finally:
        client.close() # Always close the client connection

    if not data:
        print("No new data to load.")
        return ("No new data", 200)

    # Clean and load data
    print(f"Received {len(data)} records. Cleaning and loading...")
    cleaned = [clean_record(r) for r in data]
    success = load_data_to_bigquery(cleaned)
    
    if not success:
        return ("BigQuery loading failed", 500)

    print("Ingestion complete")
    return ("OK", 200)
