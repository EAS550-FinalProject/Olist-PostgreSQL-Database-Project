DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'analyst_role') THEN
        CREATE ROLE analyst_role NOLOGIN;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user_role') THEN
        CREATE ROLE app_user_role NOLOGIN;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO analyst_role;
GRANT USAGE ON SCHEMA public TO app_user_role;


GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analyst_role;


GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO app_user_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO app_user_role;
