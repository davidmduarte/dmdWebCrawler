# Log
# Autor: David Duarte

# Build 7 - corrigido o bug de preenchimento do dicionario

def getRequest(conn):
	buffer_ = ""
	rawPost = ""
	http = {}
	buf = conn.recv(512)
	buffer_ += buf
	while len(buf) == 512:
		buf = conn.recv(512)
		buffer_ += buf

	# parse
	buffer_ = buffer_.split("\n\n")
	if(len(buffer_) > 1):
		rawPost = buffer_[1]
	buffer_ = buffer_[0]

	if len(buffer_) == 0: return http

	arr = buffer_.split("\n")
	aux = arr.pop(0).split(' ')

	http['REQUEST_METHOD'] = aux[0]
	http['URI_STRING'] = aux[1]
	if len(aux) > 2:
		http['SERVER_PROTOCOL'] = aux[2]
	for line in arr:
		aux = line.split(':')
		if len(aux) > 1:
			http[aux[0]] = aux[1];
	aux = http['URI_STRING'].split('?')
	if len(aux) == 0:
		http['FILENAME'] = 'root'
	else:
		http['FILENAME'] = aux[0][1:]
		if len(aux) > 1:
			http['GET'] = Properties(queryString = aux[1])
		else:
			http['GET'] = {}
	http['POST'] = {}
	if http.has_key('Content-Length'):
		http['POST'] = Properties(queryString = rawPost)

	return http

class Properties(dict):
	def __init__(self, **d):
		for key in d.keys():
			getattr(self, key)(d[key])

	def queryString(self, s):
		for item in s.split("&"):
			part = item.split("=")
			if len(part) == 1: self.__setitem__(part[0].replace("+", " "), '')
			else: self.__setitem__(part[0].replace("+", " "), part[1].replace("+", " "))