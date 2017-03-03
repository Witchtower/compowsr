"""from OpenSSL import SSL
context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('testing_crt/server.key')
context.use_certificate_file('testing_crt/server.crt')
"""
context = ('testing_crt/server.crt', 'testing_crt/server.key')
from compowsr import app
app.run(host='127.0.0.1', port=5000, debug=True, ssl_context=context)
