import numpy as np
import matplotlib.pyplot as plt
import miepython

mu = np.linspace(0.2, 10, 300) # Inverse wavelength (um-1)
#lam = 1.0/x
#print(lam)

m = 1.33
a = 1 # Radio(um)
x = 2.0*np.pi*mu*a
qextValues = []
#qext, qsca, qback, g = miepython.ez_mie(m, d, lambda0)
for i in range(len(x)):
   # qextValues.append(miepython.mie(m, x[i])[0])  
   qextValues.append(miepython.efficiencies_mx(m, x[i])[0])

plt.plot(mu, qextValues, color='red', label="1.33")
#plt.plot(x, qsca, color='green', label="1.5")
plt.show()
