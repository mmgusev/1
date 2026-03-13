-- Create/update a non-admin application role and grant it access to the DB objects.
-- This script is intended to be re-runnable.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user LOGIN PASSWORD 'app_pass_ChangeMe!';
  ELSE
    ALTER ROLE app_user WITH LOGIN PASSWORD 'app_pass_ChangeMe!';
  END IF;
END
$$;

-- NOTE: Database `shop_demo` is created by the Postgres image via POSTGRES_DB.
-- When used in Docker init, this script will run inside that DB already.

GRANT CONNECT ON DATABASE shop_demo TO app_user;

GRANT USAGE ON SCHEMA public TO app_user;

-- Existing objects
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO app_user;