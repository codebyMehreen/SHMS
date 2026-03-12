import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access your health dashboard.'
    login_manager.login_message_category = 'info'

    from app.routes.auth    import auth
    from app.routes.main    import main
    from app.routes.health  import health
    from app.routes.ai      import ai
    from app.routes.charts  import charts
    from app.routes.reports import reports

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(health)
    app.register_blueprint(ai)
    app.register_blueprint(charts)
    app.register_blueprint(reports)

    with app.app_context():
        db.create_all()

    return app
