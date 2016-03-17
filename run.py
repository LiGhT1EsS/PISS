#!flask/bin/python

from app import app, manager
# app.run(debug=True, host='0.0.0.0')
app.debug = True
manager.run()
