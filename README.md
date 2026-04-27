# 🎓 Online Examination & Grading System

A complete full-stack web application built with Python Flask, SQLite, HTML/CSS/JS.

---

## 🚀 Local Setup Guide

### Step 1 — Prerequisites
- Python 3.9 or higher installed
- pip (comes with Python)

### Step 2 — Navigate to project folder
```bash
cd online_exam_system
```

### Step 3 — Create virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 4 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 5 — Run the application
```bash
python app.py
```

### Step 6 — Open in browser
```
http://127.0.0.1:5000
```

---

## 🔐 Default Accounts

| Role    | Email           | Password |
|---------|-----------------|----------|
| Admin   | admin@exam.com  | admin123 |

> Teachers and Students register at `/register`

---

## 📁 Project Structure

```
online_exam_system/
├── app.py                    ← Flask entry point
├── requirements.txt
├── database.db               ← Auto-created on first run
│
├── config/
│   └── config.py             ← App configuration
│
├── models/
│   └── database.py           ← DB init + get_db()
│
├── routes/
│   ├── auth_routes.py        ← Login, Register, Logout
│   ├── admin_routes.py       ← Admin panel
│   ├── teacher_routes.py     ← Exam management
│   └── student_routes.py     ← Take exams + results
│
├── templates/
│   ├── base.html
│   ├── dashboard_base.html
│   ├── login.html
│   ├── register.html
│   ├── admin/
│   ├── teacher/
│   └── student/
│
└── static/
    ├── css/style.css
    └── js/script.js
```

---

## 🎯 Features

### 🔴 Admin
- Dashboard with stats
- Add / Edit / Delete courses
- View and delete users

### 🟡 Teacher
- Create exams (select course, set timer)
- Add Multiple Choice (A–H), True/False, Essay questions
- View student results and essay answers

### 🟢 Student
- Browse available exams
- Take timed exams (auto-submit on timeout)
- One attempt per exam
- View scores, percentage, answer review

### 📊 Grading
- Auto-grade MC and True/False
- Essay stored for manual review
- Grade letters: A (≥90%), B (≥80%), C (≥70%), D (≥60%), F (<60%)
