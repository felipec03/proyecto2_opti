"""
solver.py – Módulo de resolución del Problema de Localización de Plantas
             Capacitadas (CFLP) para la gestión de residuos en Temuco.

Modelo MILP (Programación Lineal Entera Mixta):

    min  Σ_j  F_j · Y_j   +   Σ_i Σ_j  C_ij · X_ij

    s.a.
        (1)  Σ_j X_ij  =  W_i              ∀ i ∈ I   (satisfacción de demanda)
        (2)  Σ_i X_ij  ≤  Cap_j · Y_j      ∀ j ∈ J   (capacidad + activación)
        (3)  Y_j  ∈ {0, 1}                  ∀ j ∈ J
        (4)  X_ij ≥ 0                       ∀ i,j

Utiliza PuLP como interfaz de modelado y CPLEX como solver preferente,
con fallback automático a CBC (incluido en PuLP).

Autor:  Felipe Cubillos / Diego Gómez / Tomás Cárcamo
Fecha:  Marzo 2026
Ref.:   López Marín (2024), U. de Chile – sección 7.1.1
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pulp
import time


# ══════════════════════════════════════════════════════════════════════════════
#  ESTRUCTURA DE DATOS PARA RESULTADOS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ResultadoCFLP:
    """Resultado de la resolución de una instancia CFLP."""

    nombre: str                               # Nombre de la instancia
    estado: str                               # "Optimal", "Infeasible", etc.
    valor_objetivo: Optional[float] = None    # Valor de la función objetivo [CLP/día]
    tiempo_segundos: float = 0.0              # Tiempo de resolución [s]
    solver_utilizado: str = ""                 # "CPLEX_CMD" o "PULP_CBC_CMD"
    plantas_abiertas: Dict[int, bool] = field(default_factory=dict)    # Y_j
    flujos: Dict[Tuple[int, int], float] = field(default_factory=dict) # X_ij
    costo_fijo_total: float = 0.0             # Σ F_j · Y_j
    costo_transporte_total: float = 0.0       # Σ C_ij · X_ij


# ══════════════════════════════════════════════════════════════════════════════
#  SELECCIÓN DEL SOLVER
# ══════════════════════════════════════════════════════════════════════════════

def obtener_solver(tiempo_limite: int = 300, verbose: bool = False):
    """
    Intenta utilizar CPLEX; si no está disponible, usa CBC.

    Parámetros
    ----------
    tiempo_limite : int
        Tiempo máximo de resolución en segundos.
    verbose : bool
        Si True, el solver imprime su log en consola.

    Retorna
    -------
    solver : pulp solver
    nombre : str
    """
    msg = 1 if verbose else 0

    # Intentar CPLEX primero
    try:
        cplex_solver = pulp.CPLEX_CMD(msg=msg, timeLimit=tiempo_limite)
        if cplex_solver.available():
            return cplex_solver, "CPLEX_CMD"
    except Exception:
        pass

    # Fallback a CBC (incluido con PuLP)
    cbc_solver = pulp.PULP_CBC_CMD(msg=msg, timeLimit=tiempo_limite)
    return cbc_solver, "PULP_CBC_CMD"


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCIÓN PRINCIPAL DE RESOLUCIÓN
# ══════════════════════════════════════════════════════════════════════════════

def resolver_cflp(
    nombre: str,
    I: List[int],
    J: List[int],
    W: Dict[int, float],
    C: Dict[Tuple[int, int], float],
    F: Dict[int, float],
    Cap: Dict[int, float],
    tiempo_limite: int = 300,
    verbose: bool = False,
) -> ResultadoCFLP:
    """
    Formula y resuelve una instancia del problema CFLP.

    Parámetros
    ----------
    nombre : str
        Identificador de la instancia.
    I : list[int]
        Índices de los macrosectores generadores de residuos.
    J : list[int]
        Índices de las ubicaciones candidatas para plantas.
    W : dict[int, float]
        Demanda diaria del macrosector i [ton/día].
    C : dict[(int,int), float]
        Costo de transporte unitario de i a j [CLP/ton].
    F : dict[int, float]
        Costo fijo de instalar y operar la planta j [CLP/día].
    Cap : dict[int, float]
        Capacidad máxima de procesamiento de la planta j [ton/día].
    tiempo_limite : int
        Tiempo máximo de resolución en segundos (default 300).
    verbose : bool
        Si True, imprime log del solver.

    Retorna
    -------
    ResultadoCFLP
        Objeto con la solución completa.
    """

    # ── 1. Crear el problema de minimización ──────────────────────────────
    prob = pulp.LpProblem(f"CFLP_{nombre}", pulp.LpMinimize)

    # ── 2. Variables de decisión ──────────────────────────────────────────
    #   Y_j ∈ {0, 1}: abrir planta en j
    Y = pulp.LpVariable.dicts("Y", J, cat=pulp.LpBinary)

    #   X_ij ≥ 0: flujo de residuos de i a j [ton/día]
    X = pulp.LpVariable.dicts("X", [(i, j) for i in I for j in J],
                              lowBound=0, cat=pulp.LpContinuous)

    # ── 3. Función objetivo ───────────────────────────────────────────────
    #   min  Σ_j F_j · Y_j  +  Σ_i Σ_j C_ij · X_ij
    prob += (
        pulp.lpSum(F[j] * Y[j] for j in J) +
        pulp.lpSum(C[(i, j)] * X[(i, j)] for i in I for j in J)
    ), "Costo_Total"

    # ── 4. Restricciones ──────────────────────────────────────────────────

    # (R1) Satisfacción integral de la demanda:
    #      Σ_j X_ij = W_i   ∀ i ∈ I
    for i in I:
        prob += (
            pulp.lpSum(X[(i, j)] for j in J) == W[i],
            f"Demanda_{i}"
        )

    # (R2) Límite de capacidad y activación lógica (Big-M):
    #      Σ_i X_ij ≤ Cap_j · Y_j   ∀ j ∈ J
    for j in J:
        prob += (
            pulp.lpSum(X[(i, j)] for i in I) <= Cap[j] * Y[j],
            f"Capacidad_{j}"
        )

    # (R3) y (R4) están implícitas en la definición de las variables.

    # ── 5. Resolver ───────────────────────────────────────────────────────
    solver, solver_nombre = obtener_solver(tiempo_limite, verbose)

    t_inicio = time.perf_counter()
    prob.solve(solver)
    t_fin = time.perf_counter()

    tiempo_resolucion = t_fin - t_inicio
    estado = pulp.LpStatus[prob.status]

    # ── 6. Extraer resultados ─────────────────────────────────────────────
    resultado = ResultadoCFLP(
        nombre=nombre,
        estado=estado,
        tiempo_segundos=round(tiempo_resolucion, 6),
        solver_utilizado=solver_nombre,
    )

    if estado == "Optimal":
        resultado.valor_objetivo = round(pulp.value(prob.objective), 2)

        # Plantas abiertas
        for j in J:
            resultado.plantas_abiertas[j] = int(Y[j].varValue) == 1

        # Flujos de asignación
        for i in I:
            for j in J:
                val = X[(i, j)].varValue
                if val is not None and val > 1e-6:
                    resultado.flujos[(i, j)] = round(val, 4)

        # Desglose de costos
        resultado.costo_fijo_total = round(
            sum(F[j] for j in J if resultado.plantas_abiertas.get(j, False)), 2
        )
        resultado.costo_transporte_total = round(
            resultado.valor_objetivo - resultado.costo_fijo_total, 2
        )

    return resultado


# ══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES DE IMPRESIÓN
# ══════════════════════════════════════════════════════════════════════════════

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
    1: "Labranza Mayor (Rol 3251-852)",
    2: "Labranza Menor (Rol 3250-78)",
    3: "Cajón (Rol 3281-291)",
}


def imprimir_resultado(res: ResultadoCFLP) -> None:
    """Imprime un resumen formateado del resultado de la optimización."""
    print("=" * 72)
    print(f"  {res.nombre}")
    print("=" * 72)
    print(f"  Estado:              {res.estado}")
    print(f"  Solver:              {res.solver_utilizado}")
    print(f"  Tiempo de cómputo:   {res.tiempo_segundos:.6f} s")

    if res.estado != "Optimal":
        print(f"  ⚠ No se encontró solución óptima.")
        print()
        return

    print(f"  ┌─────────────────────────────────────────────┐")
    print(f"  │  Valor F. Objetivo:  {res.valor_objetivo:>16,.2f} CLP/día │")
    print(f"  │  Costo Fijo Total:   {res.costo_fijo_total:>16,.2f} CLP/día │")
    print(f"  │  Costo Transporte:   {res.costo_transporte_total:>16,.2f} CLP/día │")
    print(f"  └─────────────────────────────────────────────┘")
    print()

    # Plantas abiertas
    print("  Plantas abiertas (Y_j = 1):")
    for j, abierta in sorted(res.plantas_abiertas.items()):
        estado_str = "✓ ABIERTA" if abierta else "✗ CERRADA"
        nombre_planta = PLANTAS.get(j, f"Planta {j}")
        print(f"    j={j}  {nombre_planta:<35}  {estado_str}")
    print()

    # Matriz de flujos
    plantas_activas = [j for j, a in sorted(res.plantas_abiertas.items()) if a]
    if plantas_activas:
        print("  Flujos X_ij [ton/día]:")
        header = f"  {'Macrosector':<25}"
        for j in plantas_activas:
            header += f"  {'J'+str(j):>10}"
        header += f"  {'Total':>10}"
        print(header)
        print(f"  {'-'*25}" + f"  {'-'*10}" * (len(plantas_activas) + 1))

        for i in sorted(set(k[0] for k in res.flujos.keys())):
            nombre_ms = MACROSECTORES.get(i, f"Sector {i}")
            row = f"  {nombre_ms:<25}"
            total_fila = 0.0
            for j in plantas_activas:
                flujo = res.flujos.get((i, j), 0.0)
                total_fila += flujo
                row += f"  {flujo:>10.2f}"
            row += f"  {total_fila:>10.2f}"
            print(row)

        # Totales por planta
        row_total = f"  {'TOTAL':<25}"
        for j in plantas_activas:
            total_col = sum(v for (ii, jj), v in res.flujos.items() if jj == j)
            row_total += f"  {total_col:>10.2f}"
        gran_total = sum(res.flujos.values())
        row_total += f"  {gran_total:>10.2f}"
        print(f"  {'-'*25}" + f"  {'-'*10}" * (len(plantas_activas) + 1))
        print(row_total)

    print()
