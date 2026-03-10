import re

with open('src/logic/optimization.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Sets documentation
content = content.replace(
'''        model.Origins = pyo.Set(initialize=origins_list, doc="Cidades de Origem da Oferta")
        model.Destinations = pyo.Set(initialize=list(demand_total_capacity.keys()), doc="Armazéns de Destino")
        model.Products = pyo.Set(initialize=all_products, doc="Tipos de Produtos")''',
'''        # =========================================================================
        # 3.1 CONJUNTOS (SETS)
        # =========================================================================
        # Definem os índices sobre os quais o modelo irá operar.
        model.Origins = pyo.Set(initialize=origins_list, doc="Cidades de Origem da Oferta")
        model.Destinations = pyo.Set(initialize=list(demand_total_capacity.keys()), doc="Armazéns de Destino")
        model.Products = pyo.Set(initialize=all_products, doc="Tipos de Produtos")'''
)

# Parameters documentation
content = content.replace(
'''        def supply_init(model, o, p):
            return supply.get((o, p), 0.0)
        model.Supply = pyo.Param(model.Origins, model.Products, initialize=supply_init)''',
'''        # =========================================================================
        # 3.2 PARÂMETROS (PARAMETERS)
        # =========================================================================
        # Valores fixos conhecidos fornecidos como dados de entrada para o modelo.

        # --- Parâmetros de Oferta e Demanda ---
        def supply_init(model, o, p):
            return supply.get((o, p), 0.0)
        model.Supply = pyo.Param(model.Origins, model.Products, initialize=supply_init, doc="Oferta disponível por (Origem, Produto)")'''
)

content = content.replace(
'''        model.TotalCapacity = pyo.Param(model.Destinations, initialize=total_capacity_init)

        def initial_inventory_init(model, d):
            return demand_initial_inventory.get(d, 0.0)
        model.InitialInventory = pyo.Param(model.Destinations, initialize=initial_inventory_init)

        def dist_init(model, o, d):
            return distance.get((o, d), 999999.0)
        model.Distance = pyo.Param(model.Origins, model.Destinations, initialize=dist_init)

        def freight_init(model, o):
            return freight_cost.get(o, avg_freight)
        model.Freight = pyo.Param(model.Origins, initialize=freight_init)

        def storage_init(model, d, p):
            return storage_cost.get((d, p), 50.0)
        model.Storage = pyo.Param(model.Destinations, model.Products, initialize=storage_init)''',
'''        model.TotalCapacity = pyo.Param(model.Destinations, initialize=total_capacity_init, doc="Capacidade estática total do armazém (ton)")

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
        model.Storage = pyo.Param(model.Destinations, model.Products, initialize=storage_init, doc="Tarifa de armazenagem no Destino para o Produto (R$/ton)")'''
)


content = content.replace(
'''        model.BigMCapacity = pyo.Param(initialize=val_big_m_cap)
        model.BigMUnallocated = pyo.Param(initialize=val_big_m_unalloc)

        # Variáveis
        model.Flow = pyo.Var(model.ValidRoutes, domain=pyo.NonNegativeReals, doc="Quantidade transportada")
        model.DummyCapacity = pyo.Var(model.Destinations, domain=pyo.NonNegativeReals)
        model.DummyUnallocated = pyo.Var(model.Origins, model.Products, domain=pyo.NonNegativeReals)

        # Variável Binária para Limites Individuais de Rota
        model.RouteActive = pyo.Var(model.ValidRoutes, domain=pyo.Binary, doc="1 se a rota for usada, 0 caso contrário")

        # Objective
        def objective_rule(model):''',
'''        # --- Parâmetros de Penalização (Big M) ---
        model.BigMCapacity = pyo.Param(initialize=val_big_m_cap, doc="Custo de penalização por tonelada de capacidade artificial")
        model.BigMUnallocated = pyo.Param(initialize=val_big_m_unalloc, doc="Custo de penalização por tonelada de oferta não alocada")

        # =========================================================================
        # 3.3 VARIÁVEIS DE DECISÃO (VARIABLES)
        # =========================================================================
        # Valores que o solver tentará determinar para otimizar o resultado.

        # Fluxo de produto (quantidade a ser transportada) em toneladas
        model.Flow = pyo.Var(model.ValidRoutes, domain=pyo.NonNegativeReals, doc="Quantidade transportada (o, d, p)")

        # Variáveis de folga (Dummies) para garantir viabilidade matemática do modelo
        model.DummyCapacity = pyo.Var(model.Destinations, domain=pyo.NonNegativeReals, doc="Capacidade extra artificial alocada (ton)")
        model.DummyUnallocated = pyo.Var(model.Origins, model.Products, domain=pyo.NonNegativeReals, doc="Oferta não alocada a nenhum destino (ton)")

        # Variáveis Binárias para Limites
        model.RouteActive = pyo.Var(model.ValidRoutes, domain=pyo.Binary, doc="1 se a rota for usada, 0 caso contrário")
        # model.WarehouseActive declarada mais abaixo na seção de Constraints MILP

        # =========================================================================
        # 3.4 FUNÇÃO OBJETIVO (OBJECTIVE)
        # =========================================================================
        # Expressão matemática a ser minimizada (Minimizar Custos).

        def objective_rule(model):'''
)

content = content.replace(
'''        model.Objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

        # Constraints Base
        def supply_rule(model, o, p):''',
'''        model.Objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize, doc="Minimização dos Custos Totais")

        # =========================================================================
        # 3.5 RESTRIÇÕES (CONSTRAINTS)
        # =========================================================================
        # Regras que as variáveis de decisão devem obedecer obrigatoriamente.

        # Restrição 1: Conservação de Fluxo (Limite de Oferta)
        def supply_rule(model, o, p):'''
)

content = content.replace(
'''        model.SupplyConstraint = pyo.Constraint(model.Origins, model.Products, rule=supply_rule)

        def capacity_rule(model, d):''',
'''        model.SupplyConstraint = pyo.Constraint(model.Origins, model.Products, rule=supply_rule, doc="Restrição de Limite de Oferta")

        # Restrição 2: Limite de Capacidade Efetiva Estática
        def capacity_rule(model, d):'''
)

content = content.replace(
'''        model.CapacityConstraint = pyo.Constraint(model.Destinations, rule=capacity_rule)

        # MILP Constraints

        # Big M for flow logic''',
'''        model.CapacityConstraint = pyo.Constraint(model.Destinations, rule=capacity_rule, doc="Restrição de Limite de Capacidade Efetiva")

        # =========================================================================
        # 3.6 RESTRIÇÕES MILP (LIMITES LOGÍSTICOS ADICIONAIS)
        # =========================================================================

        # Big M dinâmico para limite superior lógico de fluxo'''
)

with open('src/logic/optimization.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacement applied")
