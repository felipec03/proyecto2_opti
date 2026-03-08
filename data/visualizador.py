import json
import folium
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
    print(f"Generando mapa para: {nombre_instancia}...")
    
    # Coordenada central referencial (Temuco) para iniciar el mapa
    mapa = folium.Map(location=[-38.735, -72.62], zoom_start=12)
    
    # 1. Graficar Macrosectores (Azul)
    for m_id, data in COORDENADAS["MACROSECTORES"].items():
        folium.Marker(
            location=[data["lat"], data["lng"]],
            popup=f"Macrosector {m_id}: {data['nombre']}",
            tooltip=f"Macrosector {m_id}",
            icon=folium.Icon(color="blue", icon="users", prefix='fa')
        ).add_to(mapa)

    # 2. Graficar Plantas (Verde si está abierta, Rojo si está cerrada)
    plantas_abiertas = instancia.get("plantas_abiertas", {})
    for p_id, data in COORDENADAS["PLANTAS"].items():
        esta_abierta = plantas_abiertas.get(str(p_id), False)
        color = "green" if esta_abierta else "red"
        estado_txt = "Abierta" if esta_abierta else "Cerrada"
        
        folium.Marker(
            location=[data["lat"], data["lng"]],
            popup=f"Planta {p_id}: {data['nombre']}<br>Estado: {estado_txt}",
            tooltip=f"Planta {p_id} ({estado_txt})",
            icon=folium.Icon(color=color, icon="building", prefix='fa')
        ).add_to(mapa)

    # 3. Graficar Flujos (Líneas conectando M -> P)
    flujos = instancia.get("flujos", {})
    for clave_flujo, cantidad in flujos.items():
        if cantidad > 0:
            # clave_flujo viene en formato "i,j" (ej: "1,3")
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
                    opacity=0.7,
                    tooltip=f"Flujo: {cantidad} ton<br>Desde: {coord_origen['nombre']}<br>Hacia: {coord_destino['nombre']}"
                ).add_to(mapa)

    # Crear nombre de archivo seguro
    nombre_limpio = nombre_instancia.replace(":", "").replace(" ", "_").replace("–", "-").lower()
    nombre_archivo = f"mapa_{indice:02d}_{nombre_limpio}.html"
    ruta_guardado = os.path.join(carpeta_salida, nombre_archivo)
    
    # Guardar mapa
    mapa.save(ruta_guardado)
    print(f"  -> Guardado como: {ruta_guardado}")

def generar_todos_los_mapas():
    resultados = cargar_resultados("resultados.json")
    if not resultados:
        return

    # Crear carpeta para almacenar los mapas y no ensuciar el directorio
    carpeta_salida = "mapas_resultados"
    os.makedirs(carpeta_salida, exist_ok=True)

    print(f"\nSe encontraron {len(resultados)} instancias. Iniciando procesamiento...\n")
    print("-" * 50)
    
    # Iterar y generar todos los mapas
    for i, instancia in enumerate(resultados, 1):
        generar_mapa(instancia, i, carpeta_salida)
        
    print("-" * 50)
    print(f"¡Proceso completado! Se han guardado {len(resultados)} mapas en la carpeta '{carpeta_salida}'.\n")

if __name__ == "__main__":
    generar_todos_los_mapas()