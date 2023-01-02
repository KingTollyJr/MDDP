import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import pickle as pkl
from shapely.geometry import Point,Polygon,mapping, MultiPolygon
from shapely import wkt
from pyproj import Proj, transform
import numpy as np
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

def m2deg(var):
    var = var.to_crs('epsg: 4326')
    return var


def deg2m(var):
    if var.crs == 'None':
        var.crs = 'EPSG: 4326'


    var = var.to_crs('epsg: 3857')
    return var

def resetindex(file):
    file.reset_index(inplace=True)
    return file


def readPickle(file):
    with open(file,'rb') as f:
        var = pkl.load(f)
    return var

def intersectAirports(EEZ,geometry,Airports):
#
    EEZ['Contains'] = 'N'
    EEZ['Airport geometry'] = np.nan
    for i,poly1 in EEZ.iterrows():
        for j,poly2 in Airports.iterrows():
            if poly1[geometry].intersects(poly2[geometry]) == True:
                EEZ.loc[i,'Contains'] = 'Y'
                EEZ.loc[i,'Airport geometry'] = poly2['geometry']

    return EEZ

def hasAirportbuffer(EEZ,contains):

    EEZ['Buffer'] = np.nan

    for i,poly1 in EEZ.iterrows():
        if EEZ[contains][i] == 'Y':
            EEZ.loc[i,'Buffer'] = EEZ[i]['Airport Geometry'].buffer(distance = 2000*1000/2)

    return EEZ

def doesnthaveairportbuffer(Territories,geometry,EEZ,buffer):
    for i,poly1 in Territories.iterrows():
        for j, poly2 in EEZ.iterrows():

            if poly1['index'] > 0 and Territories[i,'name'] != Territories[i-1,'name']:
                if poly1[geometry].interects(poly2[buffer]) == False:
                    centre = poly1[geometry].centroid()
                    EEZ.loc[i,'Airport Geometry'] = centre
                    EEZ.loc[i,buffer] = Territories[i]['Airport Geometry'].buffer(distance = 1300*1000/2)
            elif poly1[geometry].intersects(poly2[buffer]) ==False:
                centre = poly1[geometry].centroid()
                EEZ.loc[i, 'Airport Geometry'] = centre
                EEZ.loc[i, buffer] = Territories[i]['Airport Geometry'].buffer(distance=1300 * 1000 / 2)

    return EEZ

def EEZ2worldmap(EEZ,map):
    map['EEZ'] = np.nan

    for i,ref in map.iterrows():
        for j,ref2 in EEZ.iterrows():
            if EEZ.loc[j,'TERRITORY1'] == 'Falkland / Malvinas Islands' and map.loc[i,'name'] == 'Falkland Islands (Malvinas)':
                map.loc[i,'EEZ'] = EEZ['geometry'][j]
                map.loc[i,'name2'] = EEZ['TERRITORY1'][j]
            elif EEZ.loc[j,'TERRITORY1']==map.loc[i,'name']:
                map.loc[i,'EEZ'] = EEZ['geometry'][j]
                map.loc[i,'name2'] = EEZ['TERRITORY1'][j]
            elif EEZ.loc[j,'TERRITORY1'] == 'South Georgia and the South Sandwich Islands' and map.loc[i,'name'] == 'South Georgia & the South Sandwich Islands':
                map.loc[i, 'EEZ'] = EEZ['geometry'][j]
                map.loc[i, 'name2'] = EEZ['TERRITORY1'][j]

            elif map.loc[i,'name'] == 'British Indian Ocean Territory':
                print('indian ocean')
            else:
                print('not sure whats going on')
    return map

def airport(file,col):
    file['Airport'] = 'Y'
    for i,ref in file.iterrows():
        if file.loc[i,col] == 'Tristan da Cunha':
            file.loc[i,'Airport'] = 'N'
    return file

