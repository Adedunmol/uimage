from app.main.forms import CommentForm, EditPostForm, EditProfileAdminForm, PostForm, EditProfileForm
from flask.helpers import flash, url_for
from flask_login.utils import login_required
from . import main
from ..models import Comment, Follow, Permissions, Role, Save, User
from flask import render_template, redirect, current_app, request, session
from flask_login import current_user
from ..utils import save_image
from ..models import Post
from .. import db
import os
from ..decorators import admin_required, permission_required
from flask_sqlalchemy import get_debug_queries


path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@main.app_context_processor
def inject_permissions():
    return dict(Permissions=Permissions)

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['UIMAGE_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow Query: %s\nParameters: %s\nDuration: %s\nContext: %s\n' % (query.statement, query.parameters, query.duration, query.context)
            )
    return response

@main.route('/')
def home():
    if current_user.is_anonymous:
        return render_template('new-home.html')
    page = request.args.get('page', 1, type=int)
    session['page'] = page
    query = None
    if current_user.is_authenticated:
        query = current_user.followed_posts
    pagination = query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['UIMAGE_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('home.html', posts=posts, pagination=pagination)


@main.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.date_joined.desc()).paginate(page, per_page=current_app.config['USERS_PER_PAGE'], error_out=False)
    users = pagination.items
    return render_template('explore.html', users=users, pagination=pagination)


@main.route('/follow/<int:id>')
@login_required
@permission_required(Permissions.FOLLOW)
def follow(id):
    user = User.query.get(id)
    if user is None:
        flash('This user does not exist')
        return redirect(url_for('main.home'))
    if current_user.is_following(user):
        flash(f'You are already following {user.username}.')
        return redirect(url_for('auth.profile', id=user.id))
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {user.username}.')
    return redirect(url_for('auth.profile', id=user.id))


@main.route('/unfollow/<int:id>')
@login_required
def unfollow(id):
    user = User.query.get(id)
    if user is None:
        flash('This user does not exist.')
        return redirect(url_for('main.home'))
    if not current_user.is_following(user):
        flash(f'You were not following {user.username}.')
        return redirect(url_for('auth.profile'))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You are no more following {user.username}.')
    return redirect(url_for('auth.profile', id=user.id))


@main.route('/like/<int:id>')
@login_required
@permission_required(Permissions.LIKE)
def like(id):
    page = session.get('page')
    post = Post.query.get_or_404(id)
    current_user.like(post)
    db.session.commit()
    return redirect(url_for('main.home', page=page))


@main.route('/unlike/<int:id>')
@login_required
def unlike(id):
    page = session.get('page')
    post = Post.query.get_or_404(id)
    current_user.unlike(post)
    db.session.commit()
    return redirect(url_for('main.home', page=page))


@main.route('/save/<int:id>')
@login_required
def save(id):
    page = session.get('page')
    post = Post.query.get_or_404(id)
    current_user.save(post)
    db.session.commit()
    flash('The post is now in your saves.')
    return redirect(url_for('main.home', page=page))


@main.route('/unsave/<int:id>')
@login_required
def unsave(id):
    page = session.get('page')
    post = Post.query.get_or_404(id)
    current_user.unsave(post)
    db.session.commit()
    flash('The post is no longer in your saves.')
    url = session['url']
    return redirect(url) if url else redirect(url_for('main.home', page=page))


@main.route('/saves/<username>')
@login_required
def saves(username):
    user = User.query.filter_by(username=username).first()
    page = request.args.get('page', 1, type=int)
    pagination = user.saves.order_by(Save.timestamp.desc()).paginate(page, per_page=current_app.config['UIMAGE_POSTS_PER_PAGE'], error_out=False)
    posts = [{'post': item.post} for item in pagination.items]
    session['url'] = request.base_url
    return render_template('saved-posts.html', posts=posts, pagination=pagination)


