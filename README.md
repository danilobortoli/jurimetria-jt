# Jurimetria do Assédio Moral na Justiça do Trabalho

## 📊 Sobre o Projeto

Este repositório contém a ferramenta de análise jurimétrica desenvolvida como suporte metodológico para a tese de doutorado "Assédio Moral Sistêmico como Engrenagem do Capital: Subjetividade dos Trabalhadores e Justiça em Disputa no Brasil Contemporâneo", de autoria de Andrea Antico Soares, apresentada ao Programa de Pós-Graduação em Ciências Sociais da UNESP em 2025.

### Contexto Acadêmico

- **Instituição**: Universidade Estadual Paulista (UNESP) - Campus de Marília
- **Programa**: Pós-Graduação em Ciências Sociais
- **Área de Concentração**: Determinações do Mundo do Trabalho
- **Orientador**: Prof. Dr. Leandro de Oliveira Galastri
- **Coorientador**: Prof. Dr. Giovanni Antonio Pinto Alves

## 🎯 Objetivo

Esta ferramenta foi desenvolvida para fornecer evidências empíricas quantitativas que sustentam a tese central de que o assédio moral não constitui meramente um desvio comportamental individual, mas opera como uma tecnologia de gestão funcional à racionalidade neoliberal do capitalismo contemporâneo.

Através da análise em larga escala de decisões judiciais, o projeto busca demonstrar como o Poder Judiciário brasileiro tem respondido a esse fenômeno estrutural, revelando padrões, contradições e tendências no tratamento jurídico do assédio moral nas relações de trabalho.

## 🔍 Questões de Pesquisa

A ferramenta ajuda a responder questões fundamentais da tese:

- Como a Justiça do Trabalho tem interpretado e quantificado o assédio moral?
- Existe correlação entre setores econômicos específicos (especialmente o financeiro) e a incidência de casos?
- Qual o impacto da Reforma Trabalhista (2017) nas decisões sobre assédio moral?
- Como se manifestam as contradições entre o reconhecimento formal do direito e sua efetivação prática?
- Em que medida o tratamento jurídico individualizado contribui para a despolitização do fenômeno?

## 🛠️ Funcionalidades Principais

### 1. Coleta de Dados

- Integração com a API DataJud do CNJ para acesso aos dados públicos
- Cobertura de todos os 24 TRTs e o TST
- Período analisado: 2015 até 2024
- Queries Elasticsearch otimizadas para termos relacionados a assédio moral
- Suporte para os códigos específicos da TPU/CNJ para assédio moral (1723, 14175, 14018)
- Coleta por códigos de movimento da TPU/CNJ (219, 220, 237, 242, 236)

### 2. Processamento e Análise

- NLP (Processamento de Linguagem Natural) para extração de informações relevantes
- Identificação de padrões decisórios e argumentativos
- Análise de sentimento para classificação das decisões
- Extração de valores de indenização e tempo de tramitação
- Classificação por instância e resultado (procedente/improcedente, provido/desprovido)

### 3. Visualização de Dados

- Dashboard interativo para exploração dos resultados
- Análises por região, tribunal, período e setor econômico
- Gráficos de tendências temporais e distribuições estatísticas

## 📈 Principais Métricas Analisadas

- Taxa de procedência/improcedência dos pedidos
- Valores médios de indenização por dano moral
- Tempo médio de tramitação dos processos
- Distribuição geográfica dos casos
- Setores econômicos mais demandados
- Evolução temporal pós-Reforma Trabalhista
- Frequência de termos e argumentos jurídicos

## 🏗️ Estrutura do Projeto

