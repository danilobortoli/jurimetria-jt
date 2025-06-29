# Investigação de Matching por Números Exatos

**Data**: 2025-06-29 18:17:51

## 🎯 Objetivo
Investigar por que não encontramos o mesmo número de processo nas três instâncias (G1→G2→TST).

## 📊 Resultados da Investigação

### Números Exatos
- **Total de números únicos**: 133,053
- **Números em múltiplas instâncias**: 5,115
- **Cadeias completas G1→G2→TST**: 0

### Padrões de Cadeia Encontrados
- **G1→SUP**: 10 (0.2%)
- **G2→SUP**: 10 (0.2%)


### Problemas Identificados
- **Variações sutis nos números**: 0
- **Números comuns TST↔TRT**: 5,115
- **Arquivos TST separados**: 3
- **Arquivos TRT**: 250

## 🚨 Hipóteses para a Falta de Conexões

1. **Fragmentação por tribunal**: Cada tribunal salva apenas seus próprios casos
2. **Numeração diferente**: TST pode usar numeração diferente para recursos
3. **Filtros de coleta**: Pode haver filtros que separam as instâncias
4. **Período de coleta**: Dados podem ter sido coletados em momentos diferentes

## 💡 Próximos Passos

1. Verificar se DataJud separa dados por tribunal/instância
2. Investigar se TST usa numeração específica para recursos
3. Analisar período de coleta dos dados
4. Validar com especialista em direito trabalhista
