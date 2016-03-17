# coding: utf-8
import os
import re
import time
import urllib

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import check_password_hash
from flask import render_template, redirect, url_for, session, flash, request, Response
from qiniu import Auth, put_file
from PIL import Image

from app import app
from models import db, Users, UsersInfo, WebConfig, Images
from forms import RegisterForm, LoginForm, UploadForm, BaseSettingForm
from common import random_str, send_mail


@app.route('/')
@app.route('/index')
def index():
    data = {'title': 'Home'}
    return render_template("index.html", data=data)


@app.errorhandler(404)
def page_not_found(e):
    data = {
        'e': e,
    }
    return render_template('404.html', data=data), 404


@app.route('/404')
def e404():
    return redirect('404.html')


@app.errorhandler(500)
def internal_server_error(e):
    data = {
        'e': e,
    }
    return render_template('404.html', data=data), 500


@app.route('/500')
def e500():
    return redirect('500.html')


@app.errorhandler(405)
def method_not_allowed(e):
    data = {
        'e': e,
    }
    return render_template('405.html', data=data), 405


@app.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('register'))
        if password != confirm_password:
            flash(u'两次密码不匹配！', 'danger')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash(u'密码长度不能小于6！', 'danger')
            return redirect(url_for('register'))
        if not re.match(r'\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*', email):
            flash(u'Email地址不规范！', 'danger')
            return redirect(url_for('register'))

        # Check Username is already register
        user = Users.query.filter_by(username=username).first()
        if user is not None or user:
            flash(u'用户名已存在！', 'danger')
            return redirect(url_for('register'))

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
        return redirect(url_for('register'))
    return render_template("register.html", data=data)


@app.route('/confirm/<token>')
def confirm(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except:
        return redirect('500.html')
    user_id = data.get('user_id')
    users_info = UsersInfo.query.filter_by(user_id=user_id).first_or_404()
    if users_info.is_active == 1:
        flash(u'你已经激活过了，请登录！', 'danger')
        return redirect(url_for('login'))
    else:
        users_info.is_active = 1
        db.session.add(users_info)
        db.session.commit()
        flash(u'激活成功，请登录！', 'success')
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    data_login = {
        'form': login_form,
        'title': 'Login',
    }

    if session.get('is_login'):
        return redirect(url_for('main_view'))

    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data

        user = Users.query.filter_by(username=username).first()
        if user is None:
            flash(u'用户名或密码错误！', 'danger')
            return render_template('login.html', data=data_login)
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
                    return redirect(url_for('main_view'))
                else:
                    flash(u'用户名或密码错误！', 'danger')
                    return render_template('login.html', data=data_login)
            else:
                flash(u'您的账户尚未激活，请查看您的邮箱并验证', 'danger')
                return render_template('login.html', data=data_login)
        else:
            flash(u'用户名或密码错误！', 'danger')
            return render_template('login.html', data=data_login)
    return render_template('login.html', data=data_login)


@app.route('/logout')
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
        return render_template('logout.html', data=data)


@app.route('/main')
def main_view():
    current_username = session.get('username')
    current_user_token = session.get('user_token')
    current_user_id = session.get('user_id')
    current_is_login = session.get('is_login')
    if current_is_login is None or not current_is_login:
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))

    upload_form = UploadForm()
    data = {
        'title': 'Home',
        'current_username': current_username,
        'current_user_token': current_user_token,
        'current_user_id': current_user_id,
        'form': upload_form,
    }

    user_info = UsersInfo.query.filter_by(user_id=current_user_id).first()
    if user_info is None or not user_info:
        return redirect(url_for('e500'))
    if user_info.qiniu_access_key == '' or user_info.qiniu_secret_key == '' or \
       user_info.qiniu_bucket_name == '' or user_info.qiniu_domain == '' or \
       user_info.qiniu_access_key is None or user_info.qiniu_secret_key is None or \
       user_info.qiniu_bucket_name is None or user_info.qiniu_domain is None:
        flash(u'您还未设置七牛密钥信息，请去个人中心中设置', 'danger')
        data['no_account'] = 1
        return render_template('main.html', data=data)
    images = Images.query.filter_by(upload_user_id=current_user_id, use_default_config=0).all()
    max_upload_count = WebConfig.query.filter_by(config_name='default_upload_count').first()
    if len(images) >= int(max_upload_count.config_value):
        flash(u'您已上传的图片数量到达系统限制，使用自己的七牛密钥后可以上传更多图片，请到个人中心设置。', 'danger')
        data['no_account'] = 1
        return render_template('main.html', data=data)
    return render_template('main.html', data=data)


