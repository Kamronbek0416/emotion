from flask import Flask
from flask_login import LoginManager
from program.models import db, User
from program.config import Config
from program.routes import register_routes
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

register_routes(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Создаем директории 'uploads' и 'results', если их нет
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
    app.run(debug=True)