# Proyecto de Optimización: Gestión de Residuos Sólidos Domiciliarios en Temuco

Este proyecto implementa un modelo de **Programación Lineal Entera Mixta (MILP)** para resolver el Problema de Localización de Plantas Capacitadas (CFLP - *Capacitated Facility Location Problem*). El objetivo principal es optimizar la red logística de gestión de Residuos Sólidos Domiciliarios (RSD) en la comuna de Temuco, Región de La Araucanía, Chile.

El proyecto es una adaptación a nivel comunal de las estrategias propuestas en la tesis central de López Marín (2024), formulada originalmente como un modelo regional (MINLP).

---

## 1. Contexto y Descripción del Problema

La Región de La Araucanía enfrenta una crisis sanitaria estructural. Presenta la tasa de cobertura de servicios de aseo más baja a nivel nacional (34,7%), y el cierre de vertederos locales (como Boyeco) ha forzado a la Municipalidad de Temuco a **exportar su basura** hacia la Región del Biobío. 

Este traslado interregional impone una carga multimillonaria a las arcas comunales, elevando el costo operativo sin resolver el problema de fondo. La apertura de **Plantas de Valorización** de residuos se presenta como la solución definitiva frente a esta crisis y a las exigencias normativas de la Ley REP (Ley 20.920).

Este proyecto aborda la problemática desde la Investigación de Operaciones, buscando equilibrar:
- **Costos Fijos (CAPEX/OPEX):** Alta inversión para habilitar mega-plantas.
- **Costos Variables (Transporte):** El gasto logístico de la flota de camiones cruzando la ciudad.

---

## 2. Relación con el Paper de Referencia

El modelamiento se basa en el estudio empírico y formulaciones matemáticas del siguiente trabajo de grado:
> **López Marín, A. O. (2024).** *Optimización y evaluación de modelo de gestión de residuos sólidos domiciliarios y alternativas de tratamiento para la Región de La Araucanía.* Memoria de título, Universidad de Chile.

**Adaptación del Proyecto:**
Mientras el paper original propone un modelo No Lineal (MINLP) que abarca las 32 comunas de la región y requiere tiempos computacionales considerables (vía Gurobi), el presente modelo condensa la problemática en la capital regional (Temuco). Al linealizar y acotar el problema (MILP comunal), logramos encontrar soluciones óptimas globales en tiempos de milisegundos utilizando *solvers* de código abierto (CBC) e industriales (CPLEX).

---

## 3. Formulación Matemática (CFLP)

El motor lógico de este proyecto diseña la red a través de:

### Conjuntos (Sets)
*   **$I$**: Macrosectores generadores de basura (8 zonas poblacionales, ej: Centro, Labranza, Fundo El Carmen).
*   **$J$**: Ubicaciones candidatas para plantas de valorización (3 locaciones viables según plan regulador).

### Parámetros Exógenos (Datos de la Realidad)
*   **$W_i$**: Demanda diaria (toneladas) generada en el macrosector $i$.
*   **$C_{ij}$**: Costo logístico de trasladar 1 tonelada desde $i$ hasta la planta $j$.
*   **$F_j$**: Costo fijo diario (amortización de infraestructura y operación base) de la planta $j$.
*   **$Cap_j$**: Capacidad máxima de procesamiento diario (toneladas) de la planta $j$.

### Variables de Decisión
*   **$Y_j \in \{0, 1\}$**: Variable binaria de localización. Toma el valor `1` si la Municipalidad decide construir la planta $j$, y `0` si se descarta el terreno.
*   **$X_{ij} \ge 0$**: Variable continua de asignación. Indica cuántas toneladas exactas viajarán desde el sector $i$ hacia la planta $j$.

### Función Objetivo y Restricciones
Se minimiza la suma de costos fijos activados más los flujos de transporte ponderados, sujeto a que:
1.  El 100% de la basura de Temuco ($W_i$) debe ser recolectada y asignada.
2.  Una planta no puede superar su capacidad límite ($Cap_j$).
3.  No se puede enviar flujo $X_{ij}$ a una planta $j$ si no ha sido previamente abierta ($Y_j = 0$) [Restricción Big-M Lógica].

