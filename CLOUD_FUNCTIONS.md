# Google Cloud Functions for NYC Analytics Project

This document describes the Google Cloud Functions used in this project to fetch and update NYC open data into BigQuery.

---

## Function: `ingest_socrata_data`

**Purpose:**  
Fetches NYC open data from the Socrata API and loads it into BigQuery. Used for : 
- NYC 311 rodent complaint data
- DOHMH restaurant inspection data 

**Files:**  
- `main.py` → contains the function logic  
- `requirements.txt` → lists Python dependencies

**Trigger:**  
HTTP Trigger

**Input Parameters:**  
- Optional query parameters (e.g., `start_date`, `end_date`) can be passed in the HTTP request.

**Output:**  
- Writes to BigQuery table: `your_dataset_name.your_table_name`
- Automatically creates the table if it does not exist.

**Environment Variables:** 
SOCRATA_APP_TOKEN -> API token for Socrata 
