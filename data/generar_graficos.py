"""
generar_graficos.py – Generación de gráficos didácticos para los resultados
                      del modelo CFLP de gestión de residuos en Temuco.

Contrasta los resultados del solver MILP (PuLP/CBC) con las conclusiones
del paper base (López Marín, 2024 – U. de Chile).

Uso:
    python data/generar_graficos.py

Genera imágenes PNG en data/graficos/.

Autor:  Felipe Cubillos / Diego Gómez / Tomás Cárcamo
Fecha:  Marzo 2026
"""

import json
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")  # Renderizar sin ventana
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib import patheffects
from matplotlib.patches import FancyBboxPatch

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTADOS_PATH = os.path.join(SCRIPT_DIR, "resultados.json")
INSTANCIAS_PATH = os.path.join(SCRIPT_DIR, "instancias.json")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "graficos")

MACROSECTORES = {
    1: "Centro",
    2: "Amanecer",
    3: "Labranza",
    4: "Pueblo Nuevo",
    5: "Pedro de Valdivia",
    6: "Fundo El Carmen",
    7: "Poniente",
    8: "Costanera del Cautín",
}

PLANTAS = {
    1: "Labranza Mayor",
    2: "Labranza Menor",
    3: "Cajón",
}

# Paleta profesional
COLORES_PLANTAS = {1: "#E63946", 2: "#457B9D", 3: "#2A9D8F"}
COLOR_FIJO = "#1D3557"
COLOR_TRANSPORTE = "#E76F51"
COLOR_OBJETIVO = "#264653"
COLOR_BG = "#FAFAF8"
COLOR_GRID = "#E0E0E0"

# Paper reference data
PAPER_DIST_TOTAL_KM = {
    "1 planta regional, Rec. dif. >0%, Val_max 60%": 17627,
    "1 planta regional, Rec. dif. >0%, Val_max 70%": 16446,
    "2 plantas prov., Rec. dif. >0%, Val_max 60%": 17215,
    "2 plantas prov., Rec. dif. >0%, Val_max 70%": 15249,
}

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "figure.facecolor": COLOR_BG,
        "axes.facecolor": COLOR_BG,
        "savefig.facecolor": COLOR_BG,
        "savefig.dpi": 180,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.3,
    }
)


# ─────────────────────────────────────────────────────────────────────────────
#  CARGA DE DATOS
# ─────────────────────────────────────────────────────────────────────────────


def cargar_datos():
    with open(RESULTADOS_PATH, "r", encoding="utf-8") as f:
        resultados = json.load(f)
    with open(INSTANCIAS_PATH, "r", encoding="utf-8") as f:
        instancias = json.load(f)
    return resultados, instancias


def nombre_corto(nombre_completo: str) -> str:
    """Extrae el nombre corto de la instancia (después del ':')."""
    if ":" in nombre_completo:
        return nombre_completo.split(":", 1)[1].strip()
    return nombre_completo


# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO 1: Comparación de Valor de Función Objetivo por Instancia
# ─────────────────────────────────────────────────────────────────────────────


