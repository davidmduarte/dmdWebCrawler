urls = [
'http://www.agenciafinanceira.iol.pt',
'http://www.jornaldenegocios.pt',
'http://diariodigital.sapo.pt',
'http://jn.sapo.pt',
'http://dn.sapo.pt',
'http://diario.iol.pt/',
'http://www.rr.pt',
'http://www.rtp.pt',
'http://sol.sapo.pt',
'http://www.mundouniversitario.pt',
'http://www.i-gov.org',
'http://www.rhonline.pt',
'http://www.franchising.pt',
'http://www.destak.pt',
'http://noticias.portugalmail.pt',
'http://jornaldigital.com',
'http://www.oprimeirodejaneiro.pt',
'http://www.noticiasdamanha.net',
'http://www.oje.pt',
'http://noticias.sapo.pt',
'http://radioclube.clix.pt',
'http://www.noticiaslusofonas.com',
'http://noticias.sapo.pt/lusa',
'http://jornaldeangola.sapo.ao/',
'http://www.cmjornal.xl.pt/',
'http://www.tvnet.pt',
'http://aeiou.expresso.pt',
'http://www.mundoportugues.org',
'http://www.vidaeconomica.pt',
'http://tsf.sapo.pt',
'http://aeiou.visao.pt',
'http://www.publico.pt/',
'http://www.forum.pt',
'http://www.infofranchising.pt',
'http://www.human.pt/',
'http://www.tormo.pt/',
'http://www.canalup.tv/',
'http://economico.sapo.pt',
'http://jornaldiario.com/',
'http://www.bestfranchising.pt/',
'http://www.tvi24.iol.pt/',
'http://www.sabado.pt/',
'http://www.negociosefranchising.pt/',
'http://www.ionline.pt/'
]

import eventlet
from eventlet.green import urllib2

def fetch(url):
	htmlSource = ""
	try:
		htmlHandler = urllib2.urlopen(url, None, 5)
		contentType = htmlHandler.info().getheader('Content-Type')
		if contentType.lower().find("video") >= 0 or contentType.lower().find("image") >= 0 or contentType.lower().find("css") >= 0:
			htmlSource = ""
		else:
			htmlSource = htmlHandler.read()
			htmlHandler.close()
	except urllib2.HTTPError, e:
		htmlSource = ""
	except urllib2.URLError, e:		
		htmlSource = ""
	except:
		pass
	return htmlSource

pool = eventlet.GreenPool()

for body in pool.imap(fetch, urls):
  print "got body", len(body)