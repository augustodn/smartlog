oldCal = open('../cals/tension_20191017.cal', 'r')
newCal = open('../cals/tension_integers.cal', 'w')

oldCal.readline()
cals = oldCal.readline().split(',')

cals = [round(float(c)) for c in cals]

for i, c in enumerate(cals):
    if i is 1023:
        newCal.write("{}".format(c))
    else:
        newCal.write("{}, ".format(c))

print(i)
oldCal.close()
newCal.close()