def Optimisation(EEZ):
    intersection = []
    intersection2 = []
    area = []
    # First two loops compare all the drone coverage areas to each other
    for i,ref in EEZ.iterrows():
        for j,ref2 in EEZ.iterrows():
            # Pulls out drone areas that intersect
            if ref['dronearea'].intersects(ref2['dronearea']) == True:
                # Compares those drone areas to EEZ areas and finds where they intersect
                for k, ref3 in EEZ.iterrows():
                    if ref3['geometry'].intersects(ref['dronearea']) == True and ref3['geometry'].intersects(ref2['dronearea']) == True:
                        # Takes the intersection with the EEZ
                        # creates a polygon of the intersection area with both drone coverages
                        # Then compares the areas found with the area of the EEZ to get a coverage score
                        # chooses the best
                        intersection = (ref3['geometry'].intersection(ref['dronearea']))
                        intersection2 = (ref3['geometry'].intersection(ref2['dronearea']))
                        area1 = intersection.area
                        area2 = intersection2.area
                        EEZarea = ref3['geometry'].area

# greats a score of each drone are to EEZ area
def drones2areas(EEZ,worldmap):
    # new dataframe with the territory,EEZ and each drone coverage score
    coverage = EEZ.filter(['Territory'])
    for i,ref in worldmap.iterrows():
        name = ref['country']
        coverage[name] =np.nan
        for j,ref2 in EEZ.iterrows():
            if ref2['geometry'].intersects(ref['buffer']) == True:
                coveragearea = ref2['geometry'].intersection(ref['buffer'])
                coveragearea = coveragearea.area
                eezarea = ref2['geometry'].area

                score = coveragearea/eezarea
                coverage.loc[j,name] = score
            else:
                coverage.loc[j,name] = 0



    return coverage

def AisInzone(EEZ,AIS):
    Inzone = EEZ.filter(['Territory'])
    Inzone = Inzone.rename({'Territory':'Country Name'},axis = 1)
    Inzone['2017'] = 0
    Inzone['2018'] = 0
    Inzone['2019'] = 0
    print(Inzone)
    for i, ref in tqdm(EEZ.iterrows(),total=EEZ.shape[0]):
        for j, ref2 in AIS.iterrows():
            if ref['geometry'].intersects(ref2['buffer']) == True:
                year = ref2['Year']
                k = Inzone.loc[i,str(year)]
                k = k+1
                Inzone.loc[i,str(year)] = k

    return Inzone

def AISInDrone(EEZ,Dronebase,AIS):
    Inzone = Dronebase.filter(['country'])
    Inzone = Inzone.rename({'country':'Location'},axis = 1)
    Inzone['2017'] = 0
    Inzone['2018'] = 0
    Inzone['2019'] = 0
    Inzone['Mean'] = 0

    for i,ref in Dronebase.iterrows():
        for j, ref2 in AIS.iterrows():
            for g,ref3 in EEZ.iterrows():
                if ref['buffer'].intersects(ref2['buffer']) == True and ref3['geometry'].intersects(ref2['buffer']) == True:

                    year = ref2['Year']
                    k = Inzone.loc[i,str(year)]
                    k = k+1
                    Inzone.loc[i,str(year)] = k

    for k, ref4 in Inzone.iterrows():
        y1 = ref4['2017']
        y2 = ref4['2018']
        y3 = ref4['2019']
        g = (y1+y2+y3)/3
        Inzone.loc[k,'Mean'] = g

    return Inzone

def distance(EEZ,bases,AIS,Inzone):
    dist = pd.DataFrame(index=range(Inzone['Mean'].max()))
    for i,ref in tqdm(bases.iterrows(),total=bases.shape[0]):
        a = 0
        col = ref['country']
        dist[col] = np.nan
        for k,ref3 in EEZ.iterrows():
            if ref3['geometry'].intersects(ref['buffer']) == True:
                for j, ref2 in AIS.iterrows():
                    if ref['buffer'].intersects(ref2['buffer']) == True and ref3['geometry'].intersects(ref2['buffer']) == True:
                        d = ref['geometry'].distance(ref2['geometry'])
                        dist.loc[a,col] = d
                        a = a+1
    return dist

