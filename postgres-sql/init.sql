DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'appuser') THEN
        CREATE ROLE appuser LOGIN PASSWORD 'app_password';
    END IF;
END $$;

REVOKE ALL ON DATABASE mydb FROM PUBLIC;

GRANT CONNECT ON DATABASE mydb TO appuser;

\connect mydb

REVOKE ALL ON SCHEMA public FROM PUBLIC;

GRANT USAGE ON SCHEMA public TO appuser;

CREATE TABLE IF NOT EXISTS test_data (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL
);

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE test_data TO appuser;

GRANT USAGE ON SEQUENCE test_data_id_seq TO appuser;