def grafico_comparacion_fobj(resultados, instancias):
    """Barras horizontales comparando F.Obj de las 10 instancias."""
    fig, ax = plt.subplots(figsize=(12, 7))

    nombres = [nombre_corto(r["nombre"]) for r in resultados]
    valores = [r["valor_objetivo"] for r in resultados]
    base_val = valores[0]

    # Colorear según si supera o es menor al escenario base
    colores = []
    for v in valores:
        if v > base_val * 1.05:
            colores.append("#E63946")  # Significativamente mayor
        elif v < base_val * 0.95:
            colores.append("#2A9D8F")  # Significativamente menor
        else:
            colores.append("#457B9D")  # Similar al base

    y_pos = np.arange(len(nombres))
    bars = ax.barh(
        y_pos, valores, color=colores, edgecolor="white", height=0.65, zorder=3
    )

    # Línea de referencia del escenario base
    ax.axvline(
        base_val,
        color=COLOR_OBJETIVO,
        linestyle="--",
        linewidth=1.5,
        alpha=0.7,
        zorder=2,
        label=f"Escenario Base: {base_val:,.0f} CLP/día",
    )

    # Etiquetas de valor sobre las barras
    for bar, val in zip(bars, valores):
        pct = ((val - base_val) / base_val) * 100
        signo = "+" if pct > 0 else ""
        ax.text(
            bar.get_width() + 40000,
            bar.get_y() + bar.get_height() / 2,
            f"${val:,.0f}\n({signo}{pct:.1f}%)",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="#333333",
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(nombres, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Valor Función Objetivo [CLP/día]", fontweight="bold")
    ax.set_title(
        "Comparación del Costo Total Óptimo por Escenario\n"
        "Modelo CFLP – Gestión de Residuos Temuco",
        fontsize=15,
        pad=15,
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(axis="x", alpha=0.3, color=COLOR_GRID, zorder=0)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    ax.set_xlim(0, max(valores) * 1.22)

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "01_comparacion_funcion_objetivo.png"))
    plt.close(fig)
    print("  ✓ 01_comparacion_funcion_objetivo.png")


# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO 2: Desglose Costo Fijo vs. Costo Transporte (Stacked)
# ─────────────────────────────────────────────────────────────────────────────


def grafico_desglose_costos(resultados, instancias):
    """Barras apiladas mostrando la composición del costo total."""
    fig, ax = plt.subplots(figsize=(13, 7))

    nombres = [f"I{i + 1}" for i in range(len(resultados))]
    nombres_full = [nombre_corto(r["nombre"]) for r in resultados]
    costos_fijos = [r["costo_fijo_total"] for r in resultados]
    costos_transp = [r["costo_transporte_total"] for r in resultados]

    x = np.arange(len(nombres))
    width = 0.6

    bars_fijo = ax.bar(
        x,
        costos_fijos,
        width,
        label="Costo Fijo (CAPEX+OPEX)",
        color=COLOR_FIJO,
        edgecolor="white",
        zorder=3,
    )
    bars_transp = ax.bar(
        x,
        costos_transp,
        width,
        bottom=costos_fijos,
        label="Costo Transporte",
        color=COLOR_TRANSPORTE,
        edgecolor="white",
        zorder=3,
    )

    # Porcentaje de transporte encima
    for i, (cf, ct) in enumerate(zip(costos_fijos, costos_transp)):
        total = cf + ct
        pct_t = (ct / total) * 100
        ax.text(
            i,
            total + 50000,
            f"{pct_t:.0f}% transp.",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#555555",
            fontweight="bold",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(nombres, fontsize=10, fontweight="bold")
    ax.set_ylabel("Costo [CLP/día]", fontweight="bold")
    ax.set_title(
        "Desglose del Costo Total: Fijo vs. Transporte\n"
        "Trade-off CAPEX/OPEX vs. Logística – 10 Escenarios",
        fontsize=15,
        pad=15,
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(fontsize=10, loc="upper left", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3, color=COLOR_GRID, zorder=0)

    # Leyenda inferior con nombres completos
    legend_text = "  |  ".join([f"I{i + 1}: {n}" for i, n in enumerate(nombres_full)])
    fig.text(
        0.5,
        -0.02,
        legend_text,
        ha="center",
        fontsize=7,
        color="#666666",
        style="italic",
    )

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "02_desglose_costos_fijo_transporte.png"))
    plt.close(fig)
    print("  ✓ 02_desglose_costos_fijo_transporte.png")


# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO 3: Plantas Abiertas por Instancia (Heatmap)
# ─────────────────────────────────────────────────────────────────────────────


def grafico_heatmap_plantas(resultados, instancias):
    """Heatmap mostrando qué plantas se abren en cada escenario."""
    fig, ax = plt.subplots(figsize=(10, 5.5))

    n_inst = len(resultados)
    n_plantas = 3
    matriz = np.zeros((n_plantas, n_inst))

    for j, r in enumerate(resultados):
        for p_id, abierta in r["plantas_abiertas"].items():
            if abierta:
                matriz[int(p_id) - 1, j] = 1

    # Mapa de colores personalizado
    from matplotlib.colors import ListedColormap

    cmap = ListedColormap(["#F0F0F0", "#2A9D8F"])

    im = ax.imshow(matriz, cmap=cmap, aspect="auto", interpolation="nearest")

    # Etiquetas
    ax.set_xticks(np.arange(n_inst))
    ax.set_xticklabels(
        [f"I{i + 1}" for i in range(n_inst)], fontsize=10, fontweight="bold"
    )
    ax.set_yticks(np.arange(n_plantas))
    ax.set_yticklabels(
        [f"J{j + 1}: {PLANTAS[j + 1]}" for j in range(n_plantas)], fontsize=11
    )

    # Texto dentro de las celdas
    for i in range(n_plantas):
        for j_idx in range(n_inst):
            texto = "ABIERTA" if matriz[i, j_idx] == 1 else "cerrada"
            color = "white" if matriz[i, j_idx] == 1 else "#AAAAAA"
            weight = "bold" if matriz[i, j_idx] == 1 else "normal"
            ax.text(
                j_idx,
                i,
                texto,
                ha="center",
                va="center",
                fontsize=8,
                color=color,
                fontweight=weight,
            )

    ax.set_title(
        "Decisiones de Apertura de Plantas (Y_j) por Escenario\n"
        "El modelo elige qué plantas construir para minimizar costos",
        fontsize=14,
        pad=15,
    )

    # Bordes de celdas
    for i in range(n_plantas + 1):
        ax.axhline(i - 0.5, color="white", linewidth=2)
    for j_idx in range(n_inst + 1):
        ax.axvline(j_idx - 0.5, color="white", linewidth=2)

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "03_heatmap_plantas_abiertas.png"))
    plt.close(fig)
    print("  ✓ 03_heatmap_plantas_abiertas.png")


# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO 4: Flujos de Asignación (Sankey-like para instancia base)
# ─────────────────────────────────────────────────────────────────────────────


def grafico_flujos_asignacion(resultados, instancias, idx_highlight=[0, 1, 9]):
    """Gráficos de flujos para instancias seleccionadas (base, shock, falla)."""
    for idx in idx_highlight:
        r = resultados[idx]
        fig, ax = plt.subplots(figsize=(11, 7))

        # Posiciones verticales de macrosectores (izquierda)
        n_ms = 8
        y_ms = np.linspace(0.9, 0.1, n_ms)
        # Posiciones de plantas (derecha)
        y_pl = {1: 0.75, 2: 0.5, 3: 0.25}

        # Dibujar macrosectores
        for i in range(1, n_ms + 1):
            color_ms = "#457B9D"
            ax.annotate(
                f"  {MACROSECTORES[i]}",
                xy=(0.12, y_ms[i - 1]),
                fontsize=10,
                va="center",
                ha="left",
                fontweight="bold",
                color=color_ms,
            )
            ax.plot(0.1, y_ms[i - 1], "o", color=color_ms, markersize=10, zorder=5)

        # Dibujar plantas
        for j in [1, 2, 3]:
            abierta = r["plantas_abiertas"].get(str(j), False)
            color_pl = COLORES_PLANTAS[j] if abierta else "#CCCCCC"
            estado = "[OK]" if abierta else "[--]"
            ax.annotate(
                f"{PLANTAS[j]} {estado}  ",
                xy=(0.88, y_pl[j]),
                fontsize=10,
                va="center",
                ha="right",
                fontweight="bold",
                color=color_pl,
            )
            ax.plot(0.9, y_pl[j], "s", color=color_pl, markersize=12, zorder=5)

        # Dibujar flujos
        flujos = r.get("flujos", {})
        max_flujo = max(flujos.values()) if flujos else 1
        for clave, cantidad in flujos.items():
            origen_id, destino_id = clave.split(",")
            i, j = int(origen_id), int(destino_id)
            ancho = max(1, (cantidad / max_flujo) * 6)
            alpha = 0.3 + 0.5 * (cantidad / max_flujo)
            color_linea = COLORES_PLANTAS.get(j, "#999999")

            ax.annotate(
                "",
                xy=(0.88, y_pl[j]),
                xytext=(0.12, y_ms[i - 1]),
                arrowprops=dict(
                    arrowstyle="->,head_width=0.15",
                    color=color_linea,
                    lw=ancho,
                    alpha=alpha,
                ),
            )
            # Etiqueta de flujo
            mid_x = 0.5
            mid_y = (y_ms[i - 1] + y_pl[j]) / 2
            ax.text(
                mid_x,
                mid_y,
                f"{cantidad:.0f}t",
                fontsize=7,
                ha="center",
                va="center",
                color=color_linea,
                fontweight="bold",
                alpha=0.85,
                bbox=dict(
                    boxstyle="round,pad=0.15",
                    facecolor="white",
                    edgecolor=color_linea,
                    alpha=0.7,
                ),
            )

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        titulo = nombre_corto(r["nombre"])
        fobj = r["valor_objetivo"]
        ax.set_title(
            f"Flujos de Asignación X_ij [ton/día] – I{idx + 1}: {titulo}\n"
            f"F. Obj. = ${fobj:,.0f} CLP/día",
            fontsize=14,
            pad=15,
            fontweight="bold",
        )

        # Leyenda
        ax.text(
            0.05,
            0.02,
            "● Macrosectores generadores",
            fontsize=8,
            color="#457B9D",
            transform=ax.transAxes,
        )
        ax.text(
            0.55,
            0.02,
            "■ Plantas de valorización candidatas",
            fontsize=8,
            color="#E63946",
            transform=ax.transAxes,
        )

        fig.tight_layout()
        nombre_archivo = f"04_flujos_instancia_{idx + 1:02d}.png"
        fig.savefig(os.path.join(OUTPUT_DIR, nombre_archivo))
        plt.close(fig)
        print(f"  ✓ {nombre_archivo}")


# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO 5: Demanda por Macrosector – Variación entre Instancias
# ─────────────────────────────────────────────────────────────────────────────


def grafico_demanda_macrosectores(resultados, instancias):
    """Comparación de demanda por macrosector entre instancias clave."""
    fig, ax = plt.subplots(figsize=(13, 7))

    instancias_selec = [0, 1, 3, 7, 8]  # Base, Shock, Orgánico, Pobl, REP
    colores_sel = ["#264653", "#E63946", "#2A9D8F", "#E9C46A", "#F4A261"]

    x = np.arange(8)
    width = 0.15
    offset = -(len(instancias_selec) - 1) / 2 * width

    for k, sel_idx in enumerate(instancias_selec):
        inst = instancias[sel_idx]
        demandas = [inst["W"][str(i)] for i in range(1, 9)]
        nombre = f"I{sel_idx + 1}: {nombre_corto(inst['nombre'])}"
        ax.bar(
            x + offset + k * width,
            demandas,
            width,
            label=nombre,
            color=colores_sel[k],
            edgecolor="white",
            zorder=3,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [MACROSECTORES[i] for i in range(1, 9)], rotation=25, ha="right", fontsize=9
    )
    ax.set_ylabel("Demanda W_i [ton/día]", fontweight="bold")
    ax.set_title(
        "Variación de la Demanda por Macrosector entre Escenarios\n"
        "El modelo CFLP se adapta a diferentes patrones de generación de residuos",
        fontsize=14,
        pad=15,
    )
    ax.grid(axis="y", alpha=0.3, color=COLOR_GRID, zorder=0)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.9, ncol=2)

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "05_demanda_macrosectores.png"))
    plt.close(fig)
    print("  ✓ 05_demanda_macrosectores.png")


# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO 6: Utilización de Capacidad de Planta
# ─────────────────────────────────────────────────────────────────────────────


def grafico_utilizacion_capacidad(resultados, instancias):
    """Barra mostrando utilización de capacidad de cada planta abierta."""
    fig, axes = plt.subplots(2, 5, figsize=(18, 8), sharey=True)
    axes = axes.flatten()

    for idx, (r, inst) in enumerate(zip(resultados, instancias)):
        ax = axes[idx]
        capacidades = {int(k): v for k, v in inst["Cap"].items()}
        flujos = r.get("flujos", {})

        # Calcular flujo total a cada planta
        flujo_planta = {1: 0.0, 2: 0.0, 3: 0.0}
        for clave, cantidad in flujos.items():
            _, j_str = clave.split(",")
            j = int(j_str)
            flujo_planta[j] += cantidad

        plantas_ids = [1, 2, 3]
        caps = [capacidades[j] for j in plantas_ids]
        flujos_arr = [flujo_planta[j] for j in plantas_ids]
        pcts = [f / c * 100 if c > 0 else 0 for f, c in zip(flujos_arr, caps)]

        colores = []
        for j in plantas_ids:
            abierta = r["plantas_abiertas"].get(str(j), False)
            if abierta:
                colores.append(COLORES_PLANTAS[j])
            else:
                colores.append("#E0E0E0")

        x_pos = np.arange(3)
        # Capacidad (fondo)
        ax.bar(x_pos, caps, 0.55, color="#F0F0F0", edgecolor="#CCCCCC", zorder=2)
        # Flujo real (encima)
        ax.bar(x_pos, flujos_arr, 0.55, color=colores, edgecolor="white", zorder=3)

        for k, (fl, cap, pct) in enumerate(zip(flujos_arr, caps, pcts)):
            if fl > 0:
                ax.text(
                    k,
                    fl + 5,
                    f"{pct:.0f}%",
                    ha="center",
                    fontsize=8,
                    fontweight="bold",
                    color="#333",
                )

        ax.set_xticks(x_pos)
        ax.set_xticklabels([f"J{j}" for j in plantas_ids], fontsize=9)
        ax.set_title(f"I{idx + 1}", fontsize=11, fontweight="bold")
        ax.set_ylim(0, 450)
        ax.grid(axis="y", alpha=0.2, zorder=0)

    # Título global y eje Y
    fig.suptitle(
        "Utilización de Capacidad de Plantas – 10 Escenarios\n"
        "Barra gris = Capacidad máxima | Barra color = Flujo asignado",
        fontsize=15,
        fontweight="bold",
        y=1.02,
    )
    axes[0].set_ylabel("Toneladas/día", fontweight="bold")
    axes[5].set_ylabel("Toneladas/día", fontweight="bold")

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "06_utilizacion_capacidad.png"))
    plt.close(fig)
    print("  ✓ 06_utilizacion_capacidad.png")


# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO 7: Tiempo Computacional
# ─────────────────────────────────────────────────────────────────────────────