def Sigma(bases,dist):
    list1 = []
    list2 = []#
    if 'Unnamed: 0' in dist.columns:
        dist.drop(columns = ['Unnamed: 0'],inplace=True)
    for j,column in bases.iterrows():
        l = np.array(dist[column['country']])
        m = np.nanmean(l)
        list1.append(m)

        counts = dist[column['country']].notna().sum()
        list2.append(counts)

    bases['Mean Distance'] = list1
    bases['N'] = list2
    i = 0

    meandist = np.array(bases['Mean Distance'])
    N = np.array(bases['N'])
    sigma = []
    for column in dist.columns:
        list3 = np.array([dist[column]])
        mask = np.isnan(list3)
        list3 = list3[~mask]
        x = meandist[i]
        sumof = np.sum(np.square(list3 - x))
        sig = np.sqrt((sumof)/N[i])
        sigma.append(sig)
        i = i+1

    sigma = pd.DataFrame(sigma,columns=['Sigma'])
    sigma['Territory'] = bases['country']
    sigma = sigma.reindex(columns = ['Territory','Sigma'])
    sigma['Mean'] = list1

    return sigma

def func(m,x,b):
    y = m * x + b
    return y

def UKCoverage(EEZ,UKDrones,NonUkDrones):
    MultiUK = UKDrones['buffer'].unary_union
    NonUkDrones.rename(columns = {'country':'Territory'},inplace = True)
    MultiUK = gpd.GeoDataFrame(geometry=[MultiUK])
    MultiUK['Territory'] = 'All UK Based UAVs'
    MultiUK = MultiUK.reindex(columns = ['Territory','geometry'])
    NonUK = pd.DataFrame(NonUkDrones['Territory'])
    NonUK['geometry'] = NonUkDrones['buffer']
    NonUK = gpd.GeoDataFrame(NonUK,geometry='geometry',crs='epsg:3857')
    Drones = pd.concat([MultiUK,NonUK])
    Drones = resetindex(Drones)
    coverage = EEZ.filter(['Territory'])
    for i,ref in Drones.iterrows():
        name = ref['Territory']
        coverage[name] = np.nan
        for j,ref2 in EEZ.iterrows():
            if ref['geometry'].intersects(ref2['geometry']) == True:
                coveragearea = ref['geometry'].intersection(ref2['geometry'])
                coveragearea = coveragearea.area
                eezarea = ref2['geometry'].area
                score = coveragearea/eezarea
                coverage.loc[j,name] = score
            else:
                coverage.loc[j,name] = 0
    coverage = resetindex(coverage)
    coverage = coverage.sort_values(by=['Territory'])
    coverage = coverage.sort_index(axis=1)
    return coverage




EEZ = readPickle(r'Data\Pickled Files\EEZnew.pkl')
worldmap = readPickle(r'Data\Pickled Files\worldmap.pkl')
worldmapUK = readPickle(r'Data\Pickled Files\worldmap_UK_T.pkl')
AISDisabled = readPickle(r'Data\Pickled Files\AISDisable_time.pkl')
Airports = pd.read_csv(r'Data\Airport locations for dronesv3.csv')
Airports = gpd.GeoDataFrame(Airports,geometry=gpd.points_from_xy(Airports.lat,Airports.lon),crs='epsg:4326')
Ukdrone = pd.read_csv(r'Data\UKDroneLocation.csv')
Ukdrone = gpd.GeoDataFrame(Ukdrone,geometry=gpd.points_from_xy(Ukdrone.lat,Ukdrone.lon),crs='epsg:4326')
nonUKDrone = pd.read_csv(r'Data\NonUKDrones.csv')
nonUKDrone = gpd.GeoDataFrame(nonUKDrone,geometry=gpd.points_from_xy(nonUKDrone.lat,nonUKDrone.lon),crs = 'epsg:4326')


AISDisabled['buffer2'] = AISDisabled['geometry'].buffer(distance = 0.5)

# correcting coordinate systems
worldmapUK = deg2m(worldmapUK)
EEZ = deg2m(EEZ)
worldmap = deg2m(worldmap)
worldmapUK = deg2m(worldmapUK)
AISDisable = deg2m(AISDisabled)
Airports = deg2m(Airports)

