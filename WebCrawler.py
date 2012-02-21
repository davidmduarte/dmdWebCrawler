# WebCrawler
# Autor: David Duarte

# Build 30 - implemetado o sistema de cache para facilitar a memoria
# Build 26 - Novos links sao com do mesmo dominio
# Build 12 - Reformulacao na forma como se procura info nos site
# Build 9 - Reformulacao na forma como se sacam os sites para o disco
# Build 8 - Refeitos e testados os pedidos antigos de sistema
# Build 7 - Corrigido o bug de requests invalidos. Continua em reformulacao
# Build 6 - Ainda nao foi testado. Esta em reformulacao

import re
import urllib2
import Log
import Http
import socket
from threading import Thread
import time
import re
import json
import os
import glob
import profile

class Page:
	def __init__(self, id, link, source, depth, memoryMode=True):
		self.memoryMode = memoryMode
		self.id = id
		self.Link = link
		self.time = time.time()

		if self.memoryMode: 
			self.source_ = source
		else:
			self.writeSourceOnDisk(source)
			self.source_ = None
		self.length = len(source)
		self.NivelPesquisa = depth
		
	def source(self):
		if self.memoryMode == True:
			return self.source_
		else:
			f = open("data/" +  str(self.id) + "_" + str(self.time))
			buf = f.read()
			f.close()
			return buf

	def writeSourceOnDisk(self, source):
		f = open("data/" + str(self.id) + "_" + str(self.time), "w")
		f.write(source)
		f.close()
	
	def setMemoryMode(self, memoryMode):
		if self.memoryMode == memoryMode:
			return

		if memoryMode == True: 
			self.source_ = self.source()
			os.remove("data/" + str(self.id) + "_" + str(self.time))
		else:
			if self.length == 0:
				return
			self.writeSourceOnDisk(self.source_)
			self.source_ = None

		self.memoryMode = memoryMode

class Word:
	def __init__(self, id, designacao):
		self.id = id
		self.designacao = designacao
		self.aux = self.designacao.split('\\')[0]
		self.patern = re.compile('([^\w\-_]' + self.designacao + '[^\w\-_\+]|[^\w\-_\+]' + self.designacao + '[^\w\-_])', re.IGNORECASE | re.DOTALL)
		self.paternAux = re.compile(self.aux, re.IGNORECASE | re.DOTALL)

