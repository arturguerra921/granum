"""
Automated Benchmarking Script for the Optimization Model

Prerequisites:
Make sure the OSRM Docker container is running locally and accessible on port 5000
before executing this script locally.

Run: `docker-compose up -d osrm`
"""
import os
import time
import pandas as pd
import numpy as np

# =============================================================================
# MODEL PARAMETERS CONFIGURATION
# =============================================================================
TOGGLE_MIN_MAX_CAPACITY = False  # Set to True to use MILP model
INPUT_MIN_LOAD = None
INPUT_MAX_LOAD = None
INPUT_ALLOCATION_DAYS = 1.0
INPUT_MIN_FREIGHT = None
INPUT_MAX_FREIGHT = None
TOGGLE_PARETO = False
TOGGLE_USE_RECEPTION = False

# =============================================================================
# DATA GENERATION CONFIGURATION
# =============================================================================
INCREMENTO_OFERTAS = 10
MAXIMO_OFERTAS = 50
INCREMENTO_ARMAZENS = 5
MAXIMO_ARMAZENS = 25
MAXIMO_TONELADAS = 2_000_000
MAX_RECEPTION_PERCENTAGE = 0.8

# =============================================================================
# FILE PATHS
# =============================================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUNICIPIOS_CSV = os.path.join(PROJECT_ROOT, 'src', 'view', 'assets', 'data', 'municipios.csv')
ESTADOS_CSV = os.path.join(PROJECT_ROOT, 'src', 'view', 'assets', 'data', 'estados.csv')
ARMAZENS_CSV = os.path.join(PROJECT_ROOT, 'src', 'view', 'assets', 'data', 'Armazens_Cadastrados_Base.csv')
TARIFA_CSV = os.path.join(PROJECT_ROOT, 'src', 'view', 'assets', 'data', 'Tarifa_de_Armazenagem.csv')
FRETE_CSV = os.path.join(PROJECT_ROOT, 'src', 'view', 'assets', 'data', 'Valor_Tonelada_km.csv')

PRODUTOS = ['Soja', 'Milho', 'Trigo', 'Arroz', 'Café', 'Feijão', 'Sorgo', 'Algodão', 'Aveia']

def generate_test_pairs():
    """
    Generator that yields in-memory DataFrames for supply (ofertas) and demand (armazéns).
    Based on the exact logic from scripts/gerar_ofertas_teste.py.
    """
    print(f"Loading base data for generation...")

    if not all(os.path.exists(f) for f in [MUNICIPIOS_CSV, ESTADOS_CSV, ARMAZENS_CSV]):
        raise FileNotFoundError("One or more base CSV files are missing in src/view/assets/data/.")

    df_municipios = pd.read_csv(MUNICIPIOS_CSV)
    df_estados = pd.read_csv(ESTADOS_CSV)

    if '\ufeffcodigo_uf' in df_estados.columns:
        df_estados.rename(columns={'\ufeffcodigo_uf': 'codigo_uf'}, inplace=True)

    df_municipios = pd.merge(df_municipios, df_estados[['codigo_uf', 'uf']], on='codigo_uf', how='left')
    df_municipios['nome_formatado'] = df_municipios['nome'] + ' - ' + df_municipios['uf']

    df_armazens = pd.read_csv(ARMAZENS_CSV, sep=';', skiprows=1, encoding='latin1')

    def parse_number(val):
        if pd.isna(val) or val == '':
            return np.nan
        if isinstance(val, (int, float)):
            return float(val)
        val = str(val).strip()
        if not val:
            return np.nan
        val = val.replace('.', '').replace(',', '.')
        try:
            return float(val)
        except ValueError:
            return np.nan

    df_armazens['_cap_estatica_num'] = df_armazens['Capacidade (t)'].apply(parse_number)
    df_armazens['_cap_recepcao_num'] = df_armazens['Capacidade de Recepção'].apply(parse_number)

    filtro_armazens_validos = (df_armazens['_cap_estatica_num'] > 0) & (df_armazens['_cap_recepcao_num'] > 0)
    df_armazens_validos = df_armazens[filtro_armazens_validos].copy()

    total_armazens_validos = len(df_armazens_validos)
    if total_armazens_validos == 0:
        raise ValueError("Nenhum armazém com capacidades válidas encontrado.")

    np.random.seed(42)  # Seed para manter exemplos iguais

    # Base de Ofertas
    indices_municipios = np.random.choice(df_municipios.index, size=MAXIMO_OFERTAS, replace=True)
    df_ofertas_base = df_municipios.loc[indices_municipios].copy().reset_index(drop=True)
    df_ofertas_base.rename(columns={'nome_formatado': 'Cidade', 'latitude': 'Latitude', 'longitude': 'Longitude'}, inplace=True)
    df_ofertas_base['Produto'] = np.random.choice(PRODUTOS, size=MAXIMO_OFERTAS)

    # Base de Armazéns
    indices_armazens = np.random.choice(df_armazens_validos.index, size=MAXIMO_ARMAZENS, replace=(MAXIMO_ARMAZENS > total_armazens_validos))
    df_armazens_base = df_armazens_validos.loc[indices_armazens].copy().reset_index(drop=True)

    passos_ofertas = list(range(INCREMENTO_OFERTAS, MAXIMO_OFERTAS + 1, INCREMENTO_OFERTAS))
    if MAXIMO_OFERTAS not in passos_ofertas:
        passos_ofertas.append(MAXIMO_OFERTAS)

    passos_armazens = list(range(INCREMENTO_ARMAZENS, MAXIMO_ARMAZENS + 1, INCREMENTO_ARMAZENS))
    if MAXIMO_ARMAZENS not in passos_armazens:
        passos_armazens.append(MAXIMO_ARMAZENS)

    max_passos = max(len(passos_ofertas), len(passos_armazens))
    while len(passos_ofertas) < max_passos:
        passos_ofertas.append(passos_ofertas[-1])
    while len(passos_armazens) < max_passos:
        passos_armazens.append(passos_armazens[-1])

    test_cases = sorted(list(set(zip(passos_ofertas, passos_armazens))))

    for num_ofertas, num_armazens in test_cases:
        df_armazens_recorte = df_armazens_base.head(num_armazens).copy()
        total_estatica = df_armazens_recorte['_cap_estatica_num'].sum()
        total_recepcao = df_armazens_recorte['_cap_recepcao_num'].sum()
        recepcao_limite = total_recepcao * MAX_RECEPTION_PERCENTAGE

        df_armazens_final = df_armazens_recorte.drop(columns=['_cap_estatica_num', '_cap_recepcao_num'])

        peso_maximo_permitido = min(MAXIMO_TONELADAS, total_estatica, recepcao_limite)

        df_ofertas_recorte = df_ofertas_base.head(num_ofertas).copy()
        pesos_aleatorios = np.random.uniform(low=10, high=1000, size=num_ofertas)
        fator_normalizacao = peso_maximo_permitido / pesos_aleatorios.sum()
        pesos_normalizados = pesos_aleatorios * fator_normalizacao

        df_ofertas_recorte['Peso (ton)'] = np.round(pesos_normalizados, 2)
        diferenca = peso_maximo_permitido - df_ofertas_recorte['Peso (ton)'].sum()
        df_ofertas_recorte.loc[df_ofertas_recorte.index[-1], 'Peso (ton)'] += diferenca
        df_ofertas_recorte['Peso (ton)'] = np.round(df_ofertas_recorte['Peso (ton)'], 2)

        colunas_finais_ofertas = ["Produto", "Peso (ton)", "Cidade", "Latitude", "Longitude"]
        df_ofertas_final = df_ofertas_recorte[colunas_finais_ofertas]

        yield df_ofertas_final, df_armazens_final

