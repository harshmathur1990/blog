from flask import Blueprint
import json
from models import posts, tags
from database import engine
import sqlalchemy
from flask import request, jsonify
from utils import check_login


post_routes = Blueprint('post_routes', __name__)


def validate_data_for_create_post(data):
    error = None
    title = data.get('title')
    description = data.get('description')
    if not title and description:
        error = {
            'error': 'title and description are mandatory'
        }
    return error


@post_routes.route('/posts', methods=['POST'])
@check_login
def create_post():
    data = json.loads(request.get_data())
    error = validate_data_for_create_post(data)
    if error:
        resp = jsonify(error)
        resp.status_code = 400
        return resp
    post_insert = posts.insert()\
        .values(title=data.get('title'), description=data.get('description'), user_id=request.user.get('id'))
    conn = engine.connect()
    result = conn.execute(post_insert)
    conn.close()
    res = {
        'id': result.inserted_primary_key
    }
    resp = jsonify(res)
    resp.status_code = 201
    return resp