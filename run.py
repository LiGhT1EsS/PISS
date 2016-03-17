#!flask/bin/python

from piss import app, manager
# app.run(debug=True, host='0.0.0.0')
app.debug = True
manager.run()
