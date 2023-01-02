import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely import wkt
from shapely.wkt import dumps
import warnings
import pickle as pkl
warnings.filterwarnings('ignore')


def resetindex(file):
    file.reset_index(inplace=True)
    file.drop(columns=['index'],inplace=True)
    return file


def multiPoly(RADARSys,list_1):
    list_1['geometry'] = np.nan

    list_2 = []
    list_3 = []

    for k,ref in list_1.iterrows():
        if RADARSys['Territory'].value_counts()[ref['Territory']] > 1:
            Temp_MultiRadar = RADARSys.loc[RADARSys['Territory']==ref['Territory']]
            MultiRadar = Temp_MultiRadar['buffer'].unary_union
            list_2.append(MultiRadar)
            list_3.append(ref['Territory'])
        else:
            Temp_poly = RADARSys.loc[RADARSys['Territory']==ref['Territory']]
            Temp_poly = pd.DataFrame(Temp_poly)
            Temp_poly = resetindex(Temp_poly)
            list_1.loc[k,'geometry'] = Temp_poly.loc[0,'buffer']

    MultiPolyR = pd.DataFrame(list_2)
    MultiPolyR.rename(columns={0:'geometry'},inplace=True)
    MultiPolyR['geometry'] = MultiPolyR['geometry'].apply(dumps)
    MultiPolyR['geometry'] = MultiPolyR['geometry'].apply(wkt.loads)
    MultiPolyR['Territory'] = list_3
    MultiPolyR = gpd.GeoDataFrame(MultiPolyR,geometry='geometry')
    MultiPolyR = MultiPolyR.sort_index(axis=1)
    MultiPolyR.crs = 'epsg:3857'

    list_1 = list_1.dropna(subset=['geometry'])
    RADARSys = list_1
    RADARSys['geometry'] = RADARSys['geometry'].apply(dumps)
    RADARSys['geometry'] = RADARSys['geometry'].apply(wkt.loads)
    RADARSysMulti = gpd.GeoDataFrame(RADARSys,geometry='geometry')
    RADARSysMulti.crs = 'epsg:3857'
    RADARSysMulti = pd.concat([RADARSysMulti,MultiPolyR])

    return RADARSysMulti



def coverageFunc(EEZ,RADARSys):
    coverage = EEZ.filter(['Territory'])


    for i,ref2 in RADARSys.iterrows():
        name = ref2['Territory']
        coverage[name] = np.nan
        for j,ref in EEZ.iterrows():
            if ref2['geometry'].intersects(ref['geometry']) == True:
                coveragearea = ref2['geometry'].intersection(ref['geometry'])
                coveragearea = coveragearea.area
                eezarea = ref['geometry'].area
                score = coveragearea/eezarea
                coverage.loc[j,name] = score
            else:
                coverage.loc[j,name] = 0
    return coverage

def deg2m(var):
    if var.crs == 'None':
        var.crs = 'EPSG: 4326'


    var = var.to_crs('epsg: 3857')
    return var

def tocsv(file):
    yesno = input('Output coverage Percentage to csv? (y/n)')
    if yesno == 'y':
        file = file.sort_values(by=['Territory'])
        file = file.sort_index(axis=1)
        file.reset_index(inplace=True)
        file.drop('index',inplace=True,axis=1)
        file.to_csv(r'LandRadarCoverage.csv')
    return file

file = pd.read_csv(r'RADARTowers.csv')
world = gpd.read_file(r'AdmiBoundaries\world-administrative-boundaries.shp')

with open('Pickled Files\EEZnew.pkl','rb') as f:
    EEZ = pkl.load(f)


EEZ.reset_index(inplace=True)
list_1 = file['Territory'].tolist()
list_1 = set(list_1)
list_1 = list(list_1)

listpd = pd.DataFrame(list_1)
listpd.rename(columns={0:'Territory'},inplace=True)
listpd = listpd.sort_values(by=['Territory'])
file = file.sort_values(by=['Territory'])

listpd = resetindex(listpd)
file = resetindex(file)

radar = gpd.GeoDataFrame(file,geometry=gpd.points_from_xy(file.lat,file.lon),crs = 'epsg: 4326')

#Converts coordinates to a metres scale
radar = deg2m(radar)
EEZ = deg2m(EEZ)
world = deg2m(world)

#Radar range
rangeR = input('Range of the Radar in km: ')
radar['buffer'] = radar['geometry'].buffer(distance = int(rangeR)*1000)

radar = multiPoly(radar,listpd)
coverage = coverageFunc(EEZ,radar)
coverage = tocsv(coverage)

radar = radar.to_crs('epsg: 4326')
EEZ = EEZ.to_crs('epsg: 4326')
world = world.to_crs('epsg: 4326')


fig, ax = plt.subplots()
EEZ.plot(ax = ax,color = 'limegreen',alpha = 0.4)
radar['geometry'].plot(ax = ax,color = 'blue',alpha = 0.3)
world['geometry'].plot(ax = ax,color = 'darkgray')
ax.set_ylabel('Longitude')
ax.set_xlabel('Latitude')

plt.show()