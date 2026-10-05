
import os
import re
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from pymongo import MongoClient
    from bson.objectid import ObjectId
except ImportError:
    MongoClient = None
    ObjectId = None

from database import init_sql_database, get_all_roles, get_role_skills, get_learning_resources

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB = os.path.join(BASE_DIR, "job_skill_gap.db")
LOCAL_DB = os.path.join(BASE_DIR, "app_data.db")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

# ---------- Optional MongoDB ----------
MONGO_URI = os.getenv("MONGO_URI", "").strip()
mongo_available = False
users_collection = None
analysis_collection = None

if MONGO_URI and MongoClient:
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command("ping")
        mongo_db = mongo_client["job_skill_gap_analyzer"]
        users_collection = mongo_db["users"]
        analysis_collection = mongo_db["analysis"]
        mongo_available = True
        print("MongoDB connected.")
    except Exception as exc:
        print("MongoDB unavailable; using local SQLite fallback:", exc)

# ---------- Local fallback ----------
def local_conn():
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_local_db():
    conn = local_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, created_at TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS analysis(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, name TEXT NOT NULL,
        job_role TEXT NOT NULL, user_skills TEXT NOT NULL,
        matched_skills TEXT NOT NULL, missing_skills TEXT NOT NULL,
        match_percentage INTEGER NOT NULL, created_at TEXT NOT NULL)""")
    conn.commit()
    conn.close()

init_local_db()
init_sql_database()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def split_csv(value):
    return [x.strip() for x in value.split(",") if x.strip()]

def save_user(name, email, password):
    password_hash = generate_password_hash(password)
    if mongo_available:
        if users_collection.find_one({"email": email}):
            return False, "Email already registered."
        result = users_collection.insert_one({
            "name": name, "email": email, "password": password_hash,
            "created_at": datetime.utcnow()
        })
        session.update(user_id=str(result.inserted_id), name=name, email=email)
        return True, ""
    conn = local_conn()
    try:
        cur = conn.execute(
            "INSERT INTO users(name,email,password,created_at) VALUES(?,?,?,?)",
            (name, email, password_hash, datetime.utcnow().isoformat())
        )
        conn.commit()
        session.update(user_id=str(cur.lastrowid), name=name, email=email)
        return True, ""
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        conn.close()

def authenticate(email, password):
    if mongo_available:
        user = users_collection.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            session.update(user_id=str(user["_id"]), name=user["name"], email=user["email"])
            return True
        return False
    conn = local_conn()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    if user and check_password_hash(user["password"], password):
        session.update(user_id=str(user["id"]), name=user["name"], email=user["email"])
        return True
    return False

def save_analysis(role, user_skills, matched, missing, percentage):
    now = datetime.utcnow()
    if mongo_available:
        analysis_collection.insert_one({
            "user_id": ObjectId(session["user_id"]),
            "name": session["name"], "job_role": role,
            "user_skills": user_skills, "matched_skills": matched,
            "missing_skills": missing, "match_percentage": percentage,
            "created_at": now
        })
    else:
        conn = local_conn()
        conn.execute("""INSERT INTO analysis
            (user_id,name,job_role,user_skills,matched_skills,missing_skills,match_percentage,created_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (int(session["user_id"]), session["name"], role,
             ",".join(user_skills), ",".join(matched), ",".join(missing),
             percentage, now.isoformat()))
        conn.commit()
        conn.close()

def get_user_analyses():
    if mongo_available:
        return list(analysis_collection.find({"user_id": ObjectId(session["user_id"])}).sort("created_at", -1))
    conn = local_conn()
    rows = conn.execute("SELECT * FROM analysis WHERE user_id=? ORDER BY created_at DESC",
                        (int(session["user_id"]),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.context_processor
def inject_globals():
    return {"mongo_available": mongo_available}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or not email or not password:
            flash("Please fill all fields.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
        else:
            ok, msg = save_user(name, email, password)
            if ok:
                flash("Registration successful.", "success")
                return redirect(url_for("dashboard"))
            flash(msg, "error")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if authenticate(email, password):
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    analyses = get_user_analyses()
    total = len(analyses)
    scores = [int(a["match_percentage"]) for a in analyses]
    average = round(sum(scores) / len(scores)) if scores else 0
    return render_template("dashboard.html", total_analysis=total, average_score=average,
                           recent=analyses[:5])

@app.route("/analyze", methods=["GET", "POST"])
@login_required
def analyze():
    roles = get_all_roles()
    if request.method == "POST":
        role = request.form.get("role", "")
        skills_text = request.form.get("skills", "")
        if not role or not skills_text.strip():
            flash("Select a role and enter your skills.", "error")
            return redirect(url_for("analyze"))
        required = get_role_skills(role)
        user_skills = split_csv(skills_text)
        skill_map = {s.lower(): s for s in user_skills}
        matched = [s for s in required if s.lower() in skill_map]
        missing = [s for s in required if s.lower() not in skill_map]
        percentage = round(len(matched) / len(required) * 100) if required else 0
        recommendations = []
        for skill in missing:
            for resource in get_learning_resources(skill):
                recommendations.append({"skill": skill, **resource})
        save_analysis(role, user_skills, matched, missing, percentage)
        return render_template("result.html", role=role, matched_skills=matched,
                               missing_skills=missing, percentage=percentage,
                               recommendations=recommendations)
    return render_template("analyze.html", roles=roles)

@app.route("/resume", methods=["GET", "POST"])
@login_required
def resume_analyzer():
    roles = get_all_roles()
    result = None
    if request.method == "POST":
        text = request.form.get("resume_text", "").lower()
        role = request.form.get("role", "")
        if not text or not role:
            flash("Enter resume text and select a role.", "error")
            return redirect(url_for("resume_analyzer"))
        required = get_role_skills(role)
        found, missing = [], []
        for skill in required:
            if re.search(r"\b" + re.escape(skill.lower()) + r"\b", text):
                found.append(skill)
            else:
                missing.append(skill)
        percentage = round(len(found) / len(required) * 100) if required else 0
        result = {"role": role, "found": found, "missing": missing, "percentage": percentage}
    return render_template("resume.html", roles=roles, result=result)

@app.route("/history")
@login_required
def history():
    return render_template("history.html", analyses=get_user_analyses())

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
