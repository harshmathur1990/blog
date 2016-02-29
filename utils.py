import functools
from flask import request, jsonify
from models import token, users
from database import engine
import datetime
from sqlalchemy.sql import select


def is_logged_in(authorization):
    authenticated = False
    now = datetime.datetime.now()
    fifteen_minutes_back = now - datetime.timedelta(minutes=15)
    stmt = token.select()\
        .where(token.c.token == authorization and token.c.last_accessed_at > fifteen_minutes_back)
    conn = engine.connect()
    result = conn.execute(stmt)
    conn.close()
    if result.rowcount:
        token_obj = dict(result.fetchone())
        stmt = token.update()\
            .where(token.c.token == token_obj.get('token'))\
            .values(last_accessed_at=now)
        user_get = select([users.c.id, users.c.username])\
            .where(users.c.id == int(token_obj.get('user_id')))
        conn = engine.connect()
        conn.execute(stmt)
        user_res = conn.execute(user_get)
        conn.close()
        user = dict(user_res.fetchone())
        setattr(request, 'user', user)
        authenticated = True
    return authenticated


def unauthenticated():
    msg = {
        'error': 'Unauthenticated'
    }
    resp = jsonify(msg)
    resp.status_code = 401
    return resp


def check_login(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        authorization = request.headers.get('Authorization', None)
        if authorization and is_logged_in(authorization):
            return method(*args, **kwargs)
        else:
            return unauthenticated()
    return wrapper