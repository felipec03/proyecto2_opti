"""
==============================================================================
INSTANCIAS COMPUTACIONALES – PROBLEMA DE LOCALIZACIÓN DE PLANTAS CAPACITADAS
(CFLP) PARA LA GESTIÓN DE RESIDUOS EN LA COMUNA DE TEMUCO
==============================================================================

Modelo: Programación Lineal Entera Mixta (MILP)
Formulación: Sección 7.1.1 – Optimización de la ubicación de las plantas de
             valorización (López Marín, U. de Chile, 2024).

CONJUNTOS
---------
  I = {1, …, 8}  Macrosectores generadores de RSD en Temuco.
  J = {1, 2, 3}   Ubicaciones candidatas para plantas de valorización.

PARÁMETROS
----------
  W_i     : Demanda diaria del macrosector i              [ton/día]
  C_ij    : Costo logístico unitario i → j                [CLP/ton]
  F_j     : Costo fijo de instalación y operación         [CLP/día]
  Cap_j   : Capacidad máxima de procesamiento             [ton/día]

VARIABLES DE DECISIÓN
---------------------
  Y_j  ∈ {0, 1}  : 1 si se abre la planta en j.
  X_ij ≥ 0       : Flujo de residuos de i a j              [ton/día]

FUNCIÓN OBJETIVO
----------------
  min  Σ_j F_j·Y_j  +  Σ_i Σ_j C_ij·X_ij

RESTRICCIONES
-------------
  (1) Σ_j X_ij  = W_i          ∀ i ∈ I        (Satisfacción de demanda)
  (2) Σ_i X_ij ≤ Cap_j · Y_j   ∀ j ∈ J        (Capacidad + activación)
  (3) Y_j ∈ {0, 1}              ∀ j ∈ J
  (4) X_ij ≥ 0                  ∀ i ∈ I, j ∈ J

FUENTES DE DATOS
----------------
  [1] López Marín, A. O. (2024). "Optimización y evaluación de modelo de
      gestión de residuos sólidos domiciliarios y alternativas de tratamiento
      para la Región de la Araucanía". Memoria de título, U. de Chile.
  [2] Subsecretaría del Trabajo – Ficha Comunal Temuco. Población 2024:
      292.518 hab. https://www.subtrab.gob.cl/wp-content/uploads/2025/10/
      Temuco-Ficha-Comunal-175.pdf
  [3] Macrotrends – Temuco Metro Area Population (2024): ~356.000 hab.
  [4] Acta Concejo Municipal Temuco, 19-nov-2024. Disposición 2021: 115.700
      ton; 2023: 104.800 ton; proyección 2024: 102.500 ton.
  [5] Repositorio UChile – Tesis López Marín. Terrenos candidatos con Roles
      prediales: 3251-852, 3250-78, 3281-291. Superficies y avalúos fiscales.
  [6] Diagnóstico territorial comunal – Ministerio de las Culturas / PLADECO
      Temuco 2020-2024. Macrosectores y densidad poblacional.
  [7] Wikipedia – Localidades de Temuco y Área Metropolitana.
  [8] Rome2Rio – Distancias Temuco ↔ Labranza (~14.3–14.9 km vía S-40).
  [9] GlobalPetrolPrices.com – Diésel Chile mar-2026: 934,50 CLP/litro.
  [10] TemucoDiario – "Chao Cachureos" 2024: 496 ton extraídas.
  [11] AraucaníaDiario – Entrega 2.500 composteras Fundo El Carmen.
  [12] AraucaníaNoticias – Contenedores: 25.000 unidades, Costanera + P. de
       Valdivia.
  [13] Temuco.cl – Día del Reciclaje: 3.600 ton vidrio, 3.500 ton orgánicos.
==============================================================================
"""

# ──────────────────────────────────────────────────────────────────────────────
# IDENTIFICACIÓN DE MACROSECTORES Y UBICACIONES CANDIDATAS
# ──────────────────────────────────────────────────────────────────────────────