class WebCrawler:
	def __init__(self, host_, port_, logPath_, categories_, maxMenMB, maxTimeUrlUpdateMin):
		self.stop = -1  # recebe o search id que pretende parar
		self.hashPages = {}
		self.results = {}
		self.host = host_
		self.port = port_
		self.log = Log.Log(logPath_)
		self.categories = categories_
		self.serverStop = False
		self.serverShutdown = False
		self.nextSearchId = 0

		self.regPatern = [
			[re.compile(r'<\s*script[^<]*>.*?<\s*/script\s*>', re.IGNORECASE | re.DOTALL), ''],
			[re.compile(r'<\s*(br|strong|i|b)\*>', re.IGNORECASE), ''],
			[re.compile(r'<\s*a[^<]*?/?>', re.IGNORECASE), ''],
			[re.compile(r'<[^<]*?/?>', re.IGNORECASE), '++']
		]

		self.maxMem = maxMenMB * 1000000  # Conta bytes e nao bits
		self.maxTimeUrlUpdate = maxTimeUrlUpdateMin * 60 # Conta tempo em segundos
		self.ignoreList = ['css', 'gif', 'jpg', 'png', 'pdf', 'mov', 'swf'];

		# em testes
		self.listWords = {}

	# Not in use
	def downloadLinks(self, listLinks, threadNum):
		#print("dowloadLinks", threadNum)
	 	i = 0
		while i < len(listLinks):
			itemLink = listLinks[i]
			page = self.downloadUrl(itemLink, threadNum)
			self.hashPages[page.Link] = page

			if page.NivelPesquisa > 0:
				subUrlList = getUrlsFromHtml(page.source)
				for subUrl in subUrlList:
					link = correctUrl(subUrl, page.Link)
					listLinks.append(Page(page.id, link, "", page.NivelPesquisa-1))
			i += 1

	def downloadUrl(self, item, threadNum=0):
		success = False
		maxTries = 4
		timeout = [0.1, 0.3, 0.7, 2]
		link = item.Link
		cnt = 0

		while cnt < maxTries and success == False:
			try:
				htmlHandler = urllib2.urlopen(link, None, timeout[cnt])
				contentType = htmlHandler.info().getheader('Content-Type')
				print("contentType", contentType)
				ctlf = contentType.lower().find
				if ctlf("video") >= 0 or ctlf("image") >= 0 or ctlf("css") >= 0 or ctlf("application") >= 0 or ctlf("model") >= 0 or ctlf("audio") >= 0:
					htmlSource = ""
				else:
					htmlSource = htmlHandler.read()
				htmlHandler.close()
			except urllib2.HTTPError, e:
				success = True
				htmlSource = ""
			except urllib2.URLError, e:
				if str(e.reason).find('timed out') >= 0:
					cnt += 1
				else:
					success = True
					htmlSource = ""
			except:
				cnt += 1
			else:
				success = True

		if cnt == maxTries: htmlSource = ""

		return Page(item.id, item.Link, urllib2.unquote(htmlSource).lower(), item.NivelPesquisa)

	def searchFor(self, clienteId, listWords, listLinks):
		if self.serverStop == True:
			return -1
		
		searchId = self.nextSearchId
		self.results[searchId] = []

		if len(listWords) > 0:
			# tratar dos carateres epeciais que possa ter a lista de palavras
			tt = time.time()
			newListWords = []
			for item in listWords:
				if not self.listWords.has_key(item.id):
					self.listWords[item.id] = Word(item.id, item.designacao.lower().decode('cp1252').replace('(', '\(').replace(')', '\)').replace('+', '\+').replace(' ', '\s+'))
				newListWords.append(self.listWords[item.id])
			print("tempo", time.time() - tt)
			self.begin(newListWords, listLinks, searchId)
		
		self.nextSearchId += 1

		return str(searchId)

	def begin(self, listWords, listLinks, searchId, full = True):
		if self.serverStop == True:
			return
		#itemLink {id, Link, NivelPesquisa}
		#make an hash of links
		#server para nao duplicar links na lista
		hashPages = {}
		for item in listLinks:
			hashPages[item.Link] = 1

		i = 0
		while i < len(listLinks):
			itemLink = listLinks[i]
			newListLinks = self.findHtmlWith(itemLink, listWords, searchId, full)

			for newItem in newListLinks:
				if not hashPages.has_key(newItem.Link):
					listLinks.append(newItem)
					hashPages[newItem.Link] = 1

			if self.stop == searchId:
				self.stop = -1 # RESET STOP mechanism
				break

			if self.serverStop == True:
				#del self.results[searchId]
				break
			i += 1

		# adicionar linha de fim de pesquisa
		self.results[searchId].append([])

	#urlInfo {id, Link, NivelPesquisa}
	def findHtmlWith(self, urlInfo, listWords, searchId, full):
		if self.stop == searchId: return []
		if self.serverStop == True:
			return []

		for i in self.results[searchId]:
			if i != [] and i['link'] == urlInfo.Link: return []

		# Testar se o url ja existe e se o tempo do ultimo download foi ha menos tempo do que diz em maxTimeUrlUpdate
		downloadFlag = False
		if self.hashPages.has_key(urlInfo.Link) and (int(time.time()) - int(self.hashPages[urlInfo.Link].time)) < self.maxTimeUrlUpdate:
			#self.log.info("page allready in memory", urlInfo.Link)
			page = self.hashPages[urlInfo.Link]
			if full == False:
				page.NivelPesquisa = 0
		else:
			# testar se a memoria esta nos pincaros
			totalMem = sum([v.length for v in self.hashPages.itervalues() if v.memoryMode == True])
			#print(totalMem)
			if totalMem >= self.maxMem:
				self.log.info("Begin Cache - TotalMemory in sources (MB) ", totalMem/1000000)
				for k in self.hashPages.iterkeys():
					self.hashPages[k].setMemoryMode(False)
				totalMem = sum([v.length for v in self.hashPages.itervalues() if v.memoryMode == True])
				self.log.info("End Cache - TotalMemory in sources (MB) ", totalMem/1000000)
			# ----

			# Se entrar aqui e porque existe mas esta desactualzado
			if self.hashPages.has_key(urlInfo.Link):
				self.clearHashPagesWithId(self.hashPages[urlInfo.Link].id)
			
			page = self.downloadUrl(urlInfo)
			self.hashPages[page.Link] = page
			downloadFlag = True
			
		# sacar todos os links nesta pagina
		domain = getDomainFromUrl(page.Link)
		ret = []
		result = []
		if page.length > 0:
			if page.NivelPesquisa > 0:
				subUrlList = getUrlsFromHtml(page.source())
				for subUrl in subUrlList:
					link = correctUrl(subUrl, page.Link) 
					if getDomainFromUrl(link).find(domain) >= 0 and link.split('.')[-1] not in self.ignoreList:
						ret.append(Page(page.id, link, "", page.NivelPesquisa-1))

			# Retira todas as tags e substitui por ++ com excepcao dos bolds e afins
			source = page.source()[:] # copy string
			for patern in self.regPatern:
				source = patern[0].sub(patern[1], source)

			if page != None:
				tt = time.time()
				result = self.search_3(source, listWords)
				print("search 3", time.time() - tt, result)

			sourceLen = len(source.replace("+", ""))

			if len(result) > 0:
				#get date
				date = time.localtime()
				self.results[searchId].append({
					'id' : page.id,
					'link' : page.Link,
					'dataPesquisa' : "%d-%02d-%d %02d:%02d:%02d" % (date.tm_year, date.tm_mon, date.tm_mday, date.tm_hour, date.tm_min, date.tm_sec),
					'length' : page.length,
					'found' : result
				})

		if downloadFlag and len(result) == 0:
			self.log.info("search:", urlInfo.id, page.length, urlInfo.Link, "Url Updated")
		elif not downloadFlag and len(result) != 0:
			self.log.info("search:", urlInfo.id, page.length, urlInfo.Link, "Found words", result)
		elif downloadFlag and len(result) != 0:
			self.log.info("search:", urlInfo.id, page.length, urlInfo.Link, "Url Updated and Found words", result)

		return ret

	def search(self, source, listWords):
		#print("searching")
		res = []
		for word in listWords:
			# tem que passar a ser uma regular expression
			#found = source.find(word.designacao)
			found = word.patern.search(source)
			if found != None:
				res.append({
					"id" : word.id,
					"word" : word.designacao,
					"pos" : found.start()
				})

		return res

	def search_3(self, source, listWords):
		#print("searching")
		res = []
		for word in listWords:
			if word.paternAux.search(source) != None:
				found = word.patern.search(source)
				if found != None:
					res.append({
						"id" : word.id,
						"word" : word.designacao,
						"pos" : found.start()
					})

		return res

	def getSearchInfo(self, searchId):
		return self.results[searchId]

	def deleteSearchInfo(self, searchId):
		del self.results[searchId]

	def clearHashPagesWithId(self, id):
		keys = []
		for k in self.hashPages.iterkeys():
			if self.hashPages[k].id == id:
				keys.append(k)
		for k in keys:
			try:
				self.hashPages[k].setMemoryMode(True)
			except:
				self.log.info("BUG on clearHahPagesWithId", k, self.hasPages[k].id, self.hasPages[k].time)
			del self.hashPages[k]

	def clearHashPages(self):
		genKeys = [k for k in self.hashPages.iterkeys()]
		for k in genKeys:
			try:
				self.hashPages[k].setMemoryMode(True)
			except:
				self.log.info("BUG on clearHashPages", k, self.hashPages[k].id, self.hashPages[k].time)
			del self.hashPages[k]

	def start(self):
		self.log.info("-- Web Crawler Server Started --")
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server.bind((self.host, self.port))
		server.listen(10)

		while not self.serverShutdown:
			conn, addr = server.accept()
			self.log.info("Socket Connection accept")

			http = Http.getRequest(conn)
			self.log.info("Request URI_STRING", http)

			if not http.has_key('GET'):
				conn.close()
				continue
			try:
				Thread(target=self.parseRequests, args=(http, conn)).start()
			except Exception, errtxt:
				print errtxt

		self.log.info("-- Web Crawler Server Stopped --")

	def parseRequests(self, http, conn):
		if http['FILENAME'] == 'search':
			if  http['GET'].has_key('query'):
				self.results.append([]);
				buf = "{searchId:"+str(len(self.results)-1)+"};"
				conn.send(putHeadersOK("text/html", len(buf))+buf)
				listWords = [Word('0', urllib2.unquote(http['GET']['query']))]
				keys = self.hashPages.keys()
				listLinks = [Page(0, link, "", 0) for link in keys]
				try:
					Thread(target=self.begin, args=(listWords, listLinks, len(self.results)-1, False)).start()
				except Exception, errtxt:
					print errtxt
				conn.close()
				self.log.info("... a search for '"+urllib2.unquote(http['GET']['query'])+"' as been started with number "+str(len(self.results)-1))
		elif http['FILENAME'] == 'search_info':
			if http['GET'].has_key('search_id') and  http['GET'].has_key('cnt_received'):
				idx = int(http['GET']['search_id'])
				output = []
				toDel = False
				for i in xrange(int(http['GET']['cnt_received']), len(self.results[idx])):
					if self.results[idx][i] != []:
						output.append(self.results[idx][i])
					else:
						output.append("null")
						toDel = True
				buf = json.dumps(output)
				conn.send(putHeadersOK("text/html", len(buf))+buf)
				if toDel:
					del self.results[idx]
				self.log.info("... sended status on search number "+str(idx))
			else:
				buf = "[" + ",".join([str(item) for item in self.results.iterkeys()]) + "]"
				conn.send(putHeadersOK("text/html", len(buf))+buf)
				self.log.info("... sended id list of all searches");
			conn.close()
		elif http['FILENAME'] == "stop_search":
			if http['GET'].has_key("search_id"):
				self.stop = http['GET']["stopId"]
				conn.send(putHeadersOK("text/html", 2)+"ok")
			else:
				buf = "search_id needed"
				conn.send(putHeadersNotOK(len(buf))+buf)
			conn.close()
			self.log.info("... search number "+http['GET']["stopId"]+" a STOP message")
		elif http['FILENAME'] == "is_stoped":
			if self.serverStop == True:
				conn.send(putHeadersOK("text/html", 3)+"yes")
			else:
				conn.send(putHeadersOK("text/html", 2)+"no")
			conn.close()
		elif http['URI_STRING'] == "/":
			handle = open("admin/index.html", "r")
			buf = handle.read()
			handle.close()
			conn.send(putHeadersOK("text/html", len(buf))+buf)
			conn.close()
			self.log.info("... sended index.html")
		elif http['FILENAME'][-3:] in ( "css", "gif") or http['FILENAME'][-2:] == "js":
			contentType = {
				'js': 'text/javascript',
				'css': 'text/css',
				'gif': 'image/gif'
			}
			handle = open("admin/"+ http['URI_STRING'][1:], "r")
			buf = handle.read()
			handle.close()
			self.log.info(http['URI_STRING'], len(buf))
			conn.send(putHeadersOK(contentType[http['URI_STRING'].split(".")[1]], len(buf)) + buf)
			conn.close()
			self.log.info("... sended " + http['URI_STRING'][1:])
		elif http['FILENAME'] == "stop":
			conn.send("Server Stopped. Request already made will be completed.")
			conn.close()
			self.serverStop = True
		elif http['FILENAME'] == "shutdown":
			buf = "Shutting down"
			conn.send(putHeadersOK("text/html", len(buf)) + buf)
			conn.close()
			self.serverStop = True
			self.serverShutdown = True
		elif http['FILENAME'] == "log_file_list":
			pass
		elif http['FILENAME'] == "log_file":
			f = open("WebCrawler.log", "r")
			buf = f.readline()
			f.close()
			conn.send(putHeadersOK("text/html", len(buf)) + buf)
			conn.close()
		elif http['FILENAME'] == "get_categories":
			buf = "[" + ",".join([str(item) for item in self.categories]) + "]"
			conn.send(putHeadersOK("text/html", len(buf)) + buf)
			conn.close()
		elif http['FILENAME'] == "set_categories":
			if http['GET'].has_key("cat"):
				self.categories = [int(item) for item in http['GET']['cat'].split(",")]
				conn.send(putHeadersOK("text/html", len(http['GET']['cat'])) + http['GET']['cat'])
			else:
				buf = "cat parameter needed"
				conn.send(putHeadersNotOK(len(buf)) + buf)
			conn.close()
		elif http['FILENAME'] == "start":
			conn.send(responseOK("ok"))
			conn.close()
			self.serverStop = False
		elif http['FILENAME'] == "alive":
			conn.send(responseOK("yes"))
			conn.close()
		else:
			buf = "UNKNOWN REQUEST"
			conn.send(putHeadersNotOK(len(buf)) + buf)
			conn.close()

