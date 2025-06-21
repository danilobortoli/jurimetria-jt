# Novos Scripts para Análise de Fluxo e Estatística

Este documento descreve os novos scripts adicionados ao projeto para ampliar a análise dos dados coletados sobre assédio moral na Justiça do Trabalho.

## 1. Coleta Completa e Incremental

### `run_coleta_completa.py`

Script para execução da coleta completa de dados de assédio moral para todos os tribunais (TRT2-TRT24 e TST) e todos os anos (2015-2024), de forma incremental para evitar timeouts e sobrecarga na API.

```bash
# Exemplo de uso básico (coleta todos os tribunais e anos configurados)
python run_coleta_completa.py

# Coleta apenas um intervalo específico de TRTs
python run_coleta_completa.py --trt-inicio 2 --trt-fim 5

# Coleta apenas um intervalo específico de anos
python run_coleta_completa.py --ano-inicio 2020 --ano-fim 2023

# Incluir o TST na coleta
python run_coleta_completa.py --incluir-tst

# Pular a coleta e apenas processar/analisar os dados existentes
python run_coleta_completa.py --apenas-processar
```

## 2. Análise Estatística por Tribunal

### `analise_estatistica_tribunais.py`

Script para análise estatística detalhada por tribunal e visualização de resultados dos casos de assédio moral.

```bash
# Executar a análise estatística
python analise_estatistica_tribunais.py
```

Este script produz:
- Gráficos comparativos das taxas de sucesso por tribunal
- Evolução temporal dos resultados por tribunal
- Relatório estatístico detalhado em markdown

Arquivos de saída:
- `resultados_estatisticos/taxa_sucesso_primeira_instancia.png`
- `resultados_estatisticos/taxa_provimento_segunda_instancia.png`
- `resultados_estatisticos/evolucao_taxa_sucesso_primeira_instancia.png`
- `resultados_estatisticos/heatmap_taxa_sucesso.png`
- `resultados_estatisticos/relatorio_estatistico.md`

## 3. Análise Avançada de Fluxo de Decisões

### `analise_fluxo_avancada.py`

Script para análise avançada do fluxo de processos de assédio moral através das instâncias da Justiça do Trabalho. Implementa métodos mais sofisticados para rastrear o mesmo processo através das diferentes instâncias (1ª instância, 2ª instância, TST).

```bash
# Executar a análise de fluxo
python analise_fluxo_avancada.py
```

Este script implementa:
- Correspondência de processos entre instâncias usando similaridade de números
- Inferência sobre qual parte interpôs cada recurso
- Análise das taxas de sucesso de recursos por parte (trabalhador/empregador)
- Visualização do fluxo de decisões com grafos e diagramas de Sankey

Arquivos de saída:
- `resultados_fluxo/taxa_sucesso_por_instancia.png`
- `resultados_fluxo/taxa_sucesso_recursos.png`
- `resultados_fluxo/grafo_fluxo_decisoes.png`
- `resultados_fluxo/sankey_fluxo_decisoes.html` (se plotly estiver instalado)
- `resultados_fluxo/relatorio_fluxo_decisoes.md`
- `resultados_fluxo/grupos_relacionados.json`
- `resultados_fluxo/resultados_analise.json`

## 4. Sistema Completo Integrado

### `run_sistema_completo.py`

Script principal para execução do sistema completo de análise de assédio moral na Justiça do Trabalho. Orquestra todos os componentes do sistema.

```bash
# Executar o sistema completo
python run_sistema_completo.py

# Pular etapas específicas
python run_sistema_completo.py --pular-coleta
python run_sistema_completo.py --pular-processamento
python run_sistema_completo.py --pular-analise-estatistica
python run_sistema_completo.py --pular-analise-fluxo

# Configurar intervalo de anos e tribunais
python run_sistema_completo.py --ano-inicio 2020 --ano-fim 2023 --trt-inicio 2 --trt-fim 10

# Incluir o TST na análise
python run_sistema_completo.py --incluir-tst
```

Este script:
1. Coordena a execução de todos os outros scripts
2. Gerencia retentativas em caso de falhas
3. Gera um relatório final integrado com os resultados de todas as análises

Diretório de saída:
- `relatorio_final/` - Contém um relatório integrado e todos os gráficos e análises

## Dependências Adicionais

Para executar estes novos scripts, as seguintes dependências foram adicionadas ao `requirements.txt`:

```
matplotlib>=3.6.0
seaborn>=0.12.0
networkx>=2.8.0
tqdm>=4.64.0
ipywidgets>=8.0.0
```

## Notas Importantes

1. **Análise de fluxo de decisões**: A identificação de casos relacionados entre diferentes instâncias é um desafio devido à falta de padronização nos números de processo. O script implementa uma abordagem heurística que pode não ser 100% precisa.

2. **Inferência sobre a parte recorrente**: Na ausência de dados explícitos sobre qual parte interpôs cada recurso, o script faz inferências com base no resultado anterior e atual, o que pode não capturar toda a complexidade dos processos.

3. **Amostra limitada**: O número de casos em que é possível rastrear o fluxo completo pode ser relativamente pequeno em comparação com o total de decisões.

4. **Timeout da API**: A coleta incremental visa minimizar os problemas de timeout, mas ainda podem ocorrer interrupções. O sistema foi projetado para ser resiliente e continuar de onde parou.

5. **Visualizações interativas**: Algumas visualizações (como o diagrama de Sankey) requerem a biblioteca plotly. Se não estiver disponível, apenas os gráficos estáticos serão gerados.