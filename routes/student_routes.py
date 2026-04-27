import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.database import get_db
from functools import wraps

student_bp = Blueprint('student', __name__)


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            flash('Student access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/dashboard')
@student_required
def dashboard():
    db = get_db()
    student_id = session['user_id']

    completed_ids = [r['exam_id'] for r in db.execute(
        "SELECT exam_id FROM results WHERE student_id=?", (student_id,)
    ).fetchall()]

    available_exams = db.execute(
        """SELECT e.*, c.subject_name, u.name as teacher_name,
           (SELECT COUNT(*) FROM questions WHERE exam_id=e.id) as question_count
           FROM exams e
           JOIN courses c ON e.subject_id=c.id
           JOIN users u ON e.teacher_id=u.id
           ORDER BY e.id DESC"""
    ).fetchall()

    completed_exams = db.execute(
        """SELECT r.*, e.title, c.subject_name
           FROM results r
           JOIN exams e ON r.exam_id=e.id
           JOIN courses c ON e.subject_id=c.id
           WHERE r.student_id=?
           ORDER BY r.submitted_at DESC""",
        (student_id,)
    ).fetchall()

    return render_template('student/dashboard.html',
                           available_exams=available_exams,
                           completed_exams=completed_exams,
                           completed_ids=completed_ids)


@student_bp.route('/exam/<int:exam_id>/start')
@student_required
def start_exam(exam_id):
    db = get_db()
    student_id = session['user_id']

    already_done = db.execute(
        "SELECT id FROM results WHERE student_id=? AND exam_id=?", (student_id, exam_id)
    ).fetchone()
    if already_done:
        flash('You have already completed this exam.', 'info')
        return redirect(url_for('student.dashboard'))

    exam = db.execute(
        "SELECT e.*, c.subject_name FROM exams e JOIN courses c ON e.subject_id=c.id WHERE e.id=?",
        (exam_id,)
    ).fetchone()
    if not exam:
        flash('Exam not found.', 'error')
        return redirect(url_for('student.dashboard'))

    questions = db.execute("SELECT * FROM questions WHERE exam_id=?", (exam_id,)).fetchall()
    questions_data = []
    for q in questions:
        q_dict = dict(q)
        if q_dict['choices']:
            q_dict['choices'] = json.loads(q_dict['choices'])
        questions_data.append(q_dict)

    return render_template('student/take_exam.html', exam=exam, questions=questions_data)


@student_bp.route('/exam/<int:exam_id>/submit', methods=['POST'])
@student_required
def submit_exam(exam_id):
    db = get_db()
    student_id = session['user_id']

    already_done = db.execute(
        "SELECT id FROM results WHERE student_id=? AND exam_id=?", (student_id, exam_id)
    ).fetchone()
    if already_done:
        flash('Exam already submitted.', 'info')
        return redirect(url_for('student.dashboard'))

    questions = db.execute("SELECT * FROM questions WHERE exam_id=?", (exam_id,)).fetchall()
    score = 0
    gradable = 0

    for q in questions:
        answer = request.form.get(f'question_{q["id"]}', '').strip()
        db.execute(
            "INSERT INTO student_answers (student_id, exam_id, question_id, answer) VALUES (?,?,?,?)",
            (student_id, exam_id, q['id'], answer)
        )
        if q['type'] != 'essay':
            gradable += 1
            if answer.lower() == (q['correct_answer'] or '').lower():
                score += 1

    percentage = round((score / gradable * 100), 2) if gradable > 0 else 0.0

    db.execute(
        "INSERT INTO results (student_id, exam_id, score, percentage) VALUES (?,?,?,?)",
        (student_id, exam_id, score, percentage)
    )
    db.commit()

    flash(f'Exam submitted! Score: {score}/{gradable} ({percentage}%)', 'success')
    return redirect(url_for('student.result', exam_id=exam_id))


@student_bp.route('/exam/<int:exam_id>/result')
@student_required
def result(exam_id):
    db = get_db()
    student_id = session['user_id']

    result = db.execute(
        "SELECT * FROM results WHERE student_id=? AND exam_id=?", (student_id, exam_id)
    ).fetchone()
    if not result:
        flash('No result found.', 'error')
        return redirect(url_for('student.dashboard'))

    exam = db.execute(
        "SELECT e.*, c.subject_name FROM exams e JOIN courses c ON e.subject_id=c.id WHERE e.id=?",
        (exam_id,)
    ).fetchone()

    questions = db.execute("SELECT * FROM questions WHERE exam_id=?", (exam_id,)).fetchall()
    answers = {a['question_id']: a['answer'] for a in db.execute(
        "SELECT * FROM student_answers WHERE student_id=? AND exam_id=?", (student_id, exam_id)
    ).fetchall()}

    return render_template('student/result.html', result=result, exam=exam,
                           questions=questions, answers=answers)
