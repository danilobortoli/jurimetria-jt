# Relatório de Investigação - Matching de Processos

**Data**: 2025-06-29 17:56:34

## 🎯 Objetivo
Investigar por que os dados G2 (TRT como tribunal recursal) não estão sendo conectados às cadeias processuais G1→G2→TST.

## 🔍 Resultados dos Algoritmos de Matching

| Algoritmo | G1↔G2 | G1↔TST | G2↔TST | G1↔G2↔TST | Eficiência |
|-----------|-------|--------|--------|-----------|------------|
| current | 0 | 0 | 1 | 0 | 0.0% |
| full_digits | 0 | 0 | 1 | 0 | 0.0% |
| middle_section | 42 | 9 | 115 | 1 | 0.4% |
| year_sequential | 6 | 2 | 10 | 0 | 0.0% |
| smart_core | 6 | 2 | 10 | 0 | 0.0% |


## 📊 Análise dos Resultados

### Algoritmo Atual (current)
- **G1↔G2 matches**: 0
- **G1↔TST matches**: 0
- **G1↔G2↔TST matches**: 0

### Melhor Algoritmo (middle_section)
- **G1↔G2↔TST matches**: 1
- **Melhoria**: 1 matches vs 0 (infinita)

## 🚨 Problemas Identificados

1. **Algoritmo de extração inadequado**: O método atual pode não estar capturando corretamente o núcleo comum dos processos
2. **Fragmentação real dos dados**: Possivelmente os dados G2 não estão completos no dataset
3. **Diferenças na numeração**: G2 pode usar numeração diferente de G1 no mesmo tribunal

## 💡 Recomendações

1. **Implementar algoritmo 'middle_section'**: Mostrou 1 matches vs 0 do atual
2. **Investigar missing data**: Verificar se dados G2 estão realmente ausentes
3. **Análise manual**: Validar matches encontrados manualmente

## 🔧 Próximos Passos

1. Aplicar melhor algoritmo na análise completa
2. Investigar casos onde matching falha
3. Validar resultados com especialista jurídico
