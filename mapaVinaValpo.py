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

# Crea un objeto geocoder, esto se utilizará para encontrar las latitudes y longitudes
geolocator = Nominatim(user_agent="MiAppDeGeocodificacion")

#primero necesitamos cargar los datos de ambas tablas. 
# Carga los datos de tabla_vina que tiene las direcciones
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
try:
    tabla_valpo = pd.read_table("C:\\Users\\Adminstrador\\Desktop\\MEMORIA\\Valparaiso\\BRTMPCATASN_2023_1_05301.txt", sep="|", encoding="latin-1")
except:
    tabla_valpo = pd.read_table("../Memoria/BRTMPCATASN_2023_1_05301.txt", sep="|", encoding="latin-1")
tabla_valpo.columns = nombre_columnas

#Carga los datos de tabla_vina2 que tiene los datos de los materiales
try:
    tabla2_vina = pd.read_table("C:\\Users\\Adminstrador\\Desktop\\MEMORIA\\Viña del Mar\\BRTMPCATASNL_2023_1_05302.txt", sep="|", encoding="latin-1")
except:
    tabla2_vina = pd.read_table("../Memoria/BRTMPCATASNL_2023_1_05302.txt", sep="|", encoding="latin-1")
nombre_columnas2 = ("Cod SII", "N° Manzana","N° Predial", "N° const", "Cod material", "Cod calidad",
                    "Año const", "Sup const", "Cod de destino", "Cod condicion especial")
tabla2_vina.columns = nombre_columnas2 
try:
    tabla2_valpo = pd.read_table("C:\\Users\\Adminstrador\\Desktop\\MEMORIA\\Valparaiso\\BRTMPCATASNL_2023_1_05301.txt", sep="|", encoding="latin-1")
except:
    tabla2_valpo = pd.read_table("../Memoria/BRTMPCATASNL_2023_1_05301.txt", sep="|", encoding="latin-1")
tabla2_valpo.columns = nombre_columnas2
#Las tablas no tienen las mismas dimensiones, tabla_vina es 228792 x 15 y tabla2_vina es 272532 x 10. Hay estacionamientos y bodegas consideradas, la cuales
#serán eliminadas de la tabla_vina para no considerarlas. 

# Eliminar las filas donde el valor es "Z"(estacionamientos) , "L" (Bodega y almacenaje) o "W" (sitio eriazo) en la columna "Cod destino principal"
tabla_vina = tabla_vina[~tabla_vina['Cod destino principal'].isin(['Z', 'L', 'W'])]
tabla2_vina = tabla2_vina[~tabla2_vina['Cod de destino'].isin(['Z', 'L', 'W'])]
tabla2_vina = tabla2_vina[~tabla2_vina['Cod condicion especial'].isin(['SB', 'PZ', 'AL','TM', 'CI','CA'])] 

tabla_valpo = tabla_valpo[~tabla_valpo['Cod destino principal'].isin(['Z', 'L', 'W'])]
tabla2_valpo = tabla2_valpo[~tabla2_valpo['Cod de destino'].isin(['Z', 'L', 'W'])]
tabla2_valpo = tabla2_valpo[~tabla2_valpo['Cod condicion especial'].isin(['SB', 'PZ', 'AL','TM', 'CI','CA'])] 
# Crea un diccionario para mapear los valores de Cod SII, N° Manzana y N° Predial
# con el valor de Cod material correspondiente
mapping = tabla2_vina[tabla2_vina['N° const'] == 1].set_index(['N° Manzana', 'N° Predial'])['Cod material'].to_dict()

# Crea una nueva columna 'Cod material' en tabla_vina basada en el mapeo
tabla_vina['Cod material'] = tabla_vina.set_index(['N° Manzana', 'N° Predial']).index.map(mapping)

mapping = tabla2_valpo[tabla2_valpo['N° const'] == 1].set_index(['N° Manzana', 'N° Predial'])['Cod material'].to_dict()
# Crea una nueva columna 'Cod material' en tabla_vina basada en el mapeo
tabla_valpo['Cod material'] = tabla_valpo.set_index(['N° Manzana', 'N° Predial']).index.map(mapping)
# Mostrar el resultado
#print(tabla_vina)



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
    " Y ": " ",
    "TRESNORTE" : "3 NORTE"
    
}

direccion = "PTE MEDIO SN LOS CASTANOS"



# Crea un diccionario para almacenar las ubicaciones
ubicaciones_vi = defaultdict(list)
direcciones_limpias = []

regex = re.compile(r'\s+(DP|BX|BD|BOX|BOD|DPA|DPB|EST|DPTO|DTO|OF|DEPTO|LC|BGA|BXE|ESTAC|VR|BDP|CDP|ADP|CONS|CASA|CS|LOC|LOCAL)\s+[A-Za-z0-9]+') #expresión regular r'\s+(DP|BX|BD)\s+[A-Za-z0-9]+'
#nueva_regex = re.compile(r'\s+(\d+)\s*$')  # Captura el último número al final de la cadena. Este es para las direcciones que
#tienen esta forma: "AVENIDA JORGE MONTT 1598 163" *****tengo que modificar este porque elimina cualquier número que esté al final

