BEGIN;

-- Make script re-runnable (for local dev/tests)
TRUNCATE TABLE
  enrollments,
  students,
  courses,
  groups,
  faculties
RESTART IDENTITY CASCADE;

-- Faculties
INSERT INTO faculties(name) VALUES
  ('Computer Science'),
  ('Mathematics'),
  ('Physics');

-- Groups (per faculty)
INSERT INTO groups(faculty_id, name, year_start) VALUES
  (1, 'CS-101', 2024),
  (1, 'CS-102', 2024),
  (2, 'MATH-201', 2023),
  (3, 'PHYS-301', 2022);

-- Students
INSERT INTO students(group_id, full_name, email, enrolled_at) VALUES
  (1, 'Ivan Ivanov', 'ivan.ivanov@uni.example', now()),
  (1, 'Anna Petrova', 'anna.petrova@uni.example', now()),
  (2, 'Petr Sidorov', 'petr.sidorov@uni.example', now()),
  (3, 'Olga Smirnova', 'olga.smirnova@uni.example', now()),
  (4, 'Dmitry Kuznetsov', 'dmitry.kuznetsov@uni.example', now());

-- Courses
INSERT INTO courses(code, title, credits) VALUES
  ('CS101', 'Programming 1', 6),
  ('CS102', 'Databases', 5),
  ('MATH101', 'Discrete Math', 5),
  ('PHYS101', 'Classical Mechanics', 6);

-- Enrollments (students <-> courses)
INSERT INTO enrollments(student_id, course_id, semester, grade) VALUES
  (1, 1, '2024-FALL', 88.50),
  (1, 2, '2024-FALL', NULL),
  (2, 1, '2024-FALL', 91.00),
  (2, 3, '2024-FALL', 79.00),
  (3, 2, '2024-FALL', NULL),
  (4, 3, '2023-FALL', 85.00),
  (5, 4, '2022-FALL', 72.00);

COMMIT;