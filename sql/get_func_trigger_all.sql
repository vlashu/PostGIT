SELECT 
  p.oid,
  n.nspname as "Schema",
  n.oid,
  p.proname as "Name",
 CASE
  --WHEN p.proisagg THEN 'agg'
  --WHEN p.proiswindow THEN 'window'
  WHEN p.prorettype = 'pg_catalog.trigger'::pg_catalog.regtype THEN 'trigger_func'
  ELSE 'func'
 END as "Type",
  p.proowner,
  pg_catalog.pg_get_function_result(p.oid) as "Result data type",
  pg_catalog.pg_get_function_arguments(p.oid) as "Argument data types"

FROM pg_catalog.pg_proc p
     LEFT JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
WHERE --pg_catalog.pg_function_is_visible(p.oid) AND
       n.nspname <> 'pg_catalog'
      AND n.nspname <> 'information_schema'
ORDER BY 1, 2, 4;
