import sys

from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail
from flask.ext.script import Manager, Server
from flask.ext.migrate import Migrate, MigrateCommand

from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY
from config import MailConfig

# set default encoding
reload(sys)
sys.setdefaultencoding('utf-8')

# init flask
app = Flask(__name__)

# set others library
bootstrap = Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY
app.config.from_object(MailConfig)

manager = Manager(app)
db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)

# register blueprint
from .index import index
app.register_blueprint(index)
from .user import user
app.register_blueprint(user)
from .error import error
app.register_blueprint(error)
from .upload import upload
app.register_blueprint(upload)
from .home import home
app.register_blueprint(home)
from .api import api
app.register_blueprint(api)

manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='0.0.0.0'))

