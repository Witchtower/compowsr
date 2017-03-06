# this is for testing the application with self signed certs. 
# if app goes into production, pls put it in a real webserver
context = ('testing_crt/server.crt', 'testing_crt/server.key')
from compowsr import app
app.run(host='127.0.0.1', port=5000, debug=True, ssl_context=context)
