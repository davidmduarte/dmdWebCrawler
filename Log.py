# Log
# Autor: David Duarte

# Build 22 - melhorada a forma de deteccao para zippar
# Build 21 - optimizada forma de gravacao no disco 
# Build 7  - corrigido o bug de comparacao de dias para fazer o zip
# Build 6  - perdido no tempo
# Build 5  - primeira versao funcional

import time
import zipfile
import glob
import os
import shutil
import threading
import re

class Log:
	def __init__(self, path_):
		self.path = path_
		self.lastDate = None
		self.lock = threading.Lock()
		if os.path.exists(self.path) == True:
			self.lastDate = self.getLastDateLogged()
			#d1 = self.lastDate
			#t = [str(item) for item in time.localtime()]
			#d2 = "%s-%s-%s" % (t[0], t[1], t[2])
			#if d1 != "" and d1 != d2:
			#	self.compress()
		else:
			self.lastDate = [str(item) for item in time.localtime()]
			self.lastDate = "%s-%s-%s" % (self.lastDate[0], self.lastDate[1], self.lastDate[2])

	def now(self):
		t = [str(item) for item in time.localtime()]
		t1 = "%s-%s-%s" % (t[0], t[1], t[2])
		t2 = self.lastDate
		if t2 != "" and t2 != t1:
			self.compress()
		self.lastDate = "%s-%s-%s" % (t[0], t[1], t[2])
		return "[%s-%s-%s %s:%s:%s]" % (t[0], t[1], t[2], t[3], t[4], t[5])

	def info(self, *s):
		self.lock.acquire()
		try:
			now = self.now()
			handle = open(self.path, "a")
			handle.write("INFO: " + now + " - " + str(s) + "\n")
			handle.close()
		except:
			print("ERRO em log.info. (O erro foi ignorado. O crawler continua em funcionamento)")
			print("(nao gravada em log) INFO: " + now + " - " + str(s))
			
		self.lock.release()

	def getLastDateLogged(self):
		f = open(self.path, "r")
		lines = [line for line in f.readlines() if len(line) > 0]
		f.close()
		day = ""
		ptrn = re.compile('\d+-\d+-\d+')
		i = len(lines)-1
		res = None
		while i >= 0:
			res = ptrn.search(lines[i])
			if res != None:
				day = res.group()
				break
			i -= 1
		if res == None:
			t = [str(item) for item in time.localtime()]
			day = "%s-%s-%s" % (t[0], t[1], t[2])

		return day

	def compress(self):
		# rename path
		tm = "".join([str(item) for item in time.localtime()[:3]])
		newPath = self.path.split(".")
		newPath = ".".join(newPath[:-1] + [tm, "log"])
		shutil.move(self.path, newPath)
		# open the zip file for writing, and write stuff to it
		file = zipfile.ZipFile(self.path + ".zip", "a")
		file.write(newPath, os.path.basename(newPath), zipfile.ZIP_DEFLATED)
		file.close()
		os.remove(newPath)