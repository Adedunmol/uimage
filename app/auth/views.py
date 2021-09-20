from datetime import datetime
from flask import render_template, redirect, request, current_app
from flask.helpers import flash, url_for
from flask_login.utils import login_required, login_user, logout_user
from . import auth
from .forms import ChangeEmailForm, ForgotPasswordForm, RegistrationForm, LoginForm, ChangePasswordForm, ResetPasswordForm
from app.models import Post, User
from app import db
from app.email import send_mail
from flask_login import current_user


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
            and request.blueprint != 'auth' \
            and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data.lower(),
                    username=form.username.data, 
                    password=form.password1.data,
                    date_joined=datetime.utcnow())
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_mail(user.email, 'Confirm Your Account', 'auth/mail/confirm', user=user, token=token)
        flash('A confirmation mail has been sent to you by email.')
        return redirect(url_for('auth.login')), 302
    return render_template('register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.confirm_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next = request.args.get('next')
            flash('You are now logged in.')
            return redirect(next) if next else redirect(url_for('main.home'))
        flash('Incorrect details.')
    return render_template('login.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm_token(token):
        db.session.commit()
        return redirect(url_for('main.home'))
    else:
        flash('The token is invalid or expired.')
    return redirect(url_for('main.home'))


@auth.route('/unconfirm')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('main.home'))
    return render_template('unconfirmed.html')


@auth.route('/resend-confirmation')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_mail(current_user.email, 'Confirm Your Account', 'auth/mail/confirm',
                token=token, user=current_user)
    flash('Another confirmation mail has been sent to your email.')
    return redirect(url_for('main.home'))


@auth.route('/profile/<int:id>')
@login_required
def profile(id):
    page = request.args.get('page', 1, type=int)
    user = User.query.get_or_404(id)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['UIMAGE_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    if user is None:
        flash('This user does not exist.')
        return redirect(url_for('main.home'))
    return render_template('profile.html', user=user, posts=posts, pagination=pagination)


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.confirm_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('main.home'))
        flash('Invalid Password.')
    return render_template('change-password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def reset_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.confirm_password(form.password.data):
            token = current_user.change_email_token(form.new_email.data)
            send_mail(form.new_email.data, 'Change Email', 'auth/mail/change-mail', user=current_user, token=token)
            flash('A confirmation link has been sent to you by email.')
            return redirect(url_for('main.home'))
        flash('Invalid email or password.')
    return render_template('change-email.html', form=form)


@auth.route('confirm-email/<token>')
@login_required
def change_email(token):
    if current_user.confirm_email_token(token):
        db.session.commit()
        flash('Your email has been updated.')
    else:
        flash('invalid details.')
    return redirect(url_for('main.home'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if not current_user.is_anonymous:
        return redirect(url_for('main.home'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_reset_token()
            send_mail(form.email.data, 'Forgot Password', 'auth/mail/forgot-password', user=user, token=token)
            flash('An email has been sent to you.')
            return redirect(url_for('auth.login'))
        flash('The email does not exist.')
    return render_template('forgot-password.html', form=form)


@auth.route('/forgot-password/<int:id>', methods=['GET', 'POST'])
def reset_password(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_token(token, form.password.data):
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            flash('The token is inavlid.')
    return render_template('password-reset.html', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))