with source as (
    select 
        vendorid, ratecodeid, pulocationid, dolocationid,
        lpep_pickup_datetime, lpep_dropoff_datetime,
        store_and_fwd_flag, passenger_count, trip_distance, trip_type,
        fare_amount, extra, mta_tax, tip_amount, tolls_amount,
        improvement_surcharge, total_amount, payment_type
    from {{ source('raw', 'green_tripdata') }}
),

renamed as (
    select
        cast(vendorid as integer) as vendor_id,
        {{ safe_cast('ratecodeid', 'integer') }} as rate_code_id,
        cast(pulocationid as integer) as pickup_location_id,
        cast(dolocationid as integer) as dropoff_location_id,
        cast(lpep_pickup_datetime as timestamp) as pickup_datetime,
        cast(lpep_dropoff_datetime as timestamp) as dropoff_datetime,
        cast(store_and_fwd_flag as string) as store_and_fwd_flag,
        cast(passenger_count as integer) as passenger_count,
        cast(trip_distance as numeric) as trip_distance,
        {{ safe_cast('trip_type', 'integer') }} as trip_type,
        cast(fare_amount as numeric) as fare_amount,
        cast(extra as numeric) as extra,
        cast(mta_tax as numeric) as mta_tax,
        cast(tip_amount as numeric) as tip_amount,
        cast(tolls_amount as numeric) as tolls_amount,
        cast(improvement_surcharge as numeric) as improvement_surcharge,
        cast(total_amount as numeric) as total_amount,
        {{ safe_cast('payment_type', 'integer') }} as payment_type
    from source
    where vendorid is not null
)

select * from renamed
{% if target.name == 'dev' %}
  limit 100
{% endif %}