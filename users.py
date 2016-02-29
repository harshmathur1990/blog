from flask import Blueprint
import json
from models import users, posts
from database import engine
import sqlalchemy
from flask import request, jsonify

user_routes = Blueprint('user_routes', __name__)


def validate_for_user(data):
    username = data.get('username')
    password = data.get('password')
    error = None
    if not username or not password:
        error = {
            'error': 'username and password mandatory for creating user'
        }
    return error


@user_routes.route('/users', methods=['POST'])
def create_user():
    data = json.loads(request.get_data())
    error = validate_for_user(data)
    if error:
        resp = jsonify(error)
        resp.status_code = 400
        return resp
    user_insert = users.insert()\
        .values(username=data.get('username'), password=data.get('password'))
    conn = engine.connect()
    try:
        result = conn.execute(user_insert)
    except sqlalchemy.exc.IntegrityError:
        error = {
            'error': u'username {} already exists'.format(data.get('username'))
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


@user_routes.route('/users/<user_id>')
@user_routes.route('/users')
def get_users(user_id=None):
    if not user_id:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        stmt = users.select().limit(per_page).offset((page-1)* per_page)
        total_stmt = users.select()
        conn = engine.connect()
        result = conn.execute(stmt)
        total_result = conn.execute(total_stmt)
        conn.close()
        rows = result.fetchall()
        total = total_result.rowcount
        l = [dict(r) for r in rows]
        result_resp = {
            'total': total,
            'data': l
        }
        resp = jsonify(result_resp)
        resp.status_code = 200
        return resp
    else:
        stmt = users.select().where(users.c.id == int(user_id))
        conn = engine.connect()
        result = conn.execute(stmt)
        conn.close()
        rows = result.fetchall()
        total = result.rowcount
        l = [dict(r) for r in rows]
        result_resp = {
            'total': total,
            'data': l
        }
        resp = jsonify(result_resp)
        resp.status_code = 200
        return resp


@user_routes.route('/users/<user_id>', methods=['DELETE'])
def delete_users(user_id):
    stmt = users.delete().where(users.c.id == int(user_id))
    conn = engine.connect()
    conn.execute(stmt)
    result_resp = {
        'success': True,
    }
    resp = jsonify(result_resp)
    resp.status_code = 200
    return resp


@user_routes.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = json.loads(request.get_data())
    error = validate_for_user(data)
    if error:
        resp = jsonify(error)
        resp.status_code = 400
        return resp
    stmt = users.update()\
        .where(users.c.id == int(user_id))\
        .values(username=data.get('username'), password=data.get('password'))
    conn = engine.connect()
    result = conn.execute(stmt)
    status_code = 200
    if not result.rowcount:
        user_insert = users.insert()\
            .values(username=data.get('username'), password=data.get('password'), id=int(user_id))
        conn.execute(user_insert)
        status_code = 201
    conn.close()
    res = {
        'id': user_id
    }
    resp = jsonify(res)
    resp.status_code = status_code
    return resp