MACROSECTORES = {
    1: "Centro (alta concentración comercial y de servicios)",
    2: "Amanecer",
    3: "Labranza (polo de expansión residencial periférica)",
    4: "Pueblo Nuevo",
    5: "Pedro de Valdivia",
    6: "Fundo El Carmen",
    7: "Poniente (sectores residenciales y Av. Alemania)",
    8: "Costanera del Cautín",
}

UBICACIONES_CANDIDATAS = {
    1: "Temuco – Labranza Mayor (Rol 3251-852, 7.07 ha, $849.515.129 CLP)",
    2: "Temuco – Labranza Menor (Rol 3250-78, 2.11 ha, $332.852.410 CLP)",
    3: "Temuco – Cajón (Rol 3281-291, 13.70 ha, $408.982.351 CLP)",
}


# ──────────────────────────────────────────────────────────────────────────────
# DATOS BASE (compartidos por todas las instancias salvo que se indique)
# ──────────────────────────────────────────────────────────────────────────────

# --- Demanda base W_i [ton/día] ---
# Fuentes: [2] población 292.518, [4] ~315 ton/día comunal, [6] PLADECO
W_BASE = {
    1: 65,  # Centro
    2: 40,  # Amanecer
    3: 45,  # Labranza
    4: 45,  # Pueblo Nuevo
    5: 35,  # Pedro de Valdivia
    6: 30,  # Fundo El Carmen
    7: 30,  # Poniente
    8: 25,  # Costanera del Cautín
}
# Total: 315 ton/día  ≈  102.500–115.000 ton/año

# --- Costos fijos F_j [CLP/día] ---
# Fuentes: [5] avalúos fiscales, amortización CAPEX a 15 años + OPEX base
F_BASE = {
    1: 1_800_000,  # Labranza Mayor
    2: 850_000,  # Labranza Menor
    3: 2_600_000,  # Cajón
}

# --- Capacidades Cap_j [ton/día] ---
# Fuentes: [5] análisis espacial de superficies disponibles
CAP_BASE = {
    1: 200,  # Labranza Mayor
    2: 100,  # Labranza Menor
    3: 400,  # Cajón
}

# --- Matriz de costos de transporte C_ij [CLP/ton] ---
# Fuentes: [8] distancias Rome2Rio, [9] diésel 934,50 CLP/L,
#          [1] metodología logística (combustible + depreciación + salarios)
#
# Estimación:
#   Costo ≈ d_ij [km] × 2 (ida y vuelta) × consumo [L/km] × precio [CLP/L]
#           + componente salarial y depreciación.
#   Camión recolector ≈ 0.45 L/km; carga promedio ≈ 8 ton.
#   Costo por ton ≈ (d_ij × 2 × 0.45 × 934.50) / 8 + overhead fijo/ton
#
#   Los valores se redondean e incluyen un overhead operativo (salarios,
#   mantención, peajes, tiempos muertos) de ~$3.000–$6.000 CLP/ton.
#
# Las distancias aproximadas (km) entre centroide de cada macrosector y
# cada planta candidata son:
#
#          J1(Labranza Mayor)  J2(Labranza Menor)  J3(Cajón)
#  i=1 Centro       14.5            13.8              9.2
#  i=2 Amanecer     12.0            11.3              7.5
#  i=3 Labranza      3.2             2.5             18.0
#  i=4 Pueblo Nuevo 10.5             9.8             11.0
#  i=5 Pedro Vald.   8.0             7.5             12.5
#  i=6 Fdo. Carmen  16.0            15.3             14.0
#  i=7 Poniente     11.0            10.5             13.5
#  i=8 Costanera    13.0            12.3              6.0
#
# Conversión a CLP/ton (redondeado):
#   costo_ton ≈ (d_km × 2 × 0.45 × 934.50) / 8 + 4500
#   ≈ d_km × 105.4 + 4500   (aprox)