Ukdrone = deg2m(Ukdrone)
nonUKDrone = deg2m(nonUKDrone)



worldmapUK['centre'] = worldmapUK['geometry'].centroid

# resetting index
EEZ = resetindex(EEZ)
worldmapUK = resetindex(worldmapUK)
Airports = resetindex(Airports)
AISDisable = resetindex(AISDisable)

dronerange = 2000*1000/2
pd2range = 1000*1000/2

# Drone coverage
worldmapUK = airport(worldmapUK,'name')
Airports['buffer'] = Airports['geometry'].buffer(distance = dronerange)
Airports['PD2'] = Airports['geometry'].buffer(distance = pd2range)
AIStimemean = AISDisable['gap_hours'].mean()
AIStimemean = int(AIStimemean)
worldmapUK['buffer2'] = worldmapUK['centre'].buffer(distance = dronerange)

Ukdrone['buffer'] = Ukdrone['geometry'].buffer(distance = dronerange)
nonUKDrone['buffer'] = nonUKDrone['geometry'].buffer(distance = dronerange)

CoverageFromBases = UKCoverage(EEZ,Ukdrone,nonUKDrone)

CoverageFromBases.to_csv(r'OutputData\csvs\DroneCoverageFromBases.csv')


# AIS Buffer
AISDisable['buffer'] = AISDisable['geometry'].buffer(distance = 1800*AIStimemean)

Inzone = AisInzone(EEZ,AISDisable)
# with open('Inzonev2.pkl','rb') as f:
#     Inzone = pkl.load(f)



Inzone.to_csv(r'OutputData\csvs\IllegalOccurances.csv')

AISDroneLocation = AISInDrone(EEZ,Airports,AISDisable)
AISDroneLocation.to_csv(r'OutputData\csvs\IllegalInDroneRangeNo.csv')

# with open('AISDroneLocationv6.pkl','rb') as f:
#     AISDroneLocation = pkl.load(f)
# AISDroneLocation.to_csv(r'OutputData\csvs\IllegalInDroneRangeNov6.csv')
AISDroneLocation['Mean'] = AISDroneLocation['Mean'].round()
AISDroneLocation['Mean'] = AISDroneLocation['Mean'].astype(int)
dist = distance(EEZ,Airports,AISDisable,AISDroneLocation)
# dist = pd.read_csv(r'OutputData\csvs\Distancev5.csv')

dist.to_csv(r'OutputData\csvs\Distance.csv')

sigma = Sigma(Airports,dist)

sigma['Mean'] = sigma['Mean']/1000
sigma['Sigma'] = sigma['Sigma']/1000
sigma = sigma.dropna()
ydrone = np.array([0,10])
xdrone = np.array([0,dronerange/1000])
m = (ydrone[1]-ydrone[0])/(xdrone[1]-xdrone[0])
b = ydrone[0]
j = 0
x = np.linspace(0,1000000/1000,num=1000)
l1 = []
l2 = []
AISInDroneLoc = pd.read_csv(r'OutputData\csvs\IllegalInDroneRangeNo.csv')
AISInDroneLoc['Mean Flight Time'] = np.nan
AISInDroneLoc['Mean Distance to Illegal Activity'] = np.nan
for i,ref in sigma.iterrows():
    firstbit = 1/(ref['Sigma']*np.sqrt(2*np.pi))
    secondbit = np.exp(-0.5*np.square((x-ref['Mean'])/ref['Sigma']))
    y = (firstbit*secondbit)
    xtime = ref['Mean']
    ytime = func(m,xtime,b)
    fig, ax = plt.subplots(figsize = (12,10))
    row = i //2
    if row ==3 or row == 4:
        row =2
    col = i % 2
    AISInDroneLoc.loc[i,'Mean Flight Time'] = round(ytime,2)
    AISInDroneLoc.loc[i,'Mean Distance to Illegal Activity'] = round(ref['Mean'],2)
    l1.append(col)
    l2.append(row)
    ax.plot(xdrone,ydrone,color = 'black',linestyle = '--',label = 'UAV Flight Time')
    ax.set_title(ref['Territory'])
    ax.set_ylabel('UAV Flight Time [hrs]')
    ax.set_xlabel('Distance from UAV Base [km]')
    ax.axvline(x = ref['Mean'],linestyle = 'dotted',color = 'red',label = 'Illegal Activity mean distance of: '+ str(round(ref['Mean'],2))+'km')
    ax.axhline(y = ytime,linestyle = 'dotted',color = 'black',label = 'Flight Time to mean: '+str(round(ytime,2))+'hrs')
    ax2 = ax.twinx()
    ax2.plot(x,y,color = 'red',linestyle = 'solid')
    ax2.set_ylabel('Normal Distribution of Illegal Activities')
    ax.legend(loc = 'upper left')

