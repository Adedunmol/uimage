import base64
from io import StringIO
import unittest
from base64 import b64encode
from flask import json, current_app
from werkzeug.wrappers import response
from app import create_app, db
import os
from app.models import Role, User, Post
from werkzeug.datastructures import FileStorage
import datetime


class ApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.client = self.app.test_client()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def get_api_headers(self, username, password):
        return {
            'Authorization': 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_no_auth(self):
        response = self.client.get('/api/v1/posts/', content_type='application/json')

        self.assertEqual(response.status_code, 401)

    def test_bad_auth(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('john@example.com', 'dog'))
        self.assertEqual(response.status_code, 401)

    def test_token_auth(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('bad token', ''))
        self.assertEqual(response.status_code, 401)

        response = self.client.post('/api/v1/tokens/', headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']

        response = self.client.get(
            '/api/v1/posts/',
            headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            '/api/v1/posts/1',
            headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(
            '/api/v1/posts/1',
            headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 404)

      
        filename = 'C:\\Users\\HP  ELITEBOOK  2170P\\Uimage\\app\\static/uploads\\mypic.png'
        my_file = FileStorage(
            stream=open(filename, "rb"),
        filename="mypic.png",
        content_type="image",
        )

        #create a new post
        response = self.client.post('/api/v1/posts/', content_type='multipart/form-data', 
                                    data={'file': my_file, 'caption': 'hello'}, headers={
            'Authorization': 'Basic ' + b64encode(
                ('john@example.com' + ':' + 'cat').encode('utf-8')).decode('utf-8'),
            'Accept': 'multipart/form-data',
            'Content-Type': 'multipart/form-data'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 201)

        #get a specific post
        response = self.client.patch('/api/v1/posts/1', data=json.dumps({'caption': 'hello there'}), content_type='application/json', headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

        #get a post comments
        response = self.client.get('/api/v1/posts/1/comments/', headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

        #get all comments
        response = self.client.get('/api/v1/comments/', headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

        #delete a post
        response = self.client.delete('/api/v1/posts/1', headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

        #get a user posts
        response = self.client.get('/api/v1/users/1/posts/', headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

        #get users
        response = self.client.get('/api/v1/users/', headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

        #get a user
        response = self.client.get('/api/v1/users/1/', headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

    def test_anonymous(self):
        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('', ''))
        self.assertEqual(response.status_code, 401)

    def test_unconfirmed_account(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', role=r)
        db.session.add(u)
        db.session.commit()

        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 403)