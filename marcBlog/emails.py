'''
邮件发送类
'''
from threading import Thread

from flask import url_for, current_app
from flask_mail import Message

from marcBlog.extensions import mail


# 异步发送邮件
def _send_async_mail(app, message):
    with app.app_context():
        mail.send(message)


# 发送邮件基本方法,在多线程方法中必须传入_get_current_object才能获取到代理的真实对象
def send_mail(subject, to, html):
    app = current_app._get_current_object()
    message = Message(subject, recipients=[to], html=html)
    thr = Thread(target=_send_async_mail, args=[app, message])
    thr.start()
    return thr


def send_new_comment_email(post):
    post_url = url_for('blog.show_post', post_id=post.id, _external=True) + '#comments'
    send_mail(subject='网站有新的评论待审核！', to=current_app.config['ADMIN_MAIL'],
              html='<p><i>%s</i>这篇文章有新的评论了，点击下面的链接来查看：</p>'
                   '<p><a href="%s">%s</a></p>'
                   '<p><small style="color:#868e96">不要回复这封邮件</small></p>'
                   % (post.title, post_url, post_url))


def send_new_reply_email(comment):
    post_url = url_for('blog.show_post', post_id=comment.post_id, _external=True) + '#comments'
    send_mail(subject='【Marc的个人博客】您的评论有新的回复了！', to=comment.email,
              html='您在Marc博客下的<p><i>%s</i>这篇文章下的评论有新的回复了，点击下面的链接来查看：</p>'
                   '<p><a href="%s">%s</a></p>'
                   '<p><small style="color:#868e96">不要回复这封邮件。</small></p>'
                   % (comment.post.title, post_url, post_url))
