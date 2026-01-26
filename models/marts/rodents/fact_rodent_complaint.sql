WITH base AS (
    SELECT
        *,
        DATE(created_date) AS created_dt
    FROM {{ ref('stg_rodent_complaints') }}
),

final AS (
    SELECT
        -- Fact table PK
        {{ dbt_utils.generate_surrogate_key([
            'rodent_complaint_id'
        ]) }} AS complaintID,

        -- Foreign Key → Dim_Date
        {{ dbt_utils.generate_surrogate_key(['created_dt']) }} AS date_id,

        -- Foreign Key → Dim_Location
        {{ dbt_utils.generate_surrogate_key([
            'borough',
            'zipcode',
            'community_board'
        ]) }} AS location_id,

        -- Foreign Key → Dim_Location_Type
        {{ dbt_utils.generate_surrogate_key([
            'location_type',
            'address_type'
        ]) }} AS typeID,

        -- Fact attributes
        descriptor AS complaint_descriptor,
        latitude,
        longitude

    FROM base
)

SELECT *
FROM final
