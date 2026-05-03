# -*- coding: utf-8 -*-
"""
Para calcular reaciones de vigas horizontales estaticamente
determinadas y sus diagramas de cortante V y flector M
https://www.youtube.com/watch?v=T5DKkUEisss  video de codigo

J. Daniel Garcia Castro
"""

from matplotlib import pyplot as plt
import numpy as np

#l = input('Ingrse longitud de la viga: ') # long de la viga
f = int(input('Ingrese numero de fuerzas: ')) # cant de fuerzas
f_todas = []
for i in range(f):    
    print('fuerza ',i+1)
    print('C) concentrada      D) distribuida')
    tipo_f_1 = input('Sel.: ')
    tipo_f_1 = tipo_f_1.lower()
    f_n = []
    
    if tipo_f_1 == 'c':                     # se seleccionó concentrada
        f_m = input('Magnitud (m)(indicar signo): ')
        f_n.append(f_m)                     # primero va la mag.
        f_c = input('Coordenada (m): ')
        f_n.append(f_c)                     # luego coordenada
        m = f_m * f_c
        f_n.append(m)                       # y al final el momento respecto soporte A
        f_todas.append(f_n)
    
    elif tipo_f_1 == 'd':
        print('T) triangulo  R) rectangulo')
        tipo_f_2 = input('Sel.: ')
        tipo_f_2 = tipo_f_2.lower()
        
        if tipo_f_2 == 't':
            print('triangulo')
            print('debe ser decrecinte y fuerza min > 0')
            #magnitud resultante
            f_max = int(input('Fuerza max (N): '))
            print('Seleccione si fuerza min=0 o >0 ')
            f_min_sel = 0
            while f_min_sel != (1 or 2):
                f_min_sel = int(input('1)f_min = 0      2) f_min > 0'))
            
            f_d = int(input('Metros de la fuerza aplicada (m): '))
            f_r = ( (f_max - f_min)*(f_d) )/2 + (f_d)*(f_min)
            f_n.append(f_r)
            #coordenada resultante
            f_c = int(input('Coordenada de inicio: '))
            f_c_r = f_c + (1/3)*f_d
            f_n.append(f_c_r)
            #m = - 
            f_todas.append(f_n)
        
        elif tipo_f_2 == 'r':
            print('rectangulo')
            f_m = int(input('Fuerza distribuida (N/m): '))
            f_d = int(input('Metros de la fuerza aplicada (m): '))
            f_r = f_d * f_m
            f_n.append(f_r)
            #fuerza resultante a var fuerza sub n
            f_c = int(input('Coordenada de inicio: '))
            f_c_r = (f_c + (f_d/2))            
            f_n.append(f_c_r)
            # coordenada resultante
            f_todas.append(f_n)
             
    else: print('Sel. erronea')
    
M=q/2 * (l*x - x**2)    #Ecuación de momento flector
V=q *(l/2 - x)          #Ecuación de fuerza cortante
x = np.linspace(0,l,50) #creamos la cordenada x desde 0 a l

plt.plot(x, [0]*len(x), color='k', label='Viga')
plt.xlabel('Longitud, (m)')
plt.ylabel('M y F')



#x = np.linspace(0,int(l),int(f)) # crear coordenadassde 0 hasta l separada por f
#plt.plot([0]*len(x),color='k') # grafica de la viga

sum_f_x = 0
sum_f_y = 0