def grafico_tiempos_computacionales(resultados, instancias):
    """Barras de tiempo de resolución en milisegundos."""
    fig, ax = plt.subplots(figsize=(12, 5.5))

    nombres = [f"I{i + 1}" for i in range(len(resultados))]
    tiempos_ms = [r["tiempo_segundos"] * 1000 for r in resultados]

    colores = [
        "#2A9D8F" if t < 20 else "#E9C46A" if t < 40 else "#E63946" for t in tiempos_ms
    ]

    bars = ax.bar(
        nombres, tiempos_ms, color=colores, edgecolor="white", width=0.6, zorder=3
    )

    for bar, t in zip(bars, tiempos_ms):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{t:.1f} ms",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    ax.set_ylabel("Tiempo de Resolución [ms]", fontweight="bold")
    ax.set_title(
        "Tiempo Computacional por Instancia – Solver CBC (PuLP)\n"
        "El paper usa Gurobi (MINLP regional); nuestro MILP comunal es rápido",
        fontsize=14,
        pad=15,
    )
    ax.grid(axis="y", alpha=0.3, color=COLOR_GRID, zorder=0)

    # Referencia al paper
    ax.text(
        0.98,
        0.95,
        "Paper (López Marín, 2024): MINLP regional\n"
        "con 32 comunas × 6 plantas → tiempos mayores\n"
        "por no-linealidad y escala del problema",
        transform=ax.transAxes,
        fontsize=8,
        va="top",
        ha="right",
        color="#666666",
        style="italic",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#F5F5F5", edgecolor="#CCCCCC"),
    )

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "07_tiempos_computacionales.png"))
    plt.close(fig)
    print("  ✓ 07_tiempos_computacionales.png")


# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO 8: Contraste con Paper – Alcance del Modelo
# ─────────────────────────────────────────────────────────────────────────────


