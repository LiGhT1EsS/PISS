# coding: utf-8
import os
import urllib

from flask import redirect, url_for, session, flash, Response
from PIL import Image

from . import api
from ..models import Users, Images


@api.route('/<username>/<image_name>')
def image_map(username, image_name):
    # TODO: add cache to this route
    user = Users.query.filter_by(username=username).first_or_404()
    image = Images.query.filter_by(filename=image_name).first_or_404()

    if user.id != image.upload_user_id:
        return redirect(url_for('error.e500'))

    img_link = image.link
    wp = urllib.urlopen(img_link)
    content = wp.read()
    return Response(content, mimetype='image')


@api.route('/thumbnail/<username>/<image_name>')
def thumbnail_image_map(username, image_name):
    # TODO: add cache to this route
    user = Users.query.filter_by(username=username).first_or_404()
    image = Images.query.filter_by(filename=image_name).first_or_404()

    if user.id != image.upload_user_id:
        return redirect(url_for('error.e404'))

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


@api.route('/api/get_all_images_count')
def get_all_images_count():
    if session.get('is_login') is None or not session.get('is_login'):
        flash(u'请先登录！', 'danger')
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    images = Images.query.filter_by(upload_user_id=user_id).count()
    return str(images)
