import pandas as pd
import datetime
from Utilities import divideDays


class IntraDay():
	'''
	Classe responsável por manter os dados dentro de um dia para algum ativo qualquer
	dataDay é uma list contendo os tickers de um dia qualquer de forma raw, sem nenhuma organização
	Essa classe organiza os dados em _pre, _core, _after e fornece alguns métodos interessantes
	'''
	def __init__(self,dataDay): # dataDay is one element of the list dataDays

		self.dataDay = dataDay
		self.date = dataDay[0]['time'].date()
		self._pre = []
		self._core = []
		self._pos = []

		for dt in dataDay: # dt seria pra cada datetime (time com date), por isso extraímos dt.time()
			t1 = datetime.time(9,30)
			t2 = datetime.time(16,0)

			if dt['time'].time() <= t1: # se for horário de pre
			    self._pre.append(dt)
			elif t1 < dt['time'].time() <= t2: # se for horário de core
			    self._core.append(dt)
			else: # se for o que sobrou, horário de pós
			    self._pos.append(dt)

		if len(self._core)==0: # se tivermos core nulo mas pre ou pos não nulos, varemos alguns ajustes.
			if len(self._pre) > 0:
				print('caso core vazio mas com pre')
			if len(self._pos) > 0:
				print('caso core vazio mas com pos')

		self._initializeIntradayStats()


	def _initializeIntradayStats(self):
		self.stats = {} # empty curly cria empty dict e não empty set

		# calcula volume pre market
		volPre = 0
		for b in self._pre:
			volPre = volPre + b['volume']
		self.stats['volPre'] = volPre

		# calcula money volume de pre market
		moneyVolPre = 0
		for b in self._pre:
			moneyVolPre += b['volume']*b['close']
		self.stats['moneyVolPre'] = moneyVolPre

		# calcula open value
		self.stats['openValue'] = self._core[0]['open']

		# calcula o valor mais alto do core, a hora na qual aconteceu e a position
		highCoreValue = self._core[0]['high']
		highCoreTime = self._core[0]['time'].time()
		highCorePosition = 0

		for b in self._core:
			if highCoreValue < b['high']:
				highCoreValue = b['high']
				highCoreTime = b['time'].time()
				highCorePosition = self._core.index(b)

		self.stats['highCoreValue'] = highCoreValue
		self.stats['highCoreTime'] = highCoreTime
		self.stats['highCorePosition'] = highCorePosition

		# calcula o low depois do high
		lowAfterHighValue = self._core[highCorePosition]['high']
		lowAfterHighTime = self._core[highCorePosition]['time'].time()
		lowPositionAfterHigh = highCorePosition

		for b in self._core[highCorePosition:]: # da high position pra frente
			if lowAfterHighValue > b['low']:
				lowAfterHighValue = b['low']
				lowAfterHighTime = b['time'].time()
				lowPositionAfterHigh = self._core.index(b)

		self.stats['lowAfterHighValue'] = lowAfterHighValue
		self.stats['lowAfterHighTime'] = lowAfterHighTime
		self.stats['lowPositionAfterHigh'] = lowPositionAfterHigh

		# calcula variação percentual do open até o spike

		highCoreValue = self._core[highCorePosition]['high'] # escrevendo denovo só pra não se perder
		openValue = self._core[0]['open']
		openToSpikePercent = (highCoreValue - openValue)/openValue
		self.stats['openToSpikePercent'] = openToSpikePercent

		# calcula variação percentual do spike até o low
		highCoreValue = self._core[highCorePosition]['high'] # escrevendo denovo só pra não se perder
		lowAfterHighValue = self._core[lowPositionAfterHigh]['low']
		spikeToLowPercent = (lowAfterHighValue - highCoreValue)/highCoreValue
		self.stats['spikeToLowPercent'] = spikeToLowPercent

		# calcula volume from start of core to spike
		volumeToSpike = 0
		for b in self._core[:(highCorePosition+1)]: # o mais 1 é pq em python o end é exclusive
			volumeToSpike += b['volume']
		self.stats['volumeToSpike'] = volumeToSpike

		# calcula fator (volume até o spike)/(volume pre)
		spikeToPreVolFactor = 0
		if volPre == 0:
			spikeToPreVolFactor = 0
		else:
			spikeToPreVolFactor = volumeToSpike/volPre
		self.stats['spikeToPreVolFactor'] = spikeToPreVolFactor

	def checkForTrade(self, short_after, exit_target, exit_stop):
		trade = {} # se não tiver trade nesse dia o dictionary fica vazio
		first = self._core[0]

		for bar in self._core: 
			# ENTRY POINT
			if not bool(trade): # se nenhum trade tiver sido encontrado, procura por trades
				if bar != self._core[-1]:
					variation = (bar['high'] - first['open'])/first['open']
					if variation >= short_after:
						trade['entry'] = bar
						trade['price'] = (1+short_after)*first['open']
						trade['stop'] = (1+exit_stop)*trade['price']
						trade['target'] = (1-exit_target)*trade['price'] # lembrar que pra short o target é menor
			# EXIT POINTS
			else: # se já tivermos encontrado algum trade, vamos procurar exits
				if bar['high'] >= trade['stop']:
					trade['exit'] = bar
					trade['profit'] = -exit_stop
					break # só pararemos a execução do loop apos encontrar uma entry e um stop
				if bar['low'] <= trade['target']:
					trade['exit'] = bar
					trade['profit'] = exit_target
					break
				if bar == self._core[-1]: # se for a última barra, fecha o trade no close da ultima barra
					trade['exit'] = bar
					trade['profit'] = -(bar['close'] - trade['price'])/trade['price']

		if not bool(trade): # testa se o dictionary com dados sobre um possível trade está vazio
			return None

		return trade # se o dictionary não estiver vazio, vai retornar os dados em trade

	def __repr__(self):

		s = ''
		s = s + f"{self.dataDay[0]['time'].date()}\n"
		s = s + f"{self.stats}\n"
		s = s + f"_pre\n"
		for b in self._pre:
			s = s + f"{b['time'].time()} open: {b['open']} high: {b['high']} low: {b['low']} close: {b['close']} volume: {b['volume']}\n"
		s = s + f"_core\n"
		for b in self._core:
			s = s + f"{b['time'].time()} open: {b['open']} high: {b['high']} low: {b['low']} close: {b['close']} volume: {b['volume']}\n"
		s = s + f"_pos\n"
		for b in self._pos:
			s = s + f"{b['time'].time()} open: {b['open']} high: {b['high']} low: {b['low']} close: {b['close']} volume: {b['volume']}\n"
		return s

