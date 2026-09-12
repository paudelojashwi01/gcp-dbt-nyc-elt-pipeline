# GCP + dbt NYC ELT Pipeline

## Overview 
An end-to-end analytics engineering project integrating NYC 311 rodent complaints with DOHMH restaurant inspection results to answer a real public-health question: does neighborhood rodent activity predict restaurant food-safety outcomes?

Live Dashboard → https://tinyurl.com/4297rz9s 

## Key findings (2023–2024, ~250K inspections / ~80K complaints) 

**Does neighborhood rodent activity predict restaurant grades?**	
Weak but real effect.
A-grade rate declines from 39.6% (low-rodent ZIPs) to 33.0% (high-rodent ZIPs). 
Correlation r ≈ 0.08–0.11 
Statistically present, practically small.

**Does cuisine type matter more than location?**	
Yes, rodent-related violation rates range 17–26% across cuisine types, a stronger and more consistent pattern than the location effect, holding across 50+ ZIP codes per cuisine.

**Is the city's rodent problem getting better or worse?**
The problem is improving, every borough saw fewer complaints in 2024 than 2023 (Manhattan: -8.4%).

**Where should intervention be targeted?**
13 ZIP codes show both top-quartile rodent complaints and top-quartile low-grade rates simultaneously concentrated in the Bronx.

## Architecture

- **Source data:** NYC Open Data (Socrata API) — 311 rodent complaints and DOHMH restaurant inspection results
- **Ingestion:** Google Cloud Functions, triggered on a schedule by Cloud Scheduler
- **Raw storage:** BigQuery raw tables, minimal transformation and preserves original source structure as a reference point
- **Transformation (staging):** dbt staging models: clean, filter, cast, and deduplicate the raw data
- **Transformation (mart):** dbt dimensional mart: following star schema with 2 fact tables (restaurant inspections, rodent complaints) and 6 dimension tables (date, location, restaurant, grade, violation type, location type); shared date/location dimensions let both datasets be analyzed together
- **Visualization:** Looker Studio:  stakeholder-facing dashboards for DOHMH policymakers, restaurant owners, and residents


## Tech Stack 
- GCP: BigQuery, Cloud Functions, Cloud Scheduler
- dbt Cloud 
- SQL
- Python 
- Looker Studio 

## Data Sources 
- NYC 311 Rodent Complaints 
- DOHMH Restaurant Inspection Results


