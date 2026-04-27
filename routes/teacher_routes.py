import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.database import get_db
from functools import wraps

teacher_bp = Blueprint('teacher', __name__)

# -------------------- AUTH DECORATOR --------------------
def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'teacher':
            flash('Teacher access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# -------------------- DASHBOARD --------------------
@teacher_bp.route('/dashboard')
@teacher_required
def dashboard():
    db = get_db()
    teacher_id = session['user_id']

    exams = db.execute(
        """SELECT e.*, c.subject_name,
           (SELECT COUNT(*) FROM questions WHERE exam_id = e.id) as question_count,
           (SELECT COUNT(*) FROM results WHERE exam_id = e.id) as attempt_count
           FROM exams e 
           JOIN courses c ON e.subject_id = c.id
           WHERE e.teacher_id = ? 
           ORDER BY e.id DESC""",
        (teacher_id,)
    ).fetchall()

    stats = {
        'total_exams': len(exams),
        'total_questions': db.execute(
            "SELECT COUNT(*) FROM questions q JOIN exams e ON q.exam_id=e.id WHERE e.teacher_id=?",
            (teacher_id,)
        ).fetchone()[0],
        'total_attempts': db.execute(
            "SELECT COUNT(*) FROM results r JOIN exams e ON r.exam_id=e.id WHERE e.teacher_id=?",
            (teacher_id,)
        ).fetchone()[0],
    }

    return render_template('teacher/dashboard.html', exams=exams, stats=stats)


# -------------------- CREATE EXAM --------------------
@teacher_bp.route('/exams/create', methods=['GET', 'POST'])
@teacher_required
def create_exam():
    db = get_db()
    courses = db.execute("SELECT * FROM courses ORDER BY subject_name").fetchall()

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        title = request.form.get('title', '').strip()
        timer = request.form.get('timer_minutes', 30)

        if not subject_id or not title:
            flash('Subject and title are required.', 'error')
            return render_template('teacher/create_exam.html', courses=courses)

        cur = db.execute(
            "INSERT INTO exams (subject_id, teacher_id, title, timer_minutes) VALUES (?, ?, ?, ?)",
            (subject_id, session['user_id'], title, timer)
        )
        db.commit()

        exam_id = cur.lastrowid
        flash('Exam created! Now add questions.', 'success')
        return redirect(url_for('teacher.add_questions', exam_id=exam_id))

    return render_template('teacher/create_exam.html', courses=courses)


# -------------------- ADD QUESTIONS --------------------
@teacher_bp.route('/exams/<int:exam_id>/questions', methods=['GET', 'POST'])
@teacher_required
def add_questions(exam_id):
    db = get_db()

    exam = db.execute(
        """SELECT e.*, c.subject_name 
           FROM exams e 
           JOIN courses c ON e.subject_id=c.id 
           WHERE e.id=? AND e.teacher_id=?""",
        (exam_id, session['user_id'])
    ).fetchone()

    if not exam:
        flash('Exam not found.', 'error')
        return redirect(url_for('teacher.dashboard'))

    if request.method == 'POST':
        q_text = request.form.get('question_text', '').strip()
        q_type = request.form.get('type', 'multiple_choice')
        correct = request.form.get('correct_answer', '').strip()
        choices = None

        if q_type == 'multiple_choice':
            opts = []
            for letter in 'ABCDEFGH':
                val = request.form.get(f'choice_{letter}', '').strip()
                if val:
                    opts.append({'label': letter, 'text': val})
            choices = json.dumps(opts)

        elif q_type == 'true_false':
            choices = json.dumps([
                {'label': 'True', 'text': 'True'},
                {'label': 'False', 'text': 'False'}
            ])

        if not q_text:
            flash('Question text is required.', 'error')
        else:
            db.execute(
                """INSERT INTO questions 
                (exam_id, question_text, type, choices, correct_answer) 
                VALUES (?,?,?,?,?)""",
                (exam_id, q_text, q_type, choices, correct)
            )
            db.commit()
            flash('Question added!', 'success')

    questions = db.execute(
        "SELECT * FROM questions WHERE exam_id=?",
        (exam_id,)
    ).fetchall()

    return render_template('teacher/add_questions.html', exam=exam, questions=questions)


# -------------------- EDIT EXAM --------------------
@teacher_bp.route('/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_exam(exam_id):
    db = get_db()

    exam = db.execute(
        "SELECT * FROM exams WHERE id=? AND teacher_id=?",
        (exam_id, session['user_id'])
    ).fetchone()

    if not exam:
        flash('Exam not found.', 'error')
        return redirect(url_for('teacher.dashboard'))

    courses = db.execute("SELECT * FROM courses ORDER BY subject_name").fetchall()

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        title = request.form.get('title', '').strip()
        timer = request.form.get('timer_minutes', 30)

        db.execute(
            "UPDATE exams SET subject_id=?, title=?, timer_minutes=? WHERE id=?",
            (subject_id, title, timer, exam_id)
        )
        db.commit()

        flash('Exam updated!', 'success')
        return redirect(url_for('teacher.dashboard'))

    return render_template('teacher/edit_exam.html', exam=exam, courses=courses)


# -------------------- DELETE EXAM --------------------
@teacher_bp.route('/exams/<int:exam_id>/delete', methods=['POST'])
@teacher_required
def delete_exam(exam_id):
    db = get_db()

    db.execute("DELETE FROM student_answers WHERE exam_id=?", (exam_id,))
    db.execute("DELETE FROM results WHERE exam_id=?", (exam_id,))
    db.execute("DELETE FROM questions WHERE exam_id=?", (exam_id,))
    db.execute("DELETE FROM exams WHERE id=? AND teacher_id=?", (exam_id, session['user_id']))

    db.commit()

    flash('Exam deleted.', 'info')
    return redirect(url_for('teacher.dashboard'))


# -------------------- DELETE QUESTION --------------------
@teacher_bp.route('/questions/<int:q_id>/delete', methods=['POST'])
@teacher_required
def delete_question(q_id):
    db = get_db()

    q = db.execute(
        """SELECT q.*, e.teacher_id 
           FROM questions q 
           JOIN exams e ON q.exam_id=e.id 
           WHERE q.id=?""",
        (q_id,)
    ).fetchone()

    if q and q['teacher_id'] == session['user_id']:
        exam_id = q['exam_id']
        db.execute("DELETE FROM questions WHERE id=?", (q_id,))
        db.commit()

        flash('Question deleted.', 'info')
        return redirect(url_for('teacher.add_questions', exam_id=exam_id))

    flash('Not authorized.', 'error')
    return redirect(url_for('teacher.dashboard'))


# -------------------- EXAM RESULTS --------------------
@teacher_bp.route('/exams/<int:exam_id>/results')
@teacher_required
def exam_results(exam_id):
    db = get_db()

    exam = db.execute(
        """SELECT e.*, c.subject_name 
           FROM exams e 
           JOIN courses c ON e.subject_id=c.id 
           WHERE e.id=? AND e.teacher_id=?""",
        (exam_id, session['user_id'])
    ).fetchone()

    if not exam:
        flash('Exam not found.', 'error')
        return redirect(url_for('teacher.dashboard'))

    results = db.execute(
        """SELECT r.*, u.name as student_name, u.email
           FROM results r 
           JOIN users u ON r.student_id = u.id
           WHERE r.exam_id = ? 
           ORDER BY r.percentage DESC""",
        (exam_id,)
    ).fetchall()

    essays = db.execute(
        """SELECT sa.*, u.name as student_name, q.question_text
           FROM student_answers sa
           JOIN users u ON sa.student_id = u.id
           JOIN questions q ON sa.question_id = q.id
           WHERE sa.exam_id=? AND q.type='essay'""",
        (exam_id,)
    ).fetchall()

    return render_template(
        'teacher/exam_results.html',
        exam=exam,
        results=results,
        essays=essays
    )


# -------------------- MANAGE EXAMS (FIXED ENDPOINT) --------------------
@teacher_bp.route('/manage_exams')
@teacher_required
def manage_exams():
    db = get_db()

    exams = db.execute(
        """SELECT e.*, c.subject_name,
           (SELECT COUNT(*) FROM questions WHERE exam_id=e.id) as question_count
           FROM exams e
           JOIN courses c ON e.subject_id=c.id
           WHERE e.teacher_id=?
           ORDER BY e.id DESC""",
        (session['user_id'],)
    ).fetchall()

    return render_template('teacher/manage_exams.html', exams=exams)

@teacher_bp.route('/results/<int:result_id>/view')
@teacher_required
def view_result(result_id):
    db = get_db()

    result = db.execute(
        """SELECT r.*, u.name as student_name, u.email, e.title as exam_title
           FROM results r
           JOIN users u ON r.student_id = u.id
           JOIN exams e ON r.exam_id = e.id
           WHERE r.id=?""",
        (result_id,)
    ).fetchone()

    if not result:
        flash('Result not found.', 'error')
        return redirect(url_for('teacher.dashboard'))

    answers = db.execute(
        """SELECT sa.*, q.question_text, q.correct_answer
           FROM student_answers sa
           JOIN questions q ON sa.question_id = q.id
           WHERE sa.exam_id=? AND sa.student_id=?""",
        (result['exam_id'], result['student_id'])
    ).fetchall()

    return render_template(
        'teacher/view_result.html',
        result=result,
        answers=answers
    )