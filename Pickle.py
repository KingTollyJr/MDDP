import pickle as pkl
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# This file was just used for Pickling files

oceans = gpd.read_file(r'Oceans/ne_110m_ocean.shp')
reserves =
with open(r'C:\Users\gjtho\PycharmProjects\MDDP2\Pickled Files\worldmap.pkl','rb') as f:
    worldmap = pkl.load(f)

print(oceans)
print(oceans.crs)
print(worldmap.crs)
oceans = oceans.unary_union
oceans = gpd.GeoDataFrame(geometry=[oceans])
with open('Pickled Files\OceansSingle.pkl','wb') as f:
    pkl.dump(oceans,f)

print(oceans)
fig, ax = plt.subplots()
oceans.plot(ax = ax)
worldmap.plot(ax=ax,color = 'darkgray',alpha = 0.5)

plt.show()
