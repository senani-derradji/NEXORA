DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'nexorauser') THEN
      CREATE ROLE nexorauser WITH LOGIN PASSWORD 'nexorapass';
   END IF;
END
$$;

ALTER ROLE nexorauser WITH SUPERUSER CREATEDB CREATEROLE LOGIN;

ALTER DATABASE nexoradb OWNER TO nexorauser;