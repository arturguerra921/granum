# Tutorial: Gerar Mapa do Brasil para Roteamento (OSRM)

Este guia é para quem vai realizar apenas o **pré-processamento dos dados do mapa**. Você não precisa entender de programação, apenas seguir os passos abaixo para gerar os arquivos necessários.

## Pré-requisitos

1.  **Docker Desktop:**
    *   Baixe e instale o [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/).
    *   Após instalar, abra o Docker Desktop e aguarde o ícone da baleia na barra de tarefas ficar estático (verde ou branco). **O Docker deve estar rodando durante todo o processo.**

2.  **Python:**
    *   Baixe e instale o [Python (versão mais recente)](https://www.python.org/downloads/).
    *   **IMPORTANTE:** Durante a instalação, marque a caixinha **"Add Python to PATH"**.

## Passo a Passo

1.  **Baixe este Repositório (Pasta do Projeto):**
    *   Baixe o arquivo ZIP deste projeto que lhe foi enviado.
    *   Extraia (descompacte) a pasta em um local fácil, como sua Área de Trabalho (`Desktop`).

2.  **Abra o Terminal na Pasta:**
    *   Abra a pasta extraída no Explorador de Arquivos.
    *   Clique com o botão direito em um espaço vazio da pasta e selecione **"Abrir no Terminal"** (ou segure `Shift` + clique com botão direito e selecione "Abrir janela do PowerShell aqui").

3.  **Execute o Script de Geração:**
    *   No terminal (janela preta ou azul que abriu), digite o seguinte comando e aperte `Enter`:
        ```powershell
        python scripts/setup_osrm.py
        ```
    *   **O que vai acontecer:**
        *   O script vai baixar o mapa do Brasil (~400MB).
        *   Ele vai iniciar o processamento pesado usando o Docker.
        *   **Isso pode demorar de 20 minutos a 1 hora**, dependendo do seu computador.
        *   Se aparecerem mensagens de "downloading image", é normal.

4.  **Finalização:**
    *   Quando terminar, você verá a mensagem: `OSRM processing complete.`
    *   O script criou uma pasta chamada `data` dentro da pasta do projeto.

## O Que Enviar de Volta?

1.  Vá até a pasta `data` que foi criada.
2.  Dentro dela, você encontrará uma pasta chamada `osrm`.
3.  Compacte (zipe) essa pasta `osrm` inteira.
    *   Ela conterá vários arquivos (como `.osrm`, `.osrm.hsgr`, etc.).
4.  Envie esse arquivo ZIP para o solicitante.

**Observação:** Você pode apagar a pasta do projeto e o Docker depois de enviar o arquivo, se desejar.
