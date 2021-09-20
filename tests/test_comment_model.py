import unittest
from app import create_app, db
from app.models import Comment, Role, User, Post
from datetime import datetime


class PostModelTestCase(unittest.TestCase):
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

    def test_comment(self):
        u = User(email='hello@example.com', password='cat')
        post = Post(image='/app/static/uploads/mypic.png', caption='Hello', location='Ede,Osun', timestamp=datetime.utcnow(), user=u)
        comment = Comment(body='hi', timestamp=datetime.utcnow(), user=u, post=post)
        
        self.assertTrue(comment is not None)
        self.assertTrue(comment.post is not None)
        self.assertTrue(comment.body is not None)
        self.assertTrue(comment.body_html is not None)
        self.assertTrue(comment.timestamp is not None)
        self.assertTrue(comment.user is not None)