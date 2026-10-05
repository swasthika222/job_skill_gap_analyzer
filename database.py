import sqlite3

DATABASE = "job_skill_gap.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_sql_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Job roles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL UNIQUE
        )
    """)

    # Skills table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL UNIQUE
        )
    """)

    # Role-skills mapping table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS role_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES job_roles(id),
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        )
    """)

    # Learning resources table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL,
            resource_name TEXT NOT NULL,
            resource_url TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_all_roles():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role_name
        FROM job_roles
        ORDER BY role_name
    """)

    roles = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return roles


def get_role_skills(role_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.skill_name
        FROM skills s
        JOIN role_skills rs
            ON s.id = rs.skill_id
        JOIN job_roles r
            ON r.id = rs.role_id
        WHERE r.role_name = ?
        ORDER BY s.skill_name
    """, (role_name,))

    skills = [row["skill_name"] for row in cursor.fetchall()]

    conn.close()
    return skills


def get_learning_resources(skill_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT resource_name, resource_url
        FROM learning_resources
        WHERE LOWER(skill_name) = LOWER(?)
    """, (skill_name,))

    resources = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return resources