# auth.py — UPGRADE 3: User Registration, Login, Logout

# from flask import Blueprint, render_template, request, redirect, url_for, flash, session
# from flask_login import login_user, logout_user, login_required, current_user

# auth_bp = Blueprint('auth', __name__)


# @auth_bp.route('/register', methods=['GET','POST'])
# def register():
#     if request.method == 'POST':
#         name     = request.form.get('name','').strip()
#         email    = request.form.get('email','').strip().lower()
#         password = request.form.get('password','')

#         if not name or not email or not password:
#             flash('All fields are required.', 'error')
#             return redirect(url_for('auth.register'))

#         if len(password) < 6:
#             flash('Password must be at least 6 characters.', 'error')
#             return redirect(url_for('auth.register'))

#         try:
#             from app.models.database import db, User
#             if User.query.filter_by(email=email).first():
#                 flash('An account with this email already exists.', 'error')
#                 return redirect(url_for('auth.register'))

#             user = User(name=name, email=email)
#             user.set_password(password)
#             db.session.add(user)
#             db.session.commit()

#             login_user(user)
#             flash(f'Welcome, {name}! Your account has been created.', 'success')
#             return redirect(url_for('main.index'))
#         except Exception as e:
#             flash(f'Registration error: {e}', 'error')
#             return redirect(url_for('auth.register'))

#     return render_template('auth/register.html')


# @auth_bp.route('/login', methods=['GET','POST'])
# def login():
#     if request.method == 'POST':
#         email    = request.form.get('email','').strip().lower()
#         password = request.form.get('password','')

#         try:
#             from app.models.database import User
#             user = User.query.filter_by(email=email).first()

#             if user and user.check_password(password):
#                 login_user(user)
#                 flash(f'Welcome back, {user.name}!', 'success')
#                 next_page = request.args.get('next')
#                 return redirect(next_page or url_for('main.index'))
#             else:
#                 flash('Invalid email or password.', 'error')
#         except Exception as e:
#             flash(f'Login error: {e}', 'error')

#     return render_template('auth/login.html')


# @auth_bp.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     flash('You have been logged out.', 'info')
#     return redirect(url_for('main.index'))








from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("auth.register"))

        try:
            from app.models.database import db, User

            if User.query.filter_by(email=email).first():
                flash("An account with this email already exists.", "error")
                return redirect(url_for("auth.register"))

            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            login_user(user)
            flash(f"Welcome, {name}! Your account has been created.", "success")
            return redirect(url_for("main.index"))
        except Exception as e:
            flash(f"Registration error: {e}", "error")
            return redirect(url_for("auth.register"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        try:
            from app.models.database import User
            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                login_user(user)
                flash(f"Welcome back, {user.name}!", "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("main.index"))
            else:
                flash("Invalid email or password.", "error")
        except Exception as e:
            flash(f"Login error: {e}", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))