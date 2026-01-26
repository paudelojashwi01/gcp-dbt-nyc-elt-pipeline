-- 1. Extract restaurant locations
WITH restaurant_loc AS (
    SELECT DISTINCT
        SAFE_CAST(boro AS STRING) AS boro,
        SAFE_CAST(zipcode AS STRING) AS zipcode,
        CAST(NULL AS STRING) AS community_board   -- FIXED
    FROM {{ ref('stg_restaurant_inspections') }}
    WHERE zipcode IS NOT NULL
),

-- 2. Extract rodent locations
rodent_loc AS (
    SELECT DISTINCT
        SAFE_CAST(borough AS STRING) AS boro,
        SAFE_CAST(zipcode AS STRING) AS zipcode,
        SAFE_CAST(community_board AS STRING) AS community_board
    FROM {{ ref('stg_rodent_complaints') }}
    WHERE zipcode IS NOT NULL
),

-- 3. Union (now types match)
unioned AS (
    SELECT boro, zipcode, community_board
    FROM restaurant_loc
    UNION DISTINCT
    SELECT boro, zipcode, community_board
    FROM rodent_loc
),

-- 4. Dimension with surrogate key
dim AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key([
            'boro',
            'zipcode',
            'community_board'
        ]) }} AS location_id,

        boro,
        zipcode,
        community_board
    FROM unioned
)

SELECT *
FROM dim
