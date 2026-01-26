{{ config(materialized="table") }}

WITH base AS (
    SELECT
        *,
        DATE(inspection_date) AS inspection_dt,
        DATE(record_date) AS record_dt
    FROM {{ ref('stg_restaurant_inspections') }}
),

final AS (
    SELECT
        -- Fact-level surrogate key
        {{ dbt_utils.generate_surrogate_key([
            'camis',
            'inspection_date',
            'violation_code'
        ]) }} AS fact_id,

        -- Foreign keys
        {{ dbt_utils.generate_surrogate_key(['inspection_dt']) }} AS date_id,
        {{ dbt_utils.generate_surrogate_key(['boro','zipcode','community_board']) }} AS location_id,
        {{ dbt_utils.generate_surrogate_key(['camis']) }} AS restaurant_id,
        {{ dbt_utils.generate_surrogate_key(['violation_code']) }} AS violation_type_id,
        {{ dbt_utils.generate_surrogate_key(['grade']) }} AS grade_id,

        -- Inspection type stays IN FACT (no dimension)
        inspection_type,

        -- Fact measures + grain attributes
        record_date,
        action,
        score AS inspection_score,

        -- Flags
        (violation_code IS NOT NULL) AS has_violation,

        -- TRUE if description mentions rodents/pests
        CASE
            WHEN LOWER(violation_description) LIKE '%rodent%'
              OR LOWER(violation_description) LIKE '%mice%'
              OR LOWER(violation_description) LIKE '%rats%'
            THEN TRUE
            ELSE FALSE
        END AS pest_violation_flag

    FROM base
)

SELECT *
FROM final
