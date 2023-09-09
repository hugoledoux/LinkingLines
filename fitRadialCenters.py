#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 12:44:20 2021

@author: akh
"""
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit 
import numpy as np 
import pandas as pd
from plotmod import plotlines, DotsLines
from PrePostProcess import whichForm, writeToQGIS
from htMOD import HT_center
from clusterMod import CyclicAngleDist
import numpy as np

from scipy.spatial.distance import pdist, squareform

def mysigmoid(x,a, b, c):
    return a/((1+np.e**(c*x))+0.0000001)+b

def sigmoidFit(lines, plot=False, ColorBy=None, weight='LayerNumber', ThetaRange=[-90,90], xc=None, yc=None):
    t,r=whichForm(lines)
    theta=lines[t].values
    rho=lines[r].values
    
    m=(theta>ThetaRange[0]) & (theta<ThetaRange[1])
    theta=theta[m]
    rho=rho[m]    
    
    if plot:
        fig,ax=DotsLines(lines, ColorBy=ColorBy, cmap='turbo')
        xdata=np.linspace(-90,90,200)

            
    Fits=pd.DataFrame()
    
    if 'xc' in lines.columns and xc is None:
        xc=lines['xc'].values[0]
        yc=lines['yc'].values[0]
    elif xc is None: 
        xc,yc=HT_center(lines)
        
        
    popt, pcov=curve_fit( mysigmoid, theta,rho )
    perr = np.sqrt(np.diag(pcov))
    
    residuals=rho-mysigmoid(theta, *popt)
    ss_res=np.sum(residuals**2)
    ss_tot=np.sum( (rho-np.mean(rho))**2)
    r_sq=1-(ss_res/ss_tot)
    Fits=pd.DataFrame({ "Sigmoid Fit":[popt], "Std Error": [perr], 'RSq':r_sq})
    if plot:
       
        ax[1].plot(xdata, mysigmoid(xdata, *popt), 'y-',
                 label='fit: a=%5.3f, b=%5.3f, c=%5.3f'  % tuple(popt), linewidth=3)
        ax[0].plot( popt[0], popt[1], '*g', markersize=10)
        
        plt.legend()
    
    return Fits

def CenterFunc(theta,xr,yr, xc, yc):
    rhoRadial=(xr-xc)*np.cos(np.deg2rad(theta))+(yr-yc)*np.sin(np.deg2rad(theta))
    return rhoRadial

def CenterFuncDf(centers, xc, yc):
    rhoRadial=(xr-xc)*np.cos(np.deg2rad(theta))+(yr-yc)*np.sin(np.deg2rad(theta))
    return rhoRadial
    
def RadialFit(lines,plot=False, ColorBy=None, weight='LayerNumber', ThetaRange=[-90,90], xc=None, yc=None):
    t,r=whichForm(lines)
    theta=lines[t].values
    rho=lines[r].values
    
    m=(theta>ThetaRange[0]) & (theta<ThetaRange[1])
    theta=theta[m]
    rho=rho[m]    
    
    if plot:
        fig,ax=DotsLines(lines, ColorBy=ColorBy, cmap='turbo')
        xdata=np.linspace(-90,90,200)

            
    Centers=pd.DataFrame()
    
    if 'xc' in lines.columns and xc is None:
        xc=lines['xc'].values[0]
        yc=lines['yc'].values[0]
    elif xc is None: 
        xc,yc=HT_center(lines)
        
        
    popt, pcov=curve_fit( lambda angle, xr,yr: CenterFunc(angle, xr, yr, xc, yc), theta,rho )
    perr = np.sqrt(np.diag(pcov))
    
    residuals=rho-CenterFunc(theta, *popt, xc,yc)
    ss_res=np.sum(residuals**2)
    ss_tot=np.sum( (rho-np.mean(rho))**2)
    r_sq=1-(ss_res/ss_tot)
    Centers=pd.DataFrame({ "Center":[popt], "Std Error": [perr], 'RSq':r_sq})
    if plot:
       
        ax[1].plot(xdata, CenterFunc(xdata, *popt, xc, yc), 'y-',
                 label='fit: xr=%5.3f, yr=%5.3f' % tuple(popt), linewidth=3)
        ax[0].plot( popt[0], popt[1], '*g', markersize=10)
        
        plt.legend()
    return Centers

def RadialAzimuthal(lines, Center):
    
    xdist=lines['Xmid'].values-Center['Center'][0][0]
    ydist=lines['Ymid'].values-Center['Center'][0][1]
    
    rAngle=np.rad2deg(np.arctan2(xdist,ydist))+180

    return rAngle
def CyclicAngle360(u,v):
    return (u-v)%360

def AngleSpacing(rAngle):
    
    SrAngle=np.sort(rAngle)
    
    spacing=np.abs(SrAngle[0:-2]-SrAngle[1:-1])
    
    return np.mean(spacing), np.median(spacing), np.min(spacing), np.max(spacing)

def RipleyRadial(rAngle, plot=False):
    
    """
    Measure of radial dike swarm angle "clumpiness"
    Inpsired by the Ripley K funciton https://stats.stackexchange.com/questions/122668/is-there-a-measure-of-evenness-of-spread
    
    Input: theta, array 
        array of angles in radial swarm
    
    Output: R, float 
    
     """
    tRange=CyclicAngle360( np.max(rAngle), np.min(rAngle))
    theta=rAngle[:,None]
    steps=np.arange(0,360,10)
    
    n=len(rAngle)
    l=n/360
    
    d=squareform(pdist(theta, metric=CyclicAngle360))
    
    counts=[np.histogram(i, bins=steps)[0] for i in d]
    K=l*np.cumsum(counts, axis=1)/n
    L=np.sqrt(np.sum(np.cumsum(counts, axis=1), axis=1)/(np.pi*n*(n-1)))
    
    K_Pure=np.ones(len(K))*l/n
    
    K_se=np.sum( (K-K_Pure)**2)/n
    
    if plot:
        fg,ax=plt.subplots()
        ax.plot(steps[:-1], K_Pure, 'k.-')
        ax.plot(steps[:-1], K, 'r.-')
        return K, K_se, fg, ax
    else:
        return K, K_se
    
def ExpandingR(lines,Center):
    t,r=whichForm(lines)
    tols=np.array([0.0001, 0.005, 0.01, 0.1, 0.2, 0.5, 0.75, 1])*np.ptp(lines[r].values)
    ntol=np.empty(len(tols))
    
    xdata=lines[t].values
    xc=lines['xc'].values[0]
    yc=lines['yc'].values[0]
    
    rhoPerfect=CenterFunc(xdata, Center['Center'][0][0], Center['Center'][0][1], xc, yc)
    
    ntol=[np.sum(abs(lines[r].values-rhoPerfect)<tol)/len(lines) for tol in tols]

    return ntol
    
def NearCenters(lines, Center, tol=10000, printOn=False):
    t,r=whichForm(lines)
    
    xdata=lines[t].values
    xc=lines['xc'].values[0]
    yc=lines['yc'].values[0]
    rhoPerfect=CenterFunc(xdata, Center['Center'][0][0], Center['Center'][0][1], xc, yc)
    
    close=abs(lines[r].values-rhoPerfect)<tol
    ntol=ExpandingR(lines,Center)
    Close=lines[close]
    rAngle=RadialAzimuthal(Close, Center)
    maxt=np.max(rAngle)
    mint=np.min(rAngle)
    spacing=AngleSpacing(rAngle)
    #K,K_se=RipleyRadial(rAngle)
    
    if printOn:
        print("For Center", Center['Center'][0][0], Center['Center'][0][1])
    
        print( "Max angle Range is ", CyclicAngle360(maxt, mint))
        
        print( "Angle Spacing is ")
        
        print("Mean: Median: Min: Max:")
        print(spacing)
        
    
        print("Deviation from perfect radial angle spread")
        #print("K_se:", K_se)
        print("Perfect K_se would be 0")
        
    CenterDist1= np.sqrt( (Center['Center'][0][0] - Close['Xstart'].values)**2 +  (Center['Center'][0][1] - Close['Ystart'].values)**2)
    CenterDist2= np.sqrt( (Center['Center'][0][0] - Close['Xend'].values)**2 +  (Center['Center'][0][1] - Close['Yend'].values)**2)
    
    MinDist=np.min(np.vstack((CenterDist1, CenterDist2)), axis=0)
        
    Close=Close.assign(CenterDistStart=CenterDist1, CenterDistEnd=CenterDist2, CenterDist=MinDist, CenterX=Center['Center'][0][0], CenterY=Center['Center'][0][1], RadialAngles=rAngle)

    if "T" in t:
        clusters=len(Close)
        dikes=Close['Size'].sum()
        filt=Close['TrustFilter'].sum()
        
        Center=Center.assign( Spacing=[spacing], ExpandingR=[ntol], AngleRange=CyclicAngle360(maxt, mint), ClustersN=clusters, DikesN=dikes,FilteredN=filt)
    else:
        n=len(Close)
        Center=Center.assign( Spacing=[spacing], ExpandingR=[ntol], AngleRange=CyclicAngle360(maxt, mint), nDikes=n)
        
        
    
    
    return Close, Center

    
    
def writeCenterWKT(df,name):
    
    front="POINT ("
    linestring=[]
    for i in range(len(df)):
        line=front+str( (df['Center'].iloc[i])[0])+" "+str((df['Center'].iloc[i])[1])+")"
        linestring.append(line)
    
    df['Pointstring']=linestring 
    df['Pointstring']=df['Pointstring'].astype(str)
    df.to_csv(name)
    
     # for i in theta:
     #     temp=np.abs(theta-i)
     #     for s in steps: 
     #         count=np.sum(temp<s)/n
             
     
     
     
    
    
# xdata = np.linspace(-10, 10, 100)
# rho = CenterFunc(xdata, 2500,2500, 0,0)
# rng = np.random.default_rng()
# rho_noise = 100 * rng.normal(size=xdata.size)
# ydata = rho + rho_noise
# plt.plot(xdata, ydata, 'b-', label='data, a=2500, b=2500')

# a,b=curve_fit(CenterFunc, xdata, ydata)
# xc=0
# yc=0
# a, b=curve_fit( lambda t, xr,yr: CenterFunc(t, xr, yr, xc, yc), xdata,ydata )
# xdata = np.linspace(-90, 90, 100)
# plt.plot(xdata, CenterFunc(xdata, *a, xc, yc), 'r-',
#           label='fit: a=%5.3f, b=%5.3f' % tuple(a))

# plt.ylabel('rho')
# plt.xlabel('theta')
# plt.legend()
# plt.show()