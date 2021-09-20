from flask.helpers import url_for
from . import api
from flask import jsonify, request, current_app
from ..models import Comment, Post

@api.route('/posts/<int:id>/comments/')
def get_comment_of_post(id):
    """Return comments of a post
    This endpoint returns all comments related to a post by its id."""
    page = request.args.get('page', 1, type=int)
    post = Post.query.get_or_404(id)
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(page, per_page=current_app.config['UIMAGE_COMMENTS_PER_PAGE'], error_out=False)
    comments = [comment.to_json() for comment in pagination.items]
    prev_url = None
    if pagination.has_prev:
        prev_url = url_for('api.get_comment_of_post', page=page-1)
    next_url = None
    if pagination.has_next:
        next_url = url_for('api.get_comment_of_post', page=page+1)
    
    return jsonify({
        'total': pagination.total,
        'prev_url': prev_url,
        'comments': comments,
        'next_url': next_url
    })


@api.route('/comments/')
def get_comments():
    """Return all comments
    This endpoint returns a list of comments."""
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page=current_app.config['UIMAGE_COMMENTS_PER_PAGE'], error_out=False)
    posts = [comment.to_json() for comment in pagination.items]
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page-1)
    next = None
    if pagination.has_prev:
        next = url_for('api.get_comments', page=page+1)
    return jsonify({
        'posts': posts,
        'prev_url': prev,
        'next_url': next,
        'total': pagination.total
    })