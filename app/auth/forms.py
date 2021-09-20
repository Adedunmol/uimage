from flask_wtf import FlaskForm
from flask_wtf.recaptcha import validators
from wtforms import StringField, PasswordField, SubmitField, validators, BooleanField
from wtforms.validators import Length, EqualTo, ValidationError, DataRequired, Regexp
from app.models import User


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), validators.email()])
    username = StringField('Username', validators=[DataRequired(), Length(1, 64), 
                        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots or underscores ')])
    password1 = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), Length(5, 20), EqualTo('password1', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already exists.')

    def validate_email(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log in')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(1, 64)])
    new_password2 = PasswordField('Confirm Password', validators=[DataRequired(), Length(1, 64), EqualTo('new_password')])
    submit = SubmitField('Submit')

class ChangeEmailForm(FlaskForm):
    old_email = StringField('Old Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    new_email = StringField('New Email', validators=[DataRequired(), validators.email()])
    submit = SubmitField('Submit')

    def validate_new_email(self, new_email):
        user = User.query.filter_by(email=new_email.data).first()
        if user:
            raise ValidationError('This email is taken.')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email')
    submit = SubmitField('Submit')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('This email does not exist.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Submit')