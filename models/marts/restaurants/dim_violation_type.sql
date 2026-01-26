{{ config(materialized="table") }}

WITH violations AS (
    SELECT DISTINCT
        violation_code,
        violation_description,
        critical_flag
    FROM {{ ref('stg_restaurant_inspections') }}
    WHERE violation_code IS NOT NULL
),

dim AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key([
            "violation_code"
        ]) }} AS violation_type_id,
        violation_code,
        violation_description,
        critical_flag,
        -- Derived field: pest-related?
        CASE 
            WHEN LOWER(violation_description) LIKE '%mice%'
              OR LOWER(violation_description) LIKE '%rodent%'
              OR LOWER(violation_description) LIKE '%rat%'
            THEN TRUE
            ELSE FALSE
        END AS pest_related_flag
    FROM violations
)

SELECT * FROM dim
