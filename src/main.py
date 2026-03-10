"""
main.py – Punto de entrada para la resolución de todas las instancias CFLP
           del problema de gestión de residuos de la comuna de Temuco.

Lee las instancias desde el archivo JSON (data/instancias.json), resuelve
cada una con PuLP + CPLEX (o CBC como fallback), e imprime y exporta
los resultados numéricos.

Uso:
    python src/main.py                          # resolver todas
    python src/main.py --instancia 1            # resolver solo la instancia 1
    python src/main.py --verbose                # mostrar log del solver
    python src/main.py --exportar resultados    # guardar resultados en JSON

Autor:  Felipe Cubillos / Diego Gómez / Tomás Cárcamo
Fecha:  Marzo 2026
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Forzar UTF-8 en stdout/stderr para que los caracteres Unicode (━, █, etc.)
# se muestren correctamente en terminales Windows con codificación CP1252.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Agregar el directorio raíz del proyecto al path
PROYECTO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROYECTO_DIR))

from src.solver import imprimir_resultado, resolver_cflp

# ══════════════════════════════════════════════════════════════════════════════
#  CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════════════


def cargar_instancias(ruta_json: str) -> list:
    """
    Lee el archivo JSON con las instancias y reconstruye las claves
    de la matriz de costos C_ij como tuplas (i, j).

    Parámetros
    ----------
    ruta_json : str
        Ruta al archivo instancias.json.

    Retorna
    -------
    list[dict]
        Lista de diccionarios con los datos de cada instancia.
    """
    with open(ruta_json, "r", encoding="utf-8") as f:
        datos = json.load(f)

    for inst in datos:
        # Convertir claves de C de "i,j" (string) a tuplas (int, int)
        inst["C"] = {tuple(map(int, k.split(","))): v for k, v in inst["C"].items()}
        # Convertir claves de W, F, Cap de string a int (JSON solo permite str keys)
        inst["W"] = {int(k): v for k, v in inst["W"].items()}
        inst["F"] = {int(k): v for k, v in inst["F"].items()}
        inst["Cap"] = {int(k): v for k, v in inst["Cap"].items()}

    return datos


# ══════════════════════════════════════════════════════════════════════════════
#  RESOLUCIÓN Y REPORTE
# ══════════════════════════════════════════════════════════════════════════════


def resolver_todas(instancias: list, verbose: bool = False) -> list:
    """
    Resuelve todas las instancias y retorna los resultados.

    Parámetros
    ----------
    instancias : list[dict]
        Lista de instancias cargadas desde JSON.
    verbose : bool
        Si True, imprime log del solver.

    Retorna
    -------
    list[ResultadoCFLP]
    """
    resultados = []
    total = len(instancias)

    for idx, inst in enumerate(instancias, 1):
        print(f"\n{'━' * 72}")
        print(f"  Resolviendo instancia {idx}/{total}: {inst['nombre']}")
        print(f"{'━' * 72}")

        resultado = resolver_cflp(
            nombre=inst["nombre"],
            I=inst["I"],
            J=inst["J"],
            W=inst["W"],
            C=inst["C"],
            F=inst["F"],
            Cap=inst["Cap"],
            verbose=verbose,
        )

        imprimir_resultado(resultado)
        resultados.append(resultado)

    return resultados


def imprimir_tabla_resumen(resultados: list) -> None:
    """Imprime una tabla comparativa de todas las instancias resueltas."""
    print("\n" + "█" * 72)
    print("  TABLA RESUMEN – RESULTADOS DE LAS 10 INSTANCIAS CFLP")
    print("█" * 72)
    print()

    # Encabezado
    header = (
        f"  {'#':>2}  {'Instancia':<38}  {'F.Obj [CLP/día]':>16}  "
        f"{'Tiempo [s]':>10}  {'Plantas':>8}  {'Estado':<10}"
    )
    print(header)
    print(f"  {'─' * 2}  {'─' * 38}  {'─' * 16}  {'─' * 10}  {'─' * 8}  {'─' * 10}")

    for idx, res in enumerate(resultados, 1):
        if res.estado == "Optimal":
            n_plantas = sum(1 for a in res.plantas_abiertas.values() if a)
            lista_j = ",".join(
                str(j) for j, a in sorted(res.plantas_abiertas.items()) if a
            )
            plantas_str = f"J{{{lista_j}}}"
            fobj_str = f"{res.valor_objetivo:>16,.2f}"
        else:
            plantas_str = "N/A"
            fobj_str = f"{'N/A':>16}"

        nombre_corto = res.nombre.replace("Instancia ", "").replace(": ", ": ")
        if len(nombre_corto) > 38:
            nombre_corto = nombre_corto[:35] + "..."

        print(
            f"  {idx:>2}  {nombre_corto:<38}  {fobj_str}  "
            f"{res.tiempo_segundos:>10.4f}  {plantas_str:>8}  {res.estado:<10}"
        )

    print()

    # Estadísticas generales
    tiempos = [r.tiempo_segundos for r in resultados if r.estado == "Optimal"]
    valores = [r.valor_objetivo for r in resultados if r.estado == "Optimal"]

    if tiempos:
        print(f"  Tiempo total de cómputo:     {sum(tiempos):.4f} s")
        print(f"  Tiempo promedio por inst.:    {sum(tiempos) / len(tiempos):.4f} s")
        print(
            f"  Rango de F. Objetivo:        "
            f"[{min(valores):,.2f} — {max(valores):,.2f}] CLP/día"
        )
    print()


def exportar_resultados(resultados: list, ruta_salida: str) -> None:
    """
    Exporta los resultados a un archivo JSON.

    Parámetros
    ----------
    resultados : list[ResultadoCFLP]
    ruta_salida : str
        Ruta completa del archivo de salida.
    """
    datos_export = []

    for res in resultados:
        d = {
            "nombre": res.nombre,
            "estado": res.estado,
            "valor_objetivo": res.valor_objetivo,
            "tiempo_segundos": res.tiempo_segundos,
            "solver_utilizado": res.solver_utilizado,
            "costo_fijo_total": res.costo_fijo_total,
            "costo_transporte_total": res.costo_transporte_total,
            "plantas_abiertas": {
                str(j): abierta for j, abierta in res.plantas_abiertas.items()
            },
            "flujos": {f"{i},{j}": val for (i, j), val in res.flujos.items()},
        }
        datos_export.append(d)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(datos_export, f, ensure_ascii=False, indent=2)

    print(f"  ✓ Resultados exportados a: {ruta_salida}")


# ══════════════════════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="Resolver instancias CFLP – Gestión de Residuos de Temuco"
    )
    parser.add_argument(
        "--instancia",
        type=int,
        default=None,
        help="Número de instancia a resolver (1-10). Si no se indica, se resuelven todas.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Mostrar log detallado del solver."
    )
    parser.add_argument(
        "--exportar",
        type=str,
        default=None,
        nargs="?",
        const="resultados",
        metavar="NOMBRE",
        help=(
            "Nombre base del archivo JSON de salida (se guarda en data/). "
            "Si se omite el nombre, se usa 'resultados' por defecto. "
            "Ejemplo: --exportar  o  --exportar mi_run"
        ),
    )
    parser.add_argument(
        "--datos",
        type=str,
        default=None,
        help="Ruta al archivo JSON de instancias. Por defecto: data/instancias.json",
    )
    args = parser.parse_args()

    # Determinar ruta del JSON de entrada
    if args.datos:
        ruta_json = args.datos
    else:
        ruta_json = str(PROYECTO_DIR / "data" / "instancias.json")

    if not os.path.exists(ruta_json):
        print(f"  ✗ ERROR: No se encontró el archivo de instancias: {ruta_json}")
        sys.exit(1)

    # Cargar instancias
    print(f"\n  Cargando instancias desde: {ruta_json}")
    instancias = cargar_instancias(ruta_json)
    print(f"  Se cargaron {len(instancias)} instancias.\n")

    # Filtrar si se pidió una instancia específica
    if args.instancia is not None:
        idx = args.instancia - 1
        if idx < 0 or idx >= len(instancias):
            print(
                f"  ✗ ERROR: Instancia {args.instancia} fuera de rango [1-{len(instancias)}]"
            )
            sys.exit(1)
        instancias = [instancias[idx]]

    # Resolver
    resultados = resolver_todas(instancias, verbose=args.verbose)

    # Tabla resumen (solo si se resolvieron múltiples)
    if len(resultados) > 1:
        imprimir_tabla_resumen(resultados)

    # Exportar si se solicitó
    if args.exportar:
        ruta_salida = str(PROYECTO_DIR / "data" / f"{args.exportar}.json")
        exportar_resultados(resultados, ruta_salida)


if __name__ == "__main__":
    main()
