# coding: utf-8
from flask.ext.wtf import Form
from flask.ext.wtf.file import FileField
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, SelectField
from wtforms.validators import Email, DataRequired, Length, EqualTo, Regexp


class RegisterForm(Form):
    username = StringField('Username', validators=[DataRequired(), Length(2, 64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, 64),
                                                     EqualTo('confirmPassword', message=u"密码不匹配")])
    confirmPassword = PasswordField('Confirm Password', validators=[DataRequired(), Length(6, 64)])
    email = StringField('Email', validators=[DataRequired(), Length(1, 128), Email()])
    Submit = SubmitField('Submit')


class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired(), Length(2, 64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(2, 64)])
    Submit = SubmitField('Submit')


class UploadForm(Form):
    title = StringField('title')
    description = TextAreaField('description')
    file_upload = FileField('file_upload')
    Submit = SubmitField('Submit')


class BaseSettingForm(Form):
    is_have_account = StringField('is_have_account')
    access_key = StringField('access_key')
    secret_key = StringField('secret_key')
    bucket_name = StringField('bucket_name')
    domain = StringField('domain')
    save_setting = SubmitField('save_setting')
