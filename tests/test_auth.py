'''
账号验证测试模块
'''
from flask import url_for

from tests.base import BaseTestCase


class AuthTestCase(BaseTestCase):

    def test_login_user(self):
        response = self.login()
        data = response.get_data(as_text=True)
        self.assertIn('欢迎回来，马克！', data)

    def test_fail_login(self):
        response = self.login(username='123', password='123')
        data = response.get_data(as_text=True)
        self.assertIn('错误的用户名或密码！', data)

    def test_logout_user(self):
        self.login()
        response = self.logout()
        data = response.get_data(as_text=True)
        self.assertIn('你已经登出账号！', data)