@app.route('/upload', methods=['POST'])
def upload():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))
    upload_form = UploadForm()

    # print dir(upload_form.file_upload.data)
    # print dir(upload_form.file_upload.data.stream)
    # print upload_form.file_upload.data.stream.read()
    if upload_form.validate_on_submit():
        # check access key and secret key and image limit
        current_user_id = session.get('user_id')
        user_info = UsersInfo.query.filter_by(user_id=current_user_id).first()
        if user_info is None or not user_info:
            return redirect(url_for('e500'))
        if user_info.qiniu_access_key == '' or user_info.qiniu_secret_key == '' or \
           user_info.qiniu_bucket_name == '' or user_info.qiniu_domain == '' or \
           user_info.qiniu_access_key is None or user_info.qiniu_secret_key is None or \
           user_info.qiniu_bucket_name is None or user_info.qiniu_domain is None:
            # flash(u'您还未设置七牛密钥信息，请去个人中心中设置', 'danger')
            return redirect(url_for('main_view'))
        images = Images.query.filter_by(upload_user_id=current_user_id, use_default_config=0).all()
        max_upload_count = WebConfig.query.filter_by(config_name='default_upload_count').first()
        if len(images) >= int(max_upload_count.config_value):
            # flash(u'您已上传的图片数量到达系统限制，
            # 使用自己的七牛密钥后可以上传更多图片，请到个人中心设置。', 'danger')
            return redirect(url_for('main_view'))
        upload_filename = upload_form.file_upload.data.filename
        ext = os.path.splitext(upload_filename)[1]

        # save file in tmp directory
        local_filename = random_str(32) + ext
        with open('tmp/'+local_filename, 'wb') as ff:
            ff.write(upload_form.file_upload.data.stream.read())

        # init qiniu
        current_user_id = session.get('user_id')
        users_info = UsersInfo.query.filter_by(user_id=current_user_id).first()
        access_key = users_info.qiniu_access_key
        secret_key = users_info.qiniu_secret_key
        bucket_name = users_info.qiniu_bucket_name
        domain = users_info.qiniu_domain

        q = Auth(access_key, secret_key)
        remote_filename = local_filename
        upload_token = q.upload_token(bucket_name, remote_filename, 3600)
        local_file = 'tmp/' + local_filename
        ret, info = put_file(upload_token, remote_filename, local_file)

        url = 'http://' + domain + '/' + ret['key']
        # url2 = request.host_url + session.get('username') + '/' + local_filename
        # print '[*]', url
        # insert into image table
        title = upload_form.title.data
        description = upload_form.description.data
        qiniu_have_account = session.get('qiniu_have_account')
        if qiniu_have_account is None:
            flash(u'系统错误！请稍后再试！', 'danger')
            return redirect(url_for('main_view'))
        # use_default_config = 0: use system config
        # use_default_config = 1: use user's config
        images = Images(image_id='', title=title, description=description, filename=local_filename,
                        link=url, upload_time=str(int(time.time())), upload_user_id=current_user_id,
                        use_default_config=qiniu_have_account)
        db.session.add(images)
        db.session.commit()

        user_dir = 'tmp/' + session.get('username') + '/'
        if not os.path.exists(user_dir):
            os.mkdir(user_dir)
        thumbnail_file = user_dir + local_filename
        im = Image.open(local_file)
        im.thumbnail((128, 128))
        im.save(thumbnail_file)

        if os.path.exists(local_file):
            os.remove(local_file)

        flash(u'上传成功！链接为 '+url+'，您可在个人中心中查看已上传的全部图片。', 'success')
        return redirect(url_for('main_view'))
    return redirect(url_for('main_view'))


@app.route('/my', methods=['GET'])
def me_main_view():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))

    data = {
        'title': 'Personal Center',
    }

    return render_template('my.html', data=data)


@app.route('/my_basic_info')
def my_basic_info():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))

    current_user_id = session.get('user_id')
    user_info = UsersInfo.query.filter_by(user_id=current_user_id).first()
    if user_info is None or not user_info:
        return redirect(url_for('e500'))

    already_register_time = (int(time.time()) - int(user_info.register_time))
    date_array = time.localtime(float(user_info.last_login_time))
    user_info.last_login_time = time.strftime('%Y-%m-%d %H:%M', date_array)

    images = Images.query.filter_by(upload_user_id=current_user_id).all()

    data = {
        'title': '',
        'last_login_time': user_info.last_login_time,
        'qiniu_have_account': user_info.qiniu_have_account,
        'last_login_ip': user_info.last_login_ip,
        'already_register_time': (already_register_time/(3600*24))+1,
        'images_number': len(images),
    }

    return render_template('my_basic_info.html', data=data)


