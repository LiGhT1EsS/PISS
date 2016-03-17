# coding: utf-8
import re
import time

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import check_password_hash
from flask import render_template, redirect, url_for, session, flash, request

from . import user
from .. import app
from ..models import db, Users, UsersInfo
from ..forms import RegisterForm, LoginForm
from ..common import random_str, send_mail


@user.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    data = {
        'title': 'Register',
        'form': register_form,
    }

    if register_form.validate_on_submit():
        # get data from form
        username = register_form.username.data
        password = register_form.password.data
        confirm_password = register_form.confirmPassword.data
        email = register_form.email.data

        # check data
        if len(username) < 2:
            flash(u'用户名长度不能小于2！', 'danger')
            return redirect(url_for('.register'))
        if password != confirm_password:
            flash(u'两次密码不匹配！', 'danger')
            return redirect(url_for('.register'))
        if len(password) < 6:
            flash(u'密码长度不能小于6！', 'danger')
            return redirect(url_for('.register'))
        if not re.match(r'\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*', email):
            flash(u'Email地址不规范！', 'danger')
            return redirect(url_for('.register'))

        # Check Username is already register
        user = Users.query.filter_by(username=username).first()
        if user is not None or user:
            flash(u'用户名已存在！', 'danger')
            return redirect(url_for('.register'))

        # Insert into database
        user = Users(id="", username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        user = Users.query.filter_by(username=username).first_or_404()
        tid = user.id
        users_info = UsersInfo(id="", user_id=tid,
                               register_time="", last_login_time="", last_login_ip=request.remote_addr,
                               token=random_str(32), is_active=0, qiniu_have_account=0, qiniu_access_key=None,
                               qiniu_secret_key=None, qiniu_bucket_name=None, qiniu_domain=None)
        db.session.add(users_info)
        db.session.commit()

        session['user_id'] = tid

        # Send mail
        s = Serializer(app.config['SECRET_KEY'], 3600)
        token = s.dumps({'user_id': tid})

        send_mail(email, ' Please confirm your account',
                  'mail/confirm', username=username, token=token)

        # return result
        flash(u'注册成功！请到邮箱查看验证邮件，验证通过后方可登录。', 'success')
        return redirect(url_for('.register'))
    return render_template("user/register.html", data=data)


@user.route('/confirm/<token>')
def confirm(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except:
        return redirect(url_for('error.e500'))
    user_id = data.get('user_id')
    users_info = UsersInfo.query.filter_by(user_id=user_id).first_or_404()
    if users_info.is_active == 1:
        flash(u'你已经激活过了，请登录！', 'danger')
        return redirect(url_for('user.login'))
    else:
        users_info.is_active = 1
        db.session.add(users_info)
        db.session.commit()
        flash(u'激活成功，请登录！', 'success')
        return redirect(url_for('user.login'))


@user.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    data_login = {
        'form': login_form,
        'title': 'Login',
    }

    if session.get('is_login'):
        return redirect(url_for('upload.main_view'))

    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data

        user = Users.query.filter_by(username=username).first()
        if user is None:
            flash(u'用户名或密码错误！', 'danger')
            return render_template('user/login.html', data=data_login)
        user_info = UsersInfo.query.filter_by(user_id=user.id).first()
        if user is not None and user_info is not None:
            user_info = UsersInfo.query.filter_by(user_id=user.id).first()
            if user_info.is_active == 1:
                if check_password_hash(user.password, password):
                    # set session
                    session['username'] = username
                    session['user_token'] = user_info.token
                    session['user_id'] = user.id
                    session['is_login'] = True
                    session['qiniu_have_account'] = user_info.qiniu_have_account
                    login_ip = request.remote_addr
                    user_info.last_login_ip = login_ip
                    user_info.last_login_time = time.time()
                    db.session.add(user_info)
                    db.session.commit()
                    return redirect(url_for('upload.main_view'))
                else:
                    flash(u'用户名或密码错误！', 'danger')
                    return render_template('user/login.html', data=data_login)
            else:
                flash(u'您的账户尚未激活，请查看您的邮箱并验证', 'danger')
                return render_template('user/login.html', data=data_login)
        else:
            flash(u'用户名或密码错误！', 'danger')
            return render_template('user/login.html', data=data_login)
    return render_template('user/login.html', data=data_login)


@user.route('/logout')
def logout():
    if session['is_login'] is not None and session['is_login'] is not False:
        session.pop('username')
        session.pop('user_token')
        session.pop('user_id')
        session.pop('is_login')

        data = {
            'title': 'Logout',
        }

        flash(u'你已成功退出！', 'success')
        return render_template('user/logout.html', data=data)

