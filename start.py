from OpenSSL import SSL
context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('key.priv')
context.use_certificate_file('key.pub')