def grafico_contraste_paper(resultados, instancias):
    """Infografía comparativa: nuestro MILP comunal vs. MINLP regional del paper."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    # --- Panel izquierdo: Dimensiones del problema ---
    ax = axes[0]
    categorias = [
        "Macrosectores /\nComunas",
        "Plantas\nCandidatas",
        "Variables\nBinarias",
        "Tipo de\nModelo",
    ]
    nuestro = [8, 3, 3, None]
    paper = [32, 6, None, None]
    tipo_nuestro = ["8", "3", "3 (Y_j)", "MILP"]
    tipo_paper = ["32", "6", "~70+", "MINLP"]

    y = np.arange(len(categorias))
    height = 0.3

    ax.barh(
        y + height / 2,
        [8, 3, 3, 0],
        height,
        label="Nuestro modelo (Temuco)",
        color="#2A9D8F",
        edgecolor="white",
        zorder=3,
    )
    ax.barh(
        y - height / 2,
        [32, 6, 70, 0],
        height,
        label="Paper (Araucanía completa)",
        color="#E76F51",
        edgecolor="white",
        zorder=3,
    )

    for i, (tn, tp) in enumerate(zip(tipo_nuestro, tipo_paper)):
        if i < 3:
            ax.text(
                max(nuestro[i] if nuestro[i] else 0, 2) + 1,
                i + height / 2,
                tn,
                va="center",
                fontsize=10,
                fontweight="bold",
                color="#2A9D8F",
            )
            ax.text(
                max(paper[i] if paper[i] else 0, 2) + 1,
                i - height / 2,
                tp,
                va="center",
                fontsize=10,
                fontweight="bold",
                color="#E76F51",
            )
        else:
            ax.text(
                5,
                i + height / 2,
                tn,
                va="center",
                fontsize=12,
                fontweight="bold",
                color="#2A9D8F",
            )
            ax.text(
                5,
                i - height / 2,
                tp,
                va="center",
                fontsize=12,
                fontweight="bold",
                color="#E76F51",
            )

    ax.set_yticks(y)
    ax.set_yticklabels(categorias, fontsize=11)
    ax.set_xlabel("Cantidad", fontweight="bold")
    ax.set_title("Dimensiones del Problema", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9, loc="lower right", framealpha=0.9)
    ax.grid(axis="x", alpha=0.3, color=COLOR_GRID, zorder=0)
    ax.set_xlim(0, 80)

    # --- Panel derecho: Costos del paper vs. nuestro ---
    ax2 = axes[1]

    # Del paper: costo social unitario ≈ 59.490 CLP/ton (actual)
    # Nuestro modelo base: F.Obj / demanda total
    demanda_base = sum(instancias[0]["W"][str(i)] for i in range(1, 9))
    costo_unit_nuestro = resultados[0]["valor_objetivo"] / demanda_base
    costo_unit_paper_actual = 59490  # CLP/ton (modelo actual sin valorización)
    costo_unit_paper_propuesto = 131895  # ~promedio 127100-136690 CLP/ton con valoriz.

    categorias_c = [
        "Gestión actual\n(sin valorización)",
        "Paper: Con plantas\nde valorización",
        "Nuestro MILP:\nEscenario base",
    ]
    costos_c = [costo_unit_paper_actual, costo_unit_paper_propuesto, costo_unit_nuestro]
    colores_c = ["#AAAAAA", "#E76F51", "#2A9D8F"]

    bars2 = ax2.bar(
        categorias_c, costos_c, color=colores_c, edgecolor="white", width=0.55, zorder=3
    )
    for bar, c in zip(bars2, costos_c):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 200,
            f"${c:,.0f}\nCLP/ton",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    ax2.set_ylabel("Costo Unitario [CLP/ton]", fontweight="bold")
    ax2.set_title("Costo Unitario de Gestión de RSD", fontsize=13, fontweight="bold")
    ax2.grid(axis="y", alpha=0.3, color=COLOR_GRID, zorder=0)
    ax2.set_ylim(0, max(costos_c) * 1.25)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    fig.suptitle(
        "Contraste: Nuestro Modelo MILP Comunal vs. Paper MINLP Regional\n"
        "López Marín (2024) – U. de Chile, Sección 7.1",
        fontsize=15,
        fontweight="bold",
        y=1.03,
    )

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "08_contraste_paper.png"))
    plt.close(fig)
    print("  ✓ 08_contraste_paper.png")


# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO 9: Análisis de Sensibilidad – Variación de la F.Obj
# ─────────────────────────────────────────────────────────────────────────────


def grafico_sensibilidad(resultados, instancias):
    """Spider/radar chart mostrando sensibilidad relativa al caso base."""
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    # Usar instancias 2-10 (la 1 es el base)
    n_inst = len(resultados) - 1
    base_val = resultados[0]["valor_objetivo"]

    angulos = np.linspace(0, 2 * np.pi, n_inst, endpoint=False).tolist()
    angulos += angulos[:1]  # Cerrar

    valores_norm = []
    for r in resultados[1:]:
        ratio = r["valor_objetivo"] / base_val
        valores_norm.append(ratio)
    valores_norm += valores_norm[:1]

    # Graficar
    ax.plot(
        angulos,
        valores_norm,
        "o-",
        color="#E63946",
        linewidth=2,
        markersize=8,
        zorder=5,
    )
    ax.fill(angulos, valores_norm, color="#E63946", alpha=0.15)

    # Línea base
    ax.plot(
        angulos,
        [1.0] * len(angulos),
        "--",
        color="#2A9D8F",
        linewidth=2,
        alpha=0.7,
        label="Escenario Base (ratio = 1.0)",
    )

    # Etiquetas
    etiquetas = [
        f"I{i + 2}: {nombre_corto(r['nombre'])}" for i, r in enumerate(resultados[1:])
    ]
    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(etiquetas, fontsize=8.5, fontweight="bold")

    # Valores en cada punto
    for ang, val, r in zip(angulos[:-1], valores_norm[:-1], resultados[1:]):
        pct = (val - 1) * 100
        signo = "+" if pct > 0 else ""
        ax.annotate(
            f"{signo}{pct:.1f}%",
            xy=(ang, val),
            xytext=(5, 12),
            textcoords="offset points",
            fontsize=8,
            fontweight="bold",
            color="#333",
            ha="center",
        )

    ax.set_title(
        "Análisis de Sensibilidad – Desviación Relativa al Escenario Base\n"
        "Ratio F.Obj / F.Obj_base",
        fontsize=14,
        pad=30,
        fontweight="bold",
    )
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=9)

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "09_sensibilidad_radar.png"))
    plt.close(fig)
    print("  ✓ 09_sensibilidad_radar.png")


# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO 10: Resumen Ejecutivo – Tabla Visual
# ─────────────────────────────────────────────────────────────────────────────


def grafico_tabla_resumen(resultados, instancias):
    """Tabla-resumen visual con todos los resultados clave."""
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis("off")

    columnas = [
        "Instancia",
        "Escenario",
        "F. Obj.\n[CLP/día]",
        "Costo Fijo\n[CLP/día]",
        "Costo Transp.\n[CLP/día]",
        "Plantas\nAbiertas",
        "Tiempo\n[ms]",
        "Δ vs Base",
    ]

    datos = []
    base_val = resultados[0]["valor_objetivo"]
    for i, r in enumerate(resultados):
        plantas = ", ".join([f"J{j}" for j, a in r["plantas_abiertas"].items() if a])
        delta = ((r["valor_objetivo"] - base_val) / base_val) * 100
        signo = "+" if delta > 0 else ""
        datos.append(
            [
                f"I{i + 1}",
                nombre_corto(r["nombre"]),
                f"${r['valor_objetivo']:,.0f}",
                f"${r['costo_fijo_total']:,.0f}",
                f"${r['costo_transporte_total']:,.0f}",
                plantas,
                f"{r['tiempo_segundos'] * 1000:.1f}",
                f"{signo}{delta:.1f}%" if i > 0 else "BASE",
            ]
        )

    table = ax.table(
        cellText=datos,
        colLabels=columnas,
        cellLoc="center",
        loc="center",
        colColours=["#264653"] * len(columnas),
    )

    # Estilo
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)

    # Header style
    for j in range(len(columnas)):
        cell = table[0, j]
        cell.set_text_props(color="white", fontweight="bold")
        cell.set_facecolor("#264653")
        cell.set_edgecolor("white")

    # Body style
    for i in range(1, len(datos) + 1):
        for j in range(len(columnas)):
            cell = table[i, j]
            cell.set_edgecolor("#E0E0E0")
            if i % 2 == 0:
                cell.set_facecolor("#F5F5F5")
            else:
                cell.set_facecolor("#FFFFFF")
            # Colorear delta
            if j == 7 and i > 1:
                val_delta = float(datos[i - 1][7].replace("+", "").replace("%", ""))
                if val_delta > 5:
                    cell.set_text_props(color="#E63946", fontweight="bold")
                elif val_delta < -5:
                    cell.set_text_props(color="#2A9D8F", fontweight="bold")

    ax.set_title(
        "Resumen Ejecutivo – Resultados de las 10 Instancias CFLP\n"
        "Modelo de Programación Lineal Entera Mixta – Gestión de Residuos Temuco",
        fontsize=15,
        fontweight="bold",
        pad=25,
    )

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "10_tabla_resumen.png"))
    plt.close(fig)
    print("  ✓ 10_tabla_resumen.png")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n" + "═" * 60)
    print("  GENERACIÓN DE GRÁFICOS – MODELO CFLP TEMUCO")
    print("═" * 60)
    print(f"  Resultados: {RESULTADOS_PATH}")
    print(f"  Instancias: {INSTANCIAS_PATH}")
    print(f"  Salida:     {OUTPUT_DIR}/")
    print("─" * 60 + "\n")

    resultados, instancias = cargar_datos()
    print(f"  Cargadas {len(resultados)} instancias con resultados.\n")

    grafico_comparacion_fobj(resultados, instancias)
    grafico_desglose_costos(resultados, instancias)
    grafico_heatmap_plantas(resultados, instancias)
    grafico_flujos_asignacion(resultados, instancias)
    grafico_demanda_macrosectores(resultados, instancias)
    grafico_utilizacion_capacidad(resultados, instancias)
    grafico_tiempos_computacionales(resultados, instancias)
    grafico_contraste_paper(resultados, instancias)
    grafico_sensibilidad(resultados, instancias)
    grafico_tabla_resumen(resultados, instancias)

    print("\n" + "─" * 60)
    print(f"  ✓ ¡Proceso completado! Gráficos guardados en: {OUTPUT_DIR}/")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
