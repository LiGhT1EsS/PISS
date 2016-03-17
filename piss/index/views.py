# coding: utf-8

from flask import render_template

from . import index


@index.route('/')
@index.route('/index')
def index():
    data = {'title': 'Home'}
    return render_template("index/index.html", data=data)