class Ativo():
	'''
	Classe responsável por parsear os dados de uma ação específica
	'''
	def __init__(self, name, path):

		self.name = name
		self.path = path

		data = [] # list of bars, which are dicts containing tick information
		with open(path, 'r') as file:
		    line = file.readline() # le a primeira vez e descarta o header
		    line = file.readline() # le a primeira vez e tenta continuar a ler
		    while line:
		        tokens = line.split(',')
		        bar = { 'time':datetime.datetime.strptime(tokens[0], '%Y-%m-%d %H:%M:%S'),
		                'open':float(tokens[1]),
		                'high':float(tokens[2]),
		                'low':float(tokens[3]),
		                'close':float(tokens[4]),
		                'volume':int(tokens[5])}
		        data.append(bar)
		        line = file.readline()
		data.reverse()
		self.data = data
		self._initDayData()
		self._initIntradayData()
		self._initOuterDayStats()

	@staticmethod # usamos @staticmethod e não @classmethod pois não precisaremos instanciar a classe com cls
					# na verdade nem usamos name
	def initIntradayFromDate(name, path, d): # d é a data em formato datetime.date
		# https://stackoverflow.com/questions/15718068/search-file-and-find-exact-match-and-print-line
		data = []
		with open(path, 'r') as file:
			lines = [line for line in file if line.startswith(d.strftime("%Y-%m-%d"))]
		lines.reverse()
		for line in lines:
			tokens = line.split(',')
			bar = { 'time':datetime.datetime.strptime(tokens[0], '%Y-%m-%d %H:%M:%S'),
					'open':float(tokens[1]),
					'high':float(tokens[2]),
					'low':float(tokens[3]),
					'close':float(tokens[4]),
					'volume':int(tokens[5])}
			data.append(bar)

		return IntraDay(data)

	# são os dados brutos divididos em dias, mas ainda não divididos em core, pre, pos e stats
	def _initDayData(self):
		self.dataDays = divideDays(self.data)

	# agora os dias divididos em core, pre, pos e stats, ou seja, dados intraday
	def _initIntradayData(self):
		self.intraDays = []
		for d in self.dataDays:
			self.intraDays.append( IntraDay(d) )

	# aqui vamos inicializar algumas stats que não são autocontidas em um dia, como o gap, que 
	# precisa ser calculado sempre em relação ao dia anterior
	# cuidar pois nessa função estamos quebrando encapsulamento por questão de comodidade
	def _initOuterDayStats(self):

		gap = 0
		dayBefore = self.intraDays[0]
		for day in self.intraDays:
			if dayBefore == day: # caso seja o primeiro dia, seta gap como zero, pois não faz sentido o calculo
				day.stats['gap'] = 0
				dayBefore = day
			else:
				firstOpen = day._core[0]['open']
				lastClose = dayBefore._core[-1]['close']
				day.stats['gap'] = (firstOpen - lastClose)/lastClose
				dayBefore = day

	# esse método filtra o dia de interesse e retorna um objeto da classe Intraday (aka ativo-dia)
	# https://stackoverflow.com/questions/34609935/passing-a-function-with-two-arguments-to-filter-in-python/34610018
	# https://stackoverflow.com/questions/7125467/find-object-in-list-that-has-attribute-equal-to-some-value-that-meets-any-condi
	# daria pra fazer com filter mas no final das contas next() é a melhor opção
	def fromDay(self,d):
		return next(intra for intra in self.intraDays if intra.dataDay[0]['time'].date() == d )

	def __repr__(self):
		s=''
		s = s + f"{self.intraDays}"
		return s


	def show(self):
		print(self.dataDays)