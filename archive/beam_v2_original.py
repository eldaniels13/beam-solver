#%%
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  6 14:10:14 2022

Calcula reaciones en vigas estaticamente determinadas
con soportes ubicados en los extremos de la viga o
con soporte B desplazado sobre la viga o sin soporte B.
Para cargas puntuales y/o distribuidas
Ingresar valores absolutos (sin signo)
Videos y fuentes: 
    https://www.youtube.com/watch?v=T4CSzFIrug0&ab_channel=EllibrodeNewton
    https://stackoverflow.com/

@author: danyb
"""
"""
PENDIENTES:
    terminar verificador() para revision de cargas fuera de la viga
    grafica() para puntuales
    input end='\r' osea que el input no pone enter
+"""
#%%
import numpy as np
import time

f_todas = []

def Grafica():
    # la neta no se que pedo con esta parte
    # la saque de internet
    from matplotlib import pyplot as plt
    #rectangular que abarca toda la viga
    # plotea grafica de viga, fuerza cortante y momento flector
    try: l = float(input('Longitud de la viga horizontal: '))   # longitud de viga
    except ValueError: print('Ingrese un numero')
    try: q = int(input('Valor de la carga uniformemente distribuida, kN/m: '))
    except ValueError: print('Ingrese un numero')
    x = np.linspace(0,l,50) #creamos la cordenada x desde 0 a l
    V = q *(l/2 - x)          #Ecuación de fuerza cortante
    M = q/2 * (l*x - x**2)    #Ecuación de momento flector
    #Ploteamos una líniea horizontal que regresente la longitud de la viga
    plt.plot(x, color='k', label='Viga')    # Ploteamos viga
    plt.plot([0]*len(x),color='k')     #Ploteamos x,axis para visualizar la línea
    plt.plot(-M)      #Ploteamos el momento flector
    plt.plot(V)     #Ploteamos la fueza cortante  
def Distribuida():
    print('Distribuida', end='\r')
    try: f_o = float(input('Valor inicial de la f dis (KN): '))
    except ValueError: print('Introduzca un numero')
    try: f_f = float(input('Valor final de la f dis (KN): '))
    except ValueError: print('Introduzca un numero')
    try: c_o = float(input('Coordenada de inicio (m): '))
    except ValueError: print('Introduzca un numero')
    try: c_f = float(input('Coordenada final (m): '))
    except ValueError: print('Introduzca un numero')
    f_d = c_f - c_o     # distancia de la fuerza distribuida   
# si es ascendente
    if f_o < f_f:
    # triangulo
        f_n =[]
        f_r_t = -(f_d * (f_f - f_o))/2     # fuerza resultante triangulo
        f_n.append(f_r_t)   #final menos inicial porque ascendente
        c_r_t = c_o + (2/3)*f_d     # coordenada resultante triangulo
        f_n.append(c_r_t)   #2/3 porque es 1/3 respecto a angulo de 90°
        M_t = f_r_t * c_r_t    # momento triangulo
        f_n.append(M_t)
        f_todas.append(f_n)
     # rectangulo
        f_n = []
        f_r_r = - f_d * f_o   # fuerza resultante rectangulo
        f_n.append(f_r_r)
        c_r_r = c_o + (f_d/2)   # coordenada resultante rectangulo
        f_n.append(c_r_r)
        M_r = f_r_r * c_r_r    # momento rectangulo
        f_n.append(M_r)
        f_todas.append(f_n)       
# si es descendente
    elif f_o > f_f: 
    # triangulo
        f_n =[]
        f_r_t = -(f_d * (f_o - f_f))/2     # fuerza resultante triangulo
        f_n.append(f_r_t)
        c_r_t = c_o + (1/3)*f_d     # coordenada resultante triangulo
        f_n.append(c_r_t)
        M_t = f_r_t * c_r_t    # momento triangulo
        f_n.append(M_t)
        f_todas.append(f_n)
    # rectangulo
        f_n = []
        f_r_r = - f_d * f_f   # fuerza resultante rectangulo
        f_n.append(f_r_r)
        c_r_r = c_o + (f_d/2)   # coordenada resultante rectangulo
        f_n.append(c_r_r)
        M_r = f_r_r * c_r_r    # momento rectangulo
        f_n.append(M_r)
        f_todas.append(f_n)
# si es rectangular
    elif f_o == f_f: 
        f_n = []
        f_r_r = f_d * f_f or f_o  # fuerza resultante rectangulo
        f_n.append(-f_r_r)
        c_r_r = c_o + (f_d/2)   # coordenada resultante rectangulo
        f_n.append(c_r_r)
        M_r = - f_r_r * c_r_r    # momento rectangulo
        f_n.append(M_r)
        f_todas.append(f_n)
    return f_todas
def Puntual():
    print('Puntual', end='\r')
    f_n = []
    f_m = float(input('Introduzca magnitud (KN): '))
    f_n.append(-f_m) # magnitud
    # negativa porque son cargas
    f_c = float(input('Introduzca su coordenada (m): ')) # distancia respecto de A
    f_n.append(f_c) # coordenada
    M = - f_m * f_c     #negativo porque cargas generan respecto a A sentido horario
    f_n.append(M) # momento
    f_todas.append(f_n)
    return f_todas
def loading(n):
    if type(n) == int:
        print('Loading',end = '\t')
        for i in range(n):
            print(".", end = '\r')
            time.sleep(0.45)
        print(' ')
        print(' ')
    else:
        for i in n:
            if i == '.': 
                print(i)
                time.sleep(.35)
            else:    
                print(i,end='\r')
                time.sleep(.215)
def verificador(a):
    # aun no queda, no revisa todas o no todas entran (las que deberian)
    # verificador de que las cargas esten dentro de longitud de viga        
    for fuerza in a:
        # atras de la viga o delante de la viga
        if (fuerza[1] < 0 or fuerza[1] > l): 
            print('La fuerza numero ', a.index(fuerza)+1, ' esta fuera de la viga')
            print('Desea')
            print('E) eliminar la fuerza    C) cambiar la coordenada',end='\r')
            sel = input('Sel: ').lower()
            if sel == 'e':    # eliminar la carga 
                print('Se ha eliminado la fuerza', a.index(fuerza)+1)
                a.remove(fuerza)
            elif sel == 'c':     # modificar la carga
                print('Coordenada actual: ', fuerza[1], end='\r')
                a[a.index(fuerza)][1]= float(input('Nueva coordenada: '))   # sustituir la nueva fuerza


print('==============================')
#loading('Calculo de reaciones en vigas.')
print('==============================')
#loading(4)    
#loading('VIGA.')
sop = True
while sop == True:
    l = float(input('Longitud de la viga horizontal: '))   # longitud de viga
    c_B = float(input('Coordenada del soporte en B: '))    # coordenada del soporte B    
    if c_B > l: print('La coordenada del soporte B no puede estar fuera de la viga')
    elif c_B < 0: print('La coordenada del soporte B no puede estar fuera de la viga')
    elif c_B == l: sop = 'l'
    elif 0 < c_B < l: sop = 'ml'
    elif c_B == 0: sop = '0'

loading(4)
loading('CARGAS.')
cuantas = int(input('Introduzca cuantas cargas: '))
for i in range(cuantas): 
    print(' ')
    print('Carga numero ',i+1)
    print('p) Puntual     d) Distribuida', end='\t')
    sel = input('sel: ').lower()
    if sel == 'p': Puntual()
    elif sel == 'd': Distribuida()
    elif sel == 'g': Grafica()
loading(4)
verificador(f_todas)
a = np.asarray(f_todas, dtype=np.int64) 
    # a[:,0] col 1    fuerza resultante
    # a[:,1] col 2    coordenada resultante
    # a[:,2] col 3    momento respecto A
if sop == 'l':
    R_B = -sum(a[:,2])/(l)  # ecuaciones de equilibrio
    R_A = -sum(a[:,0])-R_B
    print('Reaccion en A = ',R_A,'KN','    Reaccion en B = ',R_B,'KN') 
elif sop == 'ml':
    R_B = -sum(a[:,2])/c_B
    R_A = -sum(a[:,0])-R_B 
    print('Reaccion en A = ',R_A,'KN','    Reaccion en B = ',R_B,'KN') 
elif sop == '0':
    R_A = -sum(a[:,0])
    M_A = -sum(a[:,2])
    print('Reaccion en A = ',R_A,'KN','    Momento de reaccion en A = ',M_A,'KN*m') 

