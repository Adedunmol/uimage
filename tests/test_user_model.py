from wtforms.validators import Email
from app import db, create_app
from app.models import User, Permissions, Role, AnonymousUser
import unittest
from flask import current_app


class UserModelTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        
    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_current_app(self):
        self.assertFalse(current_app is None)

    def test_create_app(self):
        self.assertTrue(current_app.config['TESTING'] is not None)

    def test_user(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='dunmola@example.com', password='cat')

        self.assertTrue(u1 is not None)
        self.assertTrue(u2 is not None)
        self.assertTrue(u1.password_hash != u2.password_hash)
        self.assertTrue(u1.password_hash is not None)

    def test_user_role(self):
        u = User(email='john@example.com', password='cat')
        self.assertTrue(u.can(Permissions.LIKE))
        self.assertTrue(u.can(Permissions.COMMENT))
        self.assertTrue(u.can(Permissions.POST))
        self.assertTrue(u.can(Permissions.FOLLOW))
        self.assertFalse(u.can(Permissions.MODERATE))
        self.assertFalse(u.can(Permissions.ADMIN))

    def test_admin_role(self):
        u = User(email='oyewaleadedunmola@gmail.com', password='cat')
        self.assertTrue(u.can(Permissions.LIKE))
        self.assertTrue(u.can(Permissions.COMMENT))
        self.assertTrue(u.can(Permissions.POST))
        self.assertTrue(u.can(Permissions.FOLLOW))
        self.assertTrue(u.can(Permissions.MODERATE))
        self.assertTrue(u.can(Permissions.ADMIN))

    def test_moderator_role(self):
        r = Role.query.filter_by(name='Moderator').first()
        u = User(email='john@example.com', password='cat', role=r)
        self.assertTrue(u.can(Permissions.LIKE))
        self.assertTrue(u.can(Permissions.COMMENT))
        self.assertTrue(u.can(Permissions.POST))
        self.assertTrue(u.can(Permissions.FOLLOW))
        self.assertTrue(u.can(Permissions.MODERATE))
        self.assertFalse(u.can(Permissions.ADMIN))

    def test_gravatar(self):
        u = User(email='john@example.com')
        self.assertTrue(u.avatar_hash is not None)

    def test_confirm_password(self):
        u = User(email='john@example.com', password='cat')
        self.assertTrue(u.confirm_password('cat'))

    def test_is_admin(self):
        u = User(email='john@example.com', password='cat')
        self.assertFalse(u.is_admin())

    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permissions.LIKE))
        self.assertFalse(u.can(Permissions.COMMENT))
        self.assertFalse(u.can(Permissions.POST))
        self.assertFalse(u.can(Permissions.MODERATE))
        self.assertFalse(u.can(Permissions.FOLLOW))
        self.assertFalse(u.can(Permissions.ADMIN))

    def test_password_error(self):
        u = User(email='oyewaleadedunmola@gmail.com', password='cat')
        with self.assertRaises(AttributeError):
            u.password()

    def test_follow(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='dunmola@example.com', password='cat')

        u1.follow(u2)
        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))

    def test_unfollow(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='dunmola@example.com', password='cat')

        u1.follow(u2)
        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))

        u1.unfollow(u2)
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u2.is_followed_by(u1))
    
    def test_about_me_html(self):
        u1 = User(email='john@example.com', password='cat', about_me='This is going to be interesting.')

        self.assertTrue(u1.about_me is not None)
        self.assertTrue(u1.about_me_html is not None)

    def test_ping(self):
        u1 = User(email='john@example.com', password='cat')
        u1.ping()

        self.assertTrue(u1.last_seen is not None)

    def test_date_joined(self):
        u1 = User(email='john@example.com', password='cat')

        self.assertTrue(u1.date_joined is not None)
    
    def test_self_follow(self):
        u1 = User(email='john@example.com', password='cat')

        self.assertTrue(u1.is_following(u1))

    def test_urls(self):
        u = User(email='john@example.com', password='cat', confirmed=True)
        db.session.add(u)
        db.session.commit()
        self.assertIsNotNone(u)

        self.assertIsNotNone(u.instagram_url)
        self.assertIsNotNone(u.facebook_url)
        self.assertIsNotNone(u.twitter_url)

        u.instagram_handle = 'john'
        u.twitter_handle = 'john'
        u.facebook_handle = 'john'
        db.session.commit()

        self.assertIsNotNone(u.facebook_handle)
        self.assertIsNotNone(u.twitter_handle)
        self.assertIsNotNone(u.instagram_handle)