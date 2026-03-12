import json
import folium
from folium.features import DivIcon
import os

# 1. Definir las coordenadas
COORDENADAS = {
    "MACROSECTORES": {
        "1": {"nombre": "Centro", "lat": -38.7397, "lng": -72.5901},
        "2": {"nombre": "Amanecer", "lat": -38.7554, "lng": -72.6189},
        "3": {"nombre": "Labranza", "lat": -38.7758, "lng": -72.7165},
        "4": {"nombre": "Pueblo Nuevo", "lat": -38.7208, "lng": -72.5768},
        "5": {"nombre": "Pedro de Valdivia", "lat": -38.7346, "lng": -72.6247},
        "6": {"nombre": "Fundo El Carmen", "lat": -38.7214, "lng": -72.6475},
        "7": {"nombre": "Poniente", "lat": -38.7362, "lng": -72.6074},
        "8": {"nombre": "Costanera del Cautín", "lat": -38.7486, "lng": -72.5855}
    },
    "PLANTAS": {
        "1": {"nombre": "Temuco – Labranza Mayor", "lat": -38.7705, "lng": -72.6950},
        "2": {"nombre": "Temuco – Labranza Menor", "lat": -38.7650, "lng": -72.7150},
        "3": {"nombre": "Temuco – Cajón", "lat": -38.6855, "lng": -72.5360}
    }
}

def cargar_resultados(ruta_archivo="resultados.json"):
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{ruta_archivo}'.")
        return []

def generar_mapa(instancia, indice, carpeta_salida):
    nombre_instancia = instancia['nombre']
    print(f"Generando mapa {indice}: {nombre_instancia}...")
    
    mapa = folium.Map(location=[-38.735, -72.62], zoom_start=12)
    flujos = instancia.get("flujos", {})
    plantas_abiertas = instancia.get("plantas_abiertas", {})

    # Calcular el total de toneladas que recibe cada planta
    totales_planta = {"1": 0.0, "2": 0.0, "3": 0.0}
    for clave_flujo, cantidad in flujos.items():
        if cantidad > 0:
            origen, destino = clave_flujo.split(",")
            if destino in totales_planta:
                totales_planta[destino] += cantidad

    # 1. Graficar Macrosectores (Nodos de origen)
    for m_id, data in COORDENADAS["MACROSECTORES"].items():
        # Marcador clásico
        folium.Marker(
            location=[data["lat"], data["lng"]],
            popup=f"<b>{data['nombre']}</b>",
            tooltip=data['nombre'],
            icon=folium.Icon(color="blue", icon="users", prefix='fa')
        ).add_to(mapa)
        
        # Etiqueta de texto fija debajo del marcador
        folium.Marker(
            location=[data["lat"] - 0.003, data["lng"]],
            icon=DivIcon(html=f'<div style="font-size: 9pt; font-weight: bold; color: #000080; text-align: center; width: 120px; margin-left: -60px; text-shadow: 1px 1px 2px white;">{data["nombre"]}</div>')
        ).add_to(mapa)

    # 2. Graficar Plantas (Nodos de destino)
    for p_id, data in COORDENADAS["PLANTAS"].items():
        esta_abierta = plantas_abiertas.get(str(p_id), False)
        color = "green" if esta_abierta else "red"
        estado_txt = "Abierta" if esta_abierta else "Cerrada"
        total_ton = totales_planta.get(str(p_id), 0.0)
        
        # Marcador de la planta
        folium.Marker(
            location=[data["lat"], data["lng"]],
            popup=f"<b>{data['nombre']}</b><br>Estado: {estado_txt}<br>Total Recibido: {total_ton} ton",
            tooltip=f"{data['nombre']} ({estado_txt})",
            icon=folium.Icon(color=color, icon="building", prefix='fa')
        ).add_to(mapa)

        # Si está abierta, ponemos un cartel destacado con el total
        if esta_abierta:
            folium.Marker(
                location=[data["lat"] + 0.0035, data["lng"]],
                icon=DivIcon(html=f'<div style="font-size: 11pt; font-weight: bold; color: darkgreen; background-color: rgba(255,255,255,0.85); border: 2px solid darkgreen; padding: 3px 6px; border-radius: 5px; white-space: nowrap; box-shadow: 2px 2px 4px rgba(0,0,0,0.3);">Total: {total_ton} t</div>')
            ).add_to(mapa)

    # 3. Graficar Flujos (Aristas del grafo con sus pesos)
    for clave_flujo, cantidad in flujos.items():
        if cantidad > 0:
            origen_id, destino_id = clave_flujo.split(",")
            coord_origen = COORDENADAS["MACROSECTORES"].get(origen_id)
            coord_destino = COORDENADAS["PLANTAS"].get(destino_id)
            
            if coord_origen and coord_destino:
                punto_a = [coord_origen["lat"], coord_origen["lng"]]
                punto_b = [coord_destino["lat"], coord_destino["lng"]]
                
                # Dibujar línea
                folium.PolyLine(
                    locations=[punto_a, punto_b],
                    color="purple",
                    weight=3,
                    opacity=0.6,
                    tooltip=f"{coord_origen['nombre']} → {coord_destino['nombre']}: {cantidad} ton"
                ).add_to(mapa)

                # Calcular el punto medio de la línea para poner la etiqueta del flujo
                mid_lat = (punto_a[0] + punto_b[0]) / 2
                mid_lng = (punto_a[1] + punto_b[1]) / 2
                
                # Cuadro de texto en el centro de la línea
                folium.Marker(
                    location=[mid_lat, mid_lng],
                    icon=DivIcon(html=f'<div> <span style="font-size: 10pt; font-weight: bold; color: purple; background-color: rgba(255,255,255,0.8); border: 2px solid purple; padding: 2px; text-align: start; white-space: nowrap;">{cantidad} t</span></div>')
                ).add_to(mapa)

    # Crear nombre de archivo seguro y guardarlo
    nombre_limpio = nombre_instancia.replace(":", "").replace(" ", "_").replace("–", "-").lower()
    nombre_archivo = f"mapa_{indice:02d}_{nombre_limpio}.html"
    ruta_guardado = os.path.join(carpeta_salida, nombre_archivo)
    
    mapa.save(ruta_guardado)

def generar_todos_los_mapas():
    resultados = cargar_resultados("resultados.json")
    if not resultados:
        return

    carpeta_salida = "mapas_resultados"
    os.makedirs(carpeta_salida, exist_ok=True)

    print(f"\nIniciando generación de {len(resultados)} mapas de ruteo...\n" + "-" * 50)
    for i, instancia in enumerate(resultados, 1):
        generar_mapa(instancia, i, carpeta_salida)
    print("-" * 50 + f"\n¡Listo! Los mapas estilo grafo se guardaron en la carpeta '{carpeta_salida}'.\n")

if __name__ == "__main__":
    generar_todos_los_mapas()