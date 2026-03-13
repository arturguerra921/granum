import json

def update_locale(file_path, updates):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for k, v in updates.items():
        data[k] = v

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

new_keys_en = {
    "A oferta excedeu a capacidade de armazenamento dos armazéns. Não há um erro no cálculo, mas sim uma limitação física na infraestrutura de armazenamento disponível para os armazéns utilizados.": "The supply exceeded the storage capacity of the warehouses. There is no calculation error, but rather a physical limitation in the storage infrastructure available for the used warehouses.",
    "Capacidade Local vs. Global: Somar a capacidade total de todos os armazéns não garante a viabilidade. Se um armazém tiver espaço vazio, mas possuir restrições de recepção diária ou de frete que forcem envios incompatíveis, o modelo pode ser obrigado a estourar a capacidade física de outro armazém para escoar a carga.": "Local vs. Global Capacity: Summing the total capacity of all warehouses does not guarantee viability. If a warehouse has empty space but has daily reception or freight restrictions that force incompatible shipments, the model may be forced to exceed the physical capacity of another warehouse to move the cargo.",
    "Estes avisos refletem escolhas matemáticas que o modelo precisou fazer para contornar gargalos logísticos. Para evitar que o sistema ficasse 'sem solução' e mostrar onde a operação trava, o modelo utilizou uma capacidade artificial com um custo (multa) exorbitantemente alto. Portanto, os valores de custo total exibidos nesta página devem ser desconsiderados até que a questão seja resolvida.": "These warnings reflect mathematical choices the model had to make to bypass logistical bottlenecks. To avoid the system becoming 'unsolvable' and to show where the operation stalls, the model used an artificial capacity with an exorbitantly high cost (penalty). Therefore, the total cost values displayed on this page should be disregarded until the issue is resolved.",
    "Verifique se as restrições de 'Carga mínima de frete' não estão forçando o envio de cargas maiores do que o armazém suporta receber.": "Check if 'Minimum freight load' restrictions are not forcing the shipment of loads larger than the warehouse can receive.",
    "Interações de regras: Mesmo que haja muito espaço interno (capacidade estática) sobrando, se a taxa diária de recepção for insuficiente, ocorrerá um gargalo. Além disso, se houver regras rígidas de 'Frete Mínimo', o modelo pode preferir estourar essa recepção diária para garantir que os caminhões não viagem vazios.": "Rule interactions: Even if there is plenty of internal space (static capacity) remaining, if the daily reception rate is insufficient, a bottleneck will occur. Furthermore, if there are strict 'Minimum Freight' rules, the model may prefer to exceed this daily reception to ensure trucks do not travel empty.",
    "Aumente a carga máxima de recepção diária ou o número de dias úteis na configuração do modelo.": "Increase the maximum daily reception load or the number of working days in the model configuration.",
    "Distribua melhor a oferta entre outros armazéns habilitados.": "Better distribute the supply among other enabled warehouses.",
    "Verifique se as restrições de 'Carga mínima de frete' não estão obrigando o envio de volumes muito grandes de uma só vez.": "Check if 'Minimum freight load' restrictions are not forcing the shipment of very large volumes at once.",
    "Interações de regras: Isso ocorre quando os dados entram em conflito. Por exemplo, se a sobra de oferta for de 10t, mas a exigência de Frete Mínimo for de 30t, as 10t não podem ser enviadas. O mesmo acontece se um armazém só puder receber 15t diárias, mas o caminhão mínimo carrega 30t: o modelo não tem como fazer a entrega sem quebrar alguma restrição.": "Rule interactions: This occurs when data conflicts. For example, if the remaining supply is 10t, but the Minimum Freight requirement is 30t, the 10t cannot be sent. The same happens if a warehouse can only receive 15t daily, but the minimum truck carries 30t: the model cannot make the delivery without breaking a restriction.",
    "Reduza a exigência de 'Carga mínima de frete' na configuração do modelo para permitir que as sobras sejam transportadas.": "Reduce the 'Minimum freight load' requirement in the model configuration to allow leftovers to be transported.",
    "Certifique-se de que as quantidades ofertadas totais são compatíveis com os limites de carga estabelecidos.": "Ensure that the total supplied quantities are compatible with the established load limits.",
    "Verifique se os armazéns de destino possuem 'Capacidade de Recepção Diária' suficiente para receber ao menos um caminhão do tamanho mínimo exigido.": "Check if the destination warehouses have enough 'Daily Reception Capacity' to receive at least one truck of the minimum required size."
}

new_keys_pt = {k: k for k in new_keys_en.keys()}

update_locale('src/locales/en.json', new_keys_en)
update_locale('src/locales/pt.json', new_keys_pt)
