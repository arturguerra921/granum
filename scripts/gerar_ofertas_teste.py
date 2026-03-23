import pandas as pd
import numpy as np
import os

# =============================================================================
# CONFIGURAÇÕES FÁCEIS PARA O USUÁRIO EDITAR
# =============================================================================
INCREMENTO_OFERTAS = 10       # Incremento na quantidade de nós de oferta (supply) em cada nova planilha
MAXIMO_OFERTAS = 50           # Quantidade máxima de nós de oferta
INCREMENTO_ARMAZENS = 5       # Incremento na quantidade de armazéns (demand) em cada nova planilha
MAXIMO_ARMAZENS = 25          # Quantidade máxima de armazéns
MAXIMO_TONELADAS = 2_000_000  # Soma total máxima (em toneladas) de oferta permitida
MAX_RECEPTION_PERCENTAGE = 0.8 # Porcentagem máxima da capacidade de recepção total permitida para o peso da oferta
FORMATO_SAIDA = '.xlsx'       # Formato de arquivo para as planilhas geradas ('.xlsx' ou '.csv')

# Caminhos do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUNICIPIOS_CSV = os.path.join(PROJECT_ROOT, 'src', 'view', 'assets', 'data', 'municipios.csv')
ESTADOS_CSV = os.path.join(PROJECT_ROOT, 'src', 'view', 'assets', 'data', 'estados.csv')
ARMAZENS_CSV = os.path.join(PROJECT_ROOT, 'src', 'view', 'assets', 'data', 'Armazens_Cadastrados_Base.csv')
OUTPUT_DIR_OFERTAS = os.path.join(PROJECT_ROOT, 'examples', 'ofertas')
OUTPUT_DIR_ARMAZENS = os.path.join(PROJECT_ROOT, 'examples', 'armazens')

# Lista de produtos típicos armazenados em silos, graneleiros e armazéns convencionais
PRODUTOS = ['Soja', 'Milho', 'Trigo', 'Arroz', 'Café', 'Feijão', 'Sorgo', 'Algodão', 'Aveia']

