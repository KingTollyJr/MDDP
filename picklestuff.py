import pickle as pkl
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely import wkt
from shapely.geometry import Point,Polygon,mapping
from shapely.wkt import dumps

# More pickling stuff to make the final file run faster

def resetindex(file):
    file.reset_index(inplace=True)
    file.drop(columns=['index'],inplace=True)
    return file


EEZ = gpd.read_file(r'EEz\eez_v11.shp')
IOT = gpd.read_file(r'EEz\Brtitish_Indian_Territory\British_Indian_Ocean_Territory_Maritime_Limits.shp')
world = gpd.read_file(r'AdmiBoundaries\world-administrative-boundaries.shp')
IOT = IOT.to_crs('epsg:4326')

EEZ1 = EEZ.loc[EEZ['SOVEREIGN1']=='United Kingdom']
EEZ2 = EEZ.loc[EEZ['TERRITORY1']=='Chagos Archipelago']

EEZ = pd.concat([EEZ1,EEZ2])
EEZ.reset_index(inplace=True)
list1 = EEZ['TERRITORY1'].to_list()
list1 = set(list1)
list1 = list(list1)
listpd = pd.DataFrame(list1)
listpd.rename(columns={0:'Territory'},inplace=True)
listpd = listpd.sort_values(by=['Territory'])
EEZ.rename(columns={'TERRITORY1':'Territory'},inplace=True)

list_1 = listpd
list_1['geometry'] = np.nan
list_2 = []
list_3 = []


for k,ref in list_1.iterrows():
    if EEZ['Territory'].value_counts()[ref['Territory']]>1:
        TempEEZ = EEZ.loc[EEZ['Territory']==ref['Territory']]
        TempMulti = TempEEZ['geometry'].unary_union
        list_2.append(TempMulti)
        list_3.append(ref['Territory'])
    else:
        TempEEZ = EEZ.loc[EEZ['Territory']==ref['Territory']]
        TempEEZ = pd.DataFrame(TempEEZ)
        TempEEZ = resetindex(TempEEZ)
        list_1.loc[k,'geometry'] = TempEEZ.loc[0,'geometry']

MultiPoly = pd.DataFrame(list_2)
MultiPoly.rename(columns={0:'geometry'},inplace=True)
MultiPoly['geometry'] = MultiPoly['geometry'].apply(dumps)
MultiPoly['geometry'] = MultiPoly['geometry'].apply(wkt.loads)
MultiPoly['Territory'] = list_3
MultiPoly = gpd.GeoDataFrame(MultiPoly,geometry='geometry')
MultiPoly = MultiPoly.sort_index(axis=1)
MultiPoly.crs = 'epsg:4326'

list_1 = list_1.dropna(subset=['geometry'])
Poly = list_1
Poly['geometry'] = Poly['geometry'].apply(dumps)
Poly['geometry'] = Poly['geometry'].apply(wkt.loads)
Poly = gpd.GeoDataFrame(Poly,geometry='geometry')
Poly.crs = 'epsg:4326'

EEZnew = pd.concat([MultiPoly,Poly])
EEZnew = resetindex(EEZnew)
print(EEZnew['Territory'],EEZnew)

with open('Pickled Files\EEZnew.pkl','wb') as f:
    pkl.dump(EEZnew,f)


print(IOT)
print(world.crs)
print(IOT.crs)


fig,ax = plt.subplots()
EEZnew.plot(ax = ax,color = 'green')
IOT.plot(ax = ax,color = 'red',alpha = 0.5)
world.plot(ax = ax)
plt.show()
