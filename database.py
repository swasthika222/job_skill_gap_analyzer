
import sqlite3
import os

# Store the database in the same folder as this file.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "job_skill_gap.db")


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Job categories, roles, and the starter skills for each role.
JOB_DATA = {
    "IT": {
        "Backend Developer": [
            "Python", "SQL", "Flask", "Git", "REST API"
        ],
        "Data Analyst": [
            "Python", "SQL", "Excel", "Power BI", "Statistics"
        ],
        "Database Developer": [
            "SQL", "MySQL", "Database Design", "PostgreSQL"
        ],
        "Frontend Developer": [
            "HTML", "CSS", "JavaScript", "React", "Git"
        ],
        "Full Stack Developer": [
            "HTML", "CSS", "JavaScript", "Python", "SQL", "Git"
        ],
        "Python Developer": [
            "Python", "SQL", "Git", "Flask", "REST API"
        ],
        "UI/UX Designer": [
            "Figma", "Wireframing", "Prototyping", "User Research"
        ],
        "Java Developer": [
            "Java", "OOP", "SQL", "Git", "Spring Boot"
        ],
        "Software Developer": [
            "Programming", "OOP", "SQL", "Git", "Problem Solving"
        ],
        "Data Scientist": [
            "Python", "SQL", "Statistics", "Machine Learning", "Pandas"
        ],
        "AI / Machine Learning Engineer": [
            "Python", "Statistics", "Machine Learning", "NumPy", "Pandas"
        ],
        "Cloud Engineer": [
            "Linux", "Networking", "Cloud Computing", "Security", "Git"
        ],
        "DevOps Engineer": [
            "Linux", "Git", "Docker", "CI/CD", "Cloud Computing"
        ],
        "Cybersecurity Analyst": [
            "Networking", "Linux", "Cybersecurity", "Security", "Python"
        ],
        "Network Engineer": [
            "Networking", "TCP/IP", "Routing", "Switching", "Troubleshooting"
        ],
        "Software Tester / QA Engineer": [
            "Testing", "Test Cases", "Bug Tracking", "SQL", "Automation Testing"
        ],
        "IT Support Engineer": [
            "Troubleshooting", "Windows", "Networking", "Hardware",
            "Customer Support"
        ],
        "Mobile App Developer": [
            "Java", "Kotlin", "Android", "API", "Git"
        ]
    },

    "Non-IT": {
        "Accountant": [
            "Accounting", "Excel", "Tally", "GST", "Financial Reporting"
        ],
        "HR Executive": [
            "Communication", "Recruitment", "Excel", "Payroll",
            "HR Management"
        ],
        "Business Analyst": [
            "Excel", "Communication", "SQL", "Data Analysis", "Documentation"
        ],
        "Marketing Executive": [
            "Communication", "Market Research", "Marketing",
            "Presentation", "Excel"
        ],
        "Digital Marketing Executive": [
            "SEO", "Social Media Marketing", "Google Analytics",
            "Content Marketing"
        ],
        "Sales Executive": [
            "Communication", "Negotiation", "Customer Relationship",
            "Sales", "Presentation"
        ],
        "Customer Support Executive": [
            "Communication", "Problem Solving", "Customer Support",
            "Email Writing"
        ],
        "Data Entry Operator": [
            "Typing", "MS Excel", "MS Word", "Data Accuracy",
            "Attention to Detail"
        ],
        "Banking Executive": [
            "Banking Knowledge", "Communication", "Excel",
            "Customer Service", "Numerical Ability"
        ],
        "Financial Analyst": [
            "Excel", "Financial Analysis", "Accounting",
            "Data Analysis", "Financial Modeling"
        ],
        "Operations Executive": [
            "Communication", "Excel", "Problem Solving", "Planning",
            "Reporting"
        ],
        "Business Development Executive": [
            "Communication", "Sales", "Negotiation",
            "Market Research", "Presentation"
        ],
        "Recruiter": [
            "Communication", "Recruitment", "Interviewing",
            "Sourcing", "Excel"
        ],
        "Office Administrator": [
            "MS Word", "MS Excel", "Communication", "Documentation",
            "Organization"
        ],
        "Supply Chain Executive": [
            "Supply Chain Management", "Inventory Management",
            "Excel", "Planning", "Reporting"
        ],
        "Content Writer": [
            "Writing", "Grammar", "Research", "SEO", "Editing"
        ],
        "Graphic Designer": [
            "Graphic Design", "Typography", "Color Theory",
            "Adobe Photoshop", "Creativity"
        ],
        "Project Coordinator": [
            "Communication", "Planning", "Documentation",
            "Excel", "Time Management"
        ]
    }
}


