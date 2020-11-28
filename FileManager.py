import pandas as pd


class FileManager():
	'''
	Organiza os nomes e os paths de cada arquivo.
	Permite descobrir o path de um arquivo usando o seu ticker
	------------------------------------------------------------------------------------------
	Exemplo: fm = fman.FileManager()
			 fm['AAMC']
	------------------------------------------------------------------------------------------
	'''
	def __init__(self):

		self.ticker = dict()
		root = '..\\..\\..\\Data\\data_dist\\'

		# names.txt contem os pares nome_do_ticker endereço_do_csv
		# names é para que ele não use a primeira row como nomes das colunas
		# index_col=0 é para usar a primeira coluna como index, senão ele vai usar index numérico de 0 em diante
		df = pd.read_csv('names.txt', names=['name','path'], index_col=0)
		df['path'] = root + df['path']
		
		# temos que fazer essa jogada com ['path'] pois não tem solução de to_dict para apenas 1 coluna.
		self.ticker = df.to_dict()['path']
		# list(di.keys())[2] # se quisesse indexar um dictionary numericamente
		self.size = len(self.ticker)

	def __getitem__(self,i): # é o operador de quando for chamado com []
		return self.ticker[i]

	def getNames(self):
		return list(self.ticker.keys())

#	def getNames(self,start,end):
#		return list(self.ticker.keys())[start:end]

	def show(self):
		print(self.ticker)