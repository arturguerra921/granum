import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd
import sys
import io
import tempfile
import os

import time

def run_optimization_model(df_supply, df_demand, df_compat, df_dist, df_freight, df_storage, detailed_log=False,
                           toggle_min_max_capacity=False, input_carga_min=None, input_carga_max=None,
                           toggle_use_recepcao=False, input_dias_alocacao=None, input_frete_min=None, input_frete_max=None):
    """
    Roda o modelo matemático de otimização linear para alocação de produtos.
    """
    # Início do cronômetro para medir o tempo total desde a chamada até a solução
    start_time = time.time()

    # 1. Preparação dos dados

    # Oferta (Supply)
    # Primeiro, aplicar a mesma lógica de desduplicação para garantir que os nomes em df_supply combinem com df_dist
    if 'Latitude' in df_supply.columns and 'Longitude' in df_supply.columns:
        origins_df = df_supply[['Cidade', 'Latitude', 'Longitude']].drop_duplicates().dropna()
        city_counts = origins_df['Cidade'].value_counts()
        duplicates = city_counts[city_counts > 1].index

        def rename_city(row):
            if row['Cidade'] in duplicates:
                return f"{row['Cidade']} ({row['Latitude']:.4f}, {row['Longitude']:.4f})"
            return row['Cidade']

        df_supply['Cidade'] = df_supply.apply(rename_city, axis=1)

    # Group by Cidade and Produto, sum over Peso (ton)
    supply = df_supply.groupby(['Cidade', 'Produto'])['Peso (ton)'].sum().to_dict()

    # Demanda (Demand) - Usando Capacidade em toneladas do Armazém (nó destino)
    # Identify the capacity column correctly. Often it is "Capacidade Estática (t)" or similar.
    cap_col = next((c for c in df_demand.columns if 'cap' in str(c).lower() or 'ton' in str(c).lower()), None)
    estoque_col = next((c for c in df_demand.columns if 'estoque' in str(c).lower()), None)

    # Identify Public/Private warehouse.
    armazenador_col = next((c for c in df_demand.columns if 'armazenador' in str(c).lower()), None)
    name_col = next((c for c in df_demand.columns if 'armaz' in str(c).lower() or 'nome' in str(c).lower()), None)
    mun_col_dest = next((c for c in df_demand.columns if 'munic' in str(c).lower()), None)
    cda_col = next((c for c in df_demand.columns if 'cda' in str(c).lower()), None)
    reception_col = next((c for c in df_demand.columns if 'recep' in str(c).lower() or 'receb' in str(c).lower()), None)

    # Dicionários separados para capacidade total e estoque inicial
    demand_total_capacity = {}
    demand_initial_inventory = {}
    demand_reception_capacity = {}
    is_public = {}

    # Store the mapping from CDA back to full formatted name for the final output
    cda_to_name = {}

    for idx, row in df_demand.iterrows():
        # Retrieve the CDA string
        if cda_col and pd.notna(row[cda_col]):
            cda = str(row[cda_col]).strip()
        else:
            cda = f"Dest {idx}"

        # Match the exact naming convention used in the distance matrix view (CDA - Armazem - Municipio)
        parts = []
        if cda_col and pd.notna(row[cda_col]):
            parts.append(str(row[cda_col]).strip())
        if name_col and pd.notna(row[name_col]):
            parts.append(str(row[name_col]).strip())
        if mun_col_dest and pd.notna(row[mun_col_dest]):
            parts.append(str(row[mun_col_dest]).strip())

        if parts:
            dest_name_full = " - ".join(parts)
        else:
            dest_name_full = f"Dest {idx}"

        cda_to_name[cda] = dest_name_full

        # Parse capacity correctly (cleaning Brazilian number formats)
        try:
            val_str = str(row[cap_col]).replace('.', '').replace(',', '.')
            cap = float(val_str)
        except:
            cap = 0.0

        # Parse initial stock correctly
        try:
            est_str = str(row[estoque_col]).replace('.', '').replace(',', '.')
            estoque = float(est_str)
        except:
            estoque = 0.0

        # Parse reception capacity correctly
        try:
            if reception_col and pd.notna(row[reception_col]):
                rec_str = str(row[reception_col]).replace('.', '').replace(',', '.')
                recepcao = float(rec_str)
            else:
                recepcao = 0.0
        except:
            recepcao = 0.0

        # Agora mantemos capacidade, estoque e recepção separados
        demand_total_capacity[cda] = cap
        demand_initial_inventory[cda] = estoque
        demand_reception_capacity[cda] = recepcao

        # Determine if public or private
        if armazenador_col and str(row[armazenador_col]).upper() == "COMPANHIA NACIONAL DE ABASTECIMENTO":
            is_public[cda] = True
        else:
            is_public[cda] = False

    # Compatibilidade (Produto x Armazém)
    # A matriz df_compat tem produtos nas linhas ('Produto') e colunas para cada tipo de armazém.
    # Mas precisamos relacionar cada "Destino" (armazém) com o "Produto" baseado no "Tipo" do armazém.
    # Vamos criar um dicionário de compatibilidade: (produto, dest_name) -> bool

    # Identificar coluna de tipo no df_demand
    tipo_col = next((c for c in df_demand.columns if 'tipo' in str(c).lower()), None)

    # Construir dicionário de permissões do df_compat
    # df_compat tem 'Produto' e colunas com os Tipos de armazém, valores '☑' ou '☐'
    compat_dict = {}
    if not df_compat.empty:
        for _, row in df_compat.iterrows():
            prod = row['Produto']
            for t in df_compat.columns:
                if t != 'Produto':
                    # True se aceita
                    compat_dict[(prod, t)] = (row[t] == '☑')

    # Agora associar produto x destino
    prod_dest_compat = {}
    all_products = df_supply['Produto'].unique().tolist()

    for prod in all_products:
        for idx, row in df_demand.iterrows():
            if cda_col and pd.notna(row[cda_col]):
                cda = str(row[cda_col]).strip()
            else:
                cda = f"Dest {idx}"

            tipo_armazem = row[tipo_col] if tipo_col else None

            # Se não temos informação de tipo, assumimos que aceita (ou podemos rejeitar, mas assumir True é mais seguro se falhar)
            if tipo_armazem and (prod, tipo_armazem) in compat_dict:
                prod_dest_compat[(prod, cda)] = compat_dict[(prod, tipo_armazem)]
            else:
                prod_dest_compat[(prod, cda)] = True # Default fallback

    # Matriz de Distâncias
    # df_dist tem 'Origem' e colunas com 'CDA - Armazem - Municipio' ...
    distance = {}
    for _, row in df_dist.iterrows():
        orig = row['Origem']
        for col in df_dist.columns:
            if col != 'Origem':
                dest_full_name = col
                # Retrieve the CDA from the first part of the column name
                # format: "CDA - Armazem - Municipio" -> split by " - " -> get [0]
                cda = dest_full_name.split(' - ')[0].strip() if ' - ' in str(dest_full_name) else str(dest_full_name).strip()

                try:
                    distance[(orig, cda)] = float(row[col])
                except:
                    # Se for "N/A" ou falhar
                    pass

    # Custos de Frete (Valor_Tonelada_km)
    # Precisamos do custo para cada origem. Vamos usar a média ou por estado.
    # df_freight tem 'Estado' e 'Frete Tonelada Km'.
    # Para simplificar, vamos pegar a média geral se não soubermos o estado da origem,
    # ou podemos tentar extrair o estado do nome da cidade (Ex: "Brasília - DF").

    # Parse Brazilian numbers for freight
    try:
        df_freight['Frete_Num'] = df_freight['Frete Tonelada Km'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
        freight_dict = df_freight.set_index('Estado')['Frete_Num'].to_dict()
        avg_freight = df_freight['Frete_Num'].mean()
    except:
        freight_dict = {}
        avg_freight = 0.3 # default fallback

    freight_cost = {}
    for orig in df_supply['Cidade'].unique():
        # Tentativa de extrair UF
        uf = str(orig).split('-')[-1].strip() if '-' in str(orig) else None
        if uf in freight_dict:
            freight_cost[orig] = freight_dict[uf]
        else:
            freight_cost[orig] = avg_freight

    # Tarifas de Armazenagem
    # df_storage tem 'Produto', 'Armazenar_Publico', 'Armazenar_Privado'
    storage_cost = {}
    try:
        import unicodedata
        def normalize_str(s):
            if pd.isna(s):
                return ""
            s_str = str(s).strip()
            s_nfkd = unicodedata.normalize('NFKD', s_str)
            s_ascii = s_nfkd.encode('ASCII', 'ignore').decode('utf-8')
            return s_ascii.lower()

        df_storage['Pub'] = df_storage['Armazenar_Publico'].astype(str).str.replace('.', '').str.replace(',', '.').astype(float)
        df_storage['Priv'] = df_storage['Armazenar_Privado'].astype(str).str.replace('.', '').str.replace(',', '.').astype(float)
        df_storage['Prod_Norm'] = df_storage['Produto'].apply(normalize_str)

        # Build lookup dictionaries
        pub_dict = df_storage.set_index('Prod_Norm')['Pub'].to_dict()
        priv_dict = df_storage.set_index('Prod_Norm')['Priv'].to_dict()

        # Try to find "outros" as fallback, otherwise use 50.0
        fallback_pub = pub_dict.get('outros', 50.0)
        fallback_priv = priv_dict.get('outros', 50.0)

        for prod in all_products:
            prod_norm = normalize_str(prod)
            pub_val = pub_dict.get(prod_norm, fallback_pub)
            priv_val = priv_dict.get(prod_norm, fallback_priv)

            for dest in demand_total_capacity.keys():
                if is_public.get(dest, False):
                    storage_cost[(dest, prod)] = pub_val
                else:
                    storage_cost[(dest, prod)] = priv_val

    except Exception as e:
        print(f"Erro ao processar tarifas de armazenagem: {e}")
        # Default fallback
        for prod in all_products:
            for dest in demand_total_capacity.keys():
                storage_cost[(dest, prod)] = 50.0


    # 2. Despacho: LP ou MILP

    use_milp = False
    if toggle_min_max_capacity:
        if (input_carga_min is not None and str(input_carga_min).strip() != "") or \
           (input_carga_max is not None and str(input_carga_max).strip() != "") or \
           (input_frete_min is not None and str(input_frete_min).strip() != "") or \
           (input_frete_max is not None and str(input_frete_max).strip() != "") or \
           toggle_use_recepcao:
            use_milp = True

    if use_milp:
        return _run_milp_optimization_model(
            start_time=start_time,
            supply=supply, demand_total_capacity=demand_total_capacity,
            demand_initial_inventory=demand_initial_inventory,
            demand_reception_capacity=demand_reception_capacity,
            is_public=is_public, cda_to_name=cda_to_name,
            prod_dest_compat=prod_dest_compat, distance=distance,
            freight_cost=freight_cost, storage_cost=storage_cost, avg_freight=avg_freight,
            all_products=all_products, origins_list=df_supply['Cidade'].unique().tolist(),
            detailed_log=detailed_log,
            input_carga_min=input_carga_min, input_carga_max=input_carga_max,
            toggle_use_recepcao=toggle_use_recepcao, input_dias_alocacao=input_dias_alocacao,
            input_frete_min=input_frete_min, input_frete_max=input_frete_max
        )

    # 2. Construção do Modelo Pyomo (LP Original)

    # Redirecionar output diretamente para um arquivo temporário no disco (para evitar Out of Memory)
    old_stdout = sys.stdout

    log_dir = os.path.join(tempfile.gettempdir(), 'granum_logs')
    os.makedirs(log_dir, exist_ok=True)

    # Limpar arquivos antigos para não estourar o disco

    now = time.time()
    for filename in os.listdir(log_dir):
        filepath = os.path.join(log_dir, filename)
        if os.path.isfile(filepath):
            # Deleta arquivos criados há mais de 1 hora
            if os.stat(filepath).st_mtime < now - 3600:
                try:
                    os.remove(filepath)
                except Exception:
                    pass

    log_fd, log_path = tempfile.mkstemp(suffix='.txt', prefix='optimization_log_', dir=log_dir)
    log_filename = os.path.basename(log_path)
    new_stdout = os.fdopen(log_fd, 'w', encoding='utf-8')
    sys.stdout = new_stdout

    # Variables to hold structured results
    results_dict = {
        "status": "error",
        "objective": 0.0,
        "routes": [],
        "kpis": {
            "total_tons": 0.0,
            "total_km": 0.0,
            "total_freight_cost": 0.0,
            "total_storage_cost": 0.0,
            "execution_time": 0.0
        },
        "warnings": {
            "capacity": [],
            "unallocated": [],
            "general": []
        }
    }

    try:
        print("Iniciando a construção do modelo matemático...")
        model = pyo.ConcreteModel(name="Alocacao_Armazens")

        # =========================================================================
        # 2.1 CONJUNTOS (SETS)
        # =========================================================================
        # Definem os índices sobre os quais o modelo irá operar.

        model.Origins = pyo.Set(initialize=df_supply['Cidade'].unique().tolist(), doc="Cidades de Origem da Oferta")
        model.Destinations = pyo.Set(initialize=list(demand_total_capacity.keys()), doc="Armazéns de Destino")
        model.Products = pyo.Set(initialize=all_products, doc="Tipos de Produtos")

        # [BOA PRÁTICA DE PERFORMANCE]
        # Pré-filtramos as rotas válidas no Python antes de criar as variáveis de decisão.
        # Isso evita a "explosão combinatória" de variáveis vazias no solver, melhorando
        # significativamente o uso de memória e a velocidade da otimização.
        valid_routes = []
        for o in model.Origins:
            for d in model.Destinations:
                for p in model.Products:
                    if (o, d) in distance and prod_dest_compat.get((p, d), False):
                        valid_routes.append((o, d, p))

        print(f"Total de combinações (Origem x Destino x Produto) válidas: {len(valid_routes)}")
        model.ValidRoutes = pyo.Set(initialize=valid_routes, dimen=3, doc="Rotas Válidas (Origem, Destino, Produto)")

        # =========================================================================
        # 2.2 PARÂMETROS (PARAMETERS)
        # =========================================================================
        # Valores fixos conhecidos fornecidos como dados de entrada para o modelo.

        # --- Parâmetros de Oferta e Demanda ---
        def supply_init(model, o, p):
            return supply.get((o, p), 0.0)
        model.Supply = pyo.Param(model.Origins, model.Products, initialize=supply_init, doc="Oferta disponível por (Origem, Produto)")

        def total_capacity_init(model, d):
            return demand_total_capacity.get(d, 0.0)
        model.TotalCapacity = pyo.Param(model.Destinations, initialize=total_capacity_init, doc="Capacidade estática total do armazém (ton)")

        def initial_inventory_init(model, d):
            return demand_initial_inventory.get(d, 0.0)
        model.InitialInventory = pyo.Param(model.Destinations, initialize=initial_inventory_init, doc="Estoque inicial presente no armazém (ton)")

        # --- Parâmetros de Custos e Distâncias ---
        def dist_init(model, o, d):
            return distance.get((o, d), 999999.0)
        model.Distance = pyo.Param(model.Origins, model.Destinations, initialize=dist_init, doc="Distância entre Origem e Destino (km)")

        def freight_init(model, o):
            return freight_cost.get(o, avg_freight)
        model.Freight = pyo.Param(model.Origins, initialize=freight_init, doc="Custo unitário de frete (R$/ton-km) a partir da Origem")

        def storage_init(model, d, p):
            return storage_cost.get((d, p), 50.0)
        model.Storage = pyo.Param(model.Destinations, model.Products, initialize=storage_init, doc="Tarifa de armazenagem no Destino para o Produto (R$/ton)")

        # --- Parâmetros de Penalização (Big M) ---
        # Calculamos um Big M dinâmico baseado nos custos máximos do sistema
        max_freight = max(freight_cost.values()) if freight_cost else 0.0
        max_dist = max(distance.values()) if distance else 0.0
        max_storage = max(storage_cost.values()) if storage_cost else 0.0

        # Big M da Capacidade: ordens de grandeza maior que o custo de transportar e armazenar
        val_big_m_cap = (max_freight * max_dist + max_storage) * 1000
        if val_big_m_cap == 0:
            val_big_m_cap = 10000

        # Big M de Não Alocação: deve ser ainda mais alto que a falta de capacidade, forçando a alocação sempre que possível
        val_big_m_unalloc = val_big_m_cap * 10

        print(f"Valor dinâmico para Big_M (Capacidade Artificial): {val_big_m_cap:.2e}")
        print(f"Valor dinâmico para Big_M (Oferta Não Alocada): {val_big_m_unalloc:.2e}")

        model.BigMCapacity = pyo.Param(initialize=val_big_m_cap, doc="Custo de penalização por tonelada de capacidade artificial")
        model.BigMUnallocated = pyo.Param(initialize=val_big_m_unalloc, doc="Custo de penalização por tonelada de oferta não alocada")

        # =========================================================================
        # 2.3 VARIÁVEIS DE DECISÃO (VARIABLES)
        # =========================================================================
        # Valores que o solver tentará determinar para otimizar o resultado.

        # Fluxo de produto (quantidade a ser transportada) em toneladas
        model.Flow = pyo.Var(model.ValidRoutes, domain=pyo.NonNegativeReals, doc="Quantidade transportada (o, d, p)")

        # Variáveis de folga (Dummies) para garantir viabilidade matemática do modelo
        model.DummyCapacity = pyo.Var(model.Destinations, domain=pyo.NonNegativeReals, doc="Capacidade extra artificial alocada (ton)")
        model.DummyUnallocated = pyo.Var(model.Origins, model.Products, domain=pyo.NonNegativeReals, doc="Oferta não alocada a nenhum destino (ton)")

        # =========================================================================
        # 2.4 FUNÇÃO OBJETIVO (OBJECTIVE)
        # =========================================================================
        # Expressão matemática a ser minimizada (Minimizar Custos).

        def objective_rule(model):
            # Custo normal do sistema = (Custo de Frete) + (Custo de Armazenagem)
            normal_costs = sum(
                (model.Flow[o, d, p] * model.Distance[o, d] * model.Freight[o]) +
                (model.Flow[o, d, p] * model.Storage[d, p])
                for (o, d, p) in model.ValidRoutes
            )

            # Custo de penalização por violar restrições lógicas
            dummy_capacity_costs = sum(model.DummyCapacity[d] * model.BigMCapacity for d in model.Destinations)
            dummy_unallocated_costs = sum(model.DummyUnallocated[o, p] * model.BigMUnallocated for o in model.Origins for p in model.Products)

            return normal_costs + dummy_capacity_costs + dummy_unallocated_costs

        model.Objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize, doc="Minimização dos Custos Totais")

        # =========================================================================
        # 2.5 RESTRIÇÕES (CONSTRAINTS)
        # =========================================================================
        # Regras que as variáveis de decisão devem obedecer obrigatoriamente.

        # Restrição 1: Conservação de Fluxo (Limite de Oferta)
        # A oferta total disponível em uma origem para um produto DEVE ser escoada,
        # seja via alocação real (Flow) ou via folga (DummyUnallocated).
        def supply_rule(model, o, p):
            if model.Supply[o, p] <= 0:
                return pyo.Constraint.Skip

            valid_dests = [d for d in model.Destinations if (o, d, p) in model.ValidRoutes]
            if not valid_dests:
                # Não existem rotas válidas, toda a oferta vai para a variável dummy
                return model.DummyUnallocated[o, p] == model.Supply[o, p]

            flow_sum = sum(model.Flow[o, d, p] for d in valid_dests)
            return flow_sum + model.DummyUnallocated[o, p] == model.Supply[o, p]

        model.SupplyConstraint = pyo.Constraint(model.Origins, model.Products, rule=supply_rule, doc="Restrição de Limite de Oferta")

        # Restrição 2: Limite de Capacidade dos Armazéns
        # A quantidade total que chega a um destino não pode ultrapassar sua capacidade disponível real.
        # Capacidade Disponível = (Capacidade Total - Estoque Inicial)
        # Caso o solver não tenha alternativa, usará a DummyCapacity pagando a penalização.
        def capacity_rule(model, d):
            valid_ops = [(o, p) for o in model.Origins for p in model.Products if (o, d, p) in model.ValidRoutes]
            if not valid_ops:
                return pyo.Constraint.Skip

            flow_sum = sum(model.Flow[o, d, p] for (o, p) in valid_ops)

            # Tratamento para evitar capacidade efetiva negativa caso estoque inicial > total
            # Extraindo o valor numérico para permitir a verificação booleana
            effective_cap = max(0.0, pyo.value(model.TotalCapacity[d]) - pyo.value(model.InitialInventory[d]))

            if effective_cap > 0:
                return flow_sum <= (model.TotalCapacity[d] - model.InitialInventory[d]) + model.DummyCapacity[d]
            else:
                # Se efetivamente não há capacidade, o armazém só pode receber carga gerando Dummy
                return flow_sum <= model.DummyCapacity[d]

        model.CapacityConstraint = pyo.Constraint(model.Destinations, rule=capacity_rule, doc="Restrição de Limite de Capacidade Efetiva")

        #Mostrar o modelo para debug apenas se solicitado pelo usuário
        if detailed_log:
            model.pprint()

        # 3. Solucionar o modelo
        print("\nChamando solver CBC...")
        solver = SolverFactory('cbc')
        # Limite de tempo para não travar infinitamente
        solver.options['sec'] = 600

        results = solver.solve(model, tee=True)

        print("\n=== STATUS DA OTIMIZAÇÃO ===")
        print(f"Status do Solver: {results.solver.status}")
        print(f"Condição de Término: {results.solver.termination_condition}")

        if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition == pyo.TerminationCondition.optimal:
            print(f"Solução Ótima Encontrada!")

            objective_value = pyo.value(model.Objective)
            print(f"Custo Total (Função Objetivo): R$ {objective_value:,.2f}")

            results_dict["status"] = "optimal"
            results_dict["objective"] = objective_value

            print("\n--- DETALHES DO FLUXO (Alocação) ---")
            total_transported = 0
            total_km = 0.0
            total_freight_cost = 0.0
            total_storage_cost = 0.0

            for (o, d, p) in model.ValidRoutes:
                val = pyo.value(model.Flow[o, d, p])
                if val > 0.001:  # ignore floating point zeros
                    d_name = cda_to_name.get(d, d)
                    dist = pyo.value(model.Distance[o, d])
                    f_cost = pyo.value(model.Freight[o])
                    s_cost = pyo.value(model.Storage[d, p])

                    route_freight = val * dist * f_cost
                    route_storage = val * s_cost
                    route_total = route_freight + route_storage

                    print(f"De: {o} | Para: {d_name} | Produto: {p} | Qtd: {val:.2f} ton")

                    results_dict["routes"].append({
                        "Origem": o,
                        "Destino": d_name,
                        "Produto": p,
                        "Quantidade (ton)": val,
                        "Distancia (km)": dist,
                        "Custo Frete (R$)": route_freight,
                        "Custo Armazenagem (R$)": route_storage,
                        "Custo Total (R$)": route_total,
                        "Custo Frete Unitario (R$/ton-km)": f_cost,
                        "Custo Armaz. Unitario (R$/ton)": s_cost
                    })

                    total_transported += val
                    total_km += dist
                    total_freight_cost += route_freight
                    total_storage_cost += route_storage

            print(f"\nTotal de produtos alocados: {total_transported:.2f} toneladas")

            results_dict["kpis"]["total_tons"] = total_transported
            results_dict["kpis"]["total_km"] = total_km
            results_dict["kpis"]["total_freight_cost"] = total_freight_cost
            results_dict["kpis"]["total_storage_cost"] = total_storage_cost

            # Verificar uso das variáveis Dummies
            dummy_cap_used = False
            print("\n--- AVISOS: CAPACIDADE ARTIFICIAL (DUMMIES) ---")
            for d in model.Destinations:
                d_val = pyo.value(model.DummyCapacity[d])
                if d_val > 0.001:
                    dummy_cap_used = True
                    d_name = cda_to_name.get(d, d)
                    msg = f"O Armazém '{d_name}' precisou de capacidade de armazenamento artificial de {d_val:.2f} toneladas."
                    print(f"ALERTA: {msg}")
                    results_dict["warnings"]["capacity"].append(msg)

            if not dummy_cap_used:
                print("Nenhuma capacidade artificial foi necessária. O modelo encontrou solução com as capacidades reais.")

            dummy_unalloc_used = False
            print("\n--- AVISOS: OFERTA SEM ROTAS / NÃO ALOCADA (DUMMIES) ---")
            for o in model.Origins:
                for p in model.Products:
                    u_val = pyo.value(model.DummyUnallocated[o, p])
                    if u_val > 0.001:
                        dummy_unalloc_used = True
                        msg = f"A origem '{o}' possui oferta de '{p}' não alocada: {u_val:.2f} toneladas."
                        print(f"ALERTA: {msg}")
                        results_dict["warnings"]["unallocated"].append(msg)

            if not dummy_unalloc_used:
                print("Toda a oferta conseguiu ser escoada em rotas válidas para algum destino.")

            if dummy_cap_used or dummy_unalloc_used:
                print(f"\nNota: Foram utilizadas variáveis dummies com custo elevado para impedir que o modelo falhasse por inviabilidade.")
                print(f"Custo de Capacidade Artificial (Big M) = {pyo.value(model.BigMCapacity):.2e}")
                print(f"Custo de Oferta Não Alocada (Big M) = {pyo.value(model.BigMUnallocated):.2e}")

        else:
            print("Não foi possível encontrar uma solução ótima. O modelo pode estar mal-condicionado.")
            results_dict["status"] = "infeasible"
            results_dict["warnings"]["general"].append("O modelo não encontrou solução ótima.")

    except Exception as e:
        print(f"\nERRO DURANTE A OTIMIZAÇÃO: {str(e)}")
        results_dict["status"] = "error"
        results_dict["warnings"]["general"].append(f"Erro: {str(e)}")
        import traceback
        # print_exc defaults to sys.stderr. Let's print formatting to sys.stdout
        # so it gets caught in our buffer!
        print(traceback.format_exc())

    finally:
        # Registrar tempo total e imprimir no log
        end_time = time.time()
        total_time_seconds = end_time - start_time
        print(f"\nTempo de execução: {total_time_seconds:.2f} segundos.")

        # Adiciona o tempo ao dicionário de resultados
        results_dict["kpis"]["execution_time"] = total_time_seconds

        # Fechar o arquivo temporário de log e restaurar stdout
        new_stdout.close()
        sys.stdout = old_stdout

    # Retornar o nome do arquivo de log salvo e os dados estruturados
    return log_filename, results_dict