@main.route('/new-post', methods=['GET', 'POST'])
@login_required
@permission_required(Permissions.POST)
def new_post():
    form = PostForm()
    if form.validate_on_submit() and current_user.can(Permissions.POST):
        filename = save_image(form.image.data)
        post = Post(image=filename, caption=form.caption.data, location=form.location.data, user=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been published.')
        return redirect(url_for('main.home'))
    return render_template('new-post.html', form=form)


@main.route('/edit-post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    if current_user != post.user:
        return redirect(url_for('main.home'))
    form = EditPostForm()
    if form.validate_on_submit():
        if current_user.is_admin() or current_user == post.user:
            post.caption = form.caption.data
            post.location = form.location.data
            db.session.add(post)
            db.session.commit()
            flash('The post has been updated.')
            return redirect(url_for('main.home'))
        flash('This is not your post.')
    form.caption.data = post.caption
    form.location.data = post.location
    return render_template('edit-post.html', form=form)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.private = form.private.data
        current_user.location = form.location.data
        current_user.instagram_handle = form.insta_handle.data
        current_user.twitter_handle = form.twitter_handle.data
        current_user.facebook_handle = form.facebook_handle.data
        db.session.commit()
        flash('Your page has been updated.')
        return redirect(url_for('auth.profile', id=current_user.id))
    form.full_name.data = current_user.full_name
    form.username.data = current_user.username
    form.about_me.data = current_user.about_me
    form.private.data = current_user.private
    form.location.data = current_user.location
    form.insta_handle.data = current_user.instagram_handle
    form.twitter_handle.data = current_user.twitter_handle
    form.facebook_handle.data = current_user.facebook_handle
    return render_template('edit-profile.html', form=form)


@main.route('/edit-profile-admin/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get(id)
    form = EditProfileAdminForm(user)
    if form.validate_on_submit():
        user.full_name = form.full_name.data
        user.username = form.username.data
        user.about_me = form.about_me.data
        user.private = form.private.data
        user.role = Role.query.get(form.role.data)
        user.location = form.location.data
        user.instagram_handle = form.insta_handle.data
        user.twitter_handle = form.twitter_handle.data
        user.facebook_handle = form.facebook_handle.data
        db.session.commit()
        return redirect(url_for('auth.profile', id=current_user.id))
    form.full_name.data = user.full_name
    form.username.data = user.username
    form.about_me.data = user.about_me
    form.private.data = user.private
    form.role.data = user.role_id
    form.location.data = user.location
    form.insta_handle.data = user.instagram_handle
    form.twitter_handle.data = user.twitter_handle
    form.facebook_handle.data = user.facebook_handle
    return render_template('edit-profile-admin.html', form=form)


@main.route('/delete/<int:id>')
@login_required
def delete_post(id):
    post = Post.query.get(id)
    if current_user == post.user or current_user.is_admin():
        
#        os.remove(os.path.join(path, current_app.config['UPLOAD_PATH'], post.image))
        db.session.delete(post)
        db.session.commit()
        flash('The post has been deleted.')
        return redirect(url_for('main.home'))


@main.route('/followers/<username>')
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.follower.order_by(Follow.timestamp).paginate(page=page, per_page=current_app.config['USERS_PER_PAGE'], error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('users.html', follows=follows, pagination=pagination, user=user, title='Followers of')


@main.route('/following/<username>')
@login_required
def following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.order_by(Follow.timestamp).paginate(page=page, per_page=current_app.config['USERS_PER_PAGE'], error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('users.html', follows=follows, pagination=pagination, user=user, title='Followings of')


@main.route('/posts/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.comment.data, user=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('The comment has been published.')
        return redirect(url_for('.comment', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count()) // current_app.config['UIMAGE_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['UIMAGE_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form, comments=comments, pagination=pagination)


@main.route('/disable/<int:id>')
@permission_required(Permissions.MODERATE)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.commit()
    flash('The comment has been disabled.')
    return redirect(url_for('.moderate'))


@main.route('/enable/<int:id>')
@permission_required(Permissions.MODERATE)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.commit()
    flash('The comment has been enabled.')
    return redirect(url_for('.moderate'))


@main.route('/moderate')
@permission_required(Permissions.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).\
        paginate(page, per_page=current_app.config['UIMAGE_COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('moderate.html', pagination=pagination, comments=comments)