```
jurimetria-jt/
├── data/                    # Dados coletados e processados
│   ├── raw/                 # JSONs brutos da API DataJud
│   ├── processed/           # Dados estruturados para análise
│   └── consolidated/        # Dados consolidados sem duplicatas
├── src/                     # Código fonte
│   ├── collectors/          # Scripts de coleta via API
│   ├── processors/          # Processamento de texto e NLP
│   ├── analysis/            # Análises estatísticas
│   └── dashboard/           # Interface de visualização
├── notebooks/               # Jupyter notebooks exploratórios
├── tests/                   # Testes unitários
├── pipeline_assedio_moral.py # Pipeline completo com opções de linha de comando
├── run_pipeline_completo.py # Script de orquestração com retentativas e controle de erros
└── requirements.txt         # Dependências Python
```

## 🚀 Como Utilizar

### Pré-requisitos

- Python 3.8+
- Chave de API do DataJud
- Bibliotecas: pandas, numpy, spacy, nltk, streamlit, plotly, selenium

### Instalação

```bash
# Clone o repositório
git clone https://github.com/danilobortoli/jurimetria-jt.git
cd jurimetria-jt

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate   # Windows

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com sua chave da API DataJud
```

### Execução

#### Pipeline Completo (Automatizado)

```bash
# Executa todo o pipeline em sequência
python run_pipeline_completo.py

# Coleta apenas alguns TRTs específicos
python run_pipeline_completo.py --start-trt 1 --end-trt 10

# Pular etapas específicas
python run_pipeline_completo.py --skip-trts --skip-tst
```

#### Pipeline com Opções Específicas

```bash
# Coletar dados de todos os TRTs e TST
python pipeline_assedio_moral.py --collect

# Coletar apenas dados do TST
python pipeline_assedio_moral.py --collect --only-tst

# Consolidar dados coletados
python pipeline_assedio_moral.py --consolidate

# Processar dados consolidados
python pipeline_assedio_moral.py --process

# Analisar dados processados
python pipeline_assedio_moral.py --analyze
```

#### Scripts Individuais

```bash
# Coletar dados
python -m src.collectors.main

# Processar dados
python -m src.processors.main

# Analisar dados
python -m src.analysis.assedio_moral_analysis
```

## 📚 Fundamentação Teórica

Este projeto operacionaliza empiricamente os conceitos desenvolvidos na tese, particularmente:

- **Assédio moral como tecnologia de gestão**: não como desvio, mas como ferramenta sistêmica
- **Precarização subjetiva**: captura da subjetividade do trabalhador pelo capital
- **Financeirização e violência laboral**: especial atenção ao setor bancário
- **Contradições da forma jurídica**: entre proteção formal e desproteção real

## 🔬 Contribuição Científica

- **Metodológica**: Demonstra o potencial da jurimetria para análises críticas do Direito
- **Empírica**: Fornece dados quantitativos sobre um fenômeno usualmente tratado qualitativamente
- **Teórica**: Sustenta com evidências a tese do assédio moral como engrenagem do capital
- **Prática**: Oferece subsídios para políticas públicas e ação sindical

## ⚖️ Aspectos Éticos

- Utiliza apenas dados públicos disponibilizados pelo CNJ
- Preserva anonimato de partes e advogados
- Foco na análise agregada e identificação de padrões estruturais
- Compromisso com o uso responsável dos resultados

## 📊 Resultados Preliminares

Alguns achados significativos da pesquisa:

- Concentração de casos no setor financeiro/bancário
- Redução de ações pós-Reforma Trabalhista
- Disparidades regionais significativas nos valores de indenização
- Predomínio do tratamento individualizado vs. reconhecimento coletivo
- Correlação entre precarização e incidência de assédio

## 🤝 Como Contribuir

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Crie um novo Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença CC0 1.0 Universal - veja o arquivo LICENSE para mais detalhes.

## 📧 Contato

Para questões relacionadas ao projeto ou à pesquisa:

- **Autora**: Andrea Antico Soares
- **Instituição**: UNESP - Marília
- **Suporte Técnico**: Danilo Bortoli - [@danilobortoli](https://github.com/danilobortoli)

## 🙏 Agradecimentos

- CNJ pela disponibilização da API DataJud
- UNESP pelo apoio institucional
- Orientadores pela direção acadêmica
- Comunidade open source pelas ferramentas utilizadas