AISInDroneLoc.to_csv(r'OutputData\csvs\IllegalInDroneRangeNo.csv')

# drone coverage score
coverage = drones2areas(EEZ,Airports)
coverage = coverage.sort_values(by=['Territory'])
coverage = coverage.sort_index(axis=1)
# coverage.to_csv(r'OutputData\csvs\DroneCoveragev3.csv')
AISDisablePlot = pd.DataFrame(AISDisable['buffer'])
AISDisablePlot.rename(columns={'buffer':'geometry'},inplace=True)
AISDisablePlot = gpd.GeoDataFrame(AISDisablePlot,geometry='geometry',crs='epsg:3857')
AirportsPlot = pd.DataFrame(Airports['buffer'])
AirportsPlot.rename(columns={'buffer':'geometry'},inplace=True)
AirportsPlot = gpd.GeoDataFrame(AirportsPlot,geometry='geometry',crs='epsg:3857')
AirportsPlotpd2 = pd.DataFrame(Airports['PD2'])
AirportsPlotpd2.rename(columns={'PD2':'geometry'},inplace=True)
AirportsPlotpd2 = gpd.GeoDataFrame(AirportsPlotpd2,geometry='geometry',crs='epsg:3857')
worldmapUKPlot = pd.DataFrame(worldmapUK['buffer2'])
worldmapUKPlot.rename(columns={'buffer2':'geometry'},inplace=True)
worldmapUKPlot = gpd.GeoDataFrame(worldmapUKPlot,geometry='geometry',crs='epsg:3857')


worldmapUKPlot = m2deg(worldmapUKPlot)
AISDisablePlot = m2deg(AISDisablePlot)
AISDisable = m2deg(AISDisable)
EEZ = m2deg(EEZ)
worldmap= m2deg(worldmap)
worldmapUK = m2deg(worldmapUK)
AirportsPlot = m2deg(AirportsPlot)
AirportsPlotpd2 = m2deg(AirportsPlotpd2)
Airports = m2deg(Airports)
worldmapUK['centre'] = worldmapUK['geometry'].centroid
lon = worldmapUK['centre'].x
lat = worldmapUK['centre'].y

#Comment in out whatever you want plotting
fig, ax = plt.subplots(1,figsize = (12,10))

worldmap.plot(ax = ax,color = 'darkgray',label = 'World')
# worldmapUK['geometry'].plot(ax=ax,color = 'blue',label = 'UK Controlled Areas')
# worldmapUKPlot['geometry'].plot(ax = ax,color = 'blue',alpha = 0.3,label = 'Drone Radius')
# EEZ['geometry'].plot(ax=ax,color = 'limegreen',alpha = 0.5,label = 'UK & Territories EEZ')
# AirportsPlot['geometry'].plot(ax=ax,color = 'blue',alpha = 0.3,label = 'UAV Radius')
# worldmapUK['buffer'].plot(ax=ax,color = 'blue',alpha = 0.3)
AISDisable['buffer2'].plot(ax=ax,color = 'red',alpha = 0.3,label = 'AIS Disabling events')
ax.set_ylabel('Longitude')
ax.set_xlabel('Latitude')
ax.legend(loc = 'upper left')
# for i,ref in worldmapUK.iterrows():
#     ax.text(lon[i],lat[i],ref['name'])
# ax.set_ylim([-62.10,-41.24])
ax.set_xlim([-180,180])




plt.show()


