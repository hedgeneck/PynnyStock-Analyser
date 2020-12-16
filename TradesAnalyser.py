import FileManager as fman
import pandas as pd
import numpy as np
import datetime
import Ativo as at
import pickle
from matplotlib import pyplot as plt

class TradesAnalyser():
	'''
	Calcula os Trades e analisa eles
	'''
	def __init__(self, adl):
		self.fm = fman.FileManager()
		self.adl = adl # ADL: Ativos-Dias List
		self.fad = [] # FAD: Filtered Ativos-Dias
		self.trades = [] # trade results from last simulation

		self.prevol_threshold = 800000
		self.open_dolar_threshold = 2
		self.gap_threshold = 0.20
		self.F_low_threshold = 0
		self.F_high_threshold = 1

		self.short_after = 0.1
		self.exit_target = 0.3
		self.exit_stop = 0.3

	def setFilterParameters(self,prevol_threshold=800000,open_dolar_threshold=2,gap_threshold=0.2,
							F_low_threshold=0,F_high_threshold=1):
		self.prevol_threshold = prevol_threshold
		self.open_dolar_threshold = open_dolar_threshold
		self.gap_threshold = gap_threshold
		self.F_low_threshold = F_low_threshold
		self.F_high_threshold = F_high_threshold

	def setAlgoParameters(self,short_after = 0.1, exit_target = 0.3, exit_stop = 0.3):
		self.short_after = short_after
		self.exit_target = exit_target
		self.exit_stop = exit_stop

	def runFiltering(self):
		def make_filter_prevol(threshold):
		     return lambda ad: ad['stats']['volPre'] >= threshold

		def make_filter_open_dolar(threshold):
		     return lambda ad: ad['stats']['openValue'] >= threshold

		def make_filter_gap(threshold):
		    return lambda ad: ad['stats']['gap'] >= threshold

		def make_filter_F(low_threshold, high_threshold):
		    return lambda ad: low_threshold <= ad['stats']['volPre']/ad['freefloat'] <= high_threshold

		prevol_greater_than = make_filter_prevol(self.prevol_threshold)
		open_greater_than_dolar = make_filter_open_dolar(self.open_dolar_threshold)
		gap_greater_than = make_filter_gap(self.gap_threshold)
		F_between = make_filter_F(self.F_low_threshold,self.F_high_threshold)

		filtered_ativo_dias =  filter(prevol_greater_than, self.adl)
		filtered_ativo_dias =  filter(open_greater_than_dolar, filtered_ativo_dias)
		filtered_ativo_dias =  filter(gap_greater_than, filtered_ativo_dias)
		filtered_ativo_dias =  filter(F_between, filtered_ativo_dias)
		self.fad = list(filtered_ativo_dias)

	def getFilteredDays(self):
		# vamos primeiramente criar um dataframe vazio, mas com as colunas bem definidas
		df = pd.DataFrame({'name':[],
		                   'date':[],
		                   'freefloat':[],
		                   'volPre':[],
		                   'gap':[],
		                   'openToSpike%':[],
		                   'minsToSpike':[],
		                   'volToSpike':[],
		                   'spikeToLow%':[],
		                   'minsToLowAfterSpike':[],
		                   'spikeToPreVolF':[],
		                   'factorF':[]})
		# agora popula esse dataframe com todos AtivosXDia que passaram nos critérios
		for ad in self.fad:
		    secondsToSpike = datetime.datetime.combine(datetime.date.today(), ad['stats']['highCoreTime']) - datetime.datetime.combine(datetime.date.today(), datetime.time(9,31))
		    minutesToLowAfterSpike = datetime.datetime.combine(datetime.date.today(), ad['stats']['lowAfterHighTime']) - datetime.datetime.combine(datetime.date.today(), ad['stats']['highCoreTime'])

		    df = df.append({'name':ad['name'],
		                       'date':ad['date'].strftime("%d/%m/%Y"),
		                       'freefloat':ad['freefloat'],
		                       'volPre':ad['stats']['volPre'],
		                       'gap':ad['stats']['gap'],
		                       'openToSpike%':ad['stats']['openToSpikePercent'],
		                       'minsToSpike':secondsToSpike.total_seconds()/60,
		                       'volToSpike':ad['stats']['volumeToSpike'],
		                       'spikeToLow%':ad['stats']['spikeToLowPercent'],
		                       'minsToLowAfterSpike':minutesToLowAfterSpike.total_seconds()/60,
		                       'spikeToPreVolF':ad['stats']['spikeToPreVolFactor'],
		                       'factorF':ad['stats']['moneyVolPre']/ad['freefloat']},
		                          ignore_index=True)
		return df

	def getTrades(self):
		df = pd.DataFrame({ 'name':[],
		                    'date':[],
		                    'entry_time':[],
		                    'mins_to_trade':[],
		                    'exit_time':[],
		                    'price':[],
		                    'stop':[],
		                    'target':[],
		                    'profit':[]})
		for t in self.trades:
		    if t['trade']:
		        secondsToTrade = t['trade']['entry']['time'] - datetime.datetime.combine( t['trade']['entry']['time'].date(), datetime.time(9,31) )
		        df = df.append({ 'name':t['name'],
		                         'date':t['date'], #.strftime("%d/%m/%Y"), datetime é melhor que string
		                         'entry_time':t['trade']['entry']['time'].strftime("%H:%M"),
		                         'mins_to_trade':secondsToTrade.total_seconds()/60,
		                         'exit_time':t['trade']['exit']['time'].strftime("%H:%M"),
		                         'price':t['trade']['price'],
		                         'stop':t['trade']['stop'],
		                         'target':t['trade']['target'],
		                         'profit':t['trade']['profit']},
		                       ignore_index=True)
		df = df.sort_values(by='date',ignore_index=True)
		df['cumprofit'] = (1+df['profit']).cumprod()
		#df.index = list( range(0,len(df)) ) # depois da versão 1.0 de pandas podemos usar 
											# sort_values(by='date',ignore_index=True)
		return df


	def runSimulation(self):
		trades = []
		for ad in self.fad:
		    a = at.Ativo(ad['name'],self.fm[ad['name']])
		    intra = a.fromDay(ad['date'])
		    trades.append({'name': ad['name'],
		                   'date': ad['date'],
		                   'trade': intra.checkForTrade(self.short_after, self.exit_target, self.exit_stop)})
		self.trades = trades

	def saveTrades(self,filename):
		with open(filename, 'wb') as filehandle: # w de write e b de binary
		    pickle.dump(self.trades,filehandle)

	def openTrades(self,filename):
		with open(filename, 'rb') as filehandle: # w de read e b de binary
		    self.trades = pickle.load(filehandle)

	def printSimResults(self, start = 10000):
		n_trades = 0
		print('Start Money:', '${:,.2f}'.format(start) )
		for t in self.trades:
		    if t['trade']: # se o trade não for None, lembrar que None é falsey
		        start = start*(1+t['trade']['profit'])
		        #print(start)
		        n_trades += 1
		print('End Money:', '${:,.2f}'.format(start) )
		print('Number of Trades:', n_trades)
		print('Number of ativo-dias:', len(self.fad) )

	def plotHistMinsToTrade(self, bins = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]):
		dft = self.getTrades()

		# https://stackoverflow.com/questions/26218704/matplotlib-histogram-with-collection-bin-for-high-values
		plt.hist( np.clip( dft['mins_to_trade'], bins[0], bins[-1] ), bins=bins, edgecolor='black' )

		plt.title('Minutes to Trade')
		plt.xlabel('Minutes')
		plt.ylabel('Total Ativos-Dias')

		plt.show()

	def __repr__(self):
		s='FILTERING PARAMETERS\n'
		s = s + f"prevol_threshold: {self.prevol_threshold}\n"
		s = s + f"open_dolar_threshold: {self.open_dolar_threshold}\n"
		s = s + f"gap_threshold: {self.gap_threshold}\n"
		s = s + f"F_low_threshold: {self.F_low_threshold}\n"
		s = s + f"F_high_threshold: {self.F_high_threshold}\n"
		s = s + f"\n"
		s = s + f'TRADING PARAMETERS\n'
		s = s + f"short_after: {self.short_after}\n"
		s = s + f"exit_target: {self.exit_target}\n"
		s = s + f"exit_stop: {self.exit_stop}\n"

		return s