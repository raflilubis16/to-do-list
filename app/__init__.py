"""Application factory – create_app()."""
import os
from flask import Flask
from .extensions import db, migrate
from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ---------- extensions ----------
    db.init_app(app)
    migrate.init_app(app, db)

    # ---------- blueprints ----------
    from .blueprints.pages import pages_bp
    from .blueprints.api import api_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ---------- database & seed ----------
    with app.app_context():
        from . import models  # noqa: F401 – register models
        db.create_all()
        _seed_defaults()

    # ---------- scheduler (hanya proses utama) ----------
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from .scheduler import init_scheduler
        init_scheduler(app)

    return app


def _seed_defaults():
    """Buat pengguna bawaan dan kategori default jika belum ada."""
    from .models import User, Category

    if not User.query.first():
        db.session.add(User(id=1, name="Pengguna", email="user@localhost"))
        db.session.commit()

    if not Category.query.first():
        defaults = [
            Category(user_id=1, name="Pekerjaan", color="#4f46e5"),
            Category(user_id=1, name="Pribadi", color="#10b981"),
            Category(user_id=1, name="Belajar", color="#f59e0b"),
            Category(user_id=1, name="Kesehatan", color="#ef4444"),
        ]
        db.session.add_all(defaults)
        db.session.commit()
