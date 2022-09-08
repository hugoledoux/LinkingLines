#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 14:45:57 2022

@author: akh
"""

from plotmod import DotsLines, whichForm
import numpy as np 
from PrePostProcess import transformXstart
import matplotlib.pyplot as plt


def dilation(df, binWidth=1700, averageWidth=1, method='Expanded'):
    t,r=whichForm(df)
    df=transformXstart(df)
    
    xs=[ min(df['Xstart'].min(), df['Xend'].min() ), max( df['Xstart'].max(), df['Xend'].max() )]
    ys=[ min(df['Ystart'].min(), df['Yend'].min() ), max( df['Ystart'].max(), df['Yend'].max() )]
    
    if np.ptp(xs) < binWidth or np.ptp(ys) < binWidth:
        binWidth=np.min( [np.ptp(xs)/10, np.ptp(ys)/10])
    
    binx=np.arange(xs[0]-binWidth, xs[1]+binWidth, binWidth)
    biny=np.arange(ys[0]-binWidth, ys[1]+binWidth, binWidth)
    
    FractionEW=np.cos(np.deg2rad(df[t].values))
    # for theta=0, Fraction EW is 1, for theta=90 fractonEW is 0
    FractionNS=abs(np.sin(np.deg2rad(df[t].values)))
    # its the opposite of above
    
    Xstart=df['Xstart'].values
    Ystart=df['Ystart'].values
    Xend=df['Xend'].values
    Yend=df['Yend'].values
    
    y=np.array([Ystart,Yend]).T
    Ystart=np.min(y, axis=1)
    Yend=np.max(y, axis=1)+1
    # for now sort Yend and Ystart, can't keep it but for now it's okay
    
    
    
    EWDilation=np.zeros_like(biny)
    NSDilation=np.zeros_like(binx)
    
    TotalEWDilation=0
    TotalNSDilation=0
    

    for i in range(len(binx)-1):
        
        # Case 1: Line Passes completely thru bin
        maskx1= np.logical_and( (Xstart< binx[i]), (Xend>binx[i+1]))
        
        #Case 2: Starts in Bin 
        maskx2=np.logical_and( (Xstart> binx[i]), (Xstart<binx[i+1]) ) 
                
        #Case3: Ends in Bin 
        maskx3=np.logical_and( (Xend> binx[i]), (Xend<binx[i+1]) ) 
        
        maskx=np.logical_or(maskx1, np.logical_or(maskx2, maskx3))
        
        #print(np.sum(maskx), "in binx",binx[i], "-", binx[i+1] )
        l=np.where(binx==binx[i])
        #print(np.sum(maskx))
        if np.isclose(np.sum(maskx), 0.0):
            NSDilation[l]=0
        elif method == 'Average':
            NSDilation[l]= np.mean(FractionNS[maskx])*averageWidth*np.sum(maskx)
        elif method== 'Total':
            NSDilation[l]= np.sum(FractionNS[maskx])*averageWidth
        elif method =='Expanded':
             NSDilation[l]= (np.sum(FractionNS[maskx1]) +
                             np.sum( (abs(Xstart[maskx2]-binx[i])/binWidth)*FractionNS[maskx2]) +
                             np.sum( (abs(Xend[maskx3]-binx[i])/binWidth)*FractionNS[maskx3]))*averageWidth

    for j in range(len(biny)-1):
         # Case 1: Line Passes completely thru bin
        masky1= np.logical_and( (Ystart< biny[j]), (Yend>biny[j+1]))
        
        #Case 2: Starts in Bin 
        masky2=np.logical_and( (Ystart> biny[j]), (Ystart<biny[j+1]) ) 
                
        #Case3: Ends in Bin 
        masky3=np.logical_and( (Yend> biny[j]), (Yend<biny[j+1]) ) 
        
        masky=np.logical_or(masky1, np.logical_or(masky2, masky3))
        
        #print(np.sum(masky), "in biny",biny[j], "-", biny[j+1] )
        l=np.where(biny==biny[j])
        #print(np.sum(masky))
        if np.isclose(np.sum(masky), 0.0):
            EWDilation[l]=0
        elif method == 'Average':
            EWDilation[l]= np.mean(FractionEW[masky])*averageWidth*np.sum(masky)
        elif method== 'Total':
            EWDilation[l]= np.sum(FractionEW[masky])*averageWidth
        elif method =='Expanded':
            EWDilation[l]= (np.sum(FractionEW[masky1]) +
                            np.sum( (abs(Ystart[masky2]-biny[j])/binWidth)*FractionEW[masky2]) +
                            np.sum( (abs(Yend[masky3]-biny[j])/binWidth)*FractionEW[masky3]))*averageWidth
            


    return EWDilation, NSDilation, binx, biny


# E: 420231 N:4905680
# E: 523230 N:5094091

#df=pd.read_csv('dikedata/crb/CJDS_FebStraightened.csv')