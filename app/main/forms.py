from flask_wtf import FlaskForm
from wtforms import FileField, StringField, SubmitField, SelectField
from wtforms.fields import core
from wtforms.fields.core import BooleanField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_wtf.file import FileRequired, FileAllowed
from flask_pagedown.fields import PageDownField
from ..models import User, Role


class PostForm(FlaskForm):
    image = FileField('Image', validators=[FileRequired(), 
                        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images and GIFs only')])
    location = StringField('Location', validators=[Length(0, 64)])
    caption = PageDownField('Caption')
    submit = SubmitField('Post')


class EditPostForm(FlaskForm):
    location = StringField('Location', validators=[Length(0, 64)])
    caption = PageDownField('Caption')
    submit = SubmitField('Update')


class EditProfileForm(FlaskForm):
    username = StringField('New Username', validators=[Length(0, 64)])
    full_name = StringField('Full Name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0,64)])
    private = BooleanField('Private')
    about_me = PageDownField('About Me')
    insta_handle = StringField('Instagram Handle', validators=[Length(0, 64)])
    twitter_handle = StringField('Twitter Handle', validators=[Length(0, 64)])
    facebook_handle = StringField('Facebook Handle', validators=[Length(0, 64)])
    submit = SubmitField('Update')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_username(self, username):
        if username.data != self.user.username and \
            User.query.filter_by(username=username.data):
            raise ValidationError('Username already taken.')



class EditProfileAdminForm(FlaskForm):
    username = StringField('New Username', validators=[Length(0, 64)])
    full_name = StringField('Full Name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0,64)])
    private = BooleanField('Private')
    role = SelectField('Role', coerce=int)
    about_me = PageDownField('About Me')
    insta_handle = StringField('Instagram Handle', validators=[Length(0, 64)])
    twitter_handle = StringField('Twitter Handle', validators=[Length(0, 64)])
    facebook_handle = StringField('Facebook Handle', validators=[Length(0, 64)])
    submit = SubmitField('Update')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_username(self, username):
        if username.data != self.user.username and \
            User.query.filter_by(username=username.data):
            raise ValidationError('Username already taken.')


class CommentForm(FlaskForm):
    comment = PageDownField('Comment')
    submit = SubmitField('Submit')
