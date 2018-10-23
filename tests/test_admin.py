'''
后台功能测试模块
'''
from  flask import url_for

from marcBlog.models import Post,Category,Comment,Link
from marcBlog.extensions import db

from tests.base import BaseTestCase

class AdminTestCase(BaseTestCase):
    def setUp(self):
        super(AdminTestCase, self).setUp()
        self.login()

        category=Category(name='Default')
        post=Post(title='testing',category=category,body='testing')
        comment=Comment(body='test comment',post=post,from_admin=True)
        link=Link(name='baidu',url='https://www.baidu.com')
        db.session.add_all([category,post,comment,link])
        db.session.commit()

    def test_new_post(self):
        response = self.client.get(url_for('admin.new_post'))
        data = response.get_data(as_text=True)
        self.assertIn('新文章', data)

        response = self.client.post(url_for('admin.new_post'), data=dict(
            title='test1',
            category=1,
            body='test1.body'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('发布成功！', data)
        self.assertIn('test1', data)
        self.assertIn('test1.body', data)

    def test_edit_post(self):
        response = self.client.get(url_for('admin.edit_post', post_id=1))
        data = response.get_data(as_text=True)
        self.assertIn('编辑文章', data)
        self.assertIn('testing', data)
        self.assertIn('testing', data)

        response = self.client.post(url_for('admin.edit_post', post_id=1), data=dict(
            title='No.1 post edited',
            category=1,
            body='No.1 post edited body'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('更改已保存。', data)
        self.assertIn('No.1 post edited', data)
        self.assertIn('No.1 post edited body', data)