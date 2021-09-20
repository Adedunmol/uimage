import unittest
from app import create_app, db
from app.models import Role, User, Post
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

    def test_post(self):
        u = User(email='hello@example.com', password='cat')
        post = Post(image='/app/static/uploads/mypic.png', caption='Hello', location='Ede,Osun', timestamp=datetime.utcnow(), user=u)
        
        self.assertTrue(post is not None)
        self.assertTrue(post.image is not None)
        self.assertTrue(post.location is not None)
        self.assertTrue(post.caption_html is not None)
        self.assertTrue(post.timestamp is not None)
        self.assertTrue(post.user is not None)

        u.like(post)
        self.assertTrue(u.has_liked(post))

        u.save(post)
        self.assertTrue(u.has_saved(post))
