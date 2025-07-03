from flask_login import UserMixin

class User(UserMixin):
    id = None
    username =  None
    name = None
    relevant = 1
    admin = 0
    color = None