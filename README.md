# Jurimetria - Análise de Assédio Moral na Justiça do Trabalho

Este projeto realiza análise jurimétrica de decisões judiciais relacionadas a casos de assédio moral na Justiça do Trabalho do Brasil. Utilizando técnicas de coleta de dados, processamento de linguagem natural e visualização, o projeto busca identificar padrões, tendências e características dos processos judiciais envolvendo assédio moral.

## O que é Jurimetria?

Jurimetria é a aplicação de métodos quantitativos e estatísticos ao estudo do Direito. Ela utiliza dados jurídicos para extrair informações e padrões que possam auxiliar na compreensão da prática jurídica, fornecer insights para tomadas de decisão e prever tendências futuras.

## Funcionalidades

- **Coleta de dados**: Integração com a API pública do DataJud do CNJ para coletar processos de todos os Tribunais Regionais do Trabalho e do TST
- **Processamento de texto**: Utilização de técnicas de NLP para extrair informações relevantes das decisões judiciais
- **Análise estatística**: Identificação de padrões, correlações e tendências nas decisões sobre assédio moral
- **Visualização de dados**: Dashboard interativo para exploração e apresentação dos resultados

## 🆕 Novidades na Versão Atual

- **API Atualizada**: Implementação da integração com os endpoints Elasticsearch da API do DataJud para cada tribunal
- **Abrangência Expandida**: Coleta de processos desde 2016 até o presente, cobrindo todos os 24 TRTs e o TST
- **Queries Otimizadas**: Construção de queries Elasticsearch específicas para assédio moral, melhorando a precisão da coleta
- **Script de Análise**: Adição de ferramenta para análise exploratória rápida dos dados coletados
- **Melhorias de Performance**: Otimização do processo de coleta e processamento de grandes volumes de dados
- **Logging Aprimorado**: Sistema de logs mais detalhado para monitoramento do processo de coleta

## Estrutura do Projeto

```
jurimetria-jt/
├── data/                # Dados coletados e processados
│   ├── raw/             # Dados brutos coletados da API
│   └── processed/       # Dados processados para análise
├── src/                 # Código fonte
│   ├── collectors/      # Scripts de coleta de dados
│   ├── processors/      # Scripts de processamento de texto
│   ├── analysis/        # Scripts de análise estatística
│   └── dashboard/       # Código do dashboard interativo
├── notebooks/           # Jupyter notebooks para análises exploratórias
├── tests/               # Testes unitários
├── analyze.py           # Script para análise rápida dos dados coletados
└── requirements.txt     # Dependências do projeto
```

## Pré-requisitos

- Python 3.8 ou superior
- Acesso à API do DataJud (requer uma chave de API válida)
- Espaço em disco para armazenamento dos dados coletados

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/danilobortoli/jurimetria-jt.git
cd jurimetria-jt
```

2. Crie um ambiente virtual Python:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate   # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com sua chave de API do DataJud
```

## Uso

### Coleta de Dados

Para coletar decisões judiciais da API do DataJud:

```bash
python -m src.collectors.main
```

Este comando coletará processos relacionados a assédio moral de todos os tribunais trabalhistas (TST e TRTs) desde 2016 até o presente.

Para analisar rapidamente os dados coletados:

```bash
python analyze.py
```

### Processamento

Para processar os dados coletados e prepará-los para análise:

```bash
python -m src.processors.main
```

Este comando processará os arquivos JSON brutos, extrairá informações relevantes e gerará um arquivo CSV consolidado com os dados processados.

### Visualização

Para executar o dashboard interativo:

```bash
streamlit run src.dashboard.app
```

O dashboard permitirá a exploração visual dos dados, com filtros por tribunal, período, tipos de decisão, entre outros.

## Exemplos de Análises

- Distribuição geográfica dos casos de assédio moral por região/estado
- Evolução temporal do número de processos e decisões
- Taxa de procedência/improcedência dos pedidos de indenização
- Valor médio das indenizações concedidas
- Palavras e termos mais frequentes nas decisões judiciais
- Tempo médio de tramitação dos processos

## Detalhes Técnicos

### Coleta de Dados (DataJud API)

A coleta utiliza a API pública do DataJud, acessando endpoints específicos para cada tribunal através de consultas Elasticsearch. As principais funcionalidades incluem:

- Autenticação com APIKey no cabeçalho da requisição
- Paginação automática para coletar grandes volumes de dados
- Construção de queries Elasticsearch otimizadas para assédio moral
- Tratamento de erros e tentativas de reconexão
- Armazenamento dos dados em formato JSON

### Processamento de Texto

O processamento utiliza bibliotecas como spaCy e NLTK para:

- Extração de entidades nomeadas (pessoas, organizações, valores)
- Análise de sentimento para classificar decisões
- Contagem de palavras e frases relevantes
- Extração de metadados como datas, valores de indenização, etc.

## Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Crie um novo Pull Request

## Licença

Este projeto está licenciado sob a licença CC0 1.0 Universal - veja o arquivo LICENSE para mais detalhes.

## Contato

Danilo Bortoli - [@danilobortoli](https://github.com/danilobortoli)