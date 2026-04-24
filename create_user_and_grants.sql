-- This script runs inside the already-created shop_demo database.
-- Docker Compose sets POSTGRES_DB=shop_demo, so the database exists before
-- these init scripts are executed.  We only need to create the app user and
-- grant the necessary privileges.

CREATE USER app_user WITH PASSWORD 'app_pass_ChangeMe!';

GRANT CONNECT ON DATABASE shop_demo TO app_user;
GRANT USAGE  ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Ensure future tables created by superuser are also accessible
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO app_user;
