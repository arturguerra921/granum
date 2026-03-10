import re

with open("src/logic/optimization.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace variables in MILP definition
new_vars = """
        # Variáveis de folga (Dummies) para garantir viabilidade matemática do modelo
        model.DummyCapacity = pyo.Var(model.Destinations, domain=pyo.NonNegativeReals, doc="Capacidade extra artificial alocada (ton)")
        model.DummyUnallocated = pyo.Var(model.Origins, model.Products, domain=pyo.NonNegativeReals, doc="Oferta não alocada a nenhum destino (ton)")
        model.DummyReception = pyo.Var(model.Destinations, domain=pyo.NonNegativeReals, doc="Capacidade diária de recepção extra artificial (ton)")
"""

code = code.replace(
    """        # Variáveis de folga (Dummies) para garantir viabilidade matemática do modelo
        model.DummyCapacity = pyo.Var(model.Destinations, domain=pyo.NonNegativeReals, doc="Capacidade extra artificial alocada (ton)")
        model.DummyUnallocated = pyo.Var(model.Origins, model.Products, domain=pyo.NonNegativeReals, doc="Oferta não alocada a nenhum destino (ton)")""",
    new_vars, 1  # Only replace in the MILP part if there are 2 occurrences. Oh wait, this replaces the LP too.
)
print("done")
