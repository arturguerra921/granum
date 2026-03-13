import re

with open('src/view/view.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Armazenamento Insuficiente
cap_search = """                html.P(translate("A oferta excedeu a capacidade de armazenamento dos armazéns. Não há um erro no cálculo, mas sim uma limitação na infraestrutura de armazenamento disponível para os armazéns utilizados.", lang), className="mb-2"),
                html.P([html.I(className="bi bi-info-circle-fill me-1"), html.B(translate("Atenção aos Resultados:", lang))], className="fw-bold mb-1"),
                html.P(translate("Os valores de custo total e outras métricas exatas exibidas nesta página devem ser desconsiderados. Para evitar que o modelo ficasse 'sem solução' e para mostrar exatamente onde estão os gargalos logísticos, o sistema utilizou uma capacidade de armazenamento artificial com um custo unitário (multa) exorbitantemente alto. Resolva as pendências abaixo e rode o modelo novamente para obter os resultados reais.", lang), className="mb-2"),"""

cap_replace = """                html.P(translate("A oferta excedeu a capacidade de armazenamento dos armazéns. Não há um erro no cálculo, mas sim uma limitação física na infraestrutura de armazenamento disponível para os armazéns utilizados.", lang), className="mb-2"),
                html.P(translate("Lembre-se da diferença entre Capacidade Local vs. Global: Apenas somar a capacidade total de todos os armazéns habilitados não garante a viabilidade da operação. Se um armazém tiver muito espaço vazio, mas possuir uma 'porta de entrada' (recepção diária) muito estreita ou restrições de frete que forcem envios incompatíveis, o modelo pode ser obrigado a estourar a capacidade física de outro armazém para escoar a carga e não deixar caminhões parados.", lang), className="mb-2"),
                html.P([html.I(className="bi bi-info-circle-fill me-1"), html.B(translate("Suposições do Modelo e Atenção aos Resultados:", lang))], className="fw-bold mb-1"),
                html.P(translate("Estes avisos refletem as escolhas matemáticas que o modelo precisou fazer para contornar gargalos logísticos. Para evitar que o sistema ficasse 'sem solução' e para mostrar exatamente onde a operação 'trava', o modelo preferiu utilizar uma capacidade de armazenamento artificial (como se alugasse um galpão extra de emergência) com um custo/multa exorbitantemente alto. Por isso, os valores de custo total exibidos aqui devem ser desconsiderados até que o gargalo seja resolvido.", lang), className="mb-2"),"""

cap_sol_search = """                html.P(html.B(translate("Possíveis Soluções:", lang))),
                html.Ul([
                    html.Li(translate("Aumente a capacidade estática dos armazéns utilizados na aba 'Armazéns'.", lang)),
                    html.Li(translate("Habilite novos armazéns na aba 'Produto e Armazéns' para distribuir melhor a carga.", lang)),
                    html.Li(translate("Reduza a quantidade ofertada na aba 'Oferta'.", lang))
                ], className="mb-0")"""

cap_sol_replace = """                html.P(html.B(translate("Possíveis Soluções:", lang))),
                html.Ul([
                    html.Li(translate("Aumente a capacidade estática dos armazéns utilizados na aba 'Armazéns'.", lang)),
                    html.Li(translate("Habilite novos armazéns na aba 'Produto e Armazéns' para distribuir melhor a carga.", lang)),
                    html.Li(translate("Reduza a quantidade ofertada na aba 'Oferta'.", lang)),
                    html.Li(translate("Verifique se as restrições de Frete Mínimo não estão forçando o envio de cargas maiores do que o armazém suporta receber de uma vez.", lang))
                ], className="mb-0")"""

content = content.replace(cap_search, cap_replace)
content = content.replace(cap_sol_search, cap_sol_replace)

# 2. Capacidade de Recepção Diária Insuficiente
rec_search = """                html.P(translate("O volume alocado superou a capacidade diária de recepção (em toneladas por dia) de um ou mais armazéns dentro do tempo estipulado.", lang), className="mb-2"),
                html.P([html.I(className="bi bi-info-circle-fill me-1"), html.B(translate("Atenção aos Resultados:", lang))], className="fw-bold mb-1"),
                html.P(translate("Os valores de custo total exibidos nesta página devem ser desconsiderados. Para evitar que o modelo ficasse 'sem solução', o sistema utilizou uma capacidade de recepção artificial com um custo unitário (multa) exorbitantemente alto. Resolva as pendências abaixo e rode o modelo novamente para obter os resultados reais.", lang), className="mb-2"),"""

rec_replace = """                html.P(translate("O volume alocado superou a capacidade diária de recepção (em toneladas por dia) de um ou mais armazéns dentro do tempo estipulado.", lang), className="mb-2"),
                html.P(translate("Interações complexas de regras: A recepção funciona como a 'porta de entrada' do armazém. Mesmo que haja muito espaço interno (capacidade estática) sobrando, se a velocidade com que o armazém consegue receber os caminhões for muito baixa, ocorrerá um gargalo. Além disso, se houver regras rígidas de 'Frete Mínimo', o modelo pode preferir estourar essa 'porta de entrada' para garantir que os caminhões não viagem vazios.", lang), className="mb-2"),
                html.P([html.I(className="bi bi-info-circle-fill me-1"), html.B(translate("Suposições do Modelo e Atenção aos Resultados:", lang))], className="fw-bold mb-1"),
                html.P(translate("Estes avisos não são erros de cálculo, mas reflexos de limitações físicas da sua operação. Para evitar que o modelo ficasse 'sem solução', o sistema preferiu 'forçar a entrada' da carga usando uma capacidade de recepção artificial com um custo (multa) exorbitantemente alto. Portanto, os valores de custo total exibidos nesta página devem ser desconsiderados até que a questão seja resolvida.", lang), className="mb-2"),"""

rec_sol_search = """                html.P(html.B(translate("Possíveis Soluções:", lang))),
                html.Ul([
                    html.Li(translate("Aumente a carga máxima de recepção diária ou os dias de alocação na configuração do modelo.", lang)),
                    html.Li(translate("Se estiver usando a capacidade do banco de dados, certifique-se de que os armazéns escolhidos possuem valores suficientes de recepção na base.", lang)),
                    html.Li(translate("Distribua melhor a oferta entre outros armazéns habilitados.", lang))
                ], className="mb-0")"""

rec_sol_replace = """                html.P(html.B(translate("Possíveis Soluções:", lang))),
                html.Ul([
                    html.Li(translate("Aumente a carga máxima de recepção diária ou o número de dias úteis na configuração do modelo para 'alargar a porta de entrada'.", lang)),
                    html.Li(translate("Se estiver usando a capacidade do banco de dados, certifique-se de que os armazéns escolhidos possuem valores suficientes de recepção na base.", lang)),
                    html.Li(translate("Distribua melhor a oferta entre outros armazéns habilitados que tenham uma recepção mais rápida.", lang)),
                    html.Li(translate("Verifique se as restrições de 'Carga mínima de frete' não estão obrigando o envio de volumes muito grandes de uma só vez para armazéns com recepção lenta.", lang))
                ], className="mb-0")"""

content = content.replace(rec_search, rec_replace)
content = content.replace(rec_sol_search, rec_sol_replace)

# 3. Conflito nas Regras de Frete Mínimo/Máximo
freight_search = """                html.P(translate("Existem ofertas não alocadas porque as restrições de frete (carga mínima ou máxima por viagem) inviabilizaram o escoamento total dessa carga para qualquer destino válido.", lang), className="mb-2"),
                html.P([html.I(className="bi bi-info-circle-fill me-1"), html.B(translate("Atenção aos Resultados:", lang))], className="fw-bold mb-1"),
                html.P(translate("Os custos totais sofreram penalização altíssima pela oferta não alocada. Quando uma rota de frete é amarrada entre um mínimo e um máximo, sobras que não formam um caminhão viável ou grandes volumes não absorvidos são penalizados em vez de transportados.", lang), className="mb-2"),"""

freight_replace = """                html.P(translate("Existem ofertas não alocadas porque as restrições de frete (carga mínima ou máxima por viagem) inviabilizaram o escoamento total dessa carga para qualquer destino válido.", lang), className="mb-2"),
                html.P(translate("Interações complexas de regras: Esse tipo de alerta ocorre quando os dados entram em conflito. Por exemplo, se a sua oferta restante for de 10 toneladas, mas você configurou que um caminhão só viaja se tiver no mínimo 30 toneladas (Frete Mínimo), essa sobra de 10 toneladas ficará travada na origem. O mesmo ocorre se um armazém só puder receber 15 toneladas por dia, mas o seu caminhão mínimo carrega 30 toneladas: o modelo não tem como fazer a entrega sem quebrar alguma regra.", lang), className="mb-2"),
                html.P([html.I(className="bi bi-info-circle-fill me-1"), html.B(translate("Suposições do Modelo e Atenção aos Resultados:", lang))], className="fw-bold mb-1"),
                html.P(translate("Não se trata de um erro no sistema, mas de um beco sem saída logístico. Nessas situações, em vez de não entregar nada, o modelo assume que essa carga problemática simplesmente não pôde ser alocada e aplica uma penalidade (multa) altíssima no custo total. Desconsidere os custos exibidos até ajustar os limites.", lang), className="mb-2"),"""

freight_sol_search = """                html.P(html.B(translate("Possíveis Soluções:", lang))),
                html.Ul([
                    html.Li(translate("Alivie as restrições de frete mínimo ou máximo na configuração do modelo.", lang)),
                    html.Li(translate("Certifique-se de que as quantidades ofertadas são compatíveis com os limites de carga estabelecidos.", lang))
                ], className="mb-0")"""

freight_sol_replace = """                html.P(html.B(translate("Possíveis Soluções:", lang))),
                html.Ul([
                    html.Li(translate("Reduza a exigência de 'Carga mínima de frete' na configuração do modelo para permitir que caminhões mais vazios façam o transporte das sobras.", lang)),
                    html.Li(translate("Certifique-se de que as quantidades ofertadas totais são múltiplos ou compatíveis com os limites de carga estabelecidos.", lang)),
                    html.Li(translate("Verifique se os armazéns de destino possuem 'Capacidade de Recepção Diária' suficiente para receber ao menos um caminhão inteiro do tamanho mínimo exigido.", lang))
                ], className="mb-0")"""

content = content.replace(freight_search, freight_replace)
content = content.replace(freight_sol_search, freight_sol_replace)

with open('src/view/view.py', 'w', encoding='utf-8') as f:
    f.write(content)
