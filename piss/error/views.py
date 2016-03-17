# coding: utf-8
from flask import render_template, redirect

from . import error


@error.route('/404')
def e404():
    return redirect('404.html')


@error.route('/500')
def e500():
    return redirect('500.html')


@error.app_errorhandler(405)
def method_not_allowed(e):
    data = {
        'e': e,
    }
    return render_template('error/405.html', data=data), 405


@error.app_errorhandler(500)
def internal_server_error(e):
    data = {
        'e': e,
    }
    return render_template('error/404.html', data=data), 500


@error.app_errorhandler(404)
def page_not_found(e):
    data = {
        'e': e,
    }
    return render_template('error/404.html', data=data), 404
