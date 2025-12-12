#!/bin/env python

import os
import datetime
import logging
logger  = logging.getLogger(__name__)

import numpy as np
import pandas as pd

import matplotlib as mpl
from matplotlib import pyplot as plt

import grapeDRF

import digital_rf as drf
import load_metadata
import sys
import re

letters = 'abcdefghijklmnopqrztuvwxyz'

mpl.rcParams['font.size']       = 12
mpl.rcParams['font.weight']     = 'bold'
mpl.rcParams['axes.grid']       = True
mpl.rcParams['axes.titlesize']  = 30
mpl.rcParams['grid.linestyle']  = ':'
mpl.rcParams['figure.figsize']  = np.array([15, 8])
mpl.rcParams['axes.xmargin']    = 0
mpl.rcParams['legend.fontsize'] = 'xx-large'

# directories ==============================================================================================================================

# set base directory for subsequent read operations and set up digital RF reader appropriate directory
base_directory='./'
data_dir=os.path.join(base_directory,'data','psws_grapeDRF')
output_dir=os.path.join(base_directory,'output')

do = drf.DigitalRFReader(data_dir)

# command line arguments ===================================================================================================================

# check for four command line arguments
n = len(sys.argv)
if n<=4:
    print ("Rerun with channel name, frequency index and start and stop hours as four command line arguments")
    exit()
if n>5:
    print ("Rerun with channel name, frequency index and start and stop hours as four command line arguments")
    exit()
    
# assign first three command line arguments to variables, check time span and that end time > start time + one hour
channel=sys.argv[1]
freq_index=int(sys.argv[2])    # Get index from metadata frequency list e.g. use grape_digital_RF_metadata.py or inspect PSWS spectrogram
hours_offset=int(sys.argv[3])  # Start time for data input and plot

if hours_offset < 0 or hours_offset > 23:
    print ("Start time (hours) must be between 0 and 23")
    exit()

if (float(sys.argv[4])-float(sys.argv[3])) <1:
    print ("Stop time must be at least one hour greater than start time")
    exit()
    
# extract station name from channel (sys arg 1)
match = re.search(r'ch0_(\w+)', channel)
if match:
    station_name = match.group(1)
    #print(station_name)
else:
    print('No station name found')

# metadata =================================================================================================================================

# Call module function to read in metadata, draws on data_dict code 
#meta_dir = os.path.join(data_dir, station_name, channel, 'metadata')
meta_dir = os.path.abspath(os.path.join(data_dir, station_name, channel, 'metadata'))
print("Resolved meta_dir =", meta_dir)
print("dmd_properties.h5 exists?", os.path.exists(os.path.join(meta_dir, 'dmd_properties.h5')))

dmr = drf.DigitalMetadataReader(os.path.join(meta_dir, 'dmd_properties.h5'))
print("DigitalMetadataReader initialized:", dmr)
print("Start time:", dmr.get_start())

    
(date, freqList, s1, s0, fs, theCallsign, grid, lat_coord, lon_coord) = load_metadata.load_grape_drf_metadata(meta_dir, channel)

