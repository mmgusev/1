BEGIN;

-- University domain model (minimum 4 related tables):
-- faculties -> groups -> students, plus courses, plus enrollments (students <-> courses)

-- Make script re-runnable (for local dev/tests)
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS groups CASCADE;
DROP TABLE IF EXISTS faculties CASCADE;

CREATE TABLE faculties (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE groups (
  id SERIAL PRIMARY KEY,
  faculty_id INTEGER NOT NULL REFERENCES faculties(id) ON DELETE RESTRICT,
  name TEXT NOT NULL,
  year_start INTEGER NOT NULL CHECK (year_start >= 1900 AND year_start <= 2100),
  UNIQUE (faculty_id, name, year_start)
);

CREATE TABLE students (
  id SERIAL PRIMARY KEY,
  group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE RESTRICT,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  enrolled_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE TABLE courses (
  id SERIAL PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  credits SMALLINT NOT NULL CHECK (credits > 0 AND credits <= 30)
);

CREATE TABLE enrollments (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
  semester TEXT NOT NULL,
  grade NUMERIC(5,2) NULL CHECK (grade IS NULL OR (grade >= 0 AND grade <= 100)),
  UNIQUE (student_id, course_id, semester)
);

COMMIT;