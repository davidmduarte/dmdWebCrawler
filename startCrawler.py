# startCrawler
# Autor: David Duarte

DB_HOST = "192.168.1.102"
DB_DRIVER = "Actual SQL Server"
DB_DATABASE = "Clipping"
DB_USER = "teste"
DB_PASSWORD = "teste123"

WC_HOST = "localhost"
WC_PORT = 3000
WC_LOGPATH = "webcrawler.log"

MAX_TIME_URL_UPDATE = 180 # minutos

MAX_SOURCE_IN_MEM = 50 # megas

# CATEGORIES_DEFINITION = {
# 	"" : 0,
# 	"Economicos/Generalistas" : 1,
# 	"TMT/Turismo/Mkt" : 2,
# 	"Imobiliario/Transportes/Jogos/TI" : 3,
# 	"Saude e bem-estar/Ambiente/Gastronomia/Arte Cultura e Lazer" : 4,
# 	"Auto/Desporto/Moda e Decoracao" : 5,
# 	"Regionais" : 6,
# 	"Blogs" : 7,
# 	"Outros" : 8,
# 	"Internacionais" : 9
# }

CATEGORIES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

from webcrawler import *
from db import *

# Inicializar o modulo que comunica com a BD
db = Db(DB_DRIVER, DB_HOST, DB_DATABASE, DB_USER, DB_PASSWORD)

# Inicializar o WebCrawler
crawler = WebCrawler(DB_DRIVER, WC_HOST, WC_PORT, WC_LOGPATH, CATEGORIES, MAX_SOURCE_IN_MEM, MAX_TIME_URL_UPDATE)

# Comecar as pesquisas que vindas da BD 
db.start(crawler)

# Comecar o modo server (para que o webcraler possa responder aos pedidos vindos de fora)
crawler.start()
