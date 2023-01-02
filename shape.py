
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import pickle as pkl
from shapely.geometry import Point,Polygon,mapping
import numpy as np

# This is the original script that doesn't really work very well.
# Use the specific python files to run such as Drones.py or LandRADARv2.py

with open('shapefile.pkl','rb') as f:
    shapefile=pkl.load(f)

with open('worldmap.pkl','rb') as f:
    worldmap = pkl.load(f)

with open('protected_areascrs500.pkl','rb') as f:
    protect_areas = pkl.load(f)

with open('ExampleSat.pkl','rb') as f:
    ExampleSat = pkl.load(f)


def deg2mSetCRS(file,both):
    if file.crs == 'None' & both =='N':
        file.crs = 'EPSG: 4326'
        return file
    elif both == 'both':
        file.crs = 'EPSG: 4326'
        file = file.to_crs('epsg:3857')
        return file

    else:
        file = file.to_crs('epsg:3857')



    file = file.to_crs('epsg:3857')
    return file

def intersect(file1,col1,file2,col2):
    file1.reset_index(inplace=True)
    file2.reset_index(inplace=True)
    inzone= []
    country =[]
    for poly1,row in file1.iterrows():
        for poly2,ref in file2.iterrows():
            if row[col1].intersects(ref[col2]) == True:
                inzone.append(ref)
                country.append(row['TERRITORY1'])



    inzone = gpd.GeoDataFrame(inzone)
    inzone = inzone.rename(columns={0:'geometry'}).set_geometry('geometry')
    inzone['CountryName'] = country


    return inzone

def intersectAirports(file1,col1,file2,col2):
#    file1.reset_index(inplace=True)
    file2.reset_index(inplace=True)
    file1['Contains'] = 'N'
    file1['Airport geometry'] = np.nan
    inzone = []
    for i,poly1 in file1.iterrows():
        for j,poly2 in file2.iterrows():
            if poly1[col1].intersects(poly2[col2]) == True:
                inzone.append(poly2)
                file1.loc[i,'Contains'] = 'Y'
                file1.loc[i,'Airport geometry'] = poly2['geometry']
    inzone = gpd.GeoDataFrame(inzone)
    inzone = inzone.rename(columns={0:'geometry'}).set_geometry('geometry')

    return inzone,file1




def intersectNoCountry(file1,col1,file2,col2):
    file1.reset_index(inplace=True)
    file2.reset_index(inplace=True)

    inzone = []
    for poly1 in file1[col1]:
        for poly2 in file2[col2]:
            if poly1.intersects(poly2) == True:
                inzone.append(poly2)


    if inzone == []:
        return print('No interections')
    else:
        inzone = gpd.GeoDataFrame(inzone)
        inzone = inzone.rename(columns={0:'geometry'}).set_geometry('geometry')
        return inzone

# Creates buffer around airports if they exist, if they don't - switches to AR3 drone
def hasAirportbuffer(file1,col1):
#    file1.reset_index(inplace=True)
    file1['Buffer'] = np.nan

    for i,poly1 in file1.iterrows():
        if file1[col1][i] == 'Y':
            file1.loc[i,'Buffer'] = file1[i]['Airport Geometry'].buffer(distance = 2000*1000/2)

    return file1


# if the country doesn't intersect with a previously made drone buffer, then gives it the AR3 flight buffer
# So only happens if the country doesn't have an airport.File 1 is the world map and file 2 is the shapefile
def doesnthaveairportbuffer(file1,col1,file2,col2):
    file1.reset_index(inplace=True)
#    file2.reset_index(inplace=True)
    for i,poly1 in file1.iterrows():
        for j, poly2 in file2.iterrows():
            if poly1[col1].interects(poly2[col2]) == False:
                centre = poly1['geometry'].centroid()
                file2.loc[i,'Airport Geometry'] = centre
                file2.loc[i,'Buffer'] = file1[i]['Airport Geometry'].buffer(distance = 1300*1000/2)
    return file2

British_indian = gpd.read_file(r'EEz/Brtitish_Indian_Territory/British_Indian_Ocean_Territory_Maritime_Limits.shp')
def linestring_to_polygon(file):
    file['geometry'] = [Polygon(mapping(x)['coordinates']) for x in file.geometry]
    return file
British_indian = linestring_to_polygon(British_indian)


UKTerritory = worldmap.loc[worldmap['status']=='UK Territory']
nonUKTerritory = worldmap.loc[worldmap['status']=='UK Non-Self-Governing Territory']
UK = worldmap.loc[worldmap['name']=='U.K. of Great Britain and Northern Ireland']
worldmap_final = pd.concat([UKTerritory,nonUKTerritory,UK])


AISdisabled = pd.read_excel(r'C:\Users\gjtho\PycharmProjects\MDDP2\ais_disabling_events.xlsx')
Airports = pd.read_csv(r'C:\Users\gjtho\PycharmProjects\MDDP2\airports.csv')


AISdisabled = AISdisabled.assign(Average_speed = 18)
AISdisabled = AISdisabled.assign(Distance_travelled = lambda x: x.Average_speed * x.gap_hours)
AISdisabled.drop('gap_id',inplace=True,axis=1)
AISdisabled.drop('mmsi',inplace=True,axis=1)


