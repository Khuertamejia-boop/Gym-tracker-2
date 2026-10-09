-- =====================================================================
-- HISTORIAS DE 24 H · PARTE 1 de 2
-- Añade «story» a los tipos de reporte. Ejecútala SOLA y espera el "Success".
-- Al final muestra los tipos que existen: deben salir user, workout, avatar y story.
-- =====================================================================
do $$
declare
  sch text;
  typ text;
begin
  select udt_schema, udt_name into sch, typ
    from information_schema.columns
   where table_schema = 'public' and table_name = 'reports' and column_name = 'target_type';
  if typ is null then
    raise exception 'No encuentro la columna reports.target_type';
  end if;
  if not exists (
    select 1 from pg_enum e
      join pg_type t on t.oid = e.enumtypid
      join pg_namespace n on n.oid = t.typnamespace
     where n.nspname = sch and t.typname = typ and e.enumlabel = 'story'
  ) then
    execute format('alter type %I.%I add value %L', sch, typ, 'story');
  end if;
end $$;

select e.enumlabel as tipos_de_reporte
  from pg_enum e
  join pg_type t on t.oid = e.enumtypid
 where t.typname = (select udt_name from information_schema.columns
                     where table_schema = 'public' and table_name = 'reports' and column_name = 'target_type')
 order by e.enumsortorder;
