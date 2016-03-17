# coding: utf-8
import os
import time
import urllib

from flask import render_template, redirect, url_for, session, flash, request
from PIL import Image

from . import home
from ..models import db, UsersInfo, WebConfig, Images
from ..forms import BaseSettingForm


@home.route('/my', methods=['GET'])
def my_main_view():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('user.login'))

    data = {
        'title': 'Personal Center',
    }

    return render_template('home/my.html', data=data)


@home.route('/my_basic_info')
def my_basic_info():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('user.login'))

    current_user_id = session.get('user_id')
    user_info = UsersInfo.query.filter_by(user_id=current_user_id).first()
    if user_info is None or not user_info:
        return redirect(url_for('error.e500'))

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

    return render_template('home/my_basic_info.html', data=data)


@home.route('/my_basic_setting', methods=['GET', 'POST'])
def my_basic_setting():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('user.login'))

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

    return render_template('home/my_basic_setting.html', data=data)


@home.route('/my_images/<int:page>')
def my_images(page=1):
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('user.login'))

    tid = session.get('user_id')
    if tid is None or not tid:
        return redirect(url_for('error.e500'))

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

    return render_template('home/my_images.html', data=data)


@home.route('/my_help')
def my_help():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('user.login'))

    data = {
        'title': '',
    }

    return render_template('home/my_help.html', data=data)


@home.route('/my_edit_image/<int:image_id>')
def my_edit_image(image_id):
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('user.login'))
    data = {
        'title': '',
        'back_page': '',
    }

    current_user_id = session.get('user_id')
    current_username = session.get('username')
    if current_user_id is None or not current_user_id:
        return redirect(url_for('error.e404'))
    if current_username is None or not current_username:
        return redirect(url_for('error.e404'))

    image = Images.query.filter_by(upload_user_id=current_user_id, image_id=image_id).first_or_404()
    if image.upload_user_id != current_user_id:
        return redirect(url_for('error.e404'))

    data['img_id'] = image.image_id
    data['img_title'] = image.title
    data['img_description'] = image.description
    data['img_link'] = image.link
    data['img_filename'] = image.filename
    data['thumbnail_url'] = request.host_url + 'thumbnail/'
    data['username'] = current_username

    return render_template('home/my_edit_image.html', data=data)


@home.route('/my_edit_image_save', methods=['POST'])
def my_edit_image_save():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('user.login'))
    if request.method == 'POST':
        new_title = request.form.get('title')
        new_description = request.form.get('description')
        image_id = request.form.get('image_id')

        if image_id is None or not image_id:
            return redirect(url_for('error.e404'))

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

        return '<div class="alert alert-success"><button type="button" class="close" data-dismiss="alert">' \
               ' &times;</button>保存成功！</div>'

    return redirect(url_for('.my_main_view'))
