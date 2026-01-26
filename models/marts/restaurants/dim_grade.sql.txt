{{ config(materialized="table") }}

WITH grades AS (
    SELECT DISTINCT
        grade,
        grade_date
    FROM {{ ref('stg_restaurant_inspections') }}
    WHERE grade IS NOT NULL
),

dim AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key([
            "grade"
        ]) }} AS grade_id,
        grade,
        -- Status: A/B/C etc.
        CASE
            WHEN grade IN ('A','B','C') THEN 'Standard Grade'
            WHEN grade = 'N' THEN 'Not Yet Graded'
            WHEN grade = 'Z' THEN 'Grade Pending'
            WHEN grade = 'P' THEN 'Reopening Pending'
            ELSE 'Unknown'
        END AS grade_status,
        grade_date
    FROM grades
)

SELECT * FROM dim