AISdisabledGDF = gpd.GeoDataFrame(AISdisabled,geometry=gpd.points_from_xy(AISdisabled.gap_start_lon,AISdisabled.gap_start_lat))
Airports = gpd.GeoDataFrame(Airports,geometry=gpd.points_from_xy(Airports.longitude_deg,Airports.latitude_deg),crs='epsg:4326')
Airports = Airports.to_crs('epsg:3857')


ExampleSatellite = pd.read_excel(r'C:\Users\gjtho\PycharmProjects\MDDP2\Satellites\ExampleSat.xlsx')


AISdisabledGDF2 = AISdisabledGDF.copy()
AISdisabledGDF2.crs = 'epsg: 4326'
AISdisabledGDF2 = AISdisabledGDF2.to_crs('epsg:3857')
AISdisabledGDF2['areapol'] = AISdisabledGDF2['geometry'].buffer(distance = 1800*50)
shapefile= shapefile.to_crs('epsg:3857')

AISinzone = intersect(shapefile,'geometry',AISdisabledGDF2,'areapol')
print(AISinzone.head(10))
AISinzoneIndian = intersectNoCountry(British_indian,'geometry',AISdisabledGDF2,'areapol')
Airportsinzone = intersect(shapefile,'geometry',Airports,'geometry')


print('intersection with Indian territory:',AISinzoneIndian)




def illegalincountry(inzone,total):
    number = pd.DataFrame(columns=['Name','Number of Occurances'])
    number['Name'] = ['Ascension','Falkland / Malvinas Islands','Pitcairn','Saint Helena','Tristan da Cunha',
                      'Anguilla','British Virgin Islands','Cayman Islands','Gibraltar','Montserrat',
                      'Turks and Caicos Islands','United Kingdom','Guernsey','Jersey','South Georgia and the South Sandwich Islands',
                      'Bermuda']
    number['Number of Occurances'] = [inzone['CountryName'].value_counts()['Ascension'],inzone['CountryName'].value_counts()['Falkland / Malvinas Islands'],
                                      inzone['CountryName'].value_counts()['Pitcairn'],inzone['CountryName'].value_counts()['Saint Helena'],
                                      inzone['CountryName'].value_counts()['Tristan da Cunha'],
                                    0,0,
                                    inzone['CountryName'].value_counts()['Cayman Islands'],0,0,
                                    0,inzone['CountryName'].value_counts()['United Kingdom'],0,
                                      0,0,
                                    inzone['CountryName'].value_counts()['Bermuda']]

    Ntotal = len(total.index)
    number['Percentage of Total'] = number['Number of Occurances']/Ntotal

    return number

Occurances = illegalincountry(AISinzone,AISdisabledGDF2)


# turning the hours into reasonable values
for i in range(len(AISdisabledGDF)):

    if AISdisabledGDF.iat[i,12]>24:
        AISdisabledGDF.iat[i,12] = 24






AISdisabledGDF.crs = 'EPSG: 4326'



worldmap_final=worldmap_final.to_crs('epsg:3857')

worldmap = worldmap.to_crs('epsg:3857')
AISdisabledGDF = AISdisabledGDF.to_crs('epsg:3857')
British_indian = British_indian.to_crs('epsg:3857')

Aiportsinzone2,shapefile2 = intersectAirports(shapefile,'geometry',Airports,'geometry')
shapefile2 = hasAirportbuffer(shapefile2,'Contains')
shapefile2 = doesnthaveairportbuffer(worldmap_final,'geometry',shapefile2,'Buffer')

AISdisabledGDF['areapol'] = AISdisabledGDF['geometry'].buffer(distance = 1800*AISdisabledGDF['gap_hours'])



#cheap dn expensive drones from centre of nation

# buffer_cheap = worldmap_final['geometry'].buffer(distance = 100000/2)
# buffer_ex = worldmap_final['geometry'].buffer(distance = (2000*1000)/2)

# Drones from airports

UAVAirports = Airportsinzone['geometry'].buffer(distance = 2000*1000/2)


fig, ax = plt.subplots(1,figsize = (18,12))
worldmap.plot(ax = ax, color = 'darkgray',edgecolor = 'black')

shapefile['geometry'].plot(ax = ax, color = 'limegreen',alpha = 0.5)
# worldmap_final['geometry'].plot(ax=ax)
# # AISdisabledGDF['areapol'].plot(ax=ax,color = 'crimson',alpha = 0.3)
# # AISdisabledGDF2['areapol'].plot(ax=ax,color = 'red')
British_indian['geometry'].plot(ax=ax,color='limegreen',alpha=0.5)
# # protect_areas['geometry'].plot(ax=ax,color='blue',alpha = 0.3)
# buffer_ex.plot(ax=ax,color = 'blue',alpha = 0.3)
# buffer_cheap.plot(ax=ax,color = 'black',alpha = 0.3)
# # ExampleSat['geometry'].plot(ax=ax,color = 'blue',alpha = 1)
# AISdisabledGDF2['areapol'].plot(ax=ax,color = 'blue',alpha = 0.5)
AISinzone.plot(ax=ax,color = 'red',alpha = 0.5)
# UAVAirports.plot(ax=ax,color ='blue',alpha = 0.3)
shapefile2['Buffer'].plot(ax=ax,color = 'blue',alpha = 0.3)


ax.set_xlabel('Longitude [m]')
ax.set_ylabel('Latitude [m]')



plt.show()

