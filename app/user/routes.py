from flask import Blueprint
user = Blueprint('user',__name__,url_prefix='/user')

@user.route('/register',methods=['GET','POST'])
def register():
    return "user registration page"