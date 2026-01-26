{{ config(materialized='table') }}

WITH raw AS (
    SELECT
        camis,
        dba,
        boro,
        building,
        street,
        zipcode,
        phone,
        cuisine_description,

        inspection_date,

        action,
        violation_code,
        violation_description,
        critical_flag,
        score,
        grade,
        grade_date,
        bbl,
        bin,
        census_tract,
        community_board,
        council_district,
        inspection_type,
        latitude,
        longitude,
        location,
        nta,

        SAFE_CAST(record_date AS STRING) AS record_date

    FROM {{ source('restaurant_sources', 'source_restaurant_inspections') }}

    WHERE inspection_date BETWEEN '2022-10-01' AND '2025-12-31'
)

SELECT *
FROM raw
