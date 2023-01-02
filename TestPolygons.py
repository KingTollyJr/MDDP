import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon,Point
import matplotlib.pyplot as plt
import numpy as np

# This was mainly written by ChatGPT3 and is just where I tested certain functions and methods before applying them


# Define the data for the plots
data = [
    [1, 2, 3, 4],
    [2, 3, 4, 5],
    [3, 4, 5, 6],
]

# Create a figure and axis
fig, ax = plt.subplots()

# Loop through the data and plot each set
for d in data:
    ax.plot(d)
plt.show()
# Show the plot
# poly1 = gpd.GeoSeries([Point([(0.4,1)])])
# poly2 = gpd.GeoSeries([Point([(0.2,0)])])
# poly1 = gpd.GeoDataFrame({'geometry':poly1})
# poly2 = gpd.GeoDataFrame({'geometry':poly2})
#
# dist = poly1.distance(poly2)
# print(dist)
#
# fig, ax = plt.subplots()
# poly2.plot(ax = ax)
# poly1.plot(ax = ax)
# plt.show()
#
# poly1 = gpd.GeoSeries([Polygon([(0,0),(1,1),(0,1)])])
# poly1 = gpd.GeoDataFrame({'geometry':poly1})
#
# poly2 = gpd.GeoSeries([Polygon([(0.6,0.2),(1,0),(0.4,0)]),Polygon([(0,0),(1,1),(0,1)])])
# poly2 = gpd.GeoDataFrame({'geometry':poly2})
# poly2['Ter'] = ['UK','UK']
#
# poly3 = gpd.GeoSeries([Point([0.4,0.6])])
# poly3= gpd.GeoDataFrame({'geometry':poly3})
#
# poly3['buffer'] = poly3['geometry'].buffer(distance = 0.2)
# print(poly3)
#
# print(poly2)
# multipoly = poly2['geometry'].unary_union
#
# multipoly = gpd.GeoDataFrame(geometry=[multipoly])
#
#
# print(multipoly)
#
# fig, ax = plt.subplots()
#
# poly2.plot(ax=ax)
#
#
# fig, ax = plt.subplots()
# multipoly.plot(ax = ax)
#
# plt.show()
#
#
#
# def multiPoly(RADARSys,list_1):
#     list_1['geometry'] = np.nan
#
#     list_2 = []
#     list_3 = []
#
#     for k,ref in list_1.iterrows():
#         if ref['Territory'] == 'Saint Helena' or ref['Territory'] =='South Georgia and the South Sandwich Islands' or ref['Territory'] == 'Tristan da Cunha':
#             print('MULTIPOLYGON')
#             Temp_MultiRadar = RADARSys.loc[RADARSys['Territory']==ref['Territory']]
#             MultiRadar = Temp_MultiRadar['buffer'].unary_union
#             list_2.append(MultiRadar)
#             list_3.append(ref['Territory'])
#         elif RADARSys['Territory'].value_counts()[ref['Territory']] > 1:
#             print(ref['Territory'])
#             Temp_MultiRadar = RADARSys.loc[RADARSys['Territory']==ref['Territory']]
#             MultiRadar = Temp_MultiRadar['buffer'].unary_union
#             list_1.loc[k,'geometry'] = MultiRadar
#             print('list 2',list_1)
#         else:
#             Temp_poly = RADARSys.loc[RADARSys['Territory']==ref['Territory']]
#             Temp_poly = pd.DataFrame(Temp_poly)
#             Temp_poly = resetindex(Temp_poly)
#             print(Temp_poly)
#             list_1.loc[k,'geometry'] = Temp_poly.loc[0,'buffer']
#
#     print('this list',list_1)
#     MultiPolyR = pd.DataFrame(list_2)
#     print(MultiPolyR)
#     MultiPolyR.rename(columns={0:'geometry'},inplace=True)
#     print(MultiPolyR)
#     MultiPolyR['geometry'] = MultiPolyR['geometry'].apply(dumps)
#     MultiPolyR['geometry'] = MultiPolyR['geometry'].apply(wkt.loads)
#     MultiPolyR['Territory'] = list_3
#     MultiPolyR = gpd.GeoDataFrame(MultiPolyR,geometry='geometry')
#     print('multipolygon dataframe',MultiPolyR)
#
#     list_1 = list_1.dropna(subset=['geometry'])
#
#     print('list 4',list_1)
#     RADARSys = list_1
#     RADARSys['geometry'] = RADARSys['geometry'].apply(dumps)
#     RADARSys['geometry'] = RADARSys['geometry'].apply(wkt.loads)
#     RADARSysMulti = gpd.GeoDataFrame(RADARSys,geometry='geometry')
#     # RADARSysMulti = gpd.GeoDataFrame(list_1,geometry=list_1['geometry'].apply(from_wkt))
#     # RADARSysMulti = RADARSysMulti.rename(columns={0:'geometry'}).set_geometry('buffer')
#     RADARSysMulti.crs = 'epsg:3857'
#
#     return RADARSysMulti,MultiPolyR