# =============================================================================
# BENCHMARK LOGIC
# =============================================================================
import sys
sys.path.append(PROJECT_ROOT)

from src.logic.osrm import OSRMClient
from src.logic.optimization import run_optimization_model

def construct_df_compat(df_ofertas, df_armazens):
    """
    Constructs an in-memory compatibility DataFrame:
    Products (rows) x Warehouse Types (columns).
    Fills all cells with '☑' indicating full compatibility.
    """
    products = df_ofertas['Produto'].unique().tolist()

    # Using 'Tipo do Armazém' from demand dataset
    # If not present, fallback to a default type
    type_col = next((c for c in df_armazens.columns if 'tipo' in str(c).lower()), None)

    if type_col and not df_armazens[type_col].empty:
        warehouse_types = df_armazens[type_col].dropna().unique().tolist()
    else:
        warehouse_types = ["Armazém Convencional", "Silo"]

    # Initialize the DataFrame
    data = {wt: ['☑'] * len(products) for wt in warehouse_types}
    df_compat = pd.DataFrame(data)
    df_compat.insert(0, "Produto", products)

    return df_compat

def build_distance_matrix(df_ofertas, df_armazens):
    """
    Uses the OSRM client to construct the distance matrix expected by the model.
    """
    client = OSRMClient(base_url="http://localhost:5000")

    # Process Supply Origins (Cidade + Lat + Lon)
    # Deduplicate origins exactly like the model does
    origins_df = df_ofertas[['Cidade', 'Latitude', 'Longitude']].drop_duplicates().dropna()
    city_counts = origins_df['Cidade'].value_counts()
    duplicates = city_counts[city_counts > 1].index

    def rename_city(row):
        if row['Cidade'] in duplicates:
            return f"{row['Cidade']} ({row['Latitude']:.4f}, {row['Longitude']:.4f})"
        return row['Cidade']

    origins_df['Cidade'] = origins_df.apply(rename_city, axis=1)

    origins_coords = list(zip(origins_df['Latitude'], origins_df['Longitude']))
    origins_names = origins_df['Cidade'].tolist()

    # Process Demand Destinations (CDA - Armazem - Municipio)
    cda_col = next((c for c in df_armazens.columns if 'cda' in str(c).lower()), None)
    name_col = next((c for c in df_armazens.columns if 'armaz' in str(c).lower() or 'nome' in str(c).lower()), None)
    mun_col = next((c for c in df_armazens.columns if 'munic' in str(c).lower()), None)
    lat_col_dest = next((c for c in df_armazens.columns if 'lat' in str(c).lower()), None)
    lon_col_dest = next((c for c in df_armazens.columns if 'long' in str(c).lower()), None)

    destinations_coords = []
    destinations_names = []

    for idx, row in df_armazens.iterrows():
        # Coordinates
        lat = row[lat_col_dest] if lat_col_dest else None
        lon = row[lon_col_dest] if lon_col_dest else None

        # If coordinates are missing, fallback to 0.0 (simulating fallback straight lines)
        if pd.isna(lat) or pd.isna(lon):
            lat, lon = 0.0, 0.0

        destinations_coords.append((float(lat), float(lon)))

        # Naming format expected by distance matrix processing
        parts = []
        if cda_col and pd.notna(row[cda_col]):
            parts.append(str(row[cda_col]).strip())
        if name_col and pd.notna(row[name_col]):
            parts.append(str(row[name_col]).strip())
        if mun_col and pd.notna(row[mun_col]):
            parts.append(str(row[mun_col]).strip())

        dest_name_full = " - ".join(parts) if parts else f"Dest {idx}"
        destinations_names.append(dest_name_full)

    # Time and generate the matrix using OSRMClient
    start_time = time.time()
    matrix_data = client.get_distance_matrix(origins_coords, destinations_coords)
    matrix_time = time.time() - start_time

    # Construct the final DataFrame
    # Columns: Origem, Dest1, Dest2...
    df_dist = pd.DataFrame(matrix_data, columns=destinations_names)

    # Convert meters to km
    # OSRM output is typically in meters, the model expects km
    df_dist = df_dist / 1000.0

    df_dist.insert(0, 'Origem', origins_names)

    return df_dist, matrix_time

