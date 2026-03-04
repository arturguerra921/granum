import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd
import sys
import io

def run_optimization_model(df_supply, df_demand, df_compat, df_dist, df_freight, df_storage):
    """
    Roda o modelo matemático de otimização linear para alocação de produtos.
    """
    # 1. Preparação dos dados

    # Oferta (Supply)
    # Group by Cidade and Produto, sum over Peso (ton)
    supply = df_supply.groupby(['Cidade', 'Produto'])['Peso (ton)'].sum().to_dict()

    # Demanda (Demand) - Usando Capacidade em toneladas do Armazém (nó destino)
    # Identify the capacity column correctly. Often it is "Capacidade Estática (t)" or similar.
    cap_col = next((c for c in df_demand.columns if 'cap' in str(c).lower() or 'ton' in str(c).lower()), None)

    # Identify Public/Private warehouse.
    armazenador_col = next((c for c in df_demand.columns if 'armazenador' in str(c).lower()), None)
    name_col = next((c for c in df_demand.columns if 'armaz' in str(c).lower() or 'nome' in str(c).lower()), None)
    mun_col_dest = next((c for c in df_demand.columns if 'munic' in str(c).lower()), None)

    demand_capacity = {}
    is_public = {}
    for idx, row in df_demand.iterrows():
        # Match the exact naming convention used in the distance matrix view
        dest_name = f"Dest {idx}"
        if name_col and mun_col_dest:
            dest_name = f"{row[name_col]} ({row[mun_col_dest]})"
        elif name_col:
            dest_name = str(row[name_col])
        elif mun_col_dest:
            dest_name = str(row[mun_col_dest])

        # Parse capacity correctly (cleaning Brazilian number formats)
        try:
            val_str = str(row[cap_col]).replace('.', '').replace(',', '.')
            cap = float(val_str)
        except:
            cap = 0.0

        demand_capacity[dest_name] = cap

        # Determine if public or private
        if armazenador_col and str(row[armazenador_col]).upper() == "COMPANHIA NACIONAL DE ABASTECIMENTO":
            is_public[dest_name] = True
        else:
            is_public[dest_name] = False

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
            dest_name = f"Dest {idx}"
            if name_col and mun_col_dest:
                dest_name = f"{row[name_col]} ({row[mun_col_dest]})"
            elif name_col:
                dest_name = str(row[name_col])
            elif mun_col_dest:
                dest_name = str(row[mun_col_dest])

            tipo_armazem = row[tipo_col] if tipo_col else None

            # Se não temos informação de tipo, assumimos que aceita (ou podemos rejeitar, mas assumir True é mais seguro se falhar)
            if tipo_armazem and (prod, tipo_armazem) in compat_dict:
                prod_dest_compat[(prod, dest_name)] = compat_dict[(prod, tipo_armazem)]
            else:
                prod_dest_compat[(prod, dest_name)] = True # Default fallback

    # Matriz de Distâncias
    # df_dist tem 'Origem' e colunas com 'Dest <idx>' ...
    distance = {}
    for _, row in df_dist.iterrows():
        orig = row['Origem']
        for col in df_dist.columns:
            if col != 'Origem':
                dest = col
                try:
                    distance[(orig, dest)] = float(row[col])
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
    try:
        # Pega a tarifa (assumimos que "Graos_Geral" serve para todos se não houver específico)
        # Parse Brazilian numbers
        df_storage['Pub'] = df_storage['Armazenar_Publico'].astype(str).str.replace('.', '').str.replace(',', '.').astype(float)
        df_storage['Priv'] = df_storage['Armazenar_Privado'].astype(str).str.replace('.', '').str.replace(',', '.').astype(float)

        # Pega a primeira linha como default
        default_pub = df_storage['Pub'].iloc[0]
        default_priv = df_storage['Priv'].iloc[0]
    except:
        default_pub = 0.0
        default_priv = 0.0

    storage_cost = {}
    for dest in demand_capacity.keys():
        if is_public.get(dest, False):
            storage_cost[dest] = default_pub
        else:
            storage_cost[dest] = default_priv


    # 2. Construção do Modelo Pyomo

    # Redirecionar output para capturar logs
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

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

        def storage_init(model, d):
            return storage_cost.get(d, 0.0)
        model.Storage = pyo.Param(model.Destinations, initialize=storage_init)

        # Função Objetivo (Objective)
        # Minimize sum(Flow * Distance * FreightCost) + sum(Flow * StorageTariff)
        def objective_rule(model):
            return sum(
                model.Flow[o, d, p] * model.Distance[o, d] * model.Freight[o] +
                model.Flow[o, d, p] * model.Storage[d]
                for (o, d, p) in model.ValidRoutes
            )
        model.Objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

        # Restrições (Constraints)

        # 1. Supply limit: A oferta deve ser totalmente alocada
        def supply_rule(model, o, p):
            if model.Supply[o, p] <= 0:
                return pyo.Constraint.Skip

            valid_dests = [d for d in model.Destinations if (o, d, p) in model.ValidRoutes]
            if not valid_dests:
                # Não tem rotas válidas para escoar esta oferta.
                # Retorna Infeasible para avisar o Pyomo (já que a soma seria 0 == Supply)
                return pyo.Constraint.Infeasible

            flow_sum = sum(model.Flow[o, d, p] for d in valid_dests)
            return flow_sum == model.Supply[o, p]

        model.SupplyConstraint = pyo.Constraint(model.Origins, model.Products, rule=supply_rule)

        # 2. Capacity limit: Não exceder a capacidade máxima do nó de demanda (soma de todos produtos de todas origens)
        def capacity_rule(model, d):
            valid_ops = [(o, p) for o in model.Origins for p in model.Products if (o, d, p) in model.ValidRoutes]
            if not valid_ops:
                return pyo.Constraint.Skip

            flow_sum = sum(model.Flow[o, d, p] for (o, p) in valid_ops)
            if model.Capacity[d] > 0:
                return flow_sum <= model.Capacity[d]
            else:
                # Se a capacidade é 0, o fluxo deve ser 0
                return flow_sum == 0

        model.CapacityConstraint = pyo.Constraint(model.Destinations, rule=capacity_rule)

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
            print(f"Custo Total (Função Objetivo): R$ {pyo.value(model.Objective):,.2f}")

            print("\n--- DETALHES DO FLUXO (Alocação) ---")
            total_transported = 0
            for (o, d, p) in model.ValidRoutes:
                val = pyo.value(model.Flow[o, d, p])
                if val > 0.001:  # ignore floating point zeros
                    print(f"De: {o} | Para: {d} | Produto: {p} | Qtd: {val:.2f} ton")
                    total_transported += val

            print(f"\nTotal de produtos alocados: {total_transported:.2f} toneladas")
        else:
            print("Não foi possível encontrar uma solução ótima. Verifique se a capacidade dos armazéns é suficiente para a oferta, ou se há rotas válidas.")

    except Exception as e:
        print(f"\nERRO DURANTE A OTIMIZAÇÃO: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Restaurar stdout
        sys.stdout = old_stdout

    # Retornar o texto capturado
    return new_stdout.getvalue()
