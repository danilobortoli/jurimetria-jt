#!/usr/bin/env python3
"""
Análise encadeada das decisões de processos trabalhistas:
- Agrupa por numero_processo
- Ordena por instância/tribunal e data
- Identifica reversões de resultado (ex: trabalhador perdeu na 1ª instância, mas ganhou recurso no TRT ou TST)
- Calcula taxas de reversão/sucesso de recursos do trabalhador
- Salva relatório em results/relatorio_cadeia_decisoes.md
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
df = pd.read_csv(data_path, low_memory=False)

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

# Redefine ordem das instâncias (confiando principalmente na coluna 'instancia')
def get_instance_order(row):
    """
    Determina a ordem/nível da instância judicial baseando-se principalmente na coluna 'instancia',
    usando outras colunas como suporte apenas quando necessário.
    
    Retorna:
    1 = Primeira instância (Varas do Trabalho)
    2 = Segunda instância (TRTs)
    3 = Terceira instância (TST)
    99 = Não identificado
    """
    # As variáveis inst, trib e classe são strings em letras minúsculas para facilitar comparações
    inst = str(row['instancia']).strip() if not pd.isna(row['instancia']) else ''
    trib = str(row['tribunal']).strip() if not pd.isna(row['tribunal']) else ''
    
    # Confie primeiro na coluna 'instancia' que tem os valores corretos
    if inst == 'Primeira Instância':
        return 1
    elif inst == 'Segunda Instância':
        return 2
    elif inst == 'TST':
        return 3
    
    # Caso a coluna instância não esteja preenchida corretamente, use o tribunal
    if trib == 'TST':
        return 3
    elif 'TRT' in trib:
        # Para TRTs, verifique se é o gabinete/órgão julgador para diferenciar
        # entre primeira e segunda instância
        orgao = str(row['orgao_julgador']).lower() if not pd.isna(row['orgao_julgador']) else ''
        classe = str(row['classe']).lower() if not pd.isna(row['classe']) else ''
        
        if ('vara' in orgao or 'vara do trabalho' in orgao or 
            'ação trabalhista' in classe and 'recurso' not in classe):
            return 1
        else:
            # Se tem 'gabinete', 'recurso', etc., é segunda instância
            return 2
    
    # Caso não consiga identificar, retorna valor padrão
    return 99

df['instance_order'] = df.apply(get_instance_order, axis=1)

# Normalização de números de processo - SIMPLIFICADA
def normalize_process_number(num):
    """
    Normaliza números de processo para permitir a correspondência entre instâncias diferentes.
    Implementa uma estratégia simplificada baseada no formato CNJ NNNNNNN-DD.AAAA.J.TR.OOOO.
    """
    if pd.isna(num):
        return None
    
    # Remove caracteres não numéricos
    digits_only = re.sub(r'\D', '', str(num))
    
    # Para processos muito curtos ou vazios
    if len(digits_only) < 7:
        return None
    
    # Extrai apenas os primeiros 15 dígitos, que contêm o número sequencial (7 dígitos),
    # dígito verificador (2 dígitos), ano (4 dígitos) e identificador do tribunal (2 dígitos)
    # Isso deve capturar a parte essencial do número que é consistente entre instâncias
    if len(digits_only) >= 15:
        return digits_only[:15]
    
    # Para números mais curtos, usa o que tiver disponível
    return digits_only

# Adiciona coluna com número de processo normalizado
df['numero_processo_norm'] = df['numero_processo'].apply(normalize_process_number)

# Antes de agrupar, vamos verificar os números de processos em diferentes instâncias
print("Análise dos números de processo e instâncias:")
print(f"Total de processos antes do agrupamento: {len(df)}")
print(f"Processos na 1ª instância: {len(df[df['instance_order'] == 1])}")
print(f"Processos na 2ª instância: {len(df[df['instance_order'] == 2])}")
print(f"Processos no TST: {len(df[df['instance_order'] == 3])}")

# Verifica o padrão dos números de processo
print("\nExemplos de números de processo em cada instância:")
for inst in [1, 2, 3]:
    inst_df = df[df['instance_order'] == inst].head(3)
    print(f"\nInstância {inst}:")
    for idx, row in inst_df.iterrows():
        print(f"  Original: {row['numero_processo']} | Normalizado: {row['numero_processo_norm']}")

# Teste mais abrangente de correspondência entre instâncias
print("\nTeste de correspondência de normalização entre tribunais diferentes:")

# Faz uma busca mais abrangente por correspondências
print("Buscando correspondências entre processos em diferentes instâncias...")

# Filtra processos por instância
primeira_inst_df = df[df['instance_order'] == 1]
segunda_inst_df = df[df['instance_order'] == 2]
tst_inst_df = df[df['instance_order'] == 3]

print(f"Total de processos na 1ª instância: {len(primeira_inst_df)}")
print(f"Total de processos na 2ª instância: {len(segunda_inst_df)}")
print(f"Total de processos no TST: {len(tst_inst_df)}")

# Constrói dicionários de processo normalizado para processo original
primeira_dict = dict(zip(primeira_inst_df['numero_processo_norm'], primeira_inst_df['numero_processo']))
segunda_dict = dict(zip(segunda_inst_df['numero_processo_norm'], segunda_inst_df['numero_processo']))
tst_dict = dict(zip(tst_inst_df['numero_processo_norm'], tst_inst_df['numero_processo']))

# Conta correspondências
matches_1_2 = set(primeira_dict.keys()) & set(segunda_dict.keys())
matches_1_3 = set(primeira_dict.keys()) & set(tst_dict.keys())
matches_2_3 = set(segunda_dict.keys()) & set(tst_dict.keys())
matches_all = set(primeira_dict.keys()) & set(segunda_dict.keys()) & set(tst_dict.keys())

print(f"\nCorrespondências encontradas:")
print(f"1ª instância → 2ª instância: {len(matches_1_2)} processos")
print(f"1ª instância → TST: {len(matches_1_3)} processos")
print(f"2ª instância → TST: {len(matches_2_3)} processos")
print(f"Processos em todas as instâncias (1ª→2ª→TST): {len(matches_all)} processos")

# Mostra alguns exemplos de correspondências
print("\nExemplos de correspondências encontradas:")
if len(matches_1_2) > 0:
    print("\n1ª instância → 2ª instância:")
    for i, norm in enumerate(list(matches_1_2)[:3]):
        print(f"  {i+1}. {primeira_dict[norm]} → {segunda_dict[norm]} (norm: {norm})")

if len(matches_1_3) > 0:
    print("\n1ª instância → TST:")
    for i, norm in enumerate(list(matches_1_3)[:3]):
        print(f"  {i+1}. {primeira_dict[norm]} → {tst_dict[norm]} (norm: {norm})")

if len(matches_all) > 0:
    print("\nTodas as instâncias (1ª→2ª→TST):")
    for i, norm in enumerate(list(matches_all)[:3]):
        print(f"  {i+1}. {primeira_dict[norm]} → {segunda_dict[norm]} → {tst_dict[norm]} (norm: {norm})")

# Informações adicionais sobre a normalização
unique_norm = df['numero_processo_norm'].nunique()
total_norm = df['numero_processo_norm'].notna().sum()
print(f"\nTotal de números de processo normalizados: {total_norm}")
print(f"Números de processo normalizados únicos: {unique_norm}")
print(f"Taxa de normalização (processos únicos / total): {unique_norm / total_norm:.2%}")

# Agrupa por processo normalizado
groups = df.groupby('numero_processo_norm')

cadeias = []
reversao_trt = 0
reversao_tst = 0
casos_totais = 0
casos_com_multiplas_instancias = 0
cadeias_exemplo = Counter()

# Debug: exemplos de cadeias reais
print("\nExemplos de cadeias reais:")
exemplo_count = 0

for numero, group in groups:
    # Pula grupos com número de processo normalizado inválido
    if numero is None or len(str(numero)) < 5:
        continue
        
    # Ordena primeiro por instância, depois por data de julgamento
    group_sorted = group.sort_values(['instance_order', 'data_julgamento'])
    
    # Verifica se temos decisões em múltiplas instâncias
    instancias_unicas = group_sorted['instance_order'].nunique()
    if instancias_unicas > 1:
        casos_com_multiplas_instancias += 1
    
    resultados = list(group_sorted['resultado_norm'])
    instancias = list(group_sorted['instance_order'])
    tribunais = list(group_sorted['tribunal'])
    numeros_originais = list(group_sorted['numero_processo'])
    
    casos_totais += 1
    cadeia = ' -> '.join(resultados)
    cadeias_exemplo[cadeia] += 1
    
    # Debug: mostrar exemplos reais - exibe processos com múltiplas instâncias
    if instancias_unicas > 1 and exemplo_count < 10:
        print(f"Processo normalizado: {numero}")
        print(f"Números originais: {numeros_originais}")
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
                    print(f"REVERSÃO TRT - Processo: {numeros_originais}")
                    print(f"Instâncias: {instancias} | Resultados: {resultados}")
                    print("---")
    
    # Reversão no TST: temos várias configurações possíveis
    if 3 in instancias and instancias_unicas >= 2:  # Se tem decisão do TST e múltiplas instâncias
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
                    print(f"REVERSÃO TST (1ª→2ª→TST) - Processo: {numeros_originais}")
                    print(f"Instâncias: {instancias} | Resultados: {resultados}")
                    print("---")
        
        # Caso 2: Perdeu no TRT (sem decisão de 1ª instância nos dados), ganhou no TST
        elif segunda_instancia_idx is not None and tst_idx is not None and primeira_instancia_idx is None:
            if (resultados[segunda_instancia_idx] == 'Desprovido' or resultados[segunda_instancia_idx] == 'Improcedente') and resultados[tst_idx] == 'Provido':
                reversao_tst += 1
                if exemplo_count < 20:
                    print(f"REVERSÃO TST (2ª→TST) - Processo: {numeros_originais}")
                    print(f"Instâncias: {instancias} | Resultados: {resultados}")
                    print("---")
        
        # Removemos o "Caso 3" que estava contando decisões isoladas do TST sem confirmação
        # de serem o mesmo processo, o que inflava artificialmente as estatísticas
    
    cadeias.append({
        'numero_processo': numeros_originais[0],  # Usa o primeiro número como referência
        'cadeia_resultados': cadeia,
        'tribunais': tribunais,
        'instancias': instancias
    })

# Relatório
report_path = os.path.join(results_dir, 'relatorio_cadeia_decisoes.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('# Relatório de Cadeia de Decisões dos Processos\n\n')
    f.write('**Nota:** Considera-se reversão quando o trabalhador perdeu na 1ª instância (Improcedente) e teve seu recurso PROVIDO no TRT (reversão no TRT), ou quando perdeu na 1ª e no TRT (Desprovido), mas teve seu recurso PROVIDO no TST (reversão no TST).\n\n')
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
        # Tenta encontrar um exemplo com múltiplas instâncias
        exemplo_multiplas = None
        for cadeia in cadeias:
            if len(set(cadeia['instancias'])) > 1:
                exemplo_multiplas = cadeia
                break
        
        # Se encontrou exemplo com múltiplas instâncias, use-o
        if exemplo_multiplas:
            f.write('\nExemplo de processo com múltiplas instâncias:\n')
            f.write(f"Processo: {exemplo_multiplas['numero_processo']}\n")
            f.write(f"Cadeia: {exemplo_multiplas['cadeia_resultados']}\n")
            f.write(f"Tribunais: {exemplo_multiplas['tribunais']}\n")
            f.write(f"Instâncias: {exemplo_multiplas['instancias']}\n")
        else:
            # Caso contrário, use o primeiro exemplo
            exemplo = cadeias[0]
            f.write('\nExemplo de processo:\n')
            f.write(f"Processo: {exemplo['numero_processo']}\n")
            f.write(f"Cadeia: {exemplo['cadeia_resultados']}\n")
            f.write(f"Tribunais: {exemplo['tribunais']}\n")
            f.write(f"Instâncias: {exemplo['instancias']}\n")

print(f"Relatório salvo em: {report_path}")
print("Análise encadeada concluída!")