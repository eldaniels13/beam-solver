# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 16:27:55 2022

@author: josed.garcia
"""
#%%
import numpy as np
from numpy import genfromtxt
import time
#my_data = genfromtxt(r'C:\Users\josed.garcia\OneDrive - ITESO\5º Semestre\Solidos Deformables\BeamDyVpy\Fuerzas.csv', delimiter=',')
#print(my_data)
#%%
l = float(input('Longitud de la viga horizontal: '))   # longitud de viga
def verificador(a):
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
                a[a.index(fuerza)][1]= float(input('Nueva coordenada: '))
                # sustituir la nueva fuerza


    print('Se han registrado las cargas')