C_BASE = {
    # (i, j): CLP/ton
    (1, 1): 6_028,
    (1, 2): 5_955,
    (1, 3): 5_470,
    (2, 1): 5_764,
    (2, 2): 5_691,
    (2, 3): 5_290,
    (3, 1): 4_837,
    (3, 2): 4_763,
    (3, 3): 6_397,
    (4, 1): 5_607,
    (4, 2): 5_532,
    (4, 3): 5_659,
    (5, 1): 5_343,
    (5, 2): 5_290,
    (5, 3): 5_818,
    (6, 1): 6_186,
    (6, 2): 6_112,
    (6, 3): 5_976,
    (7, 1): 5_659,
    (7, 2): 5_607,
    (7, 3): 5_923,
    (8, 1): 5_870,
    (8, 2): 5_796,
    (8, 3): 5_132,
}


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCIÓN AUXILIAR PARA CONSTRUIR UNA INSTANCIA
# ══════════════════════════════════════════════════════════════════════════════


def construir_instancia(nombre, descripcion, W, C, F, Cap, fuentes):
    """Devuelve un diccionario completo con los datos de una instancia."""
    return {
        "nombre": nombre,
        "descripcion": descripcion,
        "I": list(W.keys()),
        "J": list(F.keys()),
        "W": dict(W),
        "C": dict(C),
        "F": dict(F),
        "Cap": dict(Cap),
        "fuentes": fuentes,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  INSTANCIA 1 – Escenario Base de Operación Estandarizada
# ══════════════════════════════════════════════════════════════════════════════
#  Condiciones de equilibrio. Demanda total: 315 ton/día.
#  Capacidad total disponible: 700 ton (200+100+400).
#  Holgura de capacidad → decisión pura costo fijo vs. costo transporte.
#  Fuentes: [1][2][4][5][6][8][9]

instancia_01 = construir_instancia(
    nombre="Instancia 1: Escenario Base",
    descripcion=(
        "Condiciones estándar de operación con la estructura de costos y "
        "demandas promedio. Caso de control metodológico. "
        "Demanda total = 315 ton/día. Capacidad total = 700 ton/día."
    ),
    W=dict(W_BASE),
    C=dict(C_BASE),
    F=dict(F_BASE),
    Cap=dict(CAP_BASE),
    fuentes="[1][2][4][5][6][8][9]",
)


# ══════════════════════════════════════════════════════════════════════════════
#  INSTANCIA 2 – Shock de Generación por Programa "Chao Cachureos"
# ══════════════════════════════════════════════════════════════════════════════
#  Operativo masivo de erradicación de microbasurales.
#  W_2 (Amanecer):   40 → 110 ton/día  (+70)
#  W_8 (Costanera):  25 →  90 ton/día  (+65)
#  Demanda total:    315 → 450 ton/día
#  Excede Cap_3 (400) ⟹ se fuerza apertura de al menos 2 plantas.
#  Fuentes: [1][10] – TemucoDiario "Chao Cachureos" 496 ton/2024.

W_02 = dict(W_BASE)
W_02[2] = 110  # Amanecer: shock +70
W_02[8] = 90  # Costanera: shock +65

instancia_02 = construir_instancia(
    nombre="Instancia 2: Shock – Chao Cachureos",
    descripcion=(
        "Operativo masivo de erradicación de microbasurales concentrado en "
        "Amanecer y Costanera del Cautín. Demanda total = 450 ton/día. "
        "Supera capacidad individual de Cajón (400), forzando apertura de "
        "al menos dos plantas. Basado en el programa 'Chao Cachureos' de "
        "la DIMAO que extrajo 496 ton en 2024."
    ),
    W=W_02,
    C=dict(C_BASE),
    F=dict(F_BASE),
    Cap=dict(CAP_BASE),
    fuentes="[1][10]",
)


# ══════════════════════════════════════════════════════════════════════════════
#  INSTANCIA 3 – Volatilidad Macroeconómica por Alza del Diésel (+45%)
# ══════════════════════════════════════════════════════════════════════════════
#  Crisis de precios de combustible: toda la matriz C_ij sube un 45%.
#  Los costos fijos F_j permanecen estables (contratos a largo plazo).
#  Resultado esperado: consolidación en Cajón (J3). Los costos fijos son
#  tan altos (~1.8–2.6 M CLP/día) que el ahorro marginal de transporte
#  por abrir una segunda planta (≈ 167.000 CLP/día máx.) no compensa
#  el CAPEX adicional. El alza del diésel encarece los trayectos pero no
#  cambia la jerarquía de costos fijos vs. variables a esta escala.
#  Fuentes: [9][1] – GlobalPetrolPrices diésel mar-2026: ~934,50 CLP/L.
#  Históricamente ENAP ha anunciado alzas de hasta $20/L de golpe [15].

C_03 = {k: round(v * 1.45) for k, v in C_BASE.items()}

instancia_03 = construir_instancia(
    nombre="Instancia 3: Alza del Diésel (+45%)",
    descripcion=(
        "Crisis de precios del combustible. Toda la matriz de costos de "
        "transporte C_ij se incrementa en un 45%. Los costos fijos F_j "
        "permanecen estables. Penaliza distancias largas y favorece la "
        "descentralización. Diésel base: 934,50 CLP/L [9]; con el shock "
        "simula ~1.355 CLP/L."
    ),
    W=dict(W_BASE),
    C=C_03,
    F=dict(F_BASE),
    Cap=dict(CAP_BASE),
    fuentes="[1][9][15]",
)


# ══════════════════════════════════════════════════════════════════════════════
#  INSTANCIA 4 – Reducción por Desvío Orgánico Domiciliario (Composteras)
# ══════════════════════════════════════════════════════════════════════════════
#  Impacto de distribución masiva de composteras.
#  W_6 (Fundo El Carmen): 30 → 13.5 ton/día  (–55%)
#  W_7 (Poniente):        30 → 25.5 ton/día  (–15%)
#  Demanda total:         315 → 294 ton/día  (reducción de 21 ton/día)
#  Relaja restricciones de capacidad.
#  Fuentes: [1][11] – 2.500 composteras entregadas en Fdo. El Carmen.

W_04 = dict(W_BASE)
W_04[6] = 13.5  # Fundo El Carmen: -55%
W_04[7] = 25.5  # Poniente: -15%

instancia_04 = construir_instancia(
    nombre="Instancia 4: Desvío Orgánico (Composteras)",
    descripcion=(
        "Programa municipal de compostaje domiciliario reduce drásticamente "
        "la demanda de Fundo El Carmen (-55%) y Poniente (-15%). "
        "Demanda total = 294 ton/día. El 66,8% de los RSD de la región "
        "son materia orgánica [1]. Basado en las 2.500 composteras "
        "entregadas en Fundo El Carmen [11]."
    ),
    W=W_04,
    C=dict(C_BASE),
    F=dict(F_BASE),
    Cap=dict(CAP_BASE),
    fuentes="[1][11]",
)


# ══════════════════════════════════════════════════════════════════════════════
#  INSTANCIA 5 – Eficiencia Operativa por Contenedorización
# ══════════════════════════════════════════════════════════════════════════════
#  Despliegue de 25.000 contenedores (120 y 1.100 L) con entrega
#  intensiva en Costanera del Cautín y Pedro de Valdivia.
#  Descuento de 30% en C_{8,j} para todo j (Costanera) y
#  descuento de 20% en C_{5,j} para todo j (Pedro de Valdivia).
#  Fuentes: [12] – AraucaníaNoticias: 25.000 contenedores, >$1.300 M CLP.

C_05 = dict(C_BASE)
for j in [1, 2, 3]:
    C_05[(8, j)] = round(C_BASE[(8, j)] * 0.70)  # Costanera  –30%
    C_05[(5, j)] = round(C_BASE[(5, j)] * 0.80)  # P. Valdivia –20%

instancia_05 = construir_instancia(
    nombre="Instancia 5: Contenedorización",
    descripcion=(
        "Modernización de la recolección con 25.000 contenedores de 120 "
        "y 1.100 L. Reduce los costos de transporte en Costanera del "
        "Cautín (-30%) y Pedro de Valdivia (-20%) por eficiencia "
        "operativa (tiempos de parada, desgaste). Inversión > $1.300 M "
        "CLP regional [12]."
    ),
    W=dict(W_BASE),
    C=C_05,
    F=dict(F_BASE),
    Cap=dict(CAP_BASE),
    fuentes="[1][12]",
)


# ══════════════════════════════════════════════════════════════════════════════
#  INSTANCIA 6 – Subvención CAPEX vía Fondos Regionales (FNDR)
# ══════════════════════════════════════════════════════════════════════════════
#  Cajón (j=3) adjudica subsidio gubernamental del 75% sobre CAPEX.
#  F_3: 2.600.000 → 1.150.000 CLP/día
#  Resultado esperado: consolidación monopolística en Cajón.
#  Fuentes: [1][5] – Avalúo Cajón $408 M CLP; política FNDR.

F_06 = dict(F_BASE)
F_06[3] = 1_150_000  # Cajón con subsidio 75% CAPEX

instancia_06 = construir_instancia(
    nombre="Instancia 6: Subsidio FNDR para Cajón",
    descripcion=(
        "El terreno de Cajón (j=3) obtiene subsidio gubernamental del "
        "75% sobre su CAPEX a través de fondos FNDR. El costo fijo cae "
        "de $2.600.000 a $1.150.000 CLP/día, equiparándose a las plantas "
        "de Labranza. Demuestra cómo los instrumentos de financiamiento "
        "público dictan la geografía de las operaciones."
    ),
    W=dict(W_BASE),
    C=dict(C_BASE),
    F=F_06,
    Cap=dict(CAP_BASE),
    fuentes="[1][5]",
)


# ══════════════════════════════════════════════════════════════════════════════
#  INSTANCIA 7 – Efecto NIMBY y Restricciones de Uso de Suelo
# ══════════════════════════════════════════════════════════════════════════════
#  Rechazo ciudadano en Labranza (ciudad dormitorio en crecimiento).
#  Sobrecostos de mitigación ambiental y social:
#    F_1 (Labranza Mayor): 1.800.000 → 3.600.000 CLP/día  (×2)
#    F_2 (Labranza Menor):   850.000 → 1.900.000 CLP/día  (×2.24)
#  Cajón (j=3) mantiene costo sin alteraciones (vocación industrial).
#  Resultado esperado: consolidación en Cajón.
#  Fuentes: [1][7][8] – Crecimiento demográfico Labranza.

F_07 = dict(F_BASE)
F_07[1] = 3_600_000  # Labranza Mayor + mitigación NIMBY
F_07[2] = 1_900_000  # Labranza Menor + mitigación NIMBY

instancia_07 = construir_instancia(
    nombre="Instancia 7: Efecto NIMBY en Labranza",
    descripcion=(
        "Conflicto socioambiental por crecimiento residencial de Labranza. "
        "Los costos fijos de las plantas en Labranza se duplican por "
        "sistemas de biometanización hermética, encapsulamiento acústico "
        "e indemnizaciones viales. F_1: ×2.0, F_2: ×2.24. "
        "Cajón mantiene su costo (vocación industrial pura)."
    ),
    W=dict(W_BASE),
    C=dict(C_BASE),
    F=F_07,
    Cap=dict(CAP_BASE),
    fuentes="[1][7][8]",
)


# ══════════════════════════════════════════════════════════════════════════════
#  INSTANCIA 8 – Crecimiento Poblacional Acelerado (+18%)
# ══════════════════════════════════════════════════════════════════════════════
#  Proyección urbanística agresiva a 5 años. PLADECO + INE.
#  Demanda se infla transversalmente en un 18%.
#  Polos de alta densidad con ajuste puntual adicional:
#    W_5 (Pedro de Valdivia): 35 → 45 ton/día
#    W_4 (Pueblo Nuevo):     45 → 58 ton/día
#  Demanda total ≈ 375 ton/día → casi satura Cap_3 (400).
#  Fuentes: [2][3][7] – Población 2024: 292.518; metro: 356.000.

W_08 = {}
factor_18 = 1.18
for i, w in W_BASE.items():
    W_08[i] = round(w * factor_18, 1)
# Ajustes puntuales indicados en el documento:
W_08[5] = 45  # Pedro de Valdivia (explícitamente 35→45)
W_08[4] = 58  # Pueblo Nuevo (explícitamente 45→58)
# Verificar total ≈ 375
# Centro 76.7, Amanecer 47.2, Labranza 53.1, PNuevo 58, PValdivia 45,
# FCarmen 35.4, Poniente 35.4, Costanera 29.5 = ~380.3 → ajustar a ~375
W_08[1] = 73  # Centro ajustado
W_08[2] = 46  # Amanecer ajustado
W_08[3] = 52  # Labranza ajustado
W_08[6] = 35  # Fundo El Carmen
W_08[7] = 35  # Poniente
W_08[8] = 31  # Costanera

instancia_08 = construir_instancia(
    nombre="Instancia 8: Crecimiento Poblacional (+18%)",
    descripcion=(
        "Proyección urbanística agresiva a 5 años basada en PLADECO e INE. "
        "Demanda transversalmente inflada (+18%). Pedro de Valdivia pasa "
        "de 35 a 45 ton/día; Pueblo Nuevo de 45 a 58 ton/día. "
        "Demanda total ≈ 375 ton/día, acercándose al límite técnico de "
        "Cajón (400 ton/día). Margen de seguridad de 25 ton."
    ),
    W=W_08,
    C=dict(C_BASE),
    F=dict(F_BASE),
    Cap=dict(CAP_BASE),
    fuentes="[2][3][7]",
)


# ══════════════════════════════════════════════════════════════════════════════
#  INSTANCIA 9 – Cumplimiento Normativo de Reciclaje (Ley REP)
# ══════════════════════════════════════════════════════════════════════════════
#  40% de la demanda en macrosectores de altos ingresos se desvía a
#  puntos limpios y recicladores de base, esquivando el sistema CFLP.
#    W_1 (Centro):   65 → 39 ton/día  (–40%)
#    W_7 (Poniente): 30 → 18 ton/día  (–40%)
#  Metas REP regionales: 62,2% tasa de reciclaje [1].
#  DIMAO: >3.600 ton vidrio + 3.500 ton orgánicos anuales recuperadas [13].
#  Fuentes: [1][13]

W_09 = dict(W_BASE)
W_09[1] = 39  # Centro –40%
W_09[7] = 18  # Poniente –40%

instancia_09 = construir_instancia(
    nombre="Instancia 9: Cumplimiento Ley REP (Reciclaje)",
    descripcion=(
        "Segregación en origen por cumplimiento de la Ley 20.920 (REP). "
        "El 40% de la demanda en Centro y Poniente (macrosectores de "
        "altos ingresos) se desvía a puntos limpios y recicladores de "
        "base. W_1: 65→39, W_7: 30→18 ton/día. "
        "Demanda total = 277 ton/día. Meta regional: 62,2% reciclaje [1]."
    ),
    W=W_09,
    C=dict(C_BASE),
    F=dict(F_BASE),
    Cap=dict(CAP_BASE),
    fuentes="[1][13]",
)


# ══════════════════════════════════════════════════════════════════════════════
#  INSTANCIA 10 – Falla Crítica de Infraestructura en Cajón
# ══════════════════════════════════════════════════════════════════════════════
#  Falla catastrófica en sistema hidráulico de compactación de Cajón.
#  Cap_3: 400 → 130 ton/día  (degradación severa).
#  Demanda se mantiene en 315 ton/día.
#  Déficit = 315 − 130 = 185 ton → Cap_2 (100) insuficiente sola.
#  Se fuerza activación de al menos Y_1 y Y_3 (o las tres plantas).
#  Fuentes: [1]

CAP_10 = dict(CAP_BASE)
CAP_10[3] = 130  # Cajón degradada

instancia_10 = construir_instancia(
    nombre="Instancia 10: Falla Crítica en Cajón",
    descripcion=(
        "Falla catastrófica en el sistema hidráulico de compactación de "
        "la planta de Cajón (j=3). Capacidad degradada de 400 a 130 "
        "ton/día. Demanda inalterada en 315 ton/día. Déficit de 185 ton. "
        "La planta Labranza Menor (Cap=100) no cubre sola el déficit. "
        "Fuerza activación de Labranza Mayor (Cap=200) como mínimo."
    ),
    W=dict(W_BASE),
    C=dict(C_BASE),
    F=dict(F_BASE),
    Cap=CAP_10,
    fuentes="[1]",
)


# ══════════════════════════════════════════════════════════════════════════════
#  LISTA COMPLETA DE INSTANCIAS
# ══════════════════════════════════════════════════════════════════════════════

INSTANCIAS = [
    instancia_01,
    instancia_02,
    instancia_03,
    instancia_04,
    instancia_05,
    instancia_06,
    instancia_07,
    instancia_08,
    instancia_09,
    instancia_10,
]


# ══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES: Imprimir resumen y validar factibilidad
# ══════════════════════════════════════════════════════════════════════════════


def imprimir_resumen(inst):
    """Imprime un resumen legible de la instancia."""
    print("=" * 70)
    print(f"  {inst['nombre']}")
    print("=" * 70)
    print(f"  {inst['descripcion']}\n")

    W = inst["W"]
    F = inst["F"]
    Cap = inst["Cap"]
    C = inst["C"]
    I = inst["I"]
    J = inst["J"]

    total_W = sum(W.values())
    total_Cap = sum(Cap.values())

    print(f"  |I| = {len(I)} macrosectores   |J| = {len(J)} plantas candidatas")
    print(f"  Demanda total:   {total_W:>8.1f} ton/día")
    print(f"  Capacidad total: {total_Cap:>8.1f} ton/día")
    print(f"  Holgura:         {total_Cap - total_W:>8.1f} ton/día")
    print()

    # Tabla de demanda
    print("  Demanda W_i [ton/día]:")
    print(f"  {'i':>3}  {'Macrosector':<50}  {'W_i':>8}")
    print(f"  {'---':>3}  {'-' * 50}  {'--------':>8}")
    for i in I:
        nombre_ms = MACROSECTORES.get(i, f"Macrosector {i}")
        print(f"  {i:>3}  {nombre_ms:<50}  {W[i]:>8.1f}")
    print(f"  {'':>3}  {'TOTAL':<50}  {total_W:>8.1f}")
    print()

    # Tabla de plantas
    print("  Plantas candidatas:")
    print(f"  {'j':>3}  {'Ubicación':<55}  {'F_j':>12}  {'Cap_j':>8}")
    print(f"  {'---':>3}  {'-' * 55}  {'-' * 12}  {'--------':>8}")
    for j in J:
        nombre_ub = UBICACIONES_CANDIDATAS.get(j, f"Planta {j}")
        nombre_corto = nombre_ub[:55]
        print(f"  {j:>3}  {nombre_corto:<55}  {F[j]:>12,}  {Cap[j]:>8.0f}")
    print()

    # Matriz de transporte
    print("  Matriz C_ij [CLP/ton]:")
    header = f"  {'i\\j':>5}"
    for j in J:
        header += f"  {'J' + str(j):>10}"
    print(header)
    print(f"  {'-----':>5}" + f"  {'----------':>10}" * len(J))
    for i in I:
        row = f"  {i:>5}"
        for j in J:
            row += f"  {C[(i, j)]:>10,}"
        print(row)
    print()
    print(f"  Fuentes: {inst['fuentes']}")
    print()


def validar_factibilidad(inst):
    """Verifica si existe al menos una combinación de plantas factible."""
    W = inst["W"]
    Cap = inst["Cap"]
    J = inst["J"]
    total_W = sum(W.values())
    total_Cap = sum(Cap.values())

    if total_Cap < total_W:
        print(f"  ⚠ INFACTIBLE: Capacidad total ({total_Cap}) < Demanda ({total_W})")
        return False
    else:
        print(f"  ✓ FACTIBLE: Capacidad total ({total_Cap}) ≥ Demanda ({total_W})")
        return True


# ══════════════════════════════════════════════════════════════════════════════
#  EJECUCIÓN PRINCIPAL: imprimir todas las instancias
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("  INSTANCIAS CFLP – GESTIÓN DE RESIDUOS COMUNA DE TEMUCO")
    print("█" * 70 + "\n")

    for idx, inst in enumerate(INSTANCIAS, 1):
        imprimir_resumen(inst)
        validar_factibilidad(inst)
        print()
