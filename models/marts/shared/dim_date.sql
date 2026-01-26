WITH dates AS (
    SELECT DISTINCT
        DATE(inspection_date) AS full_date
    FROM {{ ref('stg_restaurant_inspections') }}
    WHERE inspection_date IS NOT NULL

    UNION DISTINCT

    SELECT DISTINCT
        DATE(created_date) AS full_date
    FROM {{ ref('stg_rodent_complaints') }}
    WHERE created_date IS NOT NULL
),

expanded AS (
    SELECT
        full_date,
        EXTRACT(YEAR FROM full_date) AS year,
        EXTRACT(QUARTER FROM full_date) AS quarter,
        EXTRACT(MONTH FROM full_date) AS month,
        FORMAT_DATE('%B', full_date) AS month_name,
        EXTRACT(DAY FROM full_date) AS day,
        EXTRACT(DAYOFWEEK FROM full_date) AS day_of_week,
        FORMAT_DATE('%A', full_date) AS day_name,
        CASE WHEN EXTRACT(DAYOFWEEK FROM full_date) IN (1,7) THEN TRUE ELSE FALSE END AS is_weekend
    FROM dates
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['full_date']) }} AS date_id,
    *
FROM expanded
