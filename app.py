from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studentos.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -------------------------
# Task Model
# -------------------------

class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text)

    completed = db.Column(db.Boolean, default=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class StudySession(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    subject = db.Column(db.String(100), nullable=False)

    duration = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

# -------------------------
# Home
# -------------------------

@app.route("/")
def home():

    return render_template("index.html")


# -------------------------
# Dashboard
# -------------------------

@app.route("/dashboard")
def dashboard():

    tasks = Task.query.order_by(
        Task.created_at.desc()
    ).all()

    pending_tasks = Task.query.filter_by(
        completed=False
    ).count()

    study_sessions = StudySession.query.order_by(
        StudySession.created_at.desc()
    ).all()

    total_study_minutes = sum(
        session.duration
        for session in study_sessions
    )

    total_study_hours = total_study_minutes // 60

    remaining_minutes = total_study_minutes % 60

    return render_template(
        "dashboard.html",
        tasks=tasks,
        study_sessions=study_sessions,
        pending_tasks=pending_tasks,
        total_study_hours=total_study_hours,
        remaining_minutes=remaining_minutes
    )

# -------------------------
# Add Task
# -------------------------

@app.route("/task/add", methods=["POST"])
def add_task():

    title = request.form.get("title")

    description = request.form.get("description")

    if title:

        task = Task(
            title=title,
            description=description
        )

        db.session.add(task)

        db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/study/add", methods=["POST"])
def add_study_session():

    subject = request.form.get("subject")

    duration = request.form.get("duration")

    if subject and duration:

        session = StudySession(
            subject=subject,
            duration=int(duration)
        )

        db.session.add(session)

        db.session.commit()

    return redirect(url_for("dashboard"))

# -------------------------
# Complete Task
# -------------------------

@app.route("/task/<int:task_id>/complete")
def complete_task(task_id):

    task = Task.query.get_or_404(task_id)

    task.completed = not task.completed

    db.session.commit()

    return redirect(url_for("dashboard"))


# -------------------------
# Delete Task
# -------------------------

@app.route("/task/<int:task_id>/delete")
def delete_task(task_id):

    task = Task.query.get_or_404(task_id)

    db.session.delete(task)

    db.session.commit()

    return redirect(url_for("dashboard"))


# -------------------------
# Create Database
# -------------------------

with app.app_context():

    db.create_all()


# -------------------------
# Run Application
# -------------------------

if __name__ == "__main__":

    app.run(debug=True)