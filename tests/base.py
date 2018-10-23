'''
单元测试上下文注册模块
'''

import unittest

from flask import url_for

from marcBlog import create_app
from marcBlog.extensions import db
from marcBlog.models import Admin


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app('testing')
        self.context=app.test_request_context()
        self.context.push()
        self.client=app.test_client()
        self.runner=app.test_cli_runner()

        db.create_all()
        user=Admin(name='marc',username='marc',about='testing',blog_title='testing',blog_sub_title='testing')
        user.set_password('123')
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.drop_all()
        self.context.pop()

    def login(self,username=None,password=None):
        if username is None and password is None:
            username='marc'
            password='123'

        return self.client.post(url_for('auth.login'),data=dict(
            username=username,
            password=password
        ),follow_redirects=True)

    def logout(self):
        return self.client.get(url_for('auth.logout'),follow_redirects=True)