import geopy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from collections import defaultdict
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import folium
from folium.plugins import MiniMap
import re
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
from requests.exceptions import ConnectionError 

# Crea un objeto geocoder
geolocator = Nominatim(user_agent="MiAppDeGeocodificacion")


# Carga los datos de tabla_vina
nombre_columnas = ("Cod SII", "N° Manzana", "N° Predial", "Dirección o nombre del predio",
                   "Avaluo Fiscal total", "Contribución semestral", "Cod destino principal",
                   "Avaluo exento propiedad", "Código SII CRBC 1", "N° Manzana RBC 1",
                   "N° predio RBC 1", "Cod SII CRBC 2", "N° Manzana RBC 2", "N° predio RBC 2",
                   "Superficie [m2]")
try:
    tabla_vina = pd.read_table("C:\\Users\\Adminstrador\\Desktop\\MEMORIA\\Viña del Mar\\BRTMPCATASN_2023_1_05302.txt", sep="|", encoding="latin-1")
except:
    tabla_vina = pd.read_table("../Memoria/BRTMPCATASN_2023_1_05302.txt", sep="|", encoding="latin-1")
tabla_vina.columns = nombre_columnas #le da los nombres a las columnas

sustituciones = {
    "PTE ": "PONIENTE ",
    "PONIEN ": "PONIENTE ",
    "MEDIO ": " 1/2 ",
    "MED ": " 1/2 ",
    "DOS ": "2 ",
    "UNO ": "1 ",
    "5MED ": "5 1/2 ",
    " NTE": "NORTE ",
    "JARDIN INFANTIL": "",
    "PPNIENTE ": "PONIENTE ",
    "1NORTE ": "1 NORTE ",
    "SN ": "SAN ",
    "LOS CASTANOS": "LOS CASTAÑOS",
    "UNO ": "1 ",
    "PJ ": "PASAJE ",
    "OTE ": "ORIENTE ",
    "3NORTE ": "3 NORTE ",
    "2NORTE ": "2 NORTE ",
    "JORGE MONTT ": "AVENIDA JORGE MONTT ",
    "PLATHS ": "PLATH ",
    "CUATRO ": "4 ",
    "OCHO ": "8 ",
    " 4PON ": " 4 PONIENTE ",
    " 3PON ": "3 PONIENTE ",
    " PON ": " PONIENTE ",
    " Y ": " "
    
}

direccion = "PTE MEDIO SN LOS CASTANOS"



# Crea un diccionario para almacenar las ubicaciones
ubicaciones = defaultdict(list)
direcciones_limpias = []

regex = re.compile(r'\s+(DP|BX|BD|BOX|BOD|DPA|DPB|EST|DPTO|DTO|OF|DEPTO|LC|BGA|BXE|ESTAC|VR|BDP|CDP|ADP|CONS)\s+[A-Za-z0-9]+') #expresión regular r'\s+(DP|BX|BD)\s+[A-Za-z0-9]+'
nueva_regex = re.compile(r'\s+(\d+)\s*$')  # Captura el último número al final de la cadena. Este es para las direcciones que
#tienen esta forma: "AVENIDA JORGE MONTT 1598 163" *****tengo que modificar este porque elimina cualquier número que esté al final

for index, row in tabla_vina.iterrows():
    d=row["Dirección o nombre del predio"]
    direccion_limpia = re.sub(regex, '', d) #esta es para las direcciones de forma "5 NORTE 580 BD 1"
    direccion_limpia = re.sub(nueva_regex, '', direccion_limpia) #esta es para las direcciones de forma "AVENIDA JORGE MONTT 1598 163"
    
    if direccion_limpia not in direcciones_limpias: #si la dirección limpia no se repite entra
        direcciones_limpias.append(direccion_limpia) #se ingresa a las direcciones limpias
        direccion = direccion_limpia + ", Viña del Mar, Chile"
        
        for clave, valor in sustituciones.items(): #acá busca en el diccionario de sustituciones y reemplaza los valores
            direccion = direccion.replace(clave, valor)

        try:
            ubicacion = geolocator.geocode(direccion, timeout=10) #acá busca las latitudes y longitudes con geolocator
            if ubicacion:
                latitud = ubicacion.latitude
                longitud = ubicacion.longitude
                ubicaciones[direccion].append((latitud, longitud))
            else:
                print(f"Direccion no encontrada: {direccion}")

        except (GeocoderUnavailable, GeocoderTimedOut, ConnectionError) as e:
            print(f"Error al obtener ubicación para: {direccion}")
            print(e)

        
    else:
        continue



#Lista con informacion de latitudes y longitudes por direccion de la tabla.
Info = []

#Agrega al resultado final las coordenadas únicas por dirección
for direc, coords_list in ubicaciones.items():
    latitud, longitud = coords_list[0]  # Tomar las coordenadas de la primera entrada
    Info.append((direc, latitud, longitud))

#Crea el mapa interactivo con Folium
mapa = folium.Map(location=[-33.015348, -71.550264], zoom_start=13)

#Agrega los marcadores al mapa
for direccion, latitud, longitud in Info:
    folium.Marker([latitud, longitud], popup=direccion).add_to(mapa)

#Agrega minimapa al mapa principal
minimap = MiniMap()
mapa.add_child(minimap)

mapa.save("mapa_interactivo.html") #aqui se muestra el mapa interactivo
mapa

#para leer de vuetla, usar esto
# https://stackoverflow.com/questions/75928467/is-it-possible-to-save-a-folium-object-in-python