---

## 4. Estructura e Implementación Computacional

El modelo fue implementado en **Python 3**, apoyado en la librería de modelamiento algebraico **`PuLP`**. El sistema está estructurado modularmente:

```bash
proyecto2_opti/
├── README.md                 # Este documento
├── data/
│   ├── instancias.json       # Datos serializados de los 10 escenarios (dictados por la realidad contingente)
│   ├── resultados.json       # Archivo generado automáticamente con la salida numérica exacta del solver
│   └── generar_graficos.py   # Script de visualización interactiva basada en resultados
│   └── graficos/             # Carpeta destino de imágenes (.png) didácticas
├── docs/                     # Documentación técnica, paper extraído y minutas
└── src/
    ├── main.py               # Orquestador del programa (CLI arguments, I/O)
    └── solver.py             # Corazón matemático: definición del MILP, heurística de fallback CPLEX -> CBC
```

### Instancias de Prueba ("Stress Testing")
En `data/instancias.json` se programaron 10 escenarios que simulan variaciones reales de la gestión municipal, forzando al solver a adaptar su estrategia:
1.  **Escenario Base:** Operación normal de recolección (315 ton/día).
2.  **Shock de Demanda:** Operativos "Chao Cachureos" disparan los flujos.
3.  **Alza del Diésel:** Incremento logístico que fuerza descentralización.
4.  **Desvío Orgánico:** Adopción masiva de composteras en *Fundo El Carmen*.
5.  **Contenedorización:** Mejora de eficiencia vehicular en puntos críticos.
6.  **Subvención FNDR:** Terrenos caros reducen su *CAPEX* drásticamente por subsidio regional.
7.  **Efecto NIMBY:** Sobrecosto de mitigación socioambiental en barrios residenciales periféricos.
8.  **Expansión Urbana:** PLADECO anticipa crecimientos densos obligando redundancia.
9.  **Normativa REP:** Mayor segregación comunal aligera peso de plantas.
10. **Falla Crítica:** Colapso mecánico sorpresivo reduce capacidad de diseño de planta matriz obligando rediseño de red "en caliente".

---

## 5. Visualización y Gráficos Didácticos

Para contrastar fehacientemente con las conclusiones de López Marín (2024), y ofrecer una herramienta ejecutiva para los tomadores de decisión municipales (DIMAO y SECPLA), se incluye el script de *Business Intelligence* `generar_graficos.py`. 

Este script lee `resultados.json` y exporta gráficos profesionales en `data/graficos/`, abordando:
- Contrastes directos de Costos (Paper vs. Nuestro Modelo).
- Desglose de "Trade-offs" (Costo Fijo vs. Transporte).
- Mapas de calor (Heatmaps) de decisiones de apertura $Y_j$.
- Rutas logísticas de asignación (Sankey-like representations).
- Tiempos milisegundos de resolución CPLEX.

---

## 6. Instrucciones de Ejecución

Para correr el proyecto localmente, asegúrese de tener configurado un entorno con Python e instaladas las librerías `pulp` y `matplotlib`. La pre-configuración de CPLEX es opcional, ya que el código hace un *fallback* automático a CBC (incluido con PuLP).

### I. Resolución Matemática
Puede ejecutar el solver para todas las instancias y exportar los resultados a JSON con el siguiente comando:
```bash
python src/main.py --exportar
```
> Opcionalmente, para resolver un solo escenario (ej. Instancia 5) con modo verboso (*solver logs* en tiempo real):
> `python src/main.py --instancia 5 --verbose`

### II. Generación de Visualizaciones Analíticas
Una vez que `data/resultados.json` ha sido actualizado por el paso anterior, compile los mapas e infografías corriendo:
```bash
python data/generar_graficos.py
```
> Explore en la carpeta `/data/graficos/` las imágenes exportadas listas para reportes en formato IEEE o presentaciones municipales.

---
**Autores:** Felipe Cubillos, Diego Gómez, Tomás Cárcamo  |  **Cátedra:** Métodos de Optimización (2-2025)