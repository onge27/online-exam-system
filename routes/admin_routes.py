from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.database import get_db
from functools import wraps

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    db = get_db()
    stats = {
        'total_users': db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        'total_students': db.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
        'total_teachers': db.execute("SELECT COUNT(*) FROM users WHERE role='teacher'").fetchone()[0],
        'total_courses': db.execute("SELECT COUNT(*) FROM courses").fetchone()[0],
        'total_exams': db.execute("SELECT COUNT(*) FROM exams").fetchone()[0],
        'total_results': db.execute("SELECT COUNT(*) FROM results").fetchone()[0],
    }
    return render_template('admin/dashboard.html', stats=stats)


# ── COURSE MANAGEMENT ──────────────────────────────────────────────────────────

@admin_bp.route('/courses')
@admin_required
def courses():
    db = get_db()
    courses = db.execute("SELECT * FROM courses ORDER BY subject_name").fetchall()
    return render_template('admin/courses.html', courses=courses)


@admin_bp.route('/courses/add', methods=['GET', 'POST'])
@admin_required
def add_course():
    if request.method == 'POST':
        name = request.form.get('subject_name', '').strip()
        if not name:
            flash('Course name is required.', 'error')
        else:
            db = get_db()
            db.execute("INSERT INTO courses (subject_name) VALUES (?)", (name,))
            db.commit()
            flash('Course added successfully!', 'success')
            return redirect(url_for('admin.courses'))
    return render_template('admin/add_course.html')


@admin_bp.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@admin_required
def edit_course(course_id):
    db = get_db()
    course = db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('admin.courses'))

    if request.method == 'POST':
        name = request.form.get('subject_name', '').strip()
        if not name:
            flash('Course name is required.', 'error')
        else:
            db.execute("UPDATE courses SET subject_name = ? WHERE id = ?", (name, course_id))
            db.commit()
            flash('Course updated successfully!', 'success')
            return redirect(url_for('admin.courses'))

    return render_template('admin/edit_course.html', course=course)


@admin_bp.route('/courses/delete/<int:course_id>', methods=['POST'])
@admin_required
def delete_course(course_id):
    db = get_db()
    db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    db.commit()
    flash('Course deleted.', 'info')
    return redirect(url_for('admin.courses'))


# ── USER MANAGEMENT ────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@admin_required
def users():
    db = get_db()
    users = db.execute("SELECT * FROM users ORDER BY role, name").fetchall()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session['user_id']:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash('User deleted.', 'info')
    return redirect(url_for('admin.users'))
