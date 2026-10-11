
import sqlite3

for path in ["app_data.db", "job_skill_gap.db"]:
    print("\nChecking:", path)

    try:
        connection = sqlite3.connect(
            "file:" + path + "?mode=ro",
            uri=True
        )

        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        print("Tables:", [table[0] for table in tables])

        for table in tables:
            name = table[0]
            if name in ["job_roles", "skills", "role_skills", "learning_resources"]:
                count = connection.execute(
                    'SELECT COUNT(*) FROM "' + name + '"'
                ).fetchone()[0]
                print(name, "rows:", count)

        connection.close()

    except Exception as error:
        print("Error:", error)
