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

	def __repr__(self):

#		# showing self.data
#		s = ''
#		for t in self.data:
#			s = s + f"{t['time']} open: {t['open']} high: {t['high']} low: {t['low']} close: {t['close']}\n"
#		return s

#		# showing self.dataDays
#		s = ''
#		for d in self.dataDays:
#			s = s + f"{d[0]['time'].date()}\n"
#			for t in d:
#				s = s + f"{t['time'].time()} open: {t['open']} high: {t['high']} low: {t['low']} close: {t['close']} volume: {t['volume']}\n"
#		return s

		# showing self.intraDays
		s=''
		s = s + f"{self.intraDays}"
		return s


	def show(self):
		print(self.dataDays)