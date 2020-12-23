import pandas as pd

def divideDays(bl):
	'''
	bl: bar list, is a list of raw days which we will divide day by day
	dbl: daily bar lis, list of raw data divided by days
	the daily data will still be raw in the sense that the lines are not
	divided among pre actual and pos market
	'''
	dbl = []
	temp_day = []
	actual_day = bl[0]

	for tick in bl:
		if tick['time'].date() == actual_day['time'].date(): # se ainda estivermos no mesmo dia
			temp_day.append(tick)
			# aqui não precisamos dar .copy no tick pois ele não é temporário.

		else: # chegou um novo dia
			dbl.append(temp_day.copy())
			temp_day.clear()
			temp_day.append(tick)
			actual_day = tick
	if temp_day: # testa se sobrou alguma coisa em temp_day, pois é pra tratar o último dia
		dbl.append(temp_day) # como é o último elemento, não precisa ser copy

	return dbl

def drawdown(s):
	dd = pd.Series(dtype='float64') # drawdown (dd) will be used to calculate maximum drawdown (mdd)
	# especificamos explicitamente o dtype para evitar uma warning

	for i in s.index:
		_dd = s[i]/max(s[:i+1].max(),1)-1 # i+1 pois slicing não é inclusive do ultimo termo
		# como não queremos dar append de 1 em s, usamos max(X,1) onde
		# X = s[:i+1].max()
		dd = dd.append( pd.Series( _dd ), ignore_index=True ) 
	return abs( dd.min() )