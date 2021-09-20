import unittest

from sqlalchemy.sql.elements import RollbackToSavepointClause
from app import create_app, db
from app.models import Role, User
import re


class HomePageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True) 

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')

        self.assertTrue('Hello' in response.get_data(as_text=True))
        self.assertEqual(response.status_code, 200)

    def test_registration_and_login(self):
        #create a new account
        response = self.client.post('/auth/register', data={
            'email': 'john@example.com',
            'username': 'john',
            'password1': '12345',
            'password2': '12345'
        })
        self.assertEqual(response.status_code, 302)

        #login with the created account
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': '12345'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Hello, john!' in response.get_data(as_text=True))
        self.assertTrue('You have not confirmed your account yet.' in response.get_data(as_text=True))

        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get(f'/auth/confirm/{token}', follow_redirects=True)
        user.confirm_token(token)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/explore')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/new-post')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/edit-profile')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/auth/change-email')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/auth/change-password')
        self.assertEqual(response.status_code, 200)

    def test_forgot_password(self):
        response = self.client.get('/auth/forgot-password')
        self.assertEqual(response.status_code, 200)