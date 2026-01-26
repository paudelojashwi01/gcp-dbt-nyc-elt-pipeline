-- Distinct location + address type combinations
WITH types AS (
    SELECT DISTINCT
        location_type,
        address_type
    FROM {{ ref('stg_rodent_complaints') }}
),

dim AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['location_type','address_type']) }} AS typeID,
        location_type,
        address_type
    FROM types
)

SELECT *
FROM dim