def init_sql_database():
    """Create database tables and insert starter roles and skills."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS role_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            UNIQUE (role_id, skill_id),
            FOREIGN KEY (role_id) REFERENCES job_roles(id),
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL,
            resource_name TEXT NOT NULL,
            resource_url TEXT NOT NULL,
            UNIQUE (skill_name, resource_name, resource_url)
        )
    """)

    # Add category to an existing job_roles table if needed.
    columns = {
        row["name"]
        for row in cursor.execute(
            "PRAGMA table_info(job_roles)"
        ).fetchall()
    }

    if "category" not in columns:
        cursor.execute("""
            ALTER TABLE job_roles
            ADD COLUMN category TEXT NOT NULL DEFAULT 'IT'
        """)

    # Insert categories, job roles, and their required skills.
    for category, roles in JOB_DATA.items():
        for role_name, skill_names in roles.items():

            cursor.execute("""
                INSERT OR IGNORE INTO job_roles (role_name, category)
                VALUES (?, ?)
            """, (role_name, category))

            # Update category for roles that already exist.
            cursor.execute("""
                UPDATE job_roles
                SET category = ?
                WHERE role_name = ?
            """, (category, role_name))

            role_row = cursor.execute("""
                SELECT id FROM job_roles
                WHERE role_name = ?
            """, (role_name,)).fetchone()

            for skill_name in skill_names:
                cursor.execute("""
                    INSERT OR IGNORE INTO skills (skill_name)
                    VALUES (?)
                """, (skill_name,))

                skill_row = cursor.execute("""
                    SELECT id FROM skills
                    WHERE skill_name = ?
                """, (skill_name,)).fetchone()

                cursor.execute("""
                    INSERT OR IGNORE INTO role_skills (role_id, skill_id)
                    VALUES (?, ?)
                """, (role_row["id"], skill_row["id"]))

    conn.commit()
    conn.close()


def get_all_roles(category=None):
    """Return every role, or only roles from a selected category."""
    conn = get_connection()

    if category:
        rows = conn.execute("""
            SELECT id, role_name, category
            FROM job_roles
            WHERE category = ?
            ORDER BY role_name
        """, (category,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT id, role_name, category
            FROM job_roles
            ORDER BY category, role_name
        """).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def get_role_skills(role_name):
    """Return the required skills for a selected job role."""
    conn = get_connection()

    rows = conn.execute("""
        SELECT DISTINCT s.skill_name
        FROM skills AS s
        JOIN role_skills AS rs ON s.id = rs.skill_id
        JOIN job_roles AS r ON r.id = rs.role_id
        WHERE r.role_name = ?
        ORDER BY s.skill_name
    """, (role_name,)).fetchall()

    conn.close()
    return [row["skill_name"] for row in rows]


def get_learning_resources(skill_name):
    """Return learning resources for a skill."""
    conn = get_connection()

    rows = conn.execute("""
        SELECT DISTINCT resource_name, resource_url
        FROM learning_resources
        WHERE LOWER(skill_name) = LOWER(?)
    """, (skill_name.strip(),)).fetchall()

    conn.close()
    return [dict(row) for row in rows]
