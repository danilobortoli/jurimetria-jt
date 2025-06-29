#!/usr/bin/env python3
"""
Análise encadeada das decisões de processos trabalhistas:
- Agrupa por numero_processo (usando apenas os 16 primeiros dígitos - raiz CNJ)
- Ordena por instância/tribunal e data
- Identifica reversões de resultado (ex: trabalhador perdeu na 1ª instância, mas ganhou recurso no TRT ou TST)
- Calcula taxas de reversão/sucesso de recursos do trabalhador
- Salva relatório em results/relatorio_cadeia_decisoes_fix.md
"""

import os
import pandas as pd
import re
from datetime import datetime
from collections import Counter

# Configurações gerais
data_path = "data/processed/processed_decisions.csv"
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

# Lê os dados processados
print("Carregando dados...")
df = pd.read_csv(data_path, low_memory=False)
print(f"Total de registros: {len(df)}")

# Converte datas para datetime
for col in ["data_ajuizamento", "data_julgamento"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# Função para padronizar resultados
RESULT_MAP = {
    'improcedente': 'Improcedente',
    'procedente': 'Procedente',
    'provido': 'Provido',
    'desprovido': 'Desprovido',
}
def normalize_result(res):
    if pd.isna(res):
        return 'Desconhecido'
    res = str(res).strip().lower()
    for key in RESULT_MAP:
        if key in res:
            return RESULT_MAP[key]
    return res.capitalize()

df['resultado_norm'] = df['resultado'].apply(normalize_result)

# Confia diretamente na coluna 'instancia' para determinar a ordem
def get_instance_order(row):
    """
    Determina a ordem/nível da instância judicial com base na coluna 'instancia'.
    """
    inst = str(row['instancia']).strip() if not pd.isna(row['instancia']) else ''
    
    if inst == 'Primeira Instância':
        return 1
    elif inst == 'Segunda Instância':
        return 2
    elif inst == 'TST':
        return 3
    
    # Caso não consiga identificar, usa o tribunal como fallback
    trib = str(row['tribunal']).strip().upper() if not pd.isna(row['tribunal']) else ''
    if trib == 'TST':
        return 3
    
    return 99  # Desconhecido

df['instance_order'] = df.apply(get_instance_order, axis=1)

# Extrai a raiz CNJ (16 primeiros dígitos) dos números de processo
def extract_cnj_root(num):
    """
    Extrai a raiz CNJ (16 primeiros dígitos) do número de processo.
    Isso inclui: sequencial (7) + DV (2) + ano (4) + justiça (1) + tribunal (2)
    e exclui os 4 últimos dígitos que mudam entre as instâncias.
    """
    if pd.isna(num):
        return None
    
    # Remove caracteres não numéricos
    digits_only = re.sub(r'\D', '', str(num))
    
    # Verifica se temos pelo menos 16 dígitos (formato CNJ completo tem 20)
    if len(digits_only) >= 16:
        return digits_only[:16]
    
    # Para números mais curtos, retorna None
    return None

# Adiciona coluna com a raiz CNJ (16 primeiros dígitos)
df['cnj_root'] = df['numero_processo'].apply(extract_cnj_root)

# Extrai os 4 últimos dígitos (código do órgão julgador)
def extract_orgao_code(num):
    """Extrai os 4 últimos dígitos que representam o código do órgão julgador."""
    if pd.isna(num):
        return None
    
    digits_only = re.sub(r'\D', '', str(num))
    
    if len(digits_only) >= 20:
        return digits_only[-4:]
    
    return None

df['cod_orgao'] = df['numero_processo'].apply(extract_orgao_code)

# Análise das raízes CNJ
print("\nAnálise das raízes CNJ:")
total_roots = df['cnj_root'].count()
unique_roots = df['cnj_root'].nunique()
print(f"Total de raízes CNJ extraídas: {total_roots}")
print(f"Raízes CNJ únicas: {unique_roots}")
print(f"Taxa de unicidade: {unique_roots / total_roots:.2%}")

# Conte quantas raízes aparecem em múltiplas instâncias
root_instances = df.groupby('cnj_root')['instance_order'].nunique()
multi_instance_roots = root_instances[root_instances > 1].count()
print(f"Raízes CNJ que aparecem em múltiplas instâncias: {multi_instance_roots}")

# Agrupa por raiz CNJ
groups = df.groupby('cnj_root')

cadeias = []
reversao_trt = 0
reversao_tst = 0
casos_totais = 0
casos_com_multiplas_instancias = 0
cadeias_exemplo = Counter()

# Debug: exemplos de cadeias reais
print("\nExemplos de cadeias reais:")
exemplo_count = 0

for raiz, group in groups:
    # Pula grupos com raiz CNJ inválida
    if raiz is None or pd.isna(raiz):
        continue
        
    # Ordena primeiro por instância, depois por data de julgamento
    group_sorted = group.sort_values(['instance_order', 'data_julgamento'])
    
    # Verifica se temos decisões em múltiplas instâncias
    instancias_unicas = group_sorted['instance_order'].nunique()
    
    # Conta apenas processos com instâncias válidas (1, 2 ou 3)
    if not all(inst in [1, 2, 3] for inst in group_sorted['instance_order'].unique()):
        continue
    
    if instancias_unicas > 1:
        casos_com_multiplas_instancias += 1
    
    resultados = list(group_sorted['resultado_norm'])
    instancias = list(group_sorted['instance_order'])
    tribunais = list(group_sorted['tribunal'])
    numeros_originais = list(group_sorted['numero_processo'])
    orgaos = list(group_sorted['cod_orgao'])
    
    casos_totais += 1
    cadeia = ' -> '.join(resultados)
    cadeias_exemplo[cadeia] += 1
    
    # Debug: mostrar exemplos de processos com múltiplas instâncias
    if instancias_unicas > 1 and exemplo_count < 10:
        print(f"Raiz CNJ: {raiz}")
        print(f"Números originais: {numeros_originais}")
        print(f"Códigos de órgãos: {orgaos}")
        print(f"Cadeia: {cadeia}")
        print(f"Instâncias: {instancias}")
        print(f"Tribunais: {tribunais}")
        print("---")
        exemplo_count += 1
    
    # Reversão no TRT: perdeu na 1ª, recurso do trabalhador foi provido no TRT
    if len(resultados) >= 2 and instancias_unicas >= 2:
        # Verifica se existe decisão de 1ª instância como Improcedente
        primeira_instancia_index = None
        for i, inst in enumerate(instancias):
            if inst == 1:
                primeira_instancia_index = i
                break
        
        # Verifica se existe decisão de 2ª instância como Provido
        segunda_instancia_index = None
        for i, inst in enumerate(instancias):
            if inst == 2:
                segunda_instancia_index = i
                break
        
        # Se temos 1ª e 2ª instâncias, verifica reversão
        if primeira_instancia_index is not None and segunda_instancia_index is not None:
            if resultados[primeira_instancia_index] == 'Improcedente' and resultados[segunda_instancia_index] == 'Provido':
                reversao_trt += 1
                if exemplo_count < 15:  # Mostrar alguns exemplos de reversão
                    print(f"REVERSÃO TRT - Raiz CNJ: {raiz}")
                    print(f"Números originais: {numeros_originais}")
                    print(f"Instâncias: {instancias} | Resultados: {resultados}")
                    print("---")
    
    # Reversão no TST: perdeu na 1ª, perdeu no TRT, ganhou no TST
    if 3 in instancias and instancias_unicas >= 2:
        # Procura decisões em cada instância
        primeira_instancia_idx = next((i for i, inst in enumerate(instancias) if inst == 1), None)
        segunda_instancia_idx = next((i for i, inst in enumerate(instancias) if inst == 2), None)
        tst_idx = next((i for i, inst in enumerate(instancias) if inst == 3), None)
        
        # Caso 1: Perdeu na 1ª, perdeu no TRT, ganhou no TST (cadeia completa)
        if (primeira_instancia_idx is not None and segunda_instancia_idx is not None and tst_idx is not None):
            if (resultados[primeira_instancia_idx] == 'Improcedente' and 
                (resultados[segunda_instancia_idx] == 'Desprovido' or resultados[segunda_instancia_idx] == 'Improcedente') and
                resultados[tst_idx] == 'Provido'):
                reversao_tst += 1
                if exemplo_count < 20:  # Mostrar exemplos de reversão no TST
                    print(f"REVERSÃO TST (1ª→2ª→TST) - Raiz CNJ: {raiz}")
                    print(f"Números originais: {numeros_originais}")
                    print(f"Instâncias: {instancias} | Resultados: {resultados}")
                    print("---")
        
        # Caso 2: Perdeu no TRT (sem decisão de 1ª instância nos dados), ganhou no TST
        elif segunda_instancia_idx is not None and tst_idx is not None and primeira_instancia_idx is None:
            if (resultados[segunda_instancia_idx] == 'Desprovido' or resultados[segunda_instancia_idx] == 'Improcedente') and resultados[tst_idx] == 'Provido':
                reversao_tst += 1
                if exemplo_count < 20:
                    print(f"REVERSÃO TST (2ª→TST) - Raiz CNJ: {raiz}")
                    print(f"Números originais: {numeros_originais}")
                    print(f"Instâncias: {instancias} | Resultados: {resultados}")
                    print("---")
    
    cadeias.append({
        'numero_processo': numeros_originais[0],  # Usa o primeiro número como referência
        'raiz_cnj': raiz,
        'cadeia_resultados': cadeia,
        'tribunais': tribunais,
        'instancias': instancias
    })

# Relatório
report_path = os.path.join(results_dir, 'relatorio_cadeia_decisoes_fix.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('# Relatório de Cadeia de Decisões dos Processos (usando raiz CNJ)\n\n')
    f.write('**Nota:** Considera-se reversão quando o trabalhador perdeu na 1ª instância (Improcedente) e teve seu recurso PROVIDO no TRT (reversão no TRT), ou quando perdeu na 1ª e no TRT (Desprovido), mas teve seu recurso PROVIDO no TST (reversão no TST).\n\n')
    f.write('**Metodologia:** Usamos os 16 primeiros dígitos do número CNJ como chave de identificação para vincular processos em diferentes instâncias, ignorando os 4 últimos dígitos que mudam conforme o órgão julgador.\n\n')
    f.write(f'Total de processos analisados: {casos_totais}\n')
    f.write(f'Processos com decisões em múltiplas instâncias: {casos_com_multiplas_instancias}\n\n')
    f.write(f'Reversões de resultado no TRT (trabalhador perdeu na 1ª instância e teve recurso PROVIDO no TRT): {reversao_trt}\n')
    if casos_com_multiplas_instancias > 0:
        f.write(f'Taxa de reversão no TRT (em relação aos processos com múltiplas instâncias): {reversao_trt / casos_com_multiplas_instancias:.2%}\n\n')
    else:
        f.write(f'Taxa de reversão no TRT: 0.00%\n\n')
    f.write(f'Reversões de resultado no TST (trabalhador perdeu na 1ª e no TRT, mas teve recurso PROVIDO no TST): {reversao_tst}\n')
    if casos_com_multiplas_instancias > 0:
        f.write(f'Taxa de reversão no TST (em relação aos processos com múltiplas instâncias): {reversao_tst / casos_com_multiplas_instancias:.2%}\n\n')
    else:
        f.write(f'Taxa de reversão no TST: 0.00%\n\n')
    f.write('## Cadeias de resultados mais comuns\n')
    for cadeia, count in cadeias_exemplo.most_common(10):
        f.write(f'- {cadeia}: {count} processos\n')
    
    if cadeias:
        f.write('\n## Exemplos de cadeias de decisão\n')
        # Tenta encontrar um exemplo com múltiplas instâncias e que inclua o TST
        exemplo_multiplas_tst = None
        for cadeia in cadeias:
            if len(set(cadeia['instancias'])) > 2 and 3 in cadeia['instancias']:
                exemplo_multiplas_tst = cadeia
                break
        
        # Se não encontrou com TST, busca qualquer cadeia com múltiplas instâncias
        if not exemplo_multiplas_tst:
            for cadeia in cadeias:
                if len(set(cadeia['instancias'])) > 1:
                    exemplo_multiplas_tst = cadeia
                    break
        
        # Usa o exemplo encontrado ou o primeiro da lista
        exemplo = exemplo_multiplas_tst if exemplo_multiplas_tst else cadeias[0]
        f.write('\nExemplo de processo:\n')
        f.write(f"Processo: {exemplo['numero_processo']}\n")
        f.write(f"Raiz CNJ: {exemplo['raiz_cnj']}\n")
        f.write(f"Cadeia: {exemplo['cadeia_resultados']}\n")
        f.write(f"Tribunais: {exemplo['tribunais']}\n")
        f.write(f"Instâncias: {exemplo['instancias']}\n")

print(f"Relatório salvo em: {report_path}")
print("Análise encadeada concluída!")