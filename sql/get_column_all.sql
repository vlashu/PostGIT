-- Список всех столбцов околотабличных объектов

SELECT a.attrelid, a.attnum, a.attname,
  pg_catalog.format_type(a.atttypid, a.atttypmod),
  (SELECT pg_catalog.pg_get_expr(d.adbin, d.adrelid, true)
   FROM pg_catalog.pg_attrdef d
   WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef),
  a.attnotnull,
  (SELECT c.collname FROM pg_catalog.pg_collation c, pg_catalog.pg_type t
   WHERE c.oid = a.attcollation AND t.oid = a.atttypid AND a.attcollation <> t.typcollation) AS attcollation,
  ''::pg_catalog.char AS attidentity,
  ''::pg_catalog.char AS attgenerated,
  a.attstorage,
  CASE WHEN a.attstattarget=-1 THEN NULL ELSE a.attstattarget END AS attstattarget,
  pg_catalog.col_description(a.attrelid, a.attnum)
FROM pg_catalog.pg_attribute a
WHERE 
  a.attrelid IN (SELECT c.oid
				FROM pg_catalog.pg_class c
				 LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
				WHERE c.relkind IN ('r','p','v','m','f','')
     				 AND n.nspname <> 'pg_catalog'
      					AND n.nspname !~ '^pg_toast'
     					 AND n.nspname <> 'information_schema'
						) 
  AND 
  a.attnum > 0 
  AND NOT a.attisdropped
ORDER BY a.attrelid, a.attnum;