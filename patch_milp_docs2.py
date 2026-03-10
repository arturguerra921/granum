import re

with open('src/logic/optimization.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
'''        model.RouteActiveMaxRule = pyo.Constraint(model.ValidRoutes, rule=route_active_max_rule)

        if frete_min is not None:''',
'''        model.RouteActiveMaxRule = pyo.Constraint(model.ValidRoutes, rule=route_active_max_rule, doc="Limite máximo de frete na rota ou ligação Big M se não estipulado")

        # Limite mínimo de Frete (opcional)
        if frete_min is not None:'''
)

content = content.replace(
'''        model.RouteActiveMinRule = pyo.Constraint(model.ValidRoutes, rule=route_active_min_rule)

        if carga_min is not None:''',
'''        model.RouteActiveMinRule = pyo.Constraint(model.ValidRoutes, rule=route_active_min_rule, doc="Limite mínimo de frete na rota caso ela seja usada")

        if carga_min is not None:'''
)

content = content.replace(
'''        model.WarehouseActive = pyo.Var(model.Destinations, domain=pyo.Binary)

        def link_warehouse_active_rule(model, d):''',
'''        model.WarehouseActive = pyo.Var(model.Destinations, domain=pyo.Binary, doc="1 se o armazém receber qualquer rota, 0 caso contrário")

        # Liga o fluxo do armazém com sua variável de ativação (WarehouseActive)
        def link_warehouse_active_rule(model, d):'''
)

content = content.replace(
'''        model.LinkWarehouseActive = pyo.Constraint(model.Destinations, rule=link_warehouse_active_rule)

        if carga_min is not None:''',
'''        model.LinkWarehouseActive = pyo.Constraint(model.Destinations, rule=link_warehouse_active_rule, doc="Vincula o armazém a rotas ativas")

        # Limite mínimo de recepção de carga no armazém (opcional)
        if carga_min is not None:'''
)

content = content.replace(
'''        model.MinReceptionRule = pyo.Constraint(model.Destinations, rule=min_reception_rule)

        def max_reception_rule(model, d):''',
'''        model.MinReceptionRule = pyo.Constraint(model.Destinations, rule=min_reception_rule, doc="Recepção Mínima do Armazém se for ativado")

        # Limite máximo de recepção de carga no armazém (opcional ou pela Cap. Recepção do Banco)
        def max_reception_rule(model, d):'''
)

content = content.replace(
'''        model.MaxReceptionRule = pyo.Constraint(model.Destinations, rule=max_reception_rule)


        if detailed_log:''',
'''        model.MaxReceptionRule = pyo.Constraint(model.Destinations, rule=max_reception_rule, doc="Recepção Máxima no Armazém com tolerância de folga Dummy")


        if detailed_log:'''
)

with open('src/logic/optimization.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacement applied")
