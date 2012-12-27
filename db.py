# db2
# Autor: David Duarte

import pyodbc
from threading import Thread
import time
import urllib2
import re
import profile

#######################
class Teste:
	def __init__(self, id, Link, NivelPesquisa):
		self.id = id
		self.Link = Link
		self.NivelPesquisa = NivelPesquisa

#######################

class Db:
	def __init__(self, server, database, user, password):
		self.server = server
		self.database = database
		self.user = user
		self.password = password

	def start(self, wc):
		wc.log.info("-- Start DB module --")
		try:
			Thread(target=run, args=(self.server, self.database, self.user, self.password, wc)).start()
		except Exception, errtxt:
			print errtxt

def run(srv, dtb, usr, psw, wc):
	while True:
		wc.log.info("DB module - Begin search")
		# server Stop ??
		if wc.serverStop == True:
			time.sleep(5)
			continue

		# get from DB and search
		wc.log.info("DB module - Conect do SQL Server", srv, dtb)
		conn = pyodbc.connect('DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (srv, dtb, usr, psw))
		cursLinks = conn.cursor()
		cursClientes = conn.cursor()
		cursPalavrasCliente = conn.cursor()
		
		cursSel = conn.cursor()
		cursIns = conn.cursor()

		wc.log.info("DB module :", "SELECT id, Link, NivelPesquisa FROM LinksPublicacoes WHERE estado = 0 AND ordem IN (%s) ORDER BY ordem" % (",".join(["'" + str(item) + "'" for item in wc.categories])))
		listLinks = cursLinks.execute("SELECT id, Link, NivelPesquisa FROM LinksPublicacoes WHERE estado = 0 AND ordem IN (%s) ORDER BY ordem" % (",".join(["'" + str(item) + "'" for item in wc.categories]))).fetchall();
		
		for rowLink in listLinks:
			cursPalavrasCliente.execute("""
			SELECT DISTINCT a.id, a.designacao
			FROM (
				SELECT DISTINCT p.id, p.designacao
				FROM ClientesPalavras cp
				INNER JOIN Palavras p ON cp.idCliente IN (
					SELECT id FROM Clientes WHERE id IN (
						SELECT idCliente 
						FROM TemasWebCliente
						WHERE idTema IN (
							SELECT idTema
							FROM TemasWebLink
							WHERE idLink = ?
						) AND estado = 0
					)
				) AND cp.idpalavra = p.id AND p.estado = 0
				WHERE p.id NOT IN (
					SELECT idPalavras 
					FROM PalavrasWebNaoPesquisaveis
				)
				UNION
				SELECT DISTINCT p.id, p.designacao
				FROM PalavrasSector ps
				INNER JOIN Palavras p ON ps.idSector IN (
					SELECT idSector 
					FROM ClienteSectores
					WHERE idcliente IN ( 
						SELECT idCliente 
						FROM TemasWebCliente
						WHERE idTema IN (
							SELECT idTema
							FROM TemasWebLink
							WHERE idLink = ?
						)
					)
				) AND ps.idpalavra = p.id AND p.estado = 0
				WHERE p.id NOT IN (
					SELECT idPalavras 
					FROM PalavrasWebNaoPesquisaveis
				)
			) a
			""", rowLink.id, rowLink.id)

			listWords = cursPalavrasCliente.fetchall()

			wc.log.info("DB module NumWords", len(listWords))

			clienteId = 0 # not importante
			#tt = time.time()
			searchId = wc.searchFor(clienteId, listWords, [rowLink])
			#print("wc.searchFor", time.time() - tt)

			if wc.serverStop == True:
				break

			# perguntar ao servidor pelos resultados da pesquisa com este searchId
			listFoundLinks = wc.getSearchInfo(int(searchId))
			for j in xrange(len(listFoundLinks) - 1):
				link = listFoundLinks[j]

				wc.log.info("DB module: SELECT * FROM CrawlerLinks WHERE url = '%s'" % (str(link['link'])))
				cursSel.execute("SELECT * FROM CrawlerLinks WHERE url = ?", link['link'])

				auxList = cursSel.fetchall()
				crawlerLinkId = 0
				ins = True

				if len(auxList) > 0: # Ja existe
					ins = False # Nao vamos inserir
					#cursSel.execute("SELECT * FROM CrawlerLinksPalavras WHERE idpalavra IN (" + ",".join(["'" + str(item['id']) + "'" for item in link['found']]) + ") ")
					#auxList = cursSel.fetchall()
					#if len(auxList) < len(link['found']):
					#	ins = True # Afinal vamos inserir na mesma
					
				if ins == True:
					# Inserir os resultados na base de dados
					wc.log.info("DB module: INSERT INTO CrawlerLinks (idLinksPublicacoes, url, datapesquisa, estado, tamanho, status_crawl) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % (str(link['id']), str(link['link']), str(link['dataPesquisa']), '0', str(link['length']), '0'))
					cursIns.execute(
						"INSERT INTO CrawlerLinks (idLinksPublicacoes, url, datapesquisa, estado, tamanho, status_crawl) VALUES (?, ?, ?, ?, ?, ?)",
						link['id'], link['link'], link['dataPesquisa'], '0', link['length'], '0'
					)
					crawlerLinkId = cursIns.execute("SELECT @@IDENTITY").fetchone()[0]
					for palavra in link['found']:
						wc.log.info("INSERT INTO CrawlerLinksPalavras (idcrawlerlink, idpalavra) VALUES ('%s', '%s')" % (str(crawlerLinkId), str(palavra['id'])))
						cursIns.execute("INSERT INTO CrawlerLinksPalavras (idcrawlerlink, idpalavra) VALUES (?, ?)", crawlerLinkId, palavra['id'])

			conn.commit()
			wc.deleteSearchInfo(int(searchId))
			wc.clearHashPages()
		wc.log.info("DB module - End Search")