'''
# Check sensible and available command line start and stop times
if int(sys.argv[4]) >= ((s1-s0)/10)/3600:
    print ("End time specified beyond end of data set: Reading to last sample in data set")
    length=int(np.floor(((((s1-s0)/10)/3600)-hours_offset)*60))    # calculate length of data in minutes
else:
    length=int(np.floor((int(sys.argv[4])-hours_offset)*60))    # calculate length of data in minutes to be sure in data set

print("Length of selected period ",length, " minutes")

# split year, month, day from full date
year, month, day = map(int, date.split('-'))

#===========================================================================================================================================

station_dct = {}
sdct    = station_dct[station_name] = {}  
#sdct['QTH'] = 'Spring Brook, PA'

if __name__ == '__main__':
    output_dir = os.path.join('output',f'{station_name}_GannonStorm')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    sDate       = datetime.datetime(year,month,day)
    eDate       = datetime.datetime(year,month,day+1)
    station     = station_name
    lat         = lat_coord
    lon         = lon_coord

    figd = {}
    figd['solar_lat']               = lat
    figd['solar_lon']               = lon
    figd['overlaySolarElevation']   = True
    figd['xlim']                    = (sDate,eDate)

    # 'center_frequencies': array([ 2.5 ,  3.33,  5.  ,  7.85, 10.  , 14.67, 15.  , 20.  , 25.  ])
    #cfreqs          = [20,15,10,5]
    cfreqs          = [3.33,7.85,14.67]
    plot_list   = []
    plot_list.append('WDgrape')
    # plot_list.append('VLF')
#    plot_list.append('gmag')

    str_sDate   = sDate.strftime('%Y%m%d.%H%M')
    str_eDate   = eDate.strftime('%Y%m%d.%H%M')
    png_ = []
    png_.append(str_sDate)
    png_.append(str_eDate)
    png_.append(station)
    for pll in plot_list:
        png_.append(pll)
        if pll == 'WDgrape':
            png_ = png_ +  ['{!s}'.format(x) for x in cfreqs]

    png_fname   = '_'.join(png_)+'.png'
    png_fpath   = os.path.join(output_dir,png_fname)


    nrows       = len(plot_list)
    if 'WDgrape' in plot_list:
        nrows += len(cfreqs) - 1
    ncols       = 1
    ax_inx      = 0
    axs         = []

    fig         = plt.figure(figsize=(22,nrows*5))
    letter_fdict = {'size':32}
    # Grape Plots ##########################
    if 'WDgrape' in plot_list:
        gDRF                        = grapeDRF.GrapeDRF(sDate,eDate,station)
        g_figd                      = figd.copy()
        for cfreq in cfreqs:
            print('   {!s} MHz...'.format(cfreq))
            ax_inx      += 1
            ax          = fig.add_subplot(nrows,ncols,ax_inx)
            axs.append(ax)
            gDRF.plot_ax(cfreq,ax,**g_figd)
            ax.set_title('({!s})'.format(letters[ax_inx-1]),loc='left',fontdict=letter_fdict)
            ax.set_title('{!s} MHz Receiver'.format(cfreq))

            rt_dop_csv = os.path.join('data','shibaji',f'LoS_doppler_{cfreq}.csv')
            if os.path.exists(rt_dop_csv):
                print(f'FOUND: {rt_dop_csv}')
                rt_dop = pd.read_csv(rt_dop_csv)
                rt_dop['time'] = pd.to_datetime(rt_dop['time'])

                xx = rt_dop['time']
                yy = rt_dop['fd']

                ax.plot(xx,yy,color='r',lw=5,zorder=1000)
            else:
                print(f'NOT FOUND: {rt_dop_csv}')

    # Finalize Figure ######################
    for ax_inx,ax in enumerate(axs):
        ax.set_xlim(sDate,eDate)
        xticks  = ax.get_xticks()
        ax.set_xticks(xticks)
        if ax_inx != len(axs)-1:
            ax.set_xlabel('')
            xtkls = ['']*len(xticks)
        else:
            ax.set_xlabel('UTC')
            xtkls   = []
            for xtk in xticks:
                dt      = mpl.dates.num2date(xtk)
                xtkl    = dt.strftime('%H:%M')
                xtkls.append(xtkl)
        ax.set_xticklabels(xtkls)

    sdct    = station_dct.get(station,{})
    if 'QTH' in sdct:
        stxt = '{!s} ({!s})'.format(station.upper(),sdct['QTH'])
    else:
        stxt = station.upper()

    txt = []
    txt.append(stxt)
    txt.append(sDate.strftime('%d %b %Y'))
    fontdict    = {'size':42,'weight':'bold'}
    fig.text(0.5,1.,'\n'.join(txt),fontdict=fontdict,ha='center',va='bottom')

    fig.tight_layout()
    fig.savefig(png_fpath,bbox_inches='tight')
    print(png_fpath)
'''    