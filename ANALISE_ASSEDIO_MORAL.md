# Análise de Assédio Moral na Justiça do Trabalho

Este documento descreve a implementação específica para análise de processos de assédio moral na Justiça do Trabalho, categorizados por instância e resultado conforme os códigos de movimento e assunto da Tabela Processual Unificada (TPU) do CNJ.

## Códigos da Tabela CNJ Utilizados

### Códigos de Assunto para Assédio Moral

Na Tabela de Assuntos do CNJ, o "assédio moral" aparece em três códigos diferentes que coexistem devido a revisões sucessivas da tabela:

1. **Código 1723** - Tradição da Justiça do Trabalho
   - Hierarquia: Direito do Trabalho → Responsabilidade Civil do Empregador → Indenização por Dano Moral → Assédio Moral

2. **Código 14175** - Introduzido na revisão de 2022-2024 para tribunais estaduais, federais e militares
   - Hierarquia: Direito Administrativo e outras matérias de Direito Público → Responsabilidade da Administração → Indenização por Dano Moral → Assédio Moral

3. **Código 14018** - Rótulo unificado adotado nas versões mais recentes do PJe
   - Utilizado em vários tribunais em paralelo ao código 1723

### Códigos de Movimento Utilizados

A análise é baseada nos seguintes códigos de movimento:

- **Primeira Instância**:
  - **219**: Procedência (resultado favorável ao trabalhador)
  - **220**: Improcedência (resultado desfavorável ao trabalhador)

- **Segunda Instância e TST**:
  - **237**: Provimento do recurso (recurso acolhido)
  - **242**: Desprovimento do recurso (recurso não provido/denegado)
  - **236**: Negação de seguimento (alternativa ao 242 em alguns tribunais)

## Pipeline de Análise

O pipeline completo implementado para esta análise inclui:

### 1. Coleta de Dados

- Extração via DataJud/SGT-CNJ com filtros específicos pelos códigos de movimento (219, 220, 237, 242, 236)
- Busca por processos classificados com os códigos de assunto específicos para assédio moral:
  - 1723: Tradicional da Justiça do Trabalho
  - 14175: Introduzido na revisão de 2022-2024 para outros tribunais
  - 14018: Rótulo unificado do PJe
- Período de coleta: 2008-2024
- Coleta separada para cada tribunal (TST e TRTs)
- Separação entre decisões de primeira e segunda instância

### 2. Processamento

- Normalização dos dados usando o número do processo como chave para evitar duplicidades
- Classificação das decisões com base nos códigos de movimento
- Extração de metadados: tribunal, vara, órgão colegiado, relator, datas, etc.
- Processamento de texto usando NLP para extrair entidades e informações relevantes
- Padronização dos resultados para análise estatística

### 3. Análise

- **Primeira Instância**: Separação entre procedentes e improcedentes
- **Segunda Instância**: Separação entre recursos providos e desprovidos
- **TST**: Separação entre recursos providos e desprovidos
- Cálculo de estatísticas por tribunal e instância
- Análise de fatores que influenciam o resultado (ex: menção a laudo pericial)
- Geração de gráficos e relatório detalhado

## Como Executar

O script `pipeline_assedio_moral.py` permite executar todo o pipeline ou apenas partes específicas:

```bash
# Executar todo o pipeline
python pipeline_assedio_moral.py --all

# Apenas coletar dados
python pipeline_assedio_moral.py --collect

# Apenas processar dados já coletados
python pipeline_assedio_moral.py --process

# Apenas analisar dados já processados
python pipeline_assedio_moral.py --analyze
```

## Resultados

Após a execução completa do pipeline, os seguintes resultados estarão disponíveis:

1. **Dados brutos**: Armazenados em `/data/raw/` em formato JSON
2. **Dados processados**: Armazenados em `/data/processed/processed_decisions.csv`
3. **Análises**: Armazenadas em `/data/analysis/`
   - Relatório em markdown: `relatorio_assedio_moral.md`
   - Gráficos: Diversos arquivos PNG com visualizações

## Interpretação dos Resultados

Os resultados são apresentados separando claramente:

- **Primeira Instância**: Procedentes vs. Improcedentes
- **Segunda Instância (TRTs)**: Recursos Providos vs. Desprovidos
- **TST**: Recursos Providos vs. Desprovidos

Esta separação permite analisar o comportamento do judiciário trabalhista em diferentes instâncias e identificar tendências e padrões nas decisões sobre assédio moral.

## Notas Importantes

1. A análise evita a duplicidade de contagem de processos, dando preferência à instância mais recente em caso de múltiplas decisões para o mesmo processo.

2. Alguns tribunais podem usar códigos alternativos para os mesmos movimentos, o que foi considerado na implementação.

3. A presença de laudo pericial e sua influência no resultado é verificada através da análise de texto das decisões.

4. Todas as decisões são classificadas binarialmente (favorável/desfavorável ao trabalhador) para facilitar a análise estatística.

5. A coleta inclui os processos desde 2008 até o presente, permitindo análise temporal das tendências de decisão.