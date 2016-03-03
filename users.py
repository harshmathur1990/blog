from flask import Blueprint
import json
from models import users, token
from database import engine
import sqlalchemy
from flask import request, jsonify
from utils import check_login, unauthenticated
from sqlalchemy.sql import select
import uuid
import datetime

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
        stmt = select([users.c.id, users.c.username, users.c.created_at, users.c.updated_at])\
            .limit(per_page).offset((page-1)* per_page)
        total_stmt = select([users.c.id])
        conn = engine.connect()
        result = conn.execute(stmt)
        total_result = conn.execute(total_stmt)
        conn.close()
        rows = result.fetchall()
        total = total_result.rowcount
    else:
        stmt = select([users.c.id, users.c.username, users.c.created_at, users.c.updated_at])\
            .where(users.c.id == int(user_id))
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


@user_routes.route('/users/<int:user_id>', methods=['DELETE'])
@check_login
def delete_users(user_id):
    if user_id != request.user.get('id'):
        error = {
            'error': 'Unauthorized'
        }
        resp = jsonify(error)
        resp.status_code = 401
        return resp
    stmt = users.delete().where(users.c.id == int(user_id))
    conn = engine.connect()
    conn.execute(stmt)
    result_resp = {
        'success': True,
    }
    resp = jsonify(result_resp)
    resp.status_code = 200
    return resp


@user_routes.route('/users/<int:user_id>', methods=['PUT'])
@check_login
def update_user(user_id):
    if user_id != request.user.get('id'):
        error = {
            'error': 'Unauthorized'
        }
        resp = jsonify(error)
        resp.status_code = 401
        return resp
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


@user_routes.route('/login', methods=['POST'])
def api_token():
    data = json.loads(request.get_data())
    error = validate_for_user(data)
    if error:
        resp = jsonify(error)
        resp.status_code = 400
        return resp
    stmt = users.select()\
        .where(users.c.username == data.get('username'))\
        .where(users.c.password == data.get('password'))
    conn = engine.connect()
    result = conn.execute(stmt)
    conn.close()
    if result.rowcount:
        # authenticated now, generate or fetch token
        user_obj = dict(result.fetchone())
        now = datetime.datetime.now()
        fifteen_minutes_back = now - datetime.timedelta(minutes=15)
        token_ext = token.select()\
            .where(token.c.user_id == user_obj.get('id'))\
            .where(token.c.last_accessed_at > fifteen_minutes_back)
        conn = engine.connect()
        fetch_token_result = conn.execute(token_ext)
        conn.close()
        if fetch_token_result.rowcount:
            # token exists, just return
            return jsonify({
                'token': dict(fetch_token_result.fetchone()).get('token')
            })
        else:
            # create, persist and return the token
            token_string = uuid.uuid4()
            token_stmt = token.insert().values(user_id=user_obj.get('id'), token=unicode(token_string))
            conn = engine.connect()
            conn.execute(token_stmt)
            conn.close()
            return jsonify({
                'token': token_string
            })
    else:
        # unauthenticated
        return unauthenticated()