import os
from flask import Flask
from flask_login import LoginManager
from flask_session import Session
from config import config

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to use the analyzer."
login_manager.login_message_category = "warning"


def create_app(config_name="default"):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )
    app.config.from_object(config[config_name])

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, "generated_resumes"), exist_ok=True)

    Session(app)

    from app.models.database import db, bcrypt
    db.init_app(app)
    bcrypt.init_app(app)

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.database import User
        return User.query.get(int(user_id))

    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.routes.history import history_bp
    app.register_blueprint(history_bp, url_prefix="/history")

    try:
        from app.routes.generator import generator_bp
        app.register_blueprint(generator_bp)
    except Exception:
        pass

    with app.app_context():
        db.create_all()

    return app