def _run_milp_optimization_model(start_time, supply, demand_total_capacity, demand_initial_inventory,
                                 demand_reception_capacity, is_public, cda_to_name,
                                 prod_dest_compat, distance, freight_cost, storage_cost, avg_freight,
                                 all_products, origins_list, detailed_log,
                                 input_carga_min, input_carga_max, toggle_use_recepcao,
                                 input_dias_alocacao, input_frete_min, input_frete_max):
    """
    Versão MILP do modelo, inclui restrições extras e variáveis binárias (RouteActive).
    """

    # Calculate days multiplier
    try:
        days = float(input_dias_alocacao) if input_dias_alocacao else 1.0
    except:
        days = 1.0

    # Parse numeric limits
    def parse_float(val):
        if val is None or str(val).strip() == "":
            return None
        try:
            return float(val)
        except:
            return None

    carga_min = parse_float(input_carga_min)
    carga_max = parse_float(input_carga_max)
    frete_min = parse_float(input_frete_min)
    frete_max = parse_float(input_frete_max)

    # Redirecionar output
    old_stdout = sys.stdout
    log_dir = os.path.join(tempfile.gettempdir(), 'granum_logs')
    os.makedirs(log_dir, exist_ok=True)

    now = time.time()
    for filename in os.listdir(log_dir):
        filepath = os.path.join(log_dir, filename)
        if os.path.isfile(filepath):
            if os.stat(filepath).st_mtime < now - 3600:
                try:
                    os.remove(filepath)
                except Exception:
                    pass

    log_fd, log_path = tempfile.mkstemp(suffix='.txt', prefix='optimization_log_milp_', dir=log_dir)
    log_filename = os.path.basename(log_path)
    new_stdout = os.fdopen(log_fd, 'w', encoding='utf-8')
    sys.stdout = new_stdout

    results_dict = {
        "status": "error",
        "objective": 0.0,
        "routes": [],
        "kpis": {
            "total_tons": 0.0,
            "total_km": 0.0,
            "total_freight_cost": 0.0,
            "total_storage_cost": 0.0,
            "execution_time": 0.0
        },
        "warnings": {
            "capacity": [],
            "unallocated": [],
            "general": []
        }
    }

    try:
        print("Iniciando a construção do modelo matemático (MILP com restrições de limite)...")
        model = pyo.ConcreteModel(name="Alocacao_Armazens_MILP")

        # =========================================================================
        # 3.1 CONJUNTOS (SETS)
        # =========================================================================
        # Definem os índices sobre os quais o modelo irá operar.
        model.Origins = pyo.Set(initialize=origins_list, doc="Cidades de Origem da Oferta")
        model.Destinations = pyo.Set(initialize=list(demand_total_capacity.keys()), doc="Armazéns de Destino")
        model.Products = pyo.Set(initialize=all_products, doc="Tipos de Produtos")

        valid_routes = []
        for o in model.Origins:
            for d in model.Destinations:
                for p in model.Products:
                    if (o, d) in distance and prod_dest_compat.get((p, d), False):
                        valid_routes.append((o, d, p))

        print(f"Total de combinações (Origem x Destino x Produto) válidas: {len(valid_routes)}")
        model.ValidRoutes = pyo.Set(initialize=valid_routes, dimen=3, doc="Rotas Válidas (Origem, Destino, Produto)")

        # =========================================================================
        # 3.2 PARÂMETROS (PARAMETERS)
        # =========================================================================
        # Valores fixos conhecidos fornecidos como dados de entrada para o modelo.

        # --- Parâmetros de Constantes e Limites Logísticos ---
        model.days = pyo.Param(initialize=days, within=pyo.Any, doc="Dias de alocação")
        model.freight_min = pyo.Param(initialize=frete_min, within=pyo.Any, doc="Carga mínima de frete por rota")
        model.freight_max = pyo.Param(initialize=frete_max, within=pyo.Any, doc="Carga máxima de frete por rota")

        def reception_min_init(model, d):
            return carga_min
        model.reception_min = pyo.Param(model.Destinations, initialize=reception_min_init, within=pyo.Any, doc="Carga mínima diária de recepção")

        def reception_max_init(model, d):
            if toggle_use_recepcao:
                return demand_reception_capacity.get(d, 0.0)
            elif carga_max is not None:
                return carga_max
            return None

        model.reception_max = pyo.Param(model.Destinations, initialize=reception_max_init, within=pyo.Any, doc="Carga máxima diária de recepção ou capacidade do banco")


        # --- Parâmetros de Oferta e Demanda ---
        def supply_init(model, o, p):
            return supply.get((o, p), 0.0)
        model.Supply = pyo.Param(model.Origins, model.Products, initialize=supply_init, doc="Oferta disponível por (Origem, Produto)")

        def total_capacity_init(model, d):
            return demand_total_capacity.get(d, 0.0)
        model.TotalCapacity = pyo.Param(model.Destinations, initialize=total_capacity_init, doc="Capacidade estática total do armazém (ton)")

        def initial_inventory_init(model, d):
            return demand_initial_inventory.get(d, 0.0)
        model.InitialInventory = pyo.Param(model.Destinations, initialize=initial_inventory_init, doc="Estoque inicial presente no armazém (ton)")

        # --- Parâmetros de Custos e Distâncias ---
        def dist_init(model, o, d):
            return distance.get((o, d), 999999.0)
        model.Distance = pyo.Param(model.Origins, model.Destinations, initialize=dist_init, doc="Distância entre Origem e Destino (km)")

        def freight_init(model, o):
            return freight_cost.get(o, avg_freight)
        model.Freight = pyo.Param(model.Origins, initialize=freight_init, doc="Custo unitário de frete (R$/ton-km) a partir da Origem")

        def storage_init(model, d, p):
            return storage_cost.get((d, p), 50.0)
        model.Storage = pyo.Param(model.Destinations, model.Products, initialize=storage_init, doc="Tarifa de armazenagem no Destino para o Produto (R$/ton)")

        max_freight = max(freight_cost.values()) if freight_cost else 0.0
        max_dist = max(distance.values()) if distance else 0.0
        max_storage = max(storage_cost.values()) if storage_cost else 0.0

        val_big_m_cap = (max_freight * max_dist + max_storage) * 1000
        if val_big_m_cap == 0:
            val_big_m_cap = 10000

        val_big_m_unalloc = val_big_m_cap * 10

        # --- Parâmetros de Penalização (Big M) ---
        model.BigMCapacity = pyo.Param(initialize=val_big_m_cap, doc="Custo de penalização por tonelada de capacidade artificial")
        model.BigMUnallocated = pyo.Param(initialize=val_big_m_unalloc, doc="Custo de penalização por tonelada de oferta não alocada")

        # Big M para as Rotas (Indexado por ValidRoutes)
        def big_m_flow_init(model, o, d, p):
            f_max = pyo.value(model.freight_max, exception=False)
            if f_max is not None:
                return f_max
            else:
                # O teto real da rota é APENAS a oferta daquela origem (já que a capacidade pode expandir com dummy)
                local_max = pyo.value(model.Supply[o, p])
                return local_max if local_max > 0 else 999999.0
                
        model.big_m_flow = pyo.Param(model.ValidRoutes, initialize=big_m_flow_init, doc="Big M Dinâmico e Local por Rota")

        # 2. Big M para os Armazéns (Indexado por Destinations)
        def big_m_warehouse_init(model, d):
            # O máximo absoluto que um armazém pode receber é a soma de toda a oferta apontada para ele
            valid_ops = [(o, p) for o in model.Origins for p in model.Products if (o, d, p) in model.ValidRoutes]
            max_possible_arrival = sum(pyo.value(model.Supply[o, p]) for (o, p) in valid_ops)
            
            return max_possible_arrival if max_possible_arrival > 0 else 999999.0
            
        model.big_m_warehouse = pyo.Param(model.Destinations, initialize=big_m_warehouse_init, doc="Big M Dinâmico por Armazém")

        # =========================================================================
        # 3.3 VARIÁVEIS DE DECISÃO (VARIABLES)
        # =========================================================================
        # Valores que o solver tentará determinar para otimizar o resultado.

        # Fluxo de produto (quantidade a ser transportada) em toneladas
        model.Flow = pyo.Var(model.ValidRoutes, domain=pyo.NonNegativeReals, doc="Quantidade transportada (o, d, p)")

        # Variáveis de folga (Dummies) para garantir viabilidade matemática do modelo
        model.DummyCapacity = pyo.Var(model.Destinations, domain=pyo.NonNegativeReals, doc="Capacidade extra artificial alocada (ton)")
        model.DummyUnallocated = pyo.Var(model.Origins, model.Products, domain=pyo.NonNegativeReals, doc="Oferta não alocada a nenhum destino (ton)")
        model.DummyReception = pyo.Var(model.Destinations, domain=pyo.NonNegativeReals, doc="Capacidade de recepção diária extra artificial alocada (ton)")

        # Variáveis Binárias para Limites
        model.RouteActive = pyo.Var(model.ValidRoutes, domain=pyo.NonNegativeIntegers, doc="Número de viagens na rota")
        # model.WarehouseActive declarada mais abaixo na seção de Constraints MILP

        # =========================================================================
        # 3.4 FUNÇÃO OBJETIVO (OBJECTIVE)
        # =========================================================================
        # Expressão matemática a ser minimizada (Minimizar Custos).

        def objective_rule(model):
            normal_costs = sum(
                (model.Flow[o, d, p] * model.Distance[o, d] * model.Freight[o]) +
                (model.Flow[o, d, p] * model.Storage[d, p])
                for (o, d, p) in model.ValidRoutes
            )
            dummy_capacity_costs = sum(model.DummyCapacity[d] * model.BigMCapacity for d in model.Destinations)
            dummy_reception_costs = sum(model.DummyReception[d] * (model.BigMCapacity * 0.1) for d in model.Destinations)
            dummy_unallocated_costs = sum(model.DummyUnallocated[o, p] * model.BigMUnallocated for o in model.Origins for p in model.Products)
            return normal_costs + dummy_capacity_costs + dummy_reception_costs + dummy_unallocated_costs

        model.Objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize, doc="Minimização dos Custos Totais")

        # =========================================================================
        # 3.5 RESTRIÇÕES (CONSTRAINTS)
        # =========================================================================
        # Regras que as variáveis de decisão devem obedecer obrigatoriamente.

        # Restrição 1: Conservação de Fluxo (Limite de Oferta)
        def supply_rule(model, o, p):
            if model.Supply[o, p] <= 0:
                return pyo.Constraint.Skip
            valid_dests = [d for d in model.Destinations if (o, d, p) in model.ValidRoutes]
            if not valid_dests:
                return model.DummyUnallocated[o, p] == model.Supply[o, p]
            flow_sum = sum(model.Flow[o, d, p] for d in valid_dests)
            return flow_sum + model.DummyUnallocated[o, p] == model.Supply[o, p]
        model.SupplyConstraint = pyo.Constraint(model.Origins, model.Products, rule=supply_rule, doc="Restrição de Limite de Oferta")

        # Restrição 2: Limite de Capacidade Efetiva Estática
        def capacity_rule(model, d):
            valid_ops = [(o, p) for o in model.Origins for p in model.Products if (o, d, p) in model.ValidRoutes]
            if not valid_ops:
                return pyo.Constraint.Skip
            flow_sum = sum(model.Flow[o, d, p] for (o, p) in valid_ops)
            effective_cap = max(0.0, pyo.value(model.TotalCapacity[d]) - pyo.value(model.InitialInventory[d]))
            if effective_cap > 0:
                return flow_sum <= (model.TotalCapacity[d] - model.InitialInventory[d]) + model.DummyCapacity[d]
            else:
                return flow_sum <= model.DummyCapacity[d]
        model.CapacityConstraint = pyo.Constraint(model.Destinations, rule=capacity_rule, doc="Restrição de Limite de Capacidade Efetiva")

# =========================================================================
        # 3.6 RESTRIÇÕES MILP (LIMITES LOGÍSTICOS ADICIONAIS)
        # =========================================================================
        print("\n--- CONFIGURAÇÕES DE LIMITES LOGÍSTICOS (MILP) ---")
        print(f"Dias de alocação considerados: {pyo.value(model.days, exception=False)}")
        if pyo.value(model.freight_min, exception=False) is not None:
            print(f"Carga mínima de frete por rota ativada: {pyo.value(model.freight_min, exception=False)} ton")
        if pyo.value(model.freight_max, exception=False) is not None:
            print(f"Carga máxima de frete por rota ativada: {pyo.value(model.freight_max, exception=False)} ton")

        if list(model.Destinations):
            if pyo.value(model.reception_min[list(model.Destinations)[0]], exception=False) is not None:
                print(f"Carga mínima diária de recepção ativada: {pyo.value(model.reception_min[list(model.Destinations)[0]], exception=False)} ton/dia (Total: {pyo.value(model.reception_min[list(model.Destinations)[0]], exception=False) * pyo.value(model.days, exception=False)} ton)")
            if toggle_use_recepcao:
                print(f"Capacidade máxima de recepção do banco de dados ativada.")
            elif pyo.value(model.reception_max[list(model.Destinations)[0]], exception=False) is not None: # Note: this assumes same for all if not toggle
                print(f"Carga máxima diária de recepção ativada: {pyo.value(model.reception_max[list(model.Destinations)[0]], exception=False)} ton/dia")

        def route_active_max_rule(model, o, d, p):
            return model.Flow[o, d, p] <= model.RouteActive[o, d, p] * model.big_m_flow[o, d, p]
            
        model.RouteActiveMaxRule = pyo.Constraint(model.ValidRoutes, rule=route_active_max_rule, doc="Limite máximo de frete ou local")

        # Limite mínimo de Frete (opcional)
        if pyo.value(model.freight_min, exception=False) is not None:
            def route_active_min_rule(model, o, d, p):
                return model.Flow[o, d, p] >= model.RouteActive[o, d, p] * pyo.value(model.freight_min, exception=False)
            model.RouteActiveMinRule = pyo.Constraint(model.ValidRoutes, rule=route_active_min_rule, doc="Limite mínimo de frete na rota caso ela seja usada")

        # Variável binária de ativação do armazém:
        # Se um armazém for usado (receber qualquer fluxo), WarehouseActive = 1
        model.WarehouseActive = pyo.Var(model.Destinations, domain=pyo.Binary, doc="1 se o armazém receber qualquer rota, 0 caso contrário")

        # Liga o fluxo do armazém com sua variável de ativação (WarehouseActive)
        def link_warehouse_active_rule(model, d):
            valid_ops = [(o, p) for o in model.Origins for p in model.Products if (o, d, p) in model.ValidRoutes]
            if not valid_ops:
                return model.WarehouseActive[d] == 0

            flow_sum = sum(model.Flow[o, d, p] for (o, p) in valid_ops)
            
            # Utilizando o parâmetro limpo
            return flow_sum <= model.WarehouseActive[d] * model.big_m_warehouse[d]
            
        model.LinkWarehouseActive = pyo.Constraint(model.Destinations, rule=link_warehouse_active_rule, doc="Vincula o armazém a rotas ativas")

        # Limite mínimo de recepção de carga no armazém (opcional)
        def min_reception_rule(model, d):
            reception_min_val = pyo.value(model.reception_min[d], exception=False)
            if reception_min_val is None:
                return pyo.Constraint.Skip

            valid_ops = [(o, p) for o in model.Origins for p in model.Products if (o, d, p) in model.ValidRoutes]
            if not valid_ops:
                return pyo.Constraint.Skip
            flow_sum = sum(model.Flow[o, d, p] for (o, p) in valid_ops)
            return flow_sum >= model.WarehouseActive[d] * (reception_min_val * pyo.value(model.days, exception=False))
        model.MinReceptionRule = pyo.Constraint(model.Destinations, rule=min_reception_rule, doc="Recepção Mínima do Armazém se for ativado")

        # Limite máximo de recepção de carga no armazém (opcional ou pela Cap. Recepção do Banco)
        # Observação: toggle_use_recepcao e carga_max são mutuamente exclusivos na lógica da UI,
        # mas aqui explicitamos a prioridade: a capacidade do banco sobressai se ativada.
        def max_reception_rule(model, d):
            valid_ops = [(o, p) for o in model.Origins for p in model.Products if (o, d, p) in model.ValidRoutes]
            if not valid_ops:
                return pyo.Constraint.Skip

            flow_sum = sum(model.Flow[o, d, p] for (o, p) in valid_ops)

            reception_max_val = pyo.value(model.reception_max[d], exception=False)
            if reception_max_val is not None:
                limit = reception_max_val * pyo.value(model.days, exception=False)
                # Flow can use dummy reception se o limite for ultrapassado
                return flow_sum <= limit + model.DummyReception[d]
            return pyo.Constraint.Skip

        model.MaxReceptionRule = pyo.Constraint(model.Destinations, rule=max_reception_rule, doc="Recepção Máxima no Armazém com tolerância de folga DummyReception")

        


        if detailed_log:
            model.pprint()

        print("\nChamando solver CBC (MILP)...")
        solver = SolverFactory('cbc')
        solver.options['sec'] = 600

        results = solver.solve(model, tee=True)

        print("\n=== STATUS DA OTIMIZAÇÃO ===")
        print(f"Status do Solver: {results.solver.status}")
        print(f"Condição de Término: {results.solver.termination_condition}")

        if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition == pyo.TerminationCondition.optimal:
            print(f"Solução Ótima Encontrada!")
            objective_value = pyo.value(model.Objective)
            print(f"Custo Total (Função Objetivo): R$ {objective_value:,.2f}")

            results_dict["status"] = "optimal"
            results_dict["objective"] = objective_value

            print("\n--- DETALHES DO FLUXO (Alocação) ---")
            total_transported = 0
            total_km = 0.0
            total_freight_cost = 0.0
            total_storage_cost = 0.0

            for (o, d, p) in model.ValidRoutes:
                val = pyo.value(model.Flow[o, d, p])
                if val > 0.001:
                    d_name = cda_to_name.get(d, d)
                    dist = pyo.value(model.Distance[o, d])
                    f_cost = pyo.value(model.Freight[o])
                    s_cost = pyo.value(model.Storage[d, p])

                    route_freight = val * dist * f_cost
                    route_storage = val * s_cost
                    route_total = route_freight + route_storage

                    viagens = pyo.value(model.RouteActive[o, d, p])
                    viagens_val = int(round(viagens)) if viagens is not None else None

                    print(f"De: {o} | Para: {d_name} | Produto: {p} | Qtd: {val:.2f} ton | Viagens: {viagens_val}")

                    results_dict["routes"].append({
                        "Origem": o,
                        "Destino": d_name,
                        "Produto": p,
                        "Quantidade (ton)": val,
                        "Distancia (km)": dist,
                        "Custo Frete (R$)": route_freight,
                        "Custo Armazenagem (R$)": route_storage,
                        "Custo Total (R$)": route_total,
                        "Custo Frete Unitario (R$/ton-km)": f_cost,
                        "Custo Armaz. Unitario (R$/ton)": s_cost,
                        "Qtd. de Viagens": viagens_val
                    })

                    total_transported += val
                    total_km += dist
                    total_freight_cost += route_freight
                    total_storage_cost += route_storage

            print(f"\nTotal de produtos alocados: {total_transported:.2f} toneladas")

            results_dict["kpis"]["total_tons"] = total_transported
            results_dict["kpis"]["total_km"] = total_km
            results_dict["kpis"]["total_freight_cost"] = total_freight_cost
            results_dict["kpis"]["total_storage_cost"] = total_storage_cost

            # Verificar uso das variáveis Dummies
            dummy_cap_used = False
            print("\n--- AVISOS: CAPACIDADE ARTIFICIAL (DUMMIES) ---")
            for d in model.Destinations:
                d_val = pyo.value(model.DummyCapacity[d])
                if d_val > 0.001:
                    dummy_cap_used = True
                    d_name = cda_to_name.get(d, d)
                    msg = f"O Armazém '{d_name}' precisou de capacidade de armazenamento artificial de {d_val:.2f} toneladas."
                    print(f"ALERTA: {msg}")
                    results_dict["warnings"]["capacity"].append(msg)

            if not dummy_cap_used:
                print("Nenhuma capacidade estática artificial foi necessária.")

            if "reception" not in results_dict["warnings"]:
                results_dict["warnings"]["reception"] = []

            dummy_reception_used = False
            print("\n--- AVISOS: RECEPÇÃO DIÁRIA ARTIFICIAL (DUMMIES) ---")
            for d in model.Destinations:
                d_val = pyo.value(model.DummyReception[d])
                if d_val > 0.001:
                    dummy_reception_used = True
                    d_name = cda_to_name.get(d, d)
                    msg = f"O Armazém '{d_name}' precisou de capacidade de recepção diária artificial de {d_val:.2f} toneladas."
                    print(f"ALERTA: {msg}")
                    results_dict["warnings"]["reception"].append(msg)

            if not dummy_reception_used:
                print("Nenhuma capacidade de recepção artificial foi necessária.")

            if "freight" not in results_dict["warnings"]:
                results_dict["warnings"]["freight"] = []

            dummy_unalloc_used = False
            print("\n--- AVISOS: OFERTA SEM ROTAS / NÃO ALOCADA (DUMMIES) ---")
            for o in model.Origins:
                for p in model.Products:
                    u_val = pyo.value(model.DummyUnallocated[o, p])
                    if u_val > 0.001:
                        dummy_unalloc_used = True

                        # Inferir se a inalocação pode ser por conta do frete apertado
                        if frete_min is not None or frete_max is not None:
                            msg = f"A origem '{o}' possui oferta de '{p}' não alocada ({u_val:.2f} toneladas). Isso provavelmente ocorreu devido às restrições de carga de frete mínima/máxima impostas."
                            print(f"ALERTA: {msg}")
                            results_dict["warnings"]["freight"].append(msg)
                        else:
                            msg = f"A origem '{o}' possui oferta de '{p}' não alocada: {u_val:.2f} toneladas."
                            print(f"ALERTA: {msg}")
                            results_dict["warnings"]["unallocated"].append(msg)

            if not dummy_unalloc_used:
                print("Toda a oferta conseguiu ser escoada em rotas válidas.")

            if dummy_cap_used or dummy_reception_used or dummy_unalloc_used:
                print(f"\nNota: Foram utilizadas variáveis dummies com custo elevado para impedir que o modelo falhasse por inviabilidade.")

        else:
            print("Não foi possível encontrar uma solução ótima.")
            results_dict["status"] = "infeasible"
            results_dict["warnings"]["general"].append("O modelo não encontrou solução ótima.")

    except Exception as e:
        print(f"\nERRO DURANTE A OTIMIZAÇÃO: {str(e)}")
        results_dict["status"] = "error"
        results_dict["warnings"]["general"].append(f"Erro: {str(e)}")
        import traceback
        print(traceback.format_exc())

    finally:
        end_time = time.time()
        total_time_seconds = end_time - start_time
        print(f"\nTempo de execução: {total_time_seconds:.2f} segundos.")
        results_dict["kpis"]["execution_time"] = total_time_seconds

        new_stdout.close()
        sys.stdout = old_stdout

    return log_filename, results_dict
