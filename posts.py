from flask import Blueprint
import json
from models import posts, tags
from database import engine
from flask import request, jsonify
from utils import check_login
from sqlalchemy.sql import select
from sqlalchemy import desc, distinct


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


@post_routes.route('/posts')
@post_routes.route('/posts/<int:post_id>')
def get_post(post_id=None):
    if post_id:
        stmt = posts.select().where(posts.c.id == int(post_id))
        conn = engine.connect()
        data = conn.execute(stmt)
        conn.close()
        rows = data.fetchall()
        total = data.rowcount
    else:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        post_select = posts.select()\
            .order_by(desc("created_by"))\
            .limit(per_page).offset((page-1) * per_page)
        all_posts = posts.select()
        conn = engine.connect()
        result_posts = conn.execute(post_select)
        all_posts_res = conn.execute(all_posts)
        conn.close()
        rows = result_posts.fetchall()
        total = all_posts_res.rowcount
    l = [dict(r) for r in rows]
    result_resp = {
        'total': total,
        'data': l
    }
    resp = jsonify(result_resp)
    resp.status_code = 200
    return resp


@post_routes.route('/posts/<int:post_id>', methods=['PUT'])
@check_login
def update_posts(post_id):
    data = json.loads(request.get_data())
    error = validate_data_for_create_post(data)
    if error:
        resp = jsonify(error)
        resp.status_code = 400
        return resp
    stmt = posts.update()\
        .values(title=data.get('title'), description=data.get('description'))\
        .where(posts.c.user_id == request.user.get('id'))\
        .where(posts.c.id == int(post_id))
    conn = engine.connect()
    result = conn.execute(stmt)
    conn.close()
    if result.rowcount:
        res = {
            'success': True
        }
        return jsonify(res)
    error = {
        'error': u'No post with id {} found for User {}'.format(post_id, request.user.get('username'))
    }
    resp = jsonify(error)
    resp.status_code = 404
    return resp


@post_routes.route('/posts/<int:post_id>', methods=['DELETE'])
@check_login
def delete_post(post_id):
    stmt = posts.delete()\
        .where(posts.c.user_id == request.user.get('id'))\
        .where(posts.c.id == int(post_id))
    conn = engine.connect()
    result = conn.execute(stmt)
    conn.close()
    if result.rowcount:
        res = {
            'success': True
        }
        return jsonify(res)
    error = {
        'error': u'No post with id {} found for User {}'.format(post_id, request.user.get('username'))
    }
    resp = jsonify(error)
    resp.status_code = 404
    return resp


@post_routes.route('/posts/<int:post_id>/tags', methods=['POST'])
@check_login
def add_tags(post_id):
    data = json.loads(request.get_data())
    tags_list = data.get('tags')
    if not isinstance(tags_list, list):
        tags_list = tags_list.split(",")
    post_exists = select([posts.c.id]).where(posts.c.id == int(post_id))
    conn = engine.connect()
    post_exists_res = conn.execute(post_exists)
    conn.close()
    if not post_exists_res.rowcount:
        error = {
            'error': u'No post with id {} found for User {}'.format(post_id, request.user.get('username'))
        }
        resp = jsonify(error)
        resp.status_code = 404
        return resp
    stmt = tags.select().where(tags.c.post_id == int(post_id))
    conn = engine.connect()
    result = conn.execute(stmt)
    conn.close()
    list_of_existing_tags = [dict(r).get('tag') for r in result.fetchall()]
    tags_to_persist = [tag for tag in tags_list if tag not in list_of_existing_tags]
    if tags_to_persist:
        conn = engine.connect()
        for one_tag in tags_to_persist:
            tag_insert = tags.insert().values(post_id=int(post_id), tag=one_tag)
            conn.execute(tag_insert)
        conn.close()
    res = {
        'success': True
    }
    return jsonify(res)


@post_routes.route('/search', methods=['POST'])
def search_by_tags():
    data = json.loads(request.get_data())
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    tags_list = data.get('tags')
    if not isinstance(tags_list, list):
        tags_list = tags_list.split(",")
    post_id_select = select([distinct(tags.c.post_id)])\
        .where(tags.c.tag.in_(tags_list))\
        .limit(per_page).offset((page-1) * per_page)
    post_total = select([distinct(tags.c.post_id)])\
        .where(tags.c.tag.in_(tags_list))
    conn = engine.connect()
    result_post_id = conn.execute(post_id_select)
    result_post_total = conn.execute(post_total)
    conn.close()
    if result_post_id.rowcount:
        post_id_list = [dict(r).get('post_id') for r in result_post_id.fetchall()]
        all_matched_posts = posts.select().where(posts.c.id.in_(post_id_list))
        conn = engine.connect()
        res_all_matched_posts = conn.execute(all_matched_posts)
        conn.close()
        res = {
            'total': result_post_total.rowcount,
            'data': [dict(r) for r in res_all_matched_posts.fetchall()]
        }
        return jsonify(res)
    else:
        res = {
            'total': result_post_total.rowcount,
            'data': []
        }
        return jsonify(res)