for index, row in tabla_vina.iterrows():
    d=row["Dirección o nombre del predio"]
    direccion_limpia = re.sub(regex, '', d) #esta es para las direcciones de forma "5 NORTE 580 BD 1"
   # direccion_limpia = re.sub(nueva_regex, '', direccion_limpia) #esta es para las direcciones de forma "AVENIDA JORGE MONTT 1598 163"
    
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
                ubicaciones_vi[direccion].append((latitud, longitud, d))
            else:
                print(f"Direccion no encontrada: {direccion}")

        except (GeocoderUnavailable, GeocoderTimedOut, ConnectionError) as e:
            print(f"Error al obtener ubicación para: {direccion}")
            print(e)

        
    else:
        continue 

sustituciones = {
    " ZANARTU ": " ZAÑARTU ",
    "AV D PORTALES ": " AVENIDA DIEGO PORTALES ",
    "AV ": " AVENIDA ",
    "AV.": " AVENIDA ",
    " ESPANA ": " ESPAÑA ",
    " SENORE ": " SEÑORET ",
    " SEN ORET ": " SEÑORET",
    " SE ORET ": " SEÑORET ",
    "ALTE ": " ALMIRANTE ",
    "ALMTE ": " ALMIRANTE ",
    "P SOTOMAYOR ": " SOTOMAYOR ",
    "AVDA ": " AVENIDA ",
    "PJ ROSS ":"PJE. ROSS ",
    
    
}

direccion = "PTE MEDIO SN LOS CASTANOS"

# Crea un diccionario para almacenar las ubicaciones
ubicaciones_va = defaultdict(list)
direcciones_limpias = []

regex = re.compile(r'\s+(DP|BX|OF|LC|BOX|BD|PISO|DPTO|E|AL|B|A|EST|REC|CS|UN)\s+[A-Za-z0-9]+') #expresión regular r'\s+(DP|BX|BD)\s+[A-Za-z0-9]+'
#nueva_regex = re.compile(r'\s+(\d+)\s*$')  # Captura el último número al final de la cadena. Este es para las direcciones que
#tienen esta forma: "AVENIDA JORGE MONTT 1598 163" *****tengo que modificar este porque elimina cualquier número que esté al final

for index, row in tabla_valpo.iterrows():
    d=row["Dirección o nombre del predio"]
    direccion_limpia = re.sub(regex, '', d) #esta es para las direcciones de forma "5 NORTE 580 BD 1"
   # direccion_limpia = re.sub(nueva_regex, '', direccion_limpia) #esta es para las direcciones de forma "AVENIDA JORGE MONTT 1598 163"
    
    if direccion_limpia not in direcciones_limpias: #si la dirección limpia no se repite entra
        direcciones_limpias.append(direccion_limpia) #se ingresa a las direcciones limpias
        direccion = direccion_limpia + ", Valparaíso, Chile"
        
        for clave, valor in sustituciones.items(): #acá busca en el diccionario de sustituciones y reemplaza los valores
            direccion = direccion.replace(clave, valor)

        try:
            ubicacion = geolocator.geocode(direccion, timeout=10) #acá busca las latitudes y longitudes con geolocator
            if ubicacion:
                latitud = ubicacion.latitude
                longitud = ubicacion.longitude
                ubicaciones_va[direccion].append((latitud, longitud, d))
            else:
                print(f"Direccion no encontrada: {direccion}")

        except (GeocoderUnavailable, GeocoderTimedOut, ConnectionError) as e:
            print(f"Error al obtener ubicación para: {direccion}")
            print(e)

        
    else:
        continue 

   # Lista con informacion de latitudes y longitudes por direccion de la tabla
Info = []
Info_vi = []
Info_va = []
# Se van a filtrar las latitudes y longitudes de acuerdo al mapa de inundación y escenarios de las simualciones
# donde el limite de latitud es 36°S = -36 y longitud 71°31.5'W = -71.525
# Agrega al resultado final las coordenadas únicas por dirección
for direc, coords_list in ubicaciones_vi.items():
    latitud, longitud, d = coords_list[0]  # Tomar las coordenadas de la primera entrada
    # Obtener el Cod material correspondiente a la dirección original
    cod_material = None
    for index, row in tabla_vina.iterrows():
        if row["Dirección o nombre del predio"] == d:
            cod_material = row["Cod material"]
            break

    # Verificar si la latitud y longitud cumplen con los límites
    if latitud >= -36 and longitud >= -71.525:
        Info_vi.append((d, latitud, longitud, cod_material))

for direc, coords_list in ubicaciones_va.items():
    latitud, longitud, d = coords_list[0]  # Tomar las coordenadas de la primera entrada
    # Obtener el Cod material correspondiente a la dirección original
    cod_material = None
    for index, row in tabla_valpo.iterrows():
        if row["Dirección o nombre del predio"] == d:
            cod_material = row["Cod material"]
            break

    # Verificar si la latitud y longitud cumplen con los límites
    if latitud >= -36 and longitud >= -71.525:
        Info_va.append((d, latitud, longitud, cod_material))

# Lista con información de latitudes, longitudes y códigos de material por dirección de la tabla de AMBAS ciudades
Info = Info_vi + Info_va

import json
with open("file.json", 'w') as f:
    # indent=2 is not needed but makes the file human-readable 
    # if the data is nested
    json.dump(Info, f, indent=2) 