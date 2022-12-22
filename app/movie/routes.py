from flask import Blueprint
movie = Blueprint('movie',__name__,url_prefix='/movie')

@movie.route('/add')
def addmovie():
    return "<h1> add movie page</h1>"