@app.route('/my_basic_setting', methods=['GET', 'POST'])
def my_basic_setting():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))

    basic_setting_form = BaseSettingForm()

    is_allow_no_qiniu_key = WebConfig.query.filter_by(config_name='is_allow_no_qiniu_key').first()
    default_upload_count = WebConfig.query.filter_by(config_name='default_upload_count').first()

    data = {
        'form': basic_setting_form,
    }

    if is_allow_no_qiniu_key.config_value == '1':
        data['is_allow_no_qiniu_key'] = is_allow_no_qiniu_key.config_value
        data['default_upload_count'] = default_upload_count.config_value

    current_user_id = session.get('user_id')
    users_info = UsersInfo.query.filter_by(user_id=current_user_id).first_or_404()

    if users_info.qiniu_have_account == 0:
        data['qiniu_have_account'] = 1
    else:
        data['current_access_key'] = users_info.qiniu_access_key
        data['current_secret_key'] = users_info.qiniu_secret_key
        data['current_bucket_name'] = users_info.qiniu_bucket_name
        data['current_domain'] = users_info.qiniu_domain

    if request.method == 'POST':

        is_have_account = request.form.get('is_have_account')
        access_key = request.form.get('access_key').strip()
        secret_key = request.form.get('secret_key').strip()
        bucket_name = request.form.get('bucket_name').strip()
        domain = request.form.get('domain').strip()

        if is_have_account is None or not is_have_account:
            # use user's qiniu account
            users_info.qiniu_have_account = 1
            users_info.qiniu_access_key = access_key
            users_info.qiniu_secret_key = secret_key
            users_info.qiniu_bucket_name = bucket_name
            if domain[:7] == 'http://':
                domain = domain[7:]
            elif domain[:8] == 'https://':
                domain = domain[8:]
            users_info.qiniu_domain = domain
            session['qiniu_have_account'] = 1

        else:
            # use system qiniu account
            default_access_key = WebConfig.query.filter_by(config_name='default_access_key').first()
            default_secret_key = WebConfig.query.filter_by(config_name='default_secret_key').first()
            default_bucket_name = WebConfig.query.filter_by(config_name='default_bucket_name').first()
            default_domain = WebConfig.query.filter_by(config_name='default_domain').first()

            if default_access_key is None or default_secret_key is None or default_bucket_name is None:
                return '<div class="alert alert-danger"><button type="button" ' \
                       'class="close" data-dismiss="alert">' \
                       '&times;</button>系统配置错误！</div>'

            users_info.qiniu_have_account = 0
            users_info.qiniu_access_key = default_access_key.config_value
            users_info.qiniu_secret_key = default_secret_key.config_value
            users_info.qiniu_bucket_name = default_bucket_name.config_value
            users_info.qiniu_domain = default_domain.config_value
            session['qiniu_have_account'] = 0

        db.session.add(users_info)
        db.session.commit()
        return '<div class="alert alert-success"><button type="button" ' \
               'class="close" data-dismiss="alert">' \
               '&times;</button>保存成功！</div>'

    return render_template('my_basic_setting.html', data=data)


@app.route('/<username>/<image_name>')
def image_map(username, image_name):
    # TODO: add cache to this route
    user = Users.query.filter_by(username=username).first_or_404()
    image = Images.query.filter_by(filename=image_name).first_or_404()

    if user.id != image.upload_user_id:
        return redirect(url_for('404'))

    img_link = image.link
    wp = urllib.urlopen(img_link)
    content = wp.read()
    return Response(content, mimetype='image')


@app.route('/thumbnail/<username>/<image_name>')
def thumbnail_image_map(username, image_name):
    # TODO: add cache to this route
    user = Users.query.filter_by(username=username).first_or_404()
    image = Images.query.filter_by(filename=image_name).first_or_404()

    if user.id != image.upload_user_id:
        return redirect(url_for('e404'))

    if not os.path.exists('tmp/'+session.get('username')+'/'+image.filename):
        # get image from qiniu
        wp = urllib.urlopen(image.link)
        content = wp.read()
        wp.close()
        with open('tmp/'+image.filename, 'wb') as ff:
            ff.write(content)
        im = Image.open('tmp/'+image.filename)
        im.thumbnail((128, 128))
        im.save('tmp/'+session.get('username')+'/'+image.filename)
        os.remove('tmp/'+image.filename)

    content = ''
    with open('tmp/' + session.get('username') + '/' + image.filename, 'rb') as ff:
        content = ff.read()
    return Response(content, mimetype='image')


