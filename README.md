# Jurimetria - Análise de Assédio Moral na Justiça do Trabalho

Este projeto realiza análise jurimétrica de decisões judiciais relacionadas a casos de assédio moral na Justiça do Trabalho.

## Funcionalidades

- Coleta de decisões judiciais através de APIs e web scraping
- Processamento e análise de texto das decisões
- Identificação de padrões e tendências jurisprudenciais
- Dashboard interativo para visualização dos resultados

## Estrutura do Projeto

```
jurimetria-jt/
├── data/               # Dados coletados e processados
├── src/               # Código fonte
│   ├── collectors/    # Scripts de coleta de dados
│   ├── processors/    # Scripts de processamento
│   ├── analysis/      # Scripts de análise
│   └── dashboard/     # Código do dashboard
├── notebooks/         # Jupyter notebooks para análises exploratórias
└── tests/            # Testes unitários
```

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual Python:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

## Uso

1. Coleta de dados:
```bash
python src/collectors/main.py
```

2. Processamento:
```bash
python src/processors/main.py
```

3. Executar o dashboard:
```bash
streamlit run src/dashboard/app.py
```

## Contribuição

Contribuições são bem-vindas! Por favor, leia o arquivo CONTRIBUTING.md para detalhes sobre nosso código de conduta e o processo para enviar pull requests.

## Licença

Este projeto está licenciado sob a licença CC0 1.0 Universal - veja o arquivo LICENSE para mais detalhes. 