def gerar_planilhas_teste():
    print(f"Iniciando a geração de testes...")
    print(f"Configurações: Máx Ofertas = {MAXIMO_OFERTAS}, Máx Armazéns = {MAXIMO_ARMAZENS}, Máx Toneladas = {MAXIMO_TONELADAS}")

    # 1. Carregar os dados base
    if not os.path.exists(MUNICIPIOS_CSV):
        print(f"Erro: O arquivo de municípios não foi encontrado em {MUNICIPIOS_CSV}")
        return
    if not os.path.exists(ESTADOS_CSV):
        print(f"Erro: O arquivo de estados não foi encontrado em {ESTADOS_CSV}")
        return
    if not os.path.exists(ARMAZENS_CSV):
        print(f"Erro: O arquivo de armazéns não foi encontrado em {ARMAZENS_CSV}")
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

    df_armazens = pd.read_csv(ARMAZENS_CSV, sep=';', skiprows=1, encoding='latin1')

    # Garantir que há municípios suficientes
    total_municipios = len(df_municipios)
    if MAXIMO_OFERTAS > total_municipios:
        print(f"Aviso: MAXIMO_OFERTAS ({MAXIMO_OFERTAS}) é maior que a quantidade de municípios ({total_municipios}). "
              f"Serão gerados múltiplos nós de oferta na mesma cidade.")

    # 2. Preparar os dados de Armazéns
    def parse_number(val):
        if pd.isna(val) or val == '':
            return np.nan
        if isinstance(val, (int, float)):
            return float(val)
        val = str(val).strip()
        if not val:
            return np.nan
        # Remover pontos de milhar e trocar vírgula por ponto
        val = val.replace('.', '').replace(',', '.')
        try:
            return float(val)
        except ValueError:
            return np.nan

    df_armazens['_cap_estatica_num'] = df_armazens['Capacidade (t)'].apply(parse_number)
    df_armazens['_cap_recepcao_num'] = df_armazens['Capacidade de Recepção'].apply(parse_number)

    # Filtrar armazéns que têm ambas as capacidades válidas (maiores que 0)
    filtro_armazens_validos = (df_armazens['_cap_estatica_num'] > 0) & (df_armazens['_cap_recepcao_num'] > 0)
    df_armazens_validos = df_armazens[filtro_armazens_validos].copy()

    total_armazens_validos = len(df_armazens_validos)
    if total_armazens_validos == 0:
        print("Erro: Nenhum armazém com 'Capacidade (t)' e 'Capacidade de Recepção' válidas foi encontrado no arquivo base.")
        return
    if MAXIMO_ARMAZENS > total_armazens_validos:
         print(f"Aviso: MAXIMO_ARMAZENS ({MAXIMO_ARMAZENS}) é maior que a quantidade de armazéns válidos ({total_armazens_validos}). "
               f"Serão sorteados armazéns repetidos.")

    # 3. Criar os DataFrames Base Máximos
    np.random.seed(42)  # Seed para manter os exemplos sempre iguais

    # Base de Ofertas
    indices_municipios = np.random.choice(df_municipios.index, size=MAXIMO_OFERTAS, replace=True)
    df_ofertas_base = df_municipios.loc[indices_municipios].copy().reset_index(drop=True)
    df_ofertas_base.rename(columns={'nome_formatado': 'Cidade', 'latitude': 'Latitude', 'longitude': 'Longitude'}, inplace=True)
    df_ofertas_base['Produto'] = np.random.choice(PRODUTOS, size=MAXIMO_OFERTAS)

    # Base de Armazéns
    indices_armazens = np.random.choice(df_armazens_validos.index, size=MAXIMO_ARMAZENS, replace=(MAXIMO_ARMAZENS > total_armazens_validos))
    df_armazens_base = df_armazens_validos.loc[indices_armazens].copy().reset_index(drop=True)

    # 4. Limpar e criar os diretórios de saída
    os.makedirs(OUTPUT_DIR_OFERTAS, exist_ok=True)
    for filename in os.listdir(OUTPUT_DIR_OFERTAS):
        file_path = os.path.join(OUTPUT_DIR_OFERTAS, filename)
        if os.path.isfile(file_path) and filename != '.gitkeep':
            os.unlink(file_path)

    os.makedirs(OUTPUT_DIR_ARMAZENS, exist_ok=True)
    for filename in os.listdir(OUTPUT_DIR_ARMAZENS):
        file_path = os.path.join(OUTPUT_DIR_ARMAZENS, filename)
        if os.path.isfile(file_path) and filename != '.gitkeep':
            os.unlink(file_path)

    # 5. Gerar progressivamente os arquivos pareados
    passos_ofertas = list(range(INCREMENTO_OFERTAS, MAXIMO_OFERTAS + 1, INCREMENTO_OFERTAS))
    if MAXIMO_OFERTAS not in passos_ofertas:
        passos_ofertas.append(MAXIMO_OFERTAS)

    passos_armazens = list(range(INCREMENTO_ARMAZENS, MAXIMO_ARMAZENS + 1, INCREMENTO_ARMAZENS))
    if MAXIMO_ARMAZENS not in passos_armazens:
        passos_armazens.append(MAXIMO_ARMAZENS)

    # Pegar o tamanho máximo para gerar todos os casos possíveis pareados
    max_passos = max(len(passos_ofertas), len(passos_armazens))

    # Preencher a lista mais curta para que ambas tenham o mesmo tamanho repetindo o último elemento
    while len(passos_ofertas) < max_passos:
        passos_ofertas.append(passos_ofertas[-1])
    while len(passos_armazens) < max_passos:
        passos_armazens.append(passos_armazens[-1])

    test_cases = list(zip(passos_ofertas, passos_armazens))
    # Remover duplicatas que podem surgir no pareamento final
    test_cases = sorted(list(set(test_cases)))

    for num_ofertas, num_armazens in test_cases:
        # A) Preparar o recorte de Armazéns
        df_armazens_recorte = df_armazens_base.head(num_armazens).copy()
        total_estatica = df_armazens_recorte['_cap_estatica_num'].sum()
        total_recepcao = df_armazens_recorte['_cap_recepcao_num'].sum()
        recepcao_limite = total_recepcao * MAX_RECEPTION_PERCENTAGE

        # Remover colunas temporárias numéricas para salvar igual ao original
        df_armazens_final = df_armazens_recorte.drop(columns=['_cap_estatica_num', '_cap_recepcao_num'])

        # B) Determinar o limite máximo de peso para as Ofertas
        peso_maximo_permitido = min(MAXIMO_TONELADAS, total_estatica, recepcao_limite)

        # C) Preparar o recorte de Ofertas
        df_ofertas_recorte = df_ofertas_base.head(num_ofertas).copy()

        pesos_aleatorios = np.random.uniform(low=10, high=1000, size=num_ofertas)
        fator_normalizacao = peso_maximo_permitido / pesos_aleatorios.sum()
        pesos_normalizados = pesos_aleatorios * fator_normalizacao

        df_ofertas_recorte['Peso (ton)'] = np.round(pesos_normalizados, 2)

        # Ajustar o último elemento para cravar no peso_maximo_permitido (devido a arredondamentos)
        diferenca = peso_maximo_permitido - df_ofertas_recorte['Peso (ton)'].sum()
        df_ofertas_recorte.loc[df_ofertas_recorte.index[-1], 'Peso (ton)'] += diferenca
        df_ofertas_recorte['Peso (ton)'] = np.round(df_ofertas_recorte['Peso (ton)'], 2)

        # Filtrar as colunas de interesse
        colunas_finais_ofertas = ["Produto", "Peso (ton)", "Cidade", "Latitude", "Longitude"]
        df_ofertas_final = df_ofertas_recorte[colunas_finais_ofertas]

        # D) Salvar os arquivos
        sufixo = f"_{num_ofertas}_sup_{num_armazens}_dem{FORMATO_SAIDA}"
        nome_arquivo_ofertas = f"ofertas{sufixo}"
        nome_arquivo_armazens = f"armazens{sufixo}"

        caminho_ofertas = os.path.join(OUTPUT_DIR_OFERTAS, nome_arquivo_ofertas)
        caminho_armazens = os.path.join(OUTPUT_DIR_ARMAZENS, nome_arquivo_armazens)

        if FORMATO_SAIDA.lower() == '.csv':
            df_ofertas_final.to_csv(caminho_ofertas, index=False, sep=';', encoding='utf-8-sig')
            df_armazens_final.to_csv(caminho_armazens, index=False, sep=';', encoding='utf-8-sig')
        elif FORMATO_SAIDA.lower() == '.xlsx':
            df_ofertas_final.to_excel(caminho_ofertas, index=False)
            df_armazens_final.to_excel(caminho_armazens, index=False)
        else:
            print(f"Formato {FORMATO_SAIDA} não suportado. Use '.csv' ou '.xlsx'.")
            break

        print(f"Gerados: {nome_arquivo_ofertas} e {nome_arquivo_armazens}")
        print(f"  -> Nós de Oferta: {num_ofertas} | Peso Total: {df_ofertas_final['Peso (ton)'].sum():,.2f} ton")
        print(f"  -> Armazéns: {num_armazens} | Cap. Estática: {total_estatica:,.2f} | Limite Recepção: {recepcao_limite:,.2f} ({MAX_RECEPTION_PERCENTAGE*100}%)\n")

    print(f"Finalizado!\nArquivos de oferta salvos em: {OUTPUT_DIR_OFERTAS}\nArquivos de armazém salvos em: {OUTPUT_DIR_ARMAZENS}")

if __name__ == "__main__":
    gerar_planilhas_teste()
