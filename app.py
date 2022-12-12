from flask import Flask, request, render_template, session, redirect, url_for
import re, os
from datetime import datetime
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from bson.objectid import ObjectId
from functools import wraps
from pymongo import MongoClient

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = ['thisissecretkey']
client = MongoClient("mongodb://localhost:27017/")
db = client['moviesdb']
user_col = db['user']
movie_col = db['movie']

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    result = user_col.find_one({"_id": ObjectId(id)})
    if result != None:
        return User(id=str(result['_id']), username=result['username'], email=result['email'],
                    password=result['password'])
    else:
        return None


class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
    def get_id(self):
        return self.id


def not_logged_in(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if 'id' in session:
            return redirect(url_for('profile'))
        else:
            return func(*args, **kwargs)
    return wrap


@app.route("/")
def home():
    msg = ''
    documents = movie_col.find()
    movies = [{item: data[item] for item in data if len(item) < 10} for data in documents]
    for movie in movies:
        movie['_id'] = str(movie['_id'])
    return render_template("home.html", movies=movies, msg=msg)


@app.route('/register', methods=['GET', 'POST'])
def register():
    status = ''
    if request.method == 'POST':
        if 'username' and 'password' and 'email' in request.form:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            check_user = user_col.find_one({'username': username})
            if check_user != None and (check_user['email'] == email or check_user['username'] == username):
                status = 'Account already exists !'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                status = 'Invalid email address !'
            elif not re.match(r'[A-Za-z0-9]+', username):
                status = 'Username must contain only characters and numbers !'
            elif not username or not password or not email:
                status = 'Please fill out the form !'
                return
            else:
                user_col.insert_one({'username': username, 'password': password, 'email': email, 'genre': None})
                status = 'You have successfully registered !'
        elif request.method == 'POST':
            status = 'Please fill out the form !'
        return render_template("user/register.html", status=status)
    return render_template("user/register.html", status=status)

#login commit
@app.route('/login', methods=['GET', 'POST'])
@not_logged_in
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        check_user = user_col.find_one({'email': email})
        if check_user and check_user['password'] == password:
            logged_user = User(str(check_user['_id']), check_user['username'], check_user['password'],
                               check_user['email'])
            login_user(logged_user)
            session['id'] = str(check_user['_id'])
            session['username'] = check_user['username'].capitalize()
            session['email'] = check_user['email']
            session['genre'] = check_user['genre'] if check_user['genre'] != None else None
            return redirect(url_for('profile'))
        else:
            msg = 'wrong user credentials'
            return render_template("user/login.html", msg=msg)
    return render_template("user/login.html", msg=msg)


@app.route('/profile')
@login_required
def profile():
    msg=''
    documents = movie_col.find()
    movies = [{item: data[item] for item in data if len(item) < 10} for data in documents]
    for movie in movies :
        movie['_id'] = str(movie['_id'])
    return render_template("user/dashboard.html", movies=movies,msg=msg)


@app.route('/account')
@login_required
def account():
    user_details = user_col.find_one({"username": session['username']})
    return render_template("user/account.html", user=user_details)


@app.route('/edit-user', methods=['GET', 'POST'])
@login_required
def edit_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        genre = request.form['genre']
        update_query = {"$set": {'username': username, 'email': email, 'genre': genre}}
        response = user_col.update_one({"_id": ObjectId(session['id'])},update_query)
        session['genre'] = genre
        session['username'] = username.capitalize()
        msg = 'updated successfully' if response.modified_count >0 else ''
        user = user_col.find_one({"_id": ObjectId(session['id'])})
        return render_template("user/edit-user.html",msg=msg,user=user)
    else:
        user = user_col.find_one({"_id": ObjectId(session['id'])})
        return render_template("user/edit-user.html", user=user)

@app.route('/logout')
def logout():
    logout_user()
    session.pop('id', None)
    session.pop('username', None)
    session.pop('email',None)
    return redirect(url_for('login'))


@app.route('/addmovie',methods=['GET','POST'])
@login_required
def addmovie():
    msg =''
    if request.method == 'POST':
        movie = request.form['movie']
        date = request.form['date']
        genre = request.form['genre']
        movie_col.insert_one({'movie':movie,'date':date,'genre':genre,'upvotes':0,'downvotes':0 ,'reviews':{}})
        msg = 'movie added successfully'
        return render_template("movie/add.html",msg=msg)
    else:
        return render_template("movie/add.html",msg=msg)


@app.route('/editmovie/<movieid>/', methods=['GET', 'POST'])
@login_required
def editmovie(movieid):
    msg = ''
    if request.method == "POST":
        movie = request.form['movie']
        date = request.form['date']
        genre = request.form['genre']
        update_query = {"$set": {'movie': movie, 'date': date, 'genre': genre}}
        response = movie_col.update_one({"_id": ObjectId(movieid)}, update_query)
        msg = 'updated successfully' if response.modified_count > 0 else ''
        movie = movie_col.find_one({"_id": ObjectId(movieid)})
        return render_template("movie/edit.html", msg=msg, movie=movie)
    else:
        movie = movie_col.find_one({"_id": ObjectId(movieid)})
        return render_template("movie/edit.html",msg=msg,movie=movie)

@app.route('/deletemovie/<movieid>/',methods=['GET','POST','DELETE'])
@login_required
def deletemovie(movieid):
    movie_col.delete_one({"_id":ObjectId(movieid)})
    movies = movie_col.find()
    movies = [{item: data[item] for item in data if len(item) < 10} for data in movies]
    return redirect(url_for("profile",movies=movies))

# def sortmovies():
#     status = ''
#     sorting_key = request.json['sorting_key']
#     order = 'desc' if 'order' not in request.json else request.json['order']
#     if sorting_key =='date':
#         movies = movie_col.find()
#         movies = list(movies)
#         for movie in movies:
#             movie['date'] = datetime.strptime(movie['date'],"%d-%m-%Y").date()
#         sorted_movies=sorted(movies,key=lambda i:i['date'])
#         output = [{item:data[item]for item in data if len(item)<10 and item!='_id'}for data in sorted_movies]
#     elif sorting_key=='upvotes':
#         sorted_movies = movie_col.find().sort("upvotes",-1)
#     elif sorting_key =='downvotes':
#         sorted_movies = movie_col.find().sort("downvotes",-1)
#     else:
#         status = "you must give a valid sorting key"
#         return jsonify({"status":status})
#     output = [{item: data[item] for item in data if len(item)<10 and item!='_id'} for data in sorted_movies]
#     output = output if order=="desc" else output[-1::-1]
#     return output
#
@app.route('/voting/<movieid>/<vote>/',methods=['GET','POST','PUT'])
@login_required
def voting(movieid,vote):
    new_vote = int(vote)
    current_user_id = session['id']
    movieid = ObjectId(movieid)
    current_movie = movie_col.find_one(movieid)
    old_upvotes,old_downvotes = current_movie['upvotes'],current_movie['downvotes']
    new_upvotes = old_upvotes
    new_downvotes = old_downvotes
    if not str(current_user_id) in current_movie:
        if new_vote ==1:
            new_upvotes+=1
        else:
            new_downvotes+=1
    else:
        user_old_vote = current_movie[str(current_user_id)]
        if user_old_vote != new_vote:
            if new_vote ==1:
                new_upvotes +=1
                new_downvotes-=1
            else:
                new_downvotes +=1
                new_upvotes -=1
    filt = {"_id":movieid}
    updated_data = {"$set":{str(current_user_id):new_vote,"upvotes":new_upvotes,"downvotes":new_downvotes}}
    movie_col.update_one(filt,updated_data)
    return redirect(url_for('profile'))
#
# @app.route("/addreview/<movieid>",methods=['PUT'])
# @jwt_required()
# def addreview(movieid):
#     movieid = ObjectId(movieid)
#     current_movie = movie_col.find_one({"_id":movieid})
#     current_user_email = get_jwt_identity()
#     current_user = user_col.find_one({"email":current_user_email})
#     user_id = str(current_user['_id'])
#     user_name = current_user['username']
#     review = request.json['review']
#     if user_id in current_movie['reviews']:
#         response = movie_col.update_one({"_id":movieid},{"$set":{"reviews."+user_id:(user_name,review)}})
#         output = "review updated successfully" if response.modified_count >0 else "nothing updated"
#     else:
#         old_reviews = current_movie['reviews']
#         old_reviews[user_id] = (user_name,review)
#         response = movie_col.update_one({"_id":movieid},{"$set":{"reviews":old_reviews}})
#         output = "review added Succesfully"
#     return jsonify({"status" :output})
if __name__ == '__main__':
    app.run(debug=True, port=9000)
