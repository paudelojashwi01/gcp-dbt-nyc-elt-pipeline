{{ config(materialized="table") }}

WITH restaurants AS (
    SELECT DISTINCT
        camis,
        dba,
        cuisine_description,
        phone,
        building,
        street,
        bin
    FROM {{ ref('stg_restaurant_inspections') }}
    WHERE camis IS NOT NULL
),

dim AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key([
            "camis", 
            "dba",
            "cuisine_description",
            "building",
            "street"
        ]) }} AS restaurant_id,
        camis,
        dba,
        cuisine_description,
        phone,
        building,
        street,
        bin
    FROM restaurants
)

SELECT * FROM dim
