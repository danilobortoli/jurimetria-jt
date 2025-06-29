# Relatório de Análise Avançada da Taxa de Sucesso de Recursos: Assédio Moral na Justiça do Trabalho

## Metodologia

Esta análise considera a cadeia completa de decisões para identificar corretamente:

1. **Quem interpôs cada recurso**: Trabalhador ou empregador
2. **Taxa de sucesso específica**: Para recursos de trabalhadores vs empregadores
3. **Padrões de reversão**: Entre diferentes instâncias
4. **Tags de movimento**: Análise baseada nos códigos de movimento da TPU/CNJ

### Códigos de Movimento Utilizados

A análise é baseada nos códigos de movimento da TPU/CNJ:

- **219**: Procedência
- **220**: Improcedência
- **237**: Provimento
- **242**: Desprovimento
- **236**: Negação de Seguimento

## Visão Geral

- **Total de cadeias de recursos analisadas**: 5463
- **Cadeias completas** (1ª → 2ª → TST): 24
- **Cadeias parciais** (1ª → 2ª ou 2ª → TST): 5439

## Taxa de Sucesso de Recursos de Trabalhadores

| Instância | Recursos com Sucesso | Recursos sem Sucesso | Total | Taxa de Sucesso |
|-----------|----------------------|----------------------|-------|----------------|
| TRT | 64 | 9 | 73 | 87.7% |
| TST | 1 | 0 | 1 | 100.0% |

## Taxa de Sucesso de Recursos de Empregadores

| Instância | Recursos com Sucesso | Recursos sem Sucesso | Total | Taxa de Sucesso |
|-----------|----------------------|----------------------|-------|----------------|
| TRT | 11 | 1 | 12 | 91.7% |
| TST | 0 | 3 | 3 | 0.0% |

## Análise por Tribunal

| Tribunal | Recursos Trabalhador | Taxa Sucesso | Recursos Empregador | Taxa Sucesso |
|----------|---------------------|--------------|---------------------|--------------|
| TRT2 | 33 | 90.9% | 6 | 100.0% |
| TRT4 | 15 | 73.3% | 1 | 100.0% |
| TRT15 | 8 | 100.0% | 3 | 66.7% |
| TRT5 | 5 | 60.0% | 1 | 100.0% |
| TRT3 | 4 | 100.0% | 1 | 100.0% |
| TRT1 | 4 | 100.0% | 0 | 0.0% |
| TRT9 | 4 | 100.0% | 0 | 0.0% |

## Padrões de Fluxo Mais Comuns

| Padrão de Fluxo | Número de Casos |
|----------------|------------------|
| Primeira Instância:Improcedente -> TST:Desprovido | 2941 |
| Segunda Instância:Provido -> TST:Desprovido | 866 |
| Primeira Instância:Procedente -> TST:Desprovido | 649 |
| Primeira Instância:Improcedente -> TST:Provido | 249 |
| Segunda Instância:Desprovido -> TST:Desprovido | 182 |
| Segunda Instância:Provido -> TST:Provido | 142 |
| Primeira Instância:Improcedente -> Primeira Instância:Improcedente | 121 |
| Primeira Instância:Procedente -> TST:Provido | 70 |
| Primeira Instância:Improcedente -> Segunda Instância:Provido | 61 |
| Primeira Instância:Procedente -> Primeira Instância:Improcedente | 37 |
| Segunda Instância:Desprovido -> TST:Provido | 30 |
| Primeira Instância:Improcedente -> Primeira Instância:Procedente | 30 |
| Primeira Instância:Procedente -> Segunda Instância:Provido | 10 |
| Primeira Instância:Improcedente -> Primeira Instância:Improcedente -> TST:Desprovido | 10 |
| Primeira Instância:Improcedente -> Segunda Instância:Desprovido | 9 |

## Conclusões

1. **Taxa geral de sucesso de recursos de trabalhadores**: 87.8% (74 recursos analisados)

2. **Taxa geral de sucesso de recursos de empregadores**: 73.3% (15 recursos analisados)

3. **Os recursos de trabalhadores têm 14.5 pontos percentuais a mais de sucesso** em comparação com os recursos de empregadores.

4. **Os recursos de trabalhadores têm maior sucesso no TST** (12.3 pontos percentuais a mais que no TRT).

### Limitações da Análise

1. **Identificação de recursos**: A análise baseia-se na inferência de quem interpôs cada recurso com base no resultado anterior e atual.
2. **Correspondência entre instâncias**: A vinculação de processos entre instâncias pode não ser perfeita devido a diferentes formatos de numeração.
3. **Amostra limitada**: O número de casos que tramitaram em múltiplas instâncias pode ser limitado.
4. **Códigos de movimento**: Alguns tribunais podem usar códigos alternativos para os mesmos movimentos.

Relatório gerado em: 2025-06-29 12:32:31