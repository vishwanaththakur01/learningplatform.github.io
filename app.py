from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from ai_engine import LearningPathwayAI
from datetime import datetime
import os
import json

app = Flask(__name__)

# ==================== CONFIGURATION ====================

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///learning_platform.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail configuration
app.config['MAIL_SERVER']   = os.environ.get('MAIL_SERVER',   'smtp.gmail.com')
app.config['MAIL_PORT']     = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@learnai.com')

db           = SQLAlchemy(app)
mail         = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize AI Engine
ai_engine = LearningPathwayAI()

# ==================== DATABASE MODELS ====================

class User(UserMixin, db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    email          = db.Column(db.String(120), unique=True, nullable=False)
    password_hash  = db.Column(db.String(256), nullable=False)
    name           = db.Column(db.String(100), nullable=False)
    learning_style = db.Column(db.String(50), default='visual')
    current_level  = db.Column(db.String(50), default='beginner')
    is_admin       = db.Column(db.Boolean, default=False)
    is_active      = db.Column(db.Boolean, default=True)
    points         = db.Column(db.Integer, default=0)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    progress        = db.relationship('UserProgress',     backref='user', lazy=True)
    achievements    = db.relationship('UserAchievement',  backref='user', lazy=True)
    quiz_attempts   = db.relationship('UserQuizAttempt',  backref='user', lazy=True)
    forum_posts     = db.relationship('ForumPost',        backref='author', lazy=True)
    forum_comments  = db.relationship('ForumComment',     backref='author', lazy=True)
    chat_sessions   = db.relationship('ChatSession',      backref='user', lazy=True)

    def to_dict(self):
        return {
            'id':             self.id,
            'name':           self.name,
            'email':          self.email,
            'learning_style': self.learning_style,
            'current_level':  self.current_level,
            'points':         self.points,
            'is_admin':       self.is_admin,
            'created_at':     self.created_at.isoformat()
        }


class Course(db.Model):
    id           = db.Column(db.String(50), primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.Text)
    topic        = db.Column(db.String(100), nullable=False)
    difficulty   = db.Column(db.String(50), default='beginner')
    content_type = db.Column(db.String(50))
    duration     = db.Column(db.Integer, default=30)
    content      = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    quizzes      = db.relationship('Quiz',       backref='course', lazy=True)
    forum_posts  = db.relationship('ForumPost',  backref='course', lazy=True)


class UserProgress(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id        = db.Column(db.String(50), db.ForeignKey('course.id'), nullable=False)
    progress_percent = db.Column(db.Integer, default=0)
    score            = db.Column(db.Float,   default=0)
    completed        = db.Column(db.Boolean, default=False)
    completed_at     = db.Column(db.DateTime)
    last_accessed    = db.Column(db.DateTime, default=datetime.utcnow)


class Achievement(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon        = db.Column(db.String(50), default='trophy')
    requirement = db.Column(db.String(200))
    points      = db.Column(db.Integer, default=10)


class UserAchievement(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    earned_at      = db.Column(db.DateTime, default=datetime.utcnow)


# ==================== QUIZ MODELS ====================

class Quiz(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    course_id   = db.Column(db.String(50), db.ForeignKey('course.id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    time_limit  = db.Column(db.Integer, default=600)   # seconds
    pass_score  = db.Column(db.Integer, default=70)    # percentage
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question',       backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts  = db.relationship('UserQuizAttempt', backref='quiz', lazy=True)


class Question(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    quiz_id         = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text            = db.Column(db.Text, nullable=False)
    question_type   = db.Column(db.String(20), default='multiple_choice')  # multiple_choice | true_false | short_answer
    options         = db.Column(db.Text)   # JSON list for MC questions
    correct_answer  = db.Column(db.Text, nullable=False)
    explanation     = db.Column(db.Text)
    points          = db.Column(db.Integer, default=1)
    order           = db.Column(db.Integer, default=0)

    def options_list(self):
        return json.loads(self.options) if self.options else []


class UserQuizAttempt(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id       = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    answers       = db.Column(db.Text)    # JSON: {question_id: answer}
    score         = db.Column(db.Float,   default=0)
    total_points  = db.Column(db.Integer, default=0)
    earned_points = db.Column(db.Integer, default=0)
    passed        = db.Column(db.Boolean, default=False)
    time_taken    = db.Column(db.Integer, default=0)   # seconds
    completed_at  = db.Column(db.DateTime, default=datetime.utcnow)


# ==================== FORUM MODELS ====================

class ForumPost(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id   = db.Column(db.String(50), db.ForeignKey('course.id'), nullable=True)
    title       = db.Column(db.String(200), nullable=False)
    body        = db.Column(db.Text, nullable=False)
    is_pinned   = db.Column(db.Boolean, default=False)
    view_count  = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comments = db.relationship('ForumComment', backref='post', lazy=True, cascade='all, delete-orphan')

    def comment_count(self):
        return ForumComment.query.filter_by(post_id=self.id).count()


class ForumComment(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    post_id    = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    is_answer  = db.Column(db.Boolean, default=False)  # marked as accepted answer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== CHAT MODELS ====================

class ChatSession(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id  = db.Column(db.String(50), nullable=True)   # optional course context
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan')


class ChatMessage(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    role       = db.Column(db.String(20), nullable=False)   # 'user' | 'assistant'
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== DECORATORS ====================

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            if request.method == 'POST':
                return jsonify({'error': 'Admin access required'}), 403
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def login_required_json(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.method == 'POST':
                return jsonify({'error': 'Authentication required'}), 401
            return login_manager.unauthorized()
        return f(*args, **kwargs)
    return decorated


# ==================== EMAIL HELPERS ====================

def send_welcome_email(user):
    try:
        msg = Message(
            subject='Welcome to LearnAI!',
            recipients=[user.email]
        )
        msg.body = (
            f"Hi {user.name},\n\n"
            "Welcome to LearnAI! Your account has been created.\n\n"
            "Start learning today by visiting your dashboard.\n\n"
            "Happy learning!\nThe LearnAI Team"
        )
        msg.html = render_template('emails/welcome.html', user=user)
        mail.send(msg)
    except Exception as e:
        app.logger.warning(f"Email send failed: {e}")


def send_achievement_email(user, achievement):
    try:
        msg = Message(
            subject=f'🏆 You earned: {achievement.name}',
            recipients=[user.email]
        )
        msg.body = (
            f"Hi {user.name},\n\n"
            f"Congratulations! You just earned the '{achievement.name}' achievement.\n"
            f"{achievement.description}\n\n"
            "Keep up the great work!\nThe LearnAI Team"
        )
        mail.send(msg)
    except Exception as e:
        app.logger.warning(f"Email send failed: {e}")


def send_quiz_result_email(user, quiz, attempt):
    try:
        status = "passed ✅" if attempt.passed else "not passed yet ❌"
        msg = Message(
            subject=f'Quiz Result: {quiz.title}',
            recipients=[user.email]
        )
        msg.body = (
            f"Hi {user.name},\n\n"
            f"You {status} the quiz '{quiz.title}'.\n"
            f"Your score: {attempt.score:.1f}%\n\n"
            "LearnAI Team"
        )
        mail.send(msg)
    except Exception as e:
        app.logger.warning(f"Email send failed: {e}")


# ==================== MAIN ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=request.form.get('remember') == 'on')
            flash('Welcome back!', 'success')
            return redirect(request.args.get('next') or url_for('dashboard'))

        flash('Invalid email or password', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name  = request.form.get('last_name',  '').strip()
        email      = request.form.get('email',      '').strip().lower()
        password   = request.form.get('password',   '')
        experience = request.form.get('experience', 'beginner')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        new_user = User(
            email         = email,
            password_hash = generate_password_hash(password),
            name          = f"{first_name} {last_name}",
            current_level = experience,
            is_admin      = User.query.count() == 0  # Make first user admin
        )
        db.session.add(new_user)
        db.session.commit()

        initialize_user_progress(new_user)
        send_welcome_email(new_user)

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():

    user_progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    completed = [p for p in user_progress if p.completed]
    avg_score = sum(p.score for p in user_progress) / len(user_progress) if user_progress else 0

    learning_path = ai_engine.generate_learning_path(
        {'learning_style': current_user.learning_style, 'current_level': current_user.current_level},
        'python'
    )

    recommendations = ai_engine.get_recommendations([], {
        'learning_style': current_user.learning_style,
        'current_level': current_user.current_level
    })

    rank = _get_user_rank(current_user.id)

    return render_template(
        'dashboard.html',
        now=datetime.now(),   # ✅ ADD THIS
        progress={
            'completed_courses': len(completed),
            'total_hours': sum(p.progress_percent for p in user_progress) // 60,
            'current_streak': 7,
            'avg_score': round(avg_score, 1),
            'python_progress': 35,
            'web_progress': 20,
            'ds_progress': 10
        },
        current_courses=learning_path[:3],
        recommendations=recommendations[:3],
        achievements=get_user_achievements(),
        leaderboard_rank=rank
    )


@app.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
    if request.method == 'POST':
        result = ai_engine.assess_learning_style(dict(request.form))
        current_user.learning_style = result['dominant_style']
        db.session.commit()
        return render_template('assessment_results.html',
            result          = result,
            recommendations = ai_engine.generate_learning_path(
                {'learning_style': result['dominant_style'], 'current_level': current_user.current_level},
                'python'
            )[:3]
        )
    return render_template('assessment.html')


@app.route('/courses')
@login_required
def courses():
    course_list = []
    for topic, difficulties in ai_engine.course_database.items():
        for difficulty, courses_in in difficulties.items():
            for course in courses_in:
                c = dict(course)
                c['topic']      = topic
                c['difficulty'] = difficulty
                course_list.append(c)
    return render_template('courses.html', courses=course_list)


@app.route('/course/<course_id>')
@login_required
def course_content(course_id):
    course = _find_course(course_id)
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('courses'))

    progress = UserProgress.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    quizzes  = Quiz.query.filter_by(course_id=course_id).all()
    posts    = ForumPost.query.filter_by(course_id=course_id).order_by(
                    ForumPost.is_pinned.desc(), ForumPost.created_at.desc()
               ).limit(5).all()

    return render_template('course_content.html',
        course   = course,
        progress = progress,
        quizzes  = quizzes,
        posts    = posts
    )



# ==================== QUIZ ROUTES ====================

@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        answers      = {}
        total_points = 0
        earned       = 0

        for question in quiz.questions:
            submitted = request.form.get(f'q_{question.id}', '').strip()
            answers[str(question.id)] = submitted
            total_points += question.points

            if question.question_type == 'multiple_choice':
                if submitted.lower() == question.correct_answer.lower():
                    earned += question.points
            elif question.question_type == 'true_false':
                if submitted.lower() == question.correct_answer.lower():
                    earned += question.points
            else:  # short_answer — basic exact/contains match
                if submitted.lower() in question.correct_answer.lower():
                    earned += question.points

        score  = (earned / total_points * 100) if total_points else 0
        passed = score >= quiz.pass_score

        attempt = UserQuizAttempt(
            user_id       = current_user.id,
            quiz_id       = quiz_id,
            answers       = json.dumps(answers),
            score         = round(score, 2),
            total_points  = total_points,
            earned_points = earned,
            passed        = passed,
            time_taken    = int(request.form.get('time_taken', 0))
        )
        db.session.add(attempt)

        # Award points for passing
        if passed:
            current_user.points += earned * 5
            _check_and_award_achievements(current_user)

        db.session.commit()
        send_quiz_result_email(current_user, quiz, attempt)

        return render_template('quiz_results.html',
            quiz     = quiz,
            attempt  = attempt,
            answers  = answers,
            questions = quiz.questions
        )

    # GET — show quiz
    return render_template('take_quiz.html', quiz=quiz)


@app.route('/quiz/<int:quiz_id>/results')
@login_required
def quiz_results_history(quiz_id):
    quiz     = Quiz.query.get_or_404(quiz_id)
    attempts = UserQuizAttempt.query.filter_by(
        user_id=current_user.id, quiz_id=quiz_id
    ).order_by(UserQuizAttempt.completed_at.desc()).all()
    return render_template('quiz_history.html', quiz=quiz, attempts=attempts)


# ==================== LEADERBOARD ROUTES ====================

@app.route('/leaderboard')
@login_required
def leaderboard():
    top_users = (
        User.query
        .filter_by(is_active=True)
        .order_by(User.points.desc())
        .limit(50)
        .all()
    )

    # Annotate each user with completed-course count
    board = []
    for idx, user in enumerate(top_users, start=1):
        completed = UserProgress.query.filter_by(user_id=user.id, completed=True).count()
        board.append({
            'rank':              idx,
            'user':              user,
            'completed_courses': completed,
            'is_current_user':   user.id == current_user.id
        })

    my_rank = _get_user_rank(current_user.id)

    return render_template('leaderboard.html', board=board, my_rank=my_rank)


# ==================== FORUM ROUTES ====================

@app.route('/forum')
@login_required
def forum():
    page  = request.args.get('page', 1, type=int)
    posts = (
        ForumPost.query
        .order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc())
        .paginate(page=page, per_page=20, error_out=False)
    )
    return render_template('forum.html', posts=posts)


@app.route('/forum/new', methods=['GET', 'POST'])
@login_required
def new_forum_post():
    if request.method == 'POST':
        title     = request.form.get('title', '').strip()
        body      = request.form.get('body',  '').strip()
        course_id = request.form.get('course_id') or None

        if not title or not body:
            flash('Title and body are required.', 'error')
            return redirect(url_for('new_forum_post'))

        post = ForumPost(
            user_id   = current_user.id,
            course_id = course_id,
            title     = title,
            body      = body
        )
        db.session.add(post)
        current_user.points += 2
        db.session.commit()

        flash('Post created!', 'success')
        return redirect(url_for('forum_post', post_id=post.id))

    course_list = [c for _, diffs in ai_engine.course_database.items()
                     for _, cs in diffs.items() for c in cs]
    return render_template('new_post.html', courses=course_list)


@app.route('/forum/<int:post_id>', methods=['GET', 'POST'])
@login_required
def forum_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    post.view_count += 1
    db.session.commit()

    if request.method == 'POST':
        body = request.form.get('body', '').strip()
        if body:
            comment = ForumComment(
                post_id = post_id,
                user_id = current_user.id,
                body    = body
            )
            db.session.add(comment)
            current_user.points += 1
            db.session.commit()
            flash('Comment added!', 'success')
        return redirect(url_for('forum_post', post_id=post_id))

    comments = ForumComment.query.filter_by(post_id=post_id)\
                .order_by(ForumComment.is_answer.desc(), ForumComment.created_at.asc()).all()
    return render_template('forum_post.html', post=post, comments=comments)


@app.route('/forum/comment/<int:comment_id>/mark-answer', methods=['POST'])
@login_required
def mark_answer(comment_id):
    comment = ForumComment.query.get_or_404(comment_id)
    post    = ForumPost.query.get(comment.post_id)

    if post.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Forbidden'}), 403

    # Toggle answer status; unmark others
    ForumComment.query.filter_by(post_id=comment.post_id, is_answer=True).update({'is_answer': False})
    comment.is_answer = True
    db.session.commit()
    return jsonify({'success': True})


@app.route('/forum/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_forum_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('Not allowed.', 'error')
        return redirect(url_for('forum'))
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'info')
    return redirect(url_for('forum'))


# ==================== AI CHATBOT ROUTES ====================

@app.route('/chat')
@login_required
def chat():
    sessions = ChatSession.query.filter_by(user_id=current_user.id)\
                .order_by(ChatSession.created_at.desc()).limit(10).all()
    return render_template('chat.html', sessions=sessions)


@app.route('/chat/session/<int:session_id>')
@login_required
def chat_session(session_id):
    sess = ChatSession.query.get_or_404(session_id)
    if sess.user_id != current_user.id:
        flash('Not found.', 'error')
        return redirect(url_for('chat'))
    return render_template('chat_session.html', session=sess, messages=sess.messages)


# ==================== ADMIN ROUTES ====================

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    stats = {
        'total_users':       User.query.count(),
        'active_users':      User.query.filter_by(is_active=True).count(),
        'total_quizzes':     Quiz.query.count(),
        'quiz_attempts':     UserQuizAttempt.query.count(),
        'forum_posts':       ForumPost.query.count(),
        'completed_courses': UserProgress.query.filter_by(completed=True).count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users)


@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page  = request.args.get('page', 1, type=int)
    query = request.args.get('q', '')
    users = User.query
    if query:
        users = users.filter(
            (User.name.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
        )
    users = users.order_by(User.created_at.desc()).paginate(page=page, per_page=25, error_out=False)
    return render_template('admin/users.html', users=users, query=query)


@app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required_json
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user.is_admin = not user.is_admin
        db.session.commit()
        return jsonify({'success': True, 'is_admin': user.is_admin})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/admin/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required_json
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user.is_active = not user.is_active
        db.session.commit()
        return jsonify({'success': True, 'is_active': user.is_active})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/admin/quizzes')
@login_required
@admin_required
def admin_quizzes():
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    return render_template('admin/quizzes.html', quizzes=quizzes)


@app.route('/admin/quizzes/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_new_quiz():
    if request.method == 'POST':
        quiz = Quiz(
            course_id   = request.form['course_id'],
            title       = request.form['title'],
            description = request.form.get('description', ''),
            time_limit  = int(request.form.get('time_limit', 600)),
            pass_score  = int(request.form.get('pass_score', 70))
        )
        db.session.add(quiz)
        db.session.flush()  # get quiz.id before adding questions

        texts    = request.form.getlist('q_text[]')
        types    = request.form.getlist('q_type[]')
        options  = request.form.getlist('q_options[]')
        answers  = request.form.getlist('q_answer[]')
        explains = request.form.getlist('q_explain[]')
        pts      = request.form.getlist('q_points[]')

        for i, text in enumerate(texts):
            if not text.strip():
                continue
            q = Question(
                quiz_id        = quiz.id,
                text           = text,
                question_type  = types[i]  if i < len(types)    else 'multiple_choice',
                options        = options[i] if i < len(options)  else '[]',
                correct_answer = answers[i] if i < len(answers)  else '',
                explanation    = explains[i] if i < len(explains) else '',
                points         = int(pts[i]) if i < len(pts) and pts[i].isdigit() else 1,
                order          = i
            )
            db.session.add(q)

        db.session.commit()
        flash('Quiz created!', 'success')
        return redirect(url_for('admin_quizzes'))

    course_list = [c for _, diffs in ai_engine.course_database.items()
                     for _, cs in diffs.items() for c in cs]
    return render_template('admin/new_quiz.html', courses=course_list)


@app.route('/admin/quizzes/<int:quiz_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted.', 'info')
    return redirect(url_for('admin_quizzes'))


@app.route('/admin/forum')
@login_required
@admin_required
def admin_forum():
    page  = request.args.get('page', 1, type=int)
    posts = ForumPost.query.order_by(ForumPost.created_at.desc()).paginate(page=page, per_page=30, error_out=False)
    return render_template('admin/forum.html', posts=posts)


@app.route('/admin/forum/pin/<int:post_id>', methods=['POST'])
@login_required
@admin_required
def admin_pin_post(post_id):
    post          = ForumPost.query.get_or_404(post_id)
    post.is_pinned = not post.is_pinned
    db.session.commit()
    return jsonify({'success': True, 'is_pinned': post.is_pinned})


# ==================== REST API ROUTES ====================

def paginated_response(query, page, per_page, serializer):
    """Helper: returns a consistent paginated JSON envelope."""
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'data':        [serializer(item) for item in pagination.items],
        'total':       pagination.total,
        'page':        pagination.page,
        'per_page':    pagination.per_page,
        'total_pages': pagination.pages,
        'has_next':    pagination.has_next,
        'has_prev':    pagination.has_prev
    })


@app.route('/api/v1/users/me', methods=['GET'])
@login_required
def api_me():
    return jsonify({'data': current_user.to_dict()})


@app.route('/api/v1/users/me', methods=['PATCH'])
@login_required
def api_update_me():
    data = request.get_json() or {}
    allowed = {'name', 'learning_style', 'current_level'}
    for key, val in data.items():
        if key in allowed:
            setattr(current_user, key, val)
    db.session.commit()
    return jsonify({'data': current_user.to_dict()})


@app.route('/api/v1/leaderboard', methods=['GET'])
@login_required
def api_leaderboard():
    page     = request.args.get('page',     1,  type=int)
    per_page = request.args.get('per_page', 20, type=int)
    return paginated_response(
        User.query.filter_by(is_active=True).order_by(User.points.desc()),
        page,
        per_page,
        lambda u: {'id': u.id, 'name': u.name, 'points': u.points}
    )


@app.route('/api/v1/courses', methods=['GET'])
@login_required
def api_courses():
    topic      = request.args.get('topic')
    difficulty = request.args.get('difficulty')

    course_list = []
    for t, difficulties in ai_engine.course_database.items():
        if topic and t != topic:
            continue
        for d, courses in difficulties.items():
            if difficulty and d != difficulty:
                continue
            for c in courses:
                entry = dict(c)
                entry['topic']      = t
                entry['difficulty'] = d
                course_list.append(entry)

    return jsonify({'data': course_list, 'total': len(course_list)})


@app.route('/api/v1/progress', methods=['GET'])
@login_required
def api_progress():
    user_progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'data': [{
            'course_id':        p.course_id,
            'progress_percent': p.progress_percent,
            'score':            p.score,
            'completed':        p.completed,
            'last_accessed':    p.last_accessed.isoformat()
        } for p in user_progress]
    })


@app.route('/api/v1/progress', methods=['POST'])
@login_required
def api_update_progress():
    data      = request.get_json() or {}
    course_id = data.get('course_id')

    if not course_id:
        return jsonify({'error': 'course_id is required'}), 400

    progress = UserProgress.query.filter_by(
        user_id=current_user.id, course_id=course_id
    ).first()

    if not progress:
        progress = UserProgress(user_id=current_user.id, course_id=course_id)
        db.session.add(progress)

    progress.progress_percent = data.get('progress', progress.progress_percent)
    progress.score            = data.get('score',    progress.score)
    progress.last_accessed    = datetime.utcnow()

    if progress.progress_percent >= 100 and not progress.completed:
        progress.completed   = True
        progress.completed_at = datetime.utcnow()
        current_user.points  += 50
        _check_and_award_achievements(current_user)

    db.session.commit()

    return jsonify({
        'data': {
            'course_id':        progress.course_id,
            'progress_percent': progress.progress_percent,
            'score':            progress.score,
            'completed':        progress.completed
        }
    })


@app.route('/api/v1/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def api_submit_quiz(quiz_id):
    quiz    = Quiz.query.get_or_404(quiz_id)
    data    = request.get_json() or {}
    answers = data.get('answers', {})

    total_points, earned = 0, 0
    results = []

    for question in quiz.questions:
        submitted    = str(answers.get(str(question.id), '')).strip()
        total_points += question.points
        correct       = submitted.lower() == question.correct_answer.lower()
        if correct:
            earned += question.points
        results.append({
            'question_id':    question.id,
            'correct':        correct,
            'your_answer':    submitted,
            'correct_answer': question.correct_answer,
            'explanation':    question.explanation
        })

    score  = round((earned / total_points * 100), 2) if total_points else 0
    passed = score >= quiz.pass_score

    attempt = UserQuizAttempt(
        user_id       = current_user.id,
        quiz_id       = quiz_id,
        answers       = json.dumps(answers),
        score         = score,
        total_points  = total_points,
        earned_points = earned,
        passed        = passed,
        time_taken    = data.get('time_taken', 0)
    )
    db.session.add(attempt)

    if passed:
        current_user.points += earned * 5
        _check_and_award_achievements(current_user)

    db.session.commit()

    return jsonify({
        'data': {
            'score':        score,
            'passed':       passed,
            'earned_points': earned,
            'total_points': total_points,
            'results':      results
        }
    })


@app.route('/api/v1/chat', methods=['POST'])
@login_required
def api_chat():
    """AI Tutor chat endpoint — creates/continues a session."""
    data       = request.get_json() or {}
    user_msg   = data.get('message', '').strip()
    session_id = data.get('session_id')
    course_id  = data.get('course_id')

    if not user_msg:
        return jsonify({'error': 'message is required'}), 400

    # Get or create chat session
    if session_id:
        chat_sess = ChatSession.query.filter_by(
            id=session_id, user_id=current_user.id
        ).first()
    else:
        chat_sess = None

    if not chat_sess:
        chat_sess = ChatSession(user_id=current_user.id, course_id=course_id)
        db.session.add(chat_sess)
        db.session.flush()

    # Save user message
    db.session.add(ChatMessage(session_id=chat_sess.id, role='user', content=user_msg))

    # Build conversation history for the AI
    history = [
        {'role': m.role, 'content': m.content}
        for m in ChatMessage.query.filter_by(session_id=chat_sess.id)
                    .order_by(ChatMessage.created_at.asc()).all()
    ]

    # Get AI response
    context = {
        'learning_style': current_user.learning_style,
        'current_level':  current_user.current_level,
        'course_id':      course_id or chat_sess.course_id
    }
    ai_reply = ai_engine.get_tutor_response(history, context)

    db.session.add(ChatMessage(session_id=chat_sess.id, role='assistant', content=ai_reply))
    db.session.commit()

    return jsonify({
        'data': {
            'session_id': chat_sess.id,
            'reply':      ai_reply
        }
    })


@app.route('/api/v1/forum/posts', methods=['GET'])
@login_required
def api_forum_posts():
    page      = request.args.get('page',      1,  type=int)
    per_page  = request.args.get('per_page', 20,  type=int)
    course_id = request.args.get('course_id')

    query = ForumPost.query
    if course_id:
        query = query.filter_by(course_id=course_id)
    query = query.order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc())

    return paginated_response(query, page, per_page, lambda p: {
        'id':            p.id,
        'title':         p.title,
        'author':        p.author.name,
        'course_id':     p.course_id,
        'comment_count': p.comment_count(),
        'view_count':    p.view_count,
        'is_pinned':     p.is_pinned,
        'created_at':    p.created_at.isoformat()
    })


@app.route('/api/assessment/submit', methods=['POST'])
@login_required
def submit_assessment_api():
    data   = request.get_json()
    result = ai_engine.assess_learning_style(data)

    current_user.learning_style = result['dominant_style']
    db.session.commit()

    return jsonify({
        'success':         True,
        'learning_style':  result['dominant_style'],
        'confidence':      result['confidence'],
        'scores':          result['scores'],
        'recommendations': ai_engine.generate_learning_path(
            {'learning_style': result['dominant_style'], 'current_level': current_user.current_level},
            'python'
        )[:3]
    })


# ==================== HELPER FUNCTIONS ====================

def _find_course(course_id):
    for topic, difficulties in ai_engine.course_database.items():
        for difficulty, courses in difficulties.items():
            for c in courses:
                if c['id'] == course_id:
                    result           = dict(c)
                    result['topic']  = topic
                    result['difficulty'] = difficulty
                    return result
    return None


def _get_user_rank(user_id):
    """Return 1-based rank of a user by points."""
    user  = User.query.get(user_id)
    if not user:
        return None
    above = User.query.filter(
        User.points > user.points, User.is_active == True
    ).count()
    return above + 1


def _check_and_award_achievements(user):
    """Award achievements based on current user state."""
    to_check = [
        ('Quick Learner',  lambda u: UserProgress.query.filter_by(user_id=u.id, completed=True).count() >= 1),
        ('Dedicated',      lambda u: u.points >= 100),
        ('Century Club',   lambda u: u.points >= 500),
        ('Quiz Master',    lambda u: UserQuizAttempt.query.filter_by(user_id=u.id, passed=True).count() >= 5),
    ]
    for name, condition in to_check:
        achievement = Achievement.query.filter_by(name=name).first()
        if not achievement:
            continue
        already = UserAchievement.query.filter_by(
            user_id=user.id, achievement_id=achievement.id
        ).first()
        if not already and condition(user):
            ua = UserAchievement(user_id=user.id, achievement_id=achievement.id)
            db.session.add(ua)
            user.points += achievement.points
            db.session.flush()
            send_achievement_email(user, achievement)


def initialize_user_progress(user):
    seed_achievements = [
        {'name': 'First Steps',   'description': 'Started your learning journey', 'icon': 'shoe-prints', 'points': 5},
        {'name': 'Quick Learner', 'description': 'Completed first course',         'icon': 'bolt',        'points': 20},
        {'name': 'Dedicated',     'description': 'Reached 100 points',             'icon': 'fire',        'points': 15},
        {'name': 'Century Club',  'description': 'Reached 500 points',             'icon': 'star',        'points': 50},
        {'name': 'Quiz Master',   'description': 'Passed 5 quizzes',               'icon': 'graduation-cap', 'points': 30},
    ]
    for a in seed_achievements:
        if not Achievement.query.filter_by(name=a['name']).first():
            db.session.add(Achievement(**a))
    db.session.flush()

    first = Achievement.query.filter_by(name='First Steps').first()
    if first:
        db.session.add(UserAchievement(user_id=user.id, achievement_id=first.id))
        user.points += first.points

    db.session.commit()


def get_user_achievements():
    unlocked_ua  = UserAchievement.query.filter_by(user_id=current_user.id).all()
    unlocked_ids = {ua.achievement_id for ua in unlocked_ua}
    all_achiev   = Achievement.query.all()

    result = []
    for a in all_achiev:
        result.append({
            'name':     a.name,
            'icon':     a.icon,
            'unlocked': a.id in unlocked_ids
        })
    return result


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('error.html', error_code=404, message='Page not found'), 404


@app.errorhandler(403)
def forbidden_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('error.html', error_code=403, message='Access denied'), 403


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', error_code=500, message='Internal server error'), 500


# ==================== CREATE DATABASE ====================

def create_database():
    with app.app_context():
        db.create_all()
        print("Database created successfully!")


if __name__ == '__main__':
    create_database()
    app.run(debug=True, host='0.0.0.0', port=5000)