@app.route('/my_images/<int:page>')
def my_images(page=1):
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))

    tid = session.get('user_id')
    if tid is None or not tid:
        return redirect(url_for('e500'))

    thumbnail_dir = 'tmp/' + session.get('username') + '/'
    if not os.path.exists(thumbnail_dir):
        os.mkdir(thumbnail_dir)
    images = Images.query.filter_by(upload_user_id=tid).\
        order_by(Images.upload_time.desc()).paginate(page, per_page=5, error_out=False)

    for image in images.items:
        # update time format
        date_array = time.localtime(float(image.upload_time))
        image.upload_time = time.strftime('%Y-%m-%d %H:%M:%S', date_array)
        # get thumbnail file, if not exists, get exists from qiniu
        if not os.path.exists(thumbnail_dir + image.filename):
            # get file from qiniu
            wp = urllib.urlopen(image.link)
            content = wp.read()
            wp.close()
            with open('tmp/'+image.filename, 'wb') as ff:
                ff.write(content)
            im = Image.open('tmp/'+image.filename)
            im.thumbnail((128, 128))
            im.save(thumbnail_dir + image.filename)
            os.remove('tmp/'+image.filename)

    data = {
        'pagination': images,
        'images': images.items,
        'thumbnail_url': request.host_url + 'thumbnail/',
        'username': session.get('username'),
        'current_page': page,
    }

    return render_template('my_images.html', data=data)


@app.route('/my_help')
def my_help():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))

    data = {
        'title': '',
    }

    return render_template('my_help.html', data=data)


@app.route('/my_edit_image/<int:image_id>')
def my_edit_image(image_id):
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))
    data = {
        'title': '',
        'back_page': '',
    }

    current_user_id = session.get('user_id')
    current_username = session.get('username')
    if current_user_id is None or not current_user_id:
        return redirect(url_for('e404'))
    if current_username is None or not current_username:
        return redirect(url_for('e404'))

    image = Images.query.filter_by(upload_user_id=current_user_id, image_id=image_id).first_or_404()
    if image.upload_user_id != current_user_id:
        return redirect(url_for('e404'))

    data['img_id'] = image.image_id
    data['img_title'] = image.title
    data['img_description'] = image.description
    data['img_link'] = image.link
    data['img_filename'] = image.filename
    data['thumbnail_url'] = request.host_url + 'thumbnail/'
    data['username'] = current_username

    return render_template('my_edit_image.html', data=data)


@app.route('/my_edit_image_save', methods=['POST'])
def my_edit_image_save():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_title = request.form.get('title')
        new_description = request.form.get('description')
        image_id = request.form.get('image_id')

        if image_id is None or not image_id:
            return redirect(url_for('e404'))

        if new_title is None or not new_title:
            return '<div class="alert alert-danger"><button type="button" ' \
                    'class="close" data-dismiss="alert">' \
                    '&times;</button>标题不能为空！</div>'

        current_user_id = session.get('user_id')
        image = Images.query.filter_by(upload_user_id=current_user_id, image_id=image_id).first_or_404()
        image.title = new_title
        image.description = new_description
        db.session.add(image)
        db.session.commit()

        return '<div class="alert alert-success"><button type="button" ' \
                'class="close" data-dismiss="alert">' \
                '&times;</button>保存成功！</div>'

    return redirect(url_for('me_main_view'))


@app.route('/api/get_all_images_count')
def get_all_images_count():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    images = Images.query.filter_by(upload_user_id=user_id).count()
    return str(images)


@app.route('/setup/<token>', methods=['GET'])
def setup(token):
    # db.create_all()
    # default config
    # 未提供七牛key的用户的最大上传数量
    web_config = WebConfig(id='', config_name='default_upload_count', config_value='10')
    db.session.add(web_config)
    # 网站是否允许未提供七牛key的用户上传, 1 - allow, 0 - deny
    web_config = WebConfig(id='', config_name='is_allow_no_qiniu_key', config_value='1')
    db.session.add(web_config)
    # 网站默认的七牛key和bucket
    web_config = WebConfig(id='', config_name='default_bucket_name', config_value='piss-default')
    db.session.add(web_config)
    web_config = WebConfig(id='',
                           config_name='default_access_key',
                           config_value='')
    db.session.add(web_config)
    web_config = WebConfig(id='',
                           config_name='default_secret_key',
                           config_value='')
    db.session.add(web_config)
    db.session.commit()
    web_config = WebConfig(id='',
                           config_name='default_domain',
                           config_value='')
    db.session.add(web_config)
    db.session.commit()
