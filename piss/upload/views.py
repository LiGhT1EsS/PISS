# coding: utf-8
import os
import time

from flask import render_template, redirect, url_for, session, flash, request, Response
from qiniu import Auth, put_file
from PIL import Image

from . import upload
from .. import db
from ..models import UsersInfo, WebConfig, Images
from ..forms import UploadForm
from ..common import random_str


@upload.route('/main')
def main_view():
    current_username = session.get('username')
    current_user_token = session.get('user_token')
    current_user_id = session.get('user_id')
    current_is_login = session.get('is_login')
    if current_is_login is None or not current_is_login:
        flash(u'请先登录！', 'danger')
        return redirect(url_for('user.login'))

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
        return redirect(url_for('error.e500'))
    if user_info.qiniu_access_key == '' or user_info.qiniu_secret_key == '' or \
       user_info.qiniu_bucket_name == '' or user_info.qiniu_domain == '' or \
       user_info.qiniu_access_key is None or user_info.qiniu_secret_key is None or \
       user_info.qiniu_bucket_name is None or user_info.qiniu_domain is None:
        flash(u'您还未设置七牛密钥信息，请去个人中心中设置', 'danger')
        data['no_account'] = 1
        return render_template('upload/main.html', data=data)
    images = Images.query.filter_by(upload_user_id=current_user_id, use_default_config=0).all()
    max_upload_count = WebConfig.query.filter_by(config_name='default_upload_count').first()
    if len(images) >= int(max_upload_count.config_value):
        flash(u'您已上传的图片数量到达系统限制，使用自己的七牛密钥后可以上传更多图片，请到个人中心设置。', 'danger')
        data['no_account'] = 1
        return render_template('upload/main.html', data=data)
    return render_template('upload/main.html', data=data)


@upload.route('/upload', methods=['POST'])
def upload():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('user.login'))
    upload_form = UploadForm()

    # print dir(upload_form.file_upload.data)
    # print dir(upload_form.file_upload.data.stream)
    # print upload_form.file_upload.data.stream.read()
    if upload_form.validate_on_submit():
        # check access key and secret key and image limit
        current_user_id = session.get('user_id')
        user_info = UsersInfo.query.filter_by(user_id=current_user_id).first()
        if user_info is None or not user_info:
            return redirect(url_for('error.e500'))
        if user_info.qiniu_access_key == '' or user_info.qiniu_secret_key == '' or \
           user_info.qiniu_bucket_name == '' or user_info.qiniu_domain == '' or \
           user_info.qiniu_access_key is None or user_info.qiniu_secret_key is None or \
           user_info.qiniu_bucket_name is None or user_info.qiniu_domain is None:
            # flash(u'您还未设置七牛密钥信息，请去个人中心中设置', 'danger')
            return redirect(url_for('.main_view'))
        images = Images.query.filter_by(upload_user_id=current_user_id, use_default_config=0).all()
        max_upload_count = WebConfig.query.filter_by(config_name='default_upload_count').first()
        if len(images) >= int(max_upload_count.config_value):
            # flash(u'您已上传的图片数量到达系统限制，
            # 使用自己的七牛密钥后可以上传更多图片，请到个人中心设置。', 'danger')
            return redirect(url_for('.main_view'))
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
        # insert into image table
        title = upload_form.title.data
        description = upload_form.description.data
        qiniu_have_account = session.get('qiniu_have_account')
        if qiniu_have_account is None:
            flash(u'系统错误！请稍后再试！', 'danger')
            return redirect(url_for('.main_view'))
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
        return redirect(url_for('.main_view'))
    return redirect(url_for('.main_view'))
