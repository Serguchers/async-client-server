import hmac

passwd = b'password'

hash = hmac.new(passwd, b'123', 'MD5')
print(hash.digest())

server_hash = hmac.new(hash.digest(), b'server', 'MD5')
print(server_hash.digest())