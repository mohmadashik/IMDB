from flask import Flask
from .movie.routes import movie
from .user.routes import user

def create_app():
    app = Flask(__name__)
    app.register_blueprint(user)
    app.register_blueprint(movie)
    return app
