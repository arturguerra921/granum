# Exemplos Gerados Localmente

Esta pasta é destinada a conter dados de exemplo gerados por scripts do projeto, que servem para testes locais (ex: estressar a aplicação com grandes volumes de ofertas).

Para gerar as planilhas de teste, rode o script `gerar_ofertas_teste.py` localizado na pasta `scripts/`:

```bash
python3 scripts/gerar_ofertas_teste.py
```

Os arquivos gerados (`.xlsx` ou `.csv`) serão salvos automaticamente na pasta `ofertas/` e são ignorados pelo Git para evitar poluição do repositório.

Você pode editar o script `scripts/gerar_ofertas_teste.py` para alterar:
- A quantidade de incremento entre planilhas
- O máximo de nós gerados
- O máximo de toneladas totais para evitar ultrapassar o limite do sistema
- O formato de saída (ex: `.xlsx` ou `.csv`)
