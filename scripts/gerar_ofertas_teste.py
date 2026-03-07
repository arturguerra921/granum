import pandas as pd
import numpy as np
import os

# =============================================================================
# CONFIGURAÇÕES FÁCEIS PARA O USUÁRIO EDITAR
# =============================================================================
INCREMENTO_NOS = 10           # Quantos nós a mais serão adicionados em cada nova planilha
MAXIMO_NOS = 100              # Quantidade máxima de nós (a última planilha gerada terá essa quantidade)
MAXIMO_TONELADAS = 2_000_000  # Soma total (em toneladas) dos pesos para a última planilha (a máxima)
FORMATO_SAIDA = '.xlsx'       # Formato de arquivo para as planilhas geradas ('.xlsx' ou '.csv')

# Caminhos do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUNICIPIOS_CSV = os.path.join(PROJECT_ROOT, 'src', 'view', 'assets', 'data', 'municipios.csv')
ESTADOS_CSV = os.path.join(PROJECT_ROOT, 'src', 'view', 'assets', 'data', 'estados.csv')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'examples', 'ofertas')

# Lista de produtos típicos armazenados em silos, graneleiros e armazéns convencionais
PRODUTOS = ['Soja', 'Milho', 'Trigo', 'Arroz', 'Café', 'Feijão', 'Sorgo', 'Algodão', 'Aveia']

def gerar_planilhas_teste():
    print(f"Iniciando a geração de testes...")
    print(f"Configurações: Máx Nós = {MAXIMO_NOS}, Máx Toneladas = {MAXIMO_TONELADAS}, Incremento = {INCREMENTO_NOS}")

    # 1. Carregar a lista de municípios e estados
    if not os.path.exists(MUNICIPIOS_CSV):
        print(f"Erro: O arquivo de municípios não foi encontrado em {MUNICIPIOS_CSV}")
        return
    if not os.path.exists(ESTADOS_CSV):
        print(f"Erro: O arquivo de estados não foi encontrado em {ESTADOS_CSV}")
        return

    df_municipios = pd.read_csv(MUNICIPIOS_CSV)
    df_estados = pd.read_csv(ESTADOS_CSV)

    # O arquivo estados.csv pode ter BOM (Byte Order Mark), por segurança removemos e renomeamos
    # ou podemos simplesmente garantir que a coluna chave está correta
    if '\ufeffcodigo_uf' in df_estados.columns:
        df_estados.rename(columns={'\ufeffcodigo_uf': 'codigo_uf'}, inplace=True)

    # Fazer merge para obter a sigla da UF
    df_municipios = pd.merge(df_municipios, df_estados[['codigo_uf', 'uf']], on='codigo_uf', how='left')

    # Criar a coluna formatada "Cidade - UF"
    df_municipios['nome_formatado'] = df_municipios['nome'] + ' - ' + df_municipios['uf']

    # Garantir que há municípios suficientes
    total_municipios = len(df_municipios)
    if MAXIMO_NOS > total_municipios:
        print(f"Aviso: MAXIMO_NOS ({MAXIMO_NOS}) é maior que a quantidade de municípios ({total_municipios}). "
              f"Serão gerados múltiplos nós na mesma cidade.")

    # 2. Sortear e criar o DataFrame base máximo (o universo com MAXIMO_NOS)
    # Isso garante que a amostra de 20 contenha a de 10, e assim por diante
    np.random.seed(42)  # Seed para manter os exemplos sempre iguais caso rodado novamente

    indices_escolhidos = np.random.choice(df_municipios.index, size=MAXIMO_NOS, replace=True)
    df_base = df_municipios.loc[indices_escolhidos].copy().reset_index(drop=True)

    # 3. Adicionar as colunas de Oferta
    # Produtos aleatórios
    df_base['Produto'] = np.random.choice(PRODUTOS, size=MAXIMO_NOS)

    # Pesos (toneladas)
    # Para não ultrapassar MAXIMO_TONELADAS, geramos pesos aleatórios e depois normalizamos
    pesos_aleatorios = np.random.uniform(low=10, high=1000, size=MAXIMO_NOS)
    fator_normalizacao = MAXIMO_TONELADAS / pesos_aleatorios.sum()
    pesos_normalizados = pesos_aleatorios * fator_normalizacao

    # Arredondar para duas casas decimais
    df_base['Peso (ton)'] = np.round(pesos_normalizados, 2)

    # A soma das toneladas normalizadas pode diferir ligeiramente por causa do arredondamento.
    # Ajustar o último elemento para cravar em MAXIMO_TONELADAS, se desejar exatidão.
    diferenca = MAXIMO_TONELADAS - df_base['Peso (ton)'].sum()
    df_base.loc[df_base.index[-1], 'Peso (ton)'] += diferenca
    df_base['Peso (ton)'] = np.round(df_base['Peso (ton)'], 2)

    # Renomear as colunas para o formato da aplicação
    df_base.rename(columns={'nome_formatado': 'Cidade', 'latitude': 'Latitude', 'longitude': 'Longitude'}, inplace=True)

    # Filtrar apenas as colunas de interesse
    colunas_finais = ["Produto", "Peso (ton)", "Cidade", "Latitude", "Longitude"]
    df_base = df_base[colunas_finais]

    # 4. Criar o diretório de saída se não existir
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 5. Gerar progressivamente as planilhas (10, 20, 30... MAXIMO_NOS)
    nos_gerados = 0

    # Assegurar que vamos gerar de INCREMENTO_NOS em INCREMENTO_NOS
    passos = list(range(INCREMENTO_NOS, MAXIMO_NOS + 1, INCREMENTO_NOS))
    # Se o máximo não for múltiplo do incremento, garantir que o último passo seja o máximo
    if MAXIMO_NOS not in passos:
        passos.append(MAXIMO_NOS)

    for passo in passos:
        # Pegar as primeiras N linhas do dataframe base
        df_recorte = df_base.head(passo).copy()

        # O nome do arquivo vai indicar a quantidade de nós
        nome_arquivo = f"ofertas_teste_{passo}_nos{FORMATO_SAIDA}"
        caminho_arquivo = os.path.join(OUTPUT_DIR, nome_arquivo)

        # Salvar o arquivo no formato escolhido
        if FORMATO_SAIDA.lower() == '.csv':
            df_recorte.to_csv(caminho_arquivo, index=False, sep=';', encoding='utf-8-sig')
        elif FORMATO_SAIDA.lower() == '.xlsx':
            df_recorte.to_excel(caminho_arquivo, index=False)
        else:
            print(f"Formato {FORMATO_SAIDA} não suportado. Use '.csv' ou '.xlsx'.")
            break

        peso_total_passo = df_recorte['Peso (ton)'].sum()
        print(f"Gerado: {nome_arquivo} | Nós: {passo} | Total de Peso (ton): {peso_total_passo:,.2f}")

    print(f"\nFinalizado! Arquivos salvos em: {OUTPUT_DIR}")

if __name__ == "__main__":
    gerar_planilhas_teste()
