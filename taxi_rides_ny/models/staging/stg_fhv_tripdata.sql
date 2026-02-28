{{ config(materialized='view') }}

select
    dispatching_base_num,
    cast(pickup_datetime as timestamp) as pickup_datetime,
    cast(dropoff_datetime as timestamp) as dropoff_datetime,
    cast(pulocationid as integer) as pickup_locationid,
    cast(dolocationid as integer) as dropoff_locationid,
    sr_flag,
    affiliated_base_number
from {{ source('raw', 'fhv_tripdata') }}
where dispatching_base_num is not null