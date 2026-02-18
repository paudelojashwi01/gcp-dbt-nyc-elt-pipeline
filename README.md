# GCP + dbt NYC ELT Pipeline

## Overview 
This project implements an end to end ELT pipeline using GCP and dbt to integrate NYC 311 rodent complaints with restaurant inspection data. The data is modeled in BigQuery using a star schema to support public health analytics and visualization. 

## Tech Stack 
- GCP: BigQuery, Cloud Functions, Cloud Scheduler
- dbt Cloud 
- SQL
- Python 
- Looker Studio 

## Data Sources 
- NYC 311 Rodent Complaints 
- DOHMH Restaurant Inspection Results

## Architecture 
The warehouse was designed using a Kimball process for query optimization for the particular use cases. 

