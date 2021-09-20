from app.api.errors import bad_request, forbidden
from flask.helpers import make_response, url_for
from . import api
from ..models import Permissions, Post, User
from flask import jsonify, request, current_app, g, abort
from ..utils import save_image
from ..errors import ValidationError
from .decorators import permission_required
from .. import db
import os

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@api.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())


@api.route('/posts/', methods=['GET'])
def get_posts():
    """Return a list of posts
    This endpoint returns a list of posts."""
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['UIMAGE_POSTS_PER_PAGE'], error_out=False)
    posts = [post.to_json() for post in pagination.items]
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page+1)
   
    return jsonify({
        'posts': posts,
        'prev_url': prev,
        'next_url': next,
        'total': pagination.total
    })

@api.route('/posts/', methods=['POST'])
@permission_required(Permissions.POST)
def new_post():
    """Create New Post
    This endpoint takes a form to create a new post."""
    if 'file' not in request.files:
        return jsonify({'error': 'Post do not have body'}), 400
    file = request.files.get('file')
    caption = request.form.get('caption', '')
    location = request.form.get('location', '')
    if file is None or file == '':
        return jsonify({'error': 'Post does not have a body.'}), 400
    filename = save_image(file)
    post = Post(image=filename, 
                caption=caption, 
                location=location)
    post.user = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, {'Location': url_for('api.get_post', id=post.id)}


@api.route('/posts/<int:id>', methods=['DELETE'])
@permission_required(Permissions.POST)
def delete_post(id):
    """Delete a post
    This endpoint deletes the post returned by its id."""
    post = Post.query.get_or_404(id)
    if g.current_user != post.user:
        return forbidden('Post is not yours.')
    page = request.args.get('page', 1, int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['UIMAGE_POSTS_PER_PAGE'], error_out=False)
#    os.remove(os.path.join(path, current_app.config['UPLOAD_PATH'], post.image))
    db.session.delete(post)
    db.session.commit()
    return jsonify({
        'success': True,
        'deleted': id,
        'total': pagination.total
    })

@api.route('/posts/<int:id>', methods=['PATCH'])
@permission_required(Permissions.POST)
def edit_post(id):
    """Edit a post
    This endpoint edits the post returned by its id."""
    body = request.get_json()
    if body is None or body == '':
        return bad_request('Post does not have a body.')
    post = Post.query.get_or_404(id)
    if post.user != g.current_user:
        return forbidden('This post is not yours.')
    post.caption = body.get('caption')
    post.location = body.get('location')
    db.session.commit()
    return jsonify({
        'success': True,
        'id': id
    })


@api.route('/users/<int:id>/posts/')
def get_user_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination =user.posts.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['UIMAGE_POSTS_PER_PAGE'], error_out=False)
    posts = [post.to_json() for post in pagination.items]
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page+1)
   
    return jsonify({
        'posts': posts,
        'prev_url': prev,
        'next_url': next,
        'total': pagination.total
    })