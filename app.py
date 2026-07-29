from flask import Flask
from flask_wtf import CSRFProtect

from config import Config
from models import db
from seed import seed_database


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf = CSRFProtect(app)

    from routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        seed_database()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
