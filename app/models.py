import hashlib
from flask.helpers import url_for
from flask_wtf.form import FlaskForm
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.orm import backref
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from . import login_manager
from flask import current_app, request
from datetime import datetime
import bleach
from markdown import markdown


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class Permissions:
    LIKE = 1
    COMMENT = 2
    FOLLOW = 4
    POST = 8
    MODERATE = 16
    ADMIN = 32

class Save(db.Model):
    __tablename__ = 'saves'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Like(db.Model):
    __tablename__ = 'likes'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)
    liker_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    disabled = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'), tags=allowed_tags, strip=True
        ))

    def to_json(self):
        comment = {
            'id': self.id,
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'post_id': self.post_id,
            'user_id': self.user_id
        }
        return comment

db.event.listen(Comment.body, 'set', Comment.on_changed_body)

class Follow(db.Model):
    __tablename__ = 'follows'
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(64))
    caption = db.Column(db.Text)
    caption_html = db.Column(db.Text)
    location = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    saves = db.relationship('Save', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'p']
        target.caption_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'), tags=allowed_tags, strip=True
        ))

    def to_json(self):
        post = {
            'id': self.id,
            'image': request.url_root + url_for('static', filename='uploads/' + self.image),
            'caption_html': self.caption_html,
            'caption': self.caption,
            'timestamp': self.timestamp,
            'likes': self.likes.count(),
            'user_id': self.user_id
        }
        return post

db.event.listen(Post.caption, 'set', Post.on_changed_body)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs) -> None:
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles_assignment = {
            'User': [Permissions.LIKE, Permissions.COMMENT,
                        Permissions.FOLLOW, Permissions.POST],
            'Moderator': [Permissions.LIKE, Permissions.COMMENT, 
                            Permissions.FOLLOW, Permissions.POST, Permissions.MODERATE],
            'Administrator': [Permissions.LIKE, Permissions.COMMENT, Permissions.FOLLOW, 
                            Permissions.POST, Permissions.MODERATE, Permissions.ADMIN]
        }

        default_role = 'User'
        for r in roles_assignment:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.set_permissions_default()
            for perm in roles_assignment[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()


    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def set_permissions_default(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self) -> str:
        return f'Role: {self.name}, Permissions: {self.permissions}'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64))
    confirmed = db.Column(db.Boolean, default=False)
    private = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text)
    about_me_html = db.Column(db.Text)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    instagram_handle = db.Column(db.String(64))
    twitter_handle = db.Column(db.String(64)) 
    facebook_handle = db.Column(db.String(64))
    full_name = db.Column(db.String(64))
    avatar_hash = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    posts = db.relationship('Post', backref='user', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    saves = db.relationship('Save', backref='user', lazy='dynamic')
    followed = db.relationship('Follow', 
                                foreign_keys=[Follow.follower_id],
                                backref=db.backref('follower', lazy='joined'),
                                lazy='dynamic', 
                                cascade='all, delete-orphan')
    follower = db.relationship('Follow', 
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['UIMAGE_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar() 
        self.follow(self)    
           

    def __repr__(self) -> str:
        return f'Username: {self.username}, email: {self.email}, role: {self.role}'

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'span']
        target.about_me_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'), tags=allowed_tags, strip=True
        ))

    def instagram_url(self):
        if self.instagram_handle is not None:
            return f'https://instagram.com/{self.instagram_handle}'

    def twitter_url(self):
        if self.twitter_handle is not None:
            return f'https://twitter.com/{self.twitter_handle}'

    def facebook_url(self):
        if self.facebook_handle is not None:
            return f'https://facebook.com/{self.facebook_handle}'

    @property
    def password(self):
        raise AttributeError('This attribute cannot be accessed')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def confirm_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_admin(self):
        return self.can(Permissions.ADMIN)

    def gravatar(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar_url(self, size=100, default='robohash', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar()
        return f'{url}/{hash}?s={size}&d={default}&r={rating}'

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
    
    def like(self, post):
        if not self.has_liked(post):
            like = Like(user=self, post=post)
            db.session.add(like)


    def unlike(self, post):
        like = self.likes.filter_by(post_id=post.id).first()
        if like:
            db.session.delete(like)

    def has_liked(self, post):
        if post is None:
            return False
        return self.likes.filter_by(post_id=post.id).first() is not None
    
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        if user is None:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None   

    def is_followed_by(self, user):
        if user is None:
            return False
        return self.follower.filter_by(follower_id=user.id).first() is not None  

    def generate_confirmation_token(self, expires=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires)
        return s.dumps({'id': self.id}).decode('UTF-8')

    def confirm_token(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('UTF-8'))
        except:
            return False
        if data['id'] is None:
            return False
        if data['id'] != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def change_email_token(self, email):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=3600)
        return s.dumps({'id': self.id, 'email': email}).decode('UTF-8')

    def confirm_email_token(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('UTF-8'))
        except:
            return False
        if data['id'] is None:
            return False
        new_mail = data['email']
        if data['id'] != self.id:
            return False
        if self.query.filter_by(email=new_mail).first() is not None:
            return False
        self.email = new_mail
        self.avatar_hash = self.gravatar()
        db.session.add(self)
        return True

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.user_id).filter(Follow.follower_id == self.id)

    def generate_auth_token(self, expires):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires)
        return s.dumps({'email': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data['email'] is None:
            return False
        email = data['email']
        return User.query.get_or_404(email)

    def generate_reset_token(self, expires=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def reset_token(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token).encode('utf-8')
        except:
            return False
        if data['id'] is None:
            return False
        user = User.query.get(id)
        user.password = new_password
        db.session.add(user)
        return True

    def to_json(self):
        user = {
            'id': self.id,
            'username': self.username,
            'about_me': self.about_me,
            'about_me_html': self.about_me_html,
            'date_joined': self.date_joined,
            'instagram_url': self.instagram_url(),
            'twitter_url': self.twitter_url(),
            'facebook_url': self.facebook_url(),
            'avatar': self.gravatar_url()
        }
        return user

    def save(self, post):
        if not self.has_saved(post):
            s = Save(user=self, post=post)
            db.session.add(s)

    def unsave(self, post):
        if self.has_saved(post):
            s = self.saves.filter_by(post_id=post.id).first()
            db.session.delete(s)

    def has_saved(self, post):
        if post is None:
            return False
        return self.saves.filter_by(post_id=post.id).first() is not None

db.event.listen(User.about_me, 'set', User.on_changed_body)


class AnonymousUser(AnonymousUserMixin):
    def can(self, perm):
        return False

    def is_admin(self):
        return False
    
    def like(self):
        return False


login_manager.anonymous_user = AnonymousUser