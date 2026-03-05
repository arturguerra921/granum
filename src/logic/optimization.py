import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd
import sys
import io
import tempfile
import os

def run_optimization_model(df_supply, df_demand, df_compat, df_dist, df_freight, df_storage):
    """
    Roda o modelo matemático de otimização linear para alocação de produtos.
    """
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

    demand_capacity = {}
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

        # A capacidade disponível é a capacidade total menos o estoque inicial
        available_cap = max(0.0, cap - estoque)

        demand_capacity[cda] = available_cap

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

            for dest in demand_capacity.keys():
                if is_public.get(dest, False):
                    storage_cost[(dest, prod)] = pub_val
                else:
                    storage_cost[(dest, prod)] = priv_val

    except Exception as e:
        print(f"Erro ao processar tarifas de armazenagem: {e}")
        # Default fallback
        for prod in all_products:
            for dest in demand_capacity.keys():
                storage_cost[(dest, prod)] = 50.0


    # 2. Construção do Modelo Pyomo

    # Redirecionar output diretamente para um arquivo temporário no disco (para evitar Out of Memory)
    old_stdout = sys.stdout

    log_dir = os.path.join(tempfile.gettempdir(), 'granum_logs')
    os.makedirs(log_dir, exist_ok=True)

    # Limpar arquivos antigos para não estourar o disco
    import time
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
            "total_storage_cost": 0.0
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

        # Conjuntos (Sets)
        model.Origins = pyo.Set(initialize=df_supply['Cidade'].unique().tolist())
        model.Destinations = pyo.Set(initialize=list(demand_capacity.keys()))
        model.Products = pyo.Set(initialize=all_products)

        # Filtrar rotas válidas (onde a distância é conhecida e o produto é aceito)
        valid_routes = []
        for o in model.Origins:
            for d in model.Destinations:
                for p in model.Products:
                    if (o, d) in distance and prod_dest_compat.get((p, d), False):
                        valid_routes.append((o, d, p))

        print(f"Total de combinações (Origem x Destino x Produto) válidas: {len(valid_routes)}")

        model.ValidRoutes = pyo.Set(initialize=valid_routes, dimen=3)

        # Variáveis (Variables) - Fluxo de produto da origem o para o destino d (em toneladas)
        model.Flow = pyo.Var(model.ValidRoutes, domain=pyo.NonNegativeReals)

        # Variável Dummy de Capacidade Extra (por armazém)
        model.DummyCapacity = pyo.Var(model.Destinations, domain=pyo.NonNegativeReals)

        # Variável Dummy de Oferta Não Alocada (por origem e produto)
        model.DummyUnallocated = pyo.Var(model.Origins, model.Products, domain=pyo.NonNegativeReals)

        # Parâmetros (Parameters)
        def supply_init(model, o, p):
            return supply.get((o, p), 0.0)
        model.Supply = pyo.Param(model.Origins, model.Products, initialize=supply_init)

        def capacity_init(model, d):
            return demand_capacity.get(d, 0.0)
        model.Capacity = pyo.Param(model.Destinations, initialize=capacity_init)

        def dist_init(model, o, d):
            return distance.get((o, d), 999999.0)
        model.Distance = pyo.Param(model.Origins, model.Destinations, initialize=dist_init)

        def freight_init(model, o):
            return freight_cost.get(o, avg_freight)
        model.Freight = pyo.Param(model.Origins, initialize=freight_init)

        def storage_init(model, d, p):
            return storage_cost.get((d, p), 50.0)
        model.Storage = pyo.Param(model.Destinations, model.Products, initialize=storage_init)

        # Calcular um big_M dinâmico com base nos custos máximos possíveis
        max_freight = max(freight_cost.values()) if freight_cost else 0.0
        max_dist = max(distance.values()) if distance else 0.0
        max_storage = max(storage_cost.values()) if storage_cost else 0.0

        # O big_M deve ser ordens de grandeza maior que os custos reais para forçar as dummies a serem usadas apenas em último caso
        big_M_capacity = (max_freight * max_dist + max_storage) * 1000000
        if big_M_capacity == 0:
            big_M_capacity = 1000000

        # O custo de não alocar (DummyUnallocated) DEVE ser muito maior que o custo de alocar usando capacidade artificial
        # Caso contrário, o solver prefere "não alocar" para economizar o custo normal de frete + armazenamento.
        big_M_unallocated = big_M_capacity * 10

        print(f"Valor dinâmico para big_M (Capacidade Artificial): {big_M_capacity:.2e}")
        print(f"Valor dinâmico para big_M (Oferta Não Alocada): {big_M_unallocated:.2e}")

        # Função Objetivo (Objective)
        # Minimize sum(Flow * Distance * FreightCost) + sum(Flow * StorageTariff) + sum(Dummies * big_M)
        def objective_rule(model):
            normal_costs = sum(
                model.Flow[o, d, p] * model.Distance[o, d] * model.Freight[o] +
                model.Flow[o, d, p] * model.Storage[d, p]
                for (o, d, p) in model.ValidRoutes
            )
            dummy_capacity_costs = sum(model.DummyCapacity[d] * big_M_capacity for d in model.Destinations)
            dummy_unallocated_costs = sum(model.DummyUnallocated[o, p] * big_M_unallocated for o in model.Origins for p in model.Products)

            return normal_costs + dummy_capacity_costs + dummy_unallocated_costs

        model.Objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

        # Restrições (Constraints)

        # 1. Supply limit: A oferta deve ser totalmente alocada (via rotas válidas ou variável dummy)
        def supply_rule(model, o, p):
            if model.Supply[o, p] <= 0:
                return pyo.Constraint.Skip

            valid_dests = [d for d in model.Destinations if (o, d, p) in model.ValidRoutes]
            if not valid_dests:
                # Não tem rotas válidas para escoar esta oferta, forçar dummy.
                return model.DummyUnallocated[o, p] == model.Supply[o, p]

            flow_sum = sum(model.Flow[o, d, p] for d in valid_dests)
            return flow_sum + model.DummyUnallocated[o, p] == model.Supply[o, p]

        model.SupplyConstraint = pyo.Constraint(model.Origins, model.Products, rule=supply_rule)

        # 2. Capacity limit: Não exceder a capacidade máxima (real + dummy)
        def capacity_rule(model, d):
            valid_ops = [(o, p) for o in model.Origins for p in model.Products if (o, d, p) in model.ValidRoutes]
            if not valid_ops:
                return pyo.Constraint.Skip

            flow_sum = sum(model.Flow[o, d, p] for (o, p) in valid_ops)
            if model.Capacity[d] > 0:
                return flow_sum <= model.Capacity[d] + model.DummyCapacity[d]
            else:
                # Se a capacidade é 0, qualquer fluxo usará apenas a dummy
                return flow_sum <= model.DummyCapacity[d]

        model.CapacityConstraint = pyo.Constraint(model.Destinations, rule=capacity_rule)

        #Mostrar o modelo para debug
        model.pprint()
        # 3. Solucionar o modelo
        print("\nChamando solver CBC...")
        solver = SolverFactory('cbc')
        # Limite de tempo para não travar infinitamente
        solver.options['sec'] = 300

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
                print(f"Custo de Capacidade Artificial (big_M) = {big_M_capacity:.2e}")
                print(f"Custo de Oferta Não Alocada (big_M * 10) = {big_M_unallocated:.2e}")

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
        # Fechar o arquivo temporário de log e restaurar stdout
        new_stdout.close()
        sys.stdout = old_stdout

    # Retornar o nome do arquivo de log salvo e os dados estruturados
    return log_filename, results_dict
