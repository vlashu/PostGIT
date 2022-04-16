SELECT t.oid, n.nspname, pgc.relnamespace, tgname, 'trigger' obj_type, pgc.relowner
FROM pg_catalog.pg_trigger t
join pg_class pgc on t.tgrelid = pgc.oid
LEFT JOIN pg_catalog.pg_namespace n ON n.oid = pgc.relnamespace
WHERE --t.tgrelid = '470805' AND 
(NOT t.tgisinternal OR (t.tgisinternal AND t.tgenabled = 'D'))
ORDER BY 1;