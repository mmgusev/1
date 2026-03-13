_ALLOWED = {
    "faculties": ["id", "name"],
    "groups": ["id", "faculty_id", "name", "year_start"],
    "students": ["id", "group_id", "full_name", "email", "enrolled_at"],
    "courses": ["id", "code", "title", "credits"],
    "enrollments": ["id", "student_id", "course_id", "semester", "grade"],
}


def get_allowed_columns():
    return _ALLOWED