import time

from werkzeug.security import generate_password_hash

from . import db


class Users(db.Model):
    __tablename__ = 'tbl_users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(128), index=True, unique=True, nullable=False)
    email = db.Column(db.String(128), index=True, unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)

    def __repr__(self):
        return '<Users %r>' % self.username


class UsersInfo(db.Model):
    __tablename__ = 'tbl_users_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('tbl_users.id'))
    register_time = db.Column(db.String(32), nullable=False)
    last_login_time = db.Column(db.String(32), nullable=False, default=str(int(time.time())))
    last_login_ip = db.Column(db.String(32), nullable=True)
    token = db.Column(db.String(32), nullable=True)
    qiniu_have_account = db.Column(db.Integer, nullable=False)
    qiniu_access_key = db.Column(db.String(64), nullable=True)
    qiniu_secret_key = db.Column(db.String(64), nullable=True)
    qiniu_bucket_name = db.Column(db.String(64), nullable=True)
    qiniu_domain = db.Column(db.String(64), nullable=True)
    is_active = db.Column(db.Integer, nullable=False)

    def __init__(self, id, user_id, register_time, last_login_time, last_login_ip, token, is_active,
                 qiniu_have_account, qiniu_access_key, qiniu_secret_key, qiniu_bucket_name, qiniu_domain):
        self.id = id
        self.user_id = user_id
        self.register_time = str(int(time.time()))
        self.last_login_time = str(int(time.time()))
        self.last_login_ip = last_login_ip
        self.token = token
        self.qiniu_have_account = qiniu_have_account
        self.qiniu_access_key = qiniu_access_key
        self.qiniu_secret_key = qiniu_secret_key
        self.qiniu_bucket_name = qiniu_bucket_name
        self.qiniu_domain = qiniu_domain
        self.is_active = is_active

    def __repr__(self):
        return '<UsersInfo %r>' % self.user_id


class Admin(db.Model):
    __tablename__ = 'tbl_admin'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(128), index=True, unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return '<Admin %r>' % self.username


class AdminInfo(db.Model):
    __tablename__ = 'tbl_admin_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('tbl_admin.id'))
    register_time = db.Column(db.String(255), nullable=False)
    last_login_time = db.Column(db.String(255), nullable=False, default=str(int(time.time())))
    last_login_ip = db.Column(db.String(32), nullable=True)

    def __init__(self, id, admin_id, register_time, last_login_time, last_login_ip):
        self.id = id
        self.admin_id = admin_id
        self.register_time = str(int(time.time()))
        self.last_login_time = str(int(time.time()))
        self.last_login_ip = last_login_ip

    def __repr__(self):
        return '<AdminInfo %r>' % self.admin_id


class Images(db.Model):
    __tablename__ = 'tbl_images'
    image_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(1024))
    link = db.Column(db.String(128), unique=True, nullable=False)       # link in piss
    filename = db.Column(db.String(64), index=True, nullable=False)
    upload_time = db.Column(db.String(32), nullable=False)
    upload_user_id = db.Column(db.Integer, db.ForeignKey('tbl_users.id'))
    use_default_config = db.Column(db.Integer, nullable=False)

    def __init__(self, image_id, title, description, filename, link, upload_time, upload_user_id, use_default_config):
        self.image_id = image_id
        self.title = title
        self.description = description
        self.filename = filename
        self.link = link
        self.upload_time = upload_time
        self.upload_user_id = upload_user_id
        self.use_default_config = use_default_config

    def __repr__(self):
        return '<Images %r-%r>' % (self.image_id, self.filename)


class WebConfig(db.Model):
    __tablename__ = 'tbl_web_config'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    config_name = db.Column(db.String(255), unique=True, index=True, nullable=False)
    config_value = db.Column(db.String(255), nullable=False)

    def __init__(self, id, config_name, config_value):
        self.id = id
        self.config_name = config_name
        self.config_value = config_value

    def __repr__(self):
        return '<WebConfig %r - %r>' % (self.config_name, self.config_value)
