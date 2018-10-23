'''
使用工厂方法初始化项目配置
'''

import logging
import os
from logging.handlers import SMTPHandler, RotatingFileHandler

import click
from flask import Flask, render_template, request
from flask_login import current_user
from flask_sqlalchemy import get_debug_queries
from flask_wtf.csrf import CSRFError

from marcBlog.blueprints.admin import admin_bp
from marcBlog.blueprints.auth import auth_bp
from marcBlog.blueprints.blog import blog_bp
from marcBlog.extensions import bootstrap, db, login_manager, csrf, ckeditor, mail, moment, toolbar, migrate
from marcBlog.models import Admin, Post, Category, Comment, Link
from marcBlog.settings import config

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def register_logging(app):
    class RequestFormatter(logging.Formatter):
        def format(self, record):
            record.url = request.url
            record.remote_addr = request.remote_addr
            return super(RequestFormatter, self).format(record)

    request_formatter = RequestFormatter(
        '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
        '%(levelname)s in %(module)s: %(message)s'
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler(
        os.path.join(basedir, 'logs/bluelog.log'),
        maxBytes=10 * 1024 * 1024, backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    mail_handler = SMTPHandler(
        mailhost=app.config['MAIL_SERVER'],
        fromaddr=app.config['MAIL_USERNAME'],
        toaddrs=app.config['ADMIN_EMAIL'],
        subject='MarcLog发现了程序错误！',
        credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']))
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(request_formatter)

    if not app.debug:
        app.logger.addHandler(mail_handler)
        app.logger.addHandler(file_handler)

def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    ckeditor.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    toolbar.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app):
    app.register_blueprint(blog_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')


def register_commands(app):
    # 初始化数据库操作,is_flag将--drop选项设为布尔值
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop')
    def initdb(drop):
        if drop:
            click.confirm('**Will** delete the database,CONTINUE?', abort=True)
            db.drop_all()
            click.echo('Drop tables...')
        db.create_all()
        click.echo('Initial database done.')

    # 初始化博客内容，包括Admin账号，博客默认分类
    @app.cli.command()
    @click.option('--username', prompt=True, help='administrator username.')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='administrator password.')
    def init(username, password):
        click.echo('Initializing database...')
        db.create_all()

        # 初始化Admin账号,用于上线阶段
        admin = Admin.query.first()
        if admin is not None:
            click.echo('Administrator already exists,updating...')
            admin.username = username
            admin.set_password(password)
        else:
            click.echo('Creating administrator...')
            admin = Admin(
                username=username,
                blog_title='Marc的个人博客',
                blog_sub_title='Music is the answer.',
                name='博客管理员',
                about='He didn\'t say anything!'
            )
            admin.set_password(password)
            db.session.add(admin)

        # 初始化Category
        category = Category.query.first()
        if category is None:
            click.echo('Creating the default category...')
            category = Category(name='随记')
            db.session.add(category)

        # 初始化数据完毕，提交数据库
        db.session.commit()
        click.echo('Done.')

    # 使用fake数据填充博客用于测试
    @app.cli.command()
    @click.option('--category', default=10, help='Quantity of categories, default is 10.')
    @click.option('--post', default=50, help='Quantity of posts, default is 50.')
    @click.option('--comment', default=500, help='Quantity of comments, default is 500.')
    def forge(category, post, comment):
        from marcBlog.fakes import fake_admin, fake_categories, fake_posts, fake_comments, fake_links

        db.drop_all()
        db.create_all()

        click.echo('Generating the administrator...')
        fake_admin()

        click.echo('Generating %d categories...' % category)
        fake_categories(category)

        click.echo('Generating %d posts...' % post)
        fake_posts(post)

        click.echo('Generating %d comments...' % comment)
        fake_comments(comment)

        click.echo('Generating links...')
        fake_links()

        click.echo('Done.')


def register_errors(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', description=e.description), 400


# 注册flask_shell上下文
def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, Admin=Admin, Post=Post, Category=Category, Comment=Comment)


# 注册模板页面上下文
def register_template_context(app):
    @app.context_processor
    def make_template_context():
        admin = Admin.query.first()
        categories = Category.query.order_by(Category.name).all()
        links = Link.query.order_by(Link.name).all()
        if current_user.is_authenticated:
            unread_comments = Comment.query.filter_by(reviewed=False).count()
        else:
            unread_comments = None
        return dict(
            admin=admin, categories=categories,
            links=links, unread_comments=unread_comments
        )


def register_request_handlers(app):
    @app.after_request
    def query_profiler(response):
        for q in get_debug_queries():
            if q.duration >= app.config['SLOW_QUERY']:
                app.logger.warning(
                    'Slow query:Duration: %fs\n Context: %s\n Query: %s\n'
                    % (q.duration, q.context, q.statement)
                )
        return response

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('marcBlog')
    app.config.from_object(config[config_name])

    register_logging(app)
    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errors(app)
    register_shell_context(app)
    register_template_context(app)
    register_request_handlers(app)

    return app