def stripQuotes(self, s):
	if len(s) > 1:
		if s[0] == "'" and s[-1] == "'": s = s.strip("'")
		elif s[0] == '"' and s[-1] == '"': s = s.strip('"')
	return s

def getUrlsFromHtml(htmlSource):
	p0 = re.compile('href\s*=\s*("([^"]*)"|\'([^\']*)\'|(\S+))', re.MULTILINE|re.IGNORECASE)
	return [item[1]+item[2]+item[3] for item in p0.findall(htmlSource)]

def correctUrl(url, parentUrl):
	test = url.split("://")
	if len(test) > 1 and len(test[0]) < 10: return url
	else: return urllib2.urlparse.urljoin(parentUrl, url)

def getDomainFromUrl(url):
	try:
		url = url.split("://")[1]
		url = url.split("/")[0]
		url = url.upper()
		url = url.replace("WWW.", "")
		return url
	except:
		return ""

def showResults(results):
	while 1:
		print("what results do I have now?")
		for i in results:
			i.showMe()
		time.sleep(10)

def putHeadersOK(contentType, length):
	return "HTTP/1.0 200 OK\r\nContent-Type: "+str(contentType)+"\r\nContent-Length: " + str(length) + "\r\n\r\n"

def responseOK(body):
	return "HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: " + str(len(body)) + "\r\n\r\n" + body

def putHeadersNotOK(length):
	return "HTTP/1.0 400 Bad Request\r\nContent-Type: text/html\r\nContent-Length: " + str(length) + "\r\n\r\n"

def responseNotOK(body):
	return "HTTP/1.0 400 Bad Request\r\nContent-Type: text/html\r\nContent-Length: " + str(len(body)) + "\r\n\r\n" + body
