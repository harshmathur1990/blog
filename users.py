from main import app
import json
from models import users, posts
from database import engine
import sqlalchemy
from flask import request, jsonify

@app.route('/users', methods=['POST'])
def create_user():
    data = json.loads(request.get_data())
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        error = {
            'error': 'username and password mandatory for creating user'
        }
        resp = jsonify(error)
        resp.status_code = 400
        return resp
    user_insert = users.insert().values(username=username, password=password)
    conn = engine.connect()
    try:
        result = conn.execute(user_insert)
    except sqlalchemy.exc.IntegrityError:
        error = {
            'error': u'username {} already exists'.format(username)
        }
        resp = jsonify(error)
        resp.status_code = 400
        conn.close()
        return resp
    conn.close()
    res = {
        'id': result.inserted_primary_key
    }
    resp = jsonify(res)
    resp.status_code = 201
    return resp


@app.route('/users/<user_id>')
def get_users(user_id=None):
    pass