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

class Attendance(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    total_classes = db.Column(
        db.Integer,
        nullable=False
    )

    attended_classes = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

def calculate_attendance_advice(attended, total, required=75):

    if total == 0:
        return {
            "percentage": 0,
            "status": "No data",
            "message": "No attendance recorded yet."
        }

    percentage = (attended / total) * 100

    if percentage < required:

        classes_needed = 0

        while (
            (attended + classes_needed)
            / (total + classes_needed)
        ) * 100 < required:

            classes_needed += 1

        return {
            "percentage": round(percentage, 1),
            "status": "At Risk",
            "message": (
                f"Attend the next {classes_needed} "
                f"class(es) to reach {required}%."
            )
        }

    else:

        classes_can_miss = 0

        while (
            attended
            / (total + classes_can_miss + 1)
        ) * 100 >= required:

            classes_can_miss += 1

        return {
            "percentage": round(percentage, 1),
            "status": "Safe",
            "message": (
                f"You can miss {classes_can_miss} "
                f"class(es) and remain at or above {required}%."
            )
        }

class Goal(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    target = db.Column(
        db.Integer,
        nullable=False
    )

    progress = db.Column(
        db.Integer,
        default=0
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

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

    attendance_records = Attendance.query.order_by(
        Attendance.subject.asc()
    ).all()

    attendance_advice = []

    for record in attendance_records:
        advice = calculate_attendance_advice(
            record.attended_classes,
            record.total_classes
        )

        attendance_advice.append({
            "subject": record.subject,
            "attended": record.attended_classes,
            "total": record.total_classes,
            "percentage": advice["percentage"],
            "status": advice["status"],
            "message": advice["message"]
        })

        total_classes = sum(
            record.total_classes
            for record in attendance_records
        )

        attended_classes = sum(
            record.attended_classes
            for record in attendance_records
        )

        if total_classes > 0:
            overall_attendance = round(
                (attended_classes / total_classes) * 100,
            1
            )

        else:

            overall_attendance = 0

    goals = Goal.query.order_by(
        Goal.created_at.desc()
    ).all()

    active_goals = Goal.query.filter_by(
        completed=False
    ).count()

    return render_template(
        "dashboard.html",
        tasks=tasks,
        study_sessions=study_sessions,
        pending_tasks=pending_tasks,
        total_study_hours=total_study_hours,
        remaining_minutes=remaining_minutes,
        attendance_records=attendance_records,
        overall_attendance=overall_attendance,
        attendance_advice=attendance_advice,
        goals=goals,
        active_goals=active_goals
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

@app.route("/attendance/add", methods=["POST"])
def add_attendance():

    subject = request.form.get("subject")

    total_classes = request.form.get("total_classes")

    attended_classes = request.form.get("attended_classes")

    if subject and total_classes and attended_classes:

        total_classes = int(total_classes)

        attended_classes = int(attended_classes)

        if (
            total_classes > 0
            and 0 <= attended_classes <= total_classes
        ):

            attendance = Attendance(
                subject=subject,
                total_classes=total_classes,
                attended_classes=attended_classes
            )

            db.session.add(attendance)

            db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/goal/add", methods=["POST"])
def add_goal():

    title = request.form.get("title")
    target = request.form.get("target")
    progress = request.form.get("progress")

    if title and target:

        target = int(target)

        progress = int(progress or 0)

        if target > 0 and 0 <= progress <= target:

            goal = Goal(
                title=title,
                target=target,
                progress=progress,
                completed=(progress == target)
            )

            db.session.add(goal)

            db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/goal/<int:goal_id>/update", methods=["POST"])
def update_goal(goal_id):

    goal = Goal.query.get_or_404(goal_id)

    progress = request.form.get("progress")

    if progress:

        progress = int(progress)

        if 0 <= progress <= goal.target:

            goal.progress = progress

            if progress == goal.target:
                goal.completed = True
            else:
                goal.completed = False

            db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/goal/<int:goal_id>/delete")
def delete_goal(goal_id):

    goal = Goal.query.get_or_404(goal_id)

    db.session.delete(goal)

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