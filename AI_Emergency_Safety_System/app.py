"""AI Emergency Safety System — Flask application entry point."""

from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect, CSRFError

from ai_model import ensure_model
from auth import auth_bp
from config import Config
from database import close_db, init_db
from emergency import emergency_bp

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    csrf.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(emergency_bp)

    app.teardown_appcontext(close_db)
    init_db()
    ensure_model()

    @app.context_processor
    def inject_globals():
        return {
            "sms_configured": Config.sms_configured(),
            "email_configured": Config.email_configured(),
        }

    @app.errorhandler(CSRFError)
    def handle_csrf(_error):
        return (
            render_template(
                "error.html",
                title="Security check failed",
                message="The form expired or was invalid. Please refresh the page and try again.",
            ),
            400,
        )

    @app.errorhandler(404)
    def handle_404(_error):
        return (
            render_template(
                "error.html",
                title="Page not found",
                message="The page you requested does not exist.",
            ),
            404,
        )

    @app.errorhandler(500)
    def handle_500(_error):
        return (
            render_template(
                "error.html",
                title="Server error",
                message="Something went wrong. The application is still running; please try again.",
            ),
            500,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)