def main():
    print("Starting Benchmark Execution...")

    # Load Cost Datasets
    try:
        df_storage = pd.read_csv(TARIFA_CSV)
        df_freight = pd.read_csv(FRETE_CSV, sep=';', encoding='latin1')
    except Exception as e:
        print(f"Error loading cost datasets: {e}")
        return

    results = []

    for idx, (df_supply, df_demand) in enumerate(generate_test_pairs()):
        num_supply_nodes = len(df_supply)
        num_demand_nodes = len(df_demand)

        print(f"\n--- Iteration {idx + 1} ---")
        print(f"Supply Nodes: {num_supply_nodes} | Demand Nodes: {num_demand_nodes}")

        # Construct dynamic matrices
        df_compat = construct_df_compat(df_supply, df_demand)
        df_dist, df_dist_time = build_distance_matrix(df_supply, df_demand)

        # Run model
        try:
            log_filename, results_dict = run_optimization_model(
                df_supply=df_supply,
                df_demand=df_demand,
                df_compat=df_compat,
                df_dist=df_dist,
                df_freight=df_freight,
                df_storage=df_storage,
                detailed_log=False,
                toggle_pareto=TOGGLE_PARETO,
                toggle_min_max_capacity=TOGGLE_MIN_MAX_CAPACITY,
                input_min_load=INPUT_MIN_LOAD,
                input_max_load=INPUT_MAX_LOAD,
                toggle_use_reception=TOGGLE_USE_RECEPTION,
                input_allocation_days=INPUT_ALLOCATION_DAYS,
                input_min_freight=INPUT_MIN_FREIGHT,
                input_max_freight=INPUT_MAX_FREIGHT,
                lang="pt"
            )

            # Extract metrics
            execution_time = results_dict.get("kpis", {}).get("execution_time", 0.0)
            optimal_value = results_dict.get("objective", 0.0)
            status = results_dict.get("status", "unknown")

            print(f"Model Status: {status}")
            print(f"Distance Matrix Time: {df_dist_time:.2f}s")
            print(f"Resolution Time: {execution_time:.2f}s")
            print(f"Optimal Value: {optimal_value:.2f}")

            results.append({
                "Number of Supply Nodes": num_supply_nodes,
                "Number of Demand Nodes": num_demand_nodes,
                "Distance Matrix Time (seconds)": df_dist_time,
                "Resolution Time (seconds)": execution_time,
                "Optimal Value": optimal_value
            })

        except Exception as e:
            print(f"Error during optimization run: {e}")
            import traceback
            traceback.print_exc()


    # Export Results
    if results:
        df_results = pd.DataFrame(results)
        output_file = os.path.join(PROJECT_ROOT, "benchmark_results.xlsx")
        try:
            df_results.to_excel(output_file, index=False)
            print(f"\nBenchmark results successfully exported to {output_file}")
        except Exception as e:
            print(f"Failed to export results: {e}")
    else:
        print("No results to export.")

if __name__ == "__main__":
    main()
