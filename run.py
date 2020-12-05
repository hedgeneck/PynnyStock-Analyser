import FileManager as fman
import Ativo as at

fm = fman.FileManager()

a = at.Ativo('YVR',fm['YVR'])

ad = a.intraDays[190]

ad.checkForTrade()

# names = fm.getNames()[0:3]

# al = [] # lista de Ativos

# for n in names:
#	print(n)
#	try:
#		a = at.Ativo(n, fm[n])
#		al.append( a )
#	except IndexError:
#		print("Ativo sem nenhum dado ou dado inconsistente")

#print(al)





# print( fm.getNames() )


# print( len(fm.getNames()) )



# fm.show()

# a = at.Ativo('ACRE', fm['ACRE'])
# a = at.Ativo('AAMC', fm['AAMC'])

# a = at.Ativo('AAME', fm['AAME'])

# print(a)
# print(a.intraDays)

# print(a.dataDays[199])
#intra = at.IntraDay( a.dataDays[199] )

#print(intra)

# print('_pre')
# print(intra._pre)
# print('_core')
# print(intra._core)
# print('_pos')
# print(intra._pos)


# print(a.data)
# print(a.data[-1])
# print(a.dataDays)
# a.show()


# print(fm['WISA'])
# print(fm['AAMC'])


# print( fm.getNames(500,600) )
# print(fm.size)

# print( fm.getNames(fm.size-100,fm.size) )

# n = fm.getNames(500,600)

# for i in n:
# 	print(i)

# l = [fm[i] for i in fm.getNames(600,700) ]
# print(l)