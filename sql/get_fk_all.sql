-- Список внешних ключей

SELECT conrelid, confrelid, conname, 
       pg_catalog.pg_get_constraintdef(oid, true) AS condef,
	   conrelid::pg_catalog.regclass AS ontable
  FROM pg_catalog.pg_constraint
WHERE confrelid IN (SELECT c.oid
				FROM pg_catalog.pg_class c
				 LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
				WHERE c.relkind IN ('r','p','v','m','f','')
     				 AND n.nspname <> 'pg_catalog'
      					AND n.nspname !~ '^pg_toast'
     					 AND n.nspname <> 'information_schema'
						)  AND contype = 'f'

UNION

SELECT r.conrelid, r.confrelid, conname,
  pg_catalog.pg_get_constraintdef(r.oid, true) as condef,
  conrelid::pg_catalog.regclass AS ontable
FROM pg_catalog.pg_constraint r
WHERE r.conrelid IN (SELECT c.oid
				FROM pg_catalog.pg_class c
				 LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
				WHERE c.relkind IN ('r','p','v','m','f','')
     				 AND n.nspname <> 'pg_catalog'
      					AND n.nspname !~ '^pg_toast'
     					 AND n.nspname <> 'information_schema'
						)  AND r.contype = 'f'
ORDER BY conname
