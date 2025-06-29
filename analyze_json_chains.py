#!/usr/bin/env python3
"""
Análise encadeada das decisões de processos trabalhistas a partir do arquivo JSON consolidado:
- Agrupa por numero_processo normalizado
- Ordena por instância e data
- Identifica reversões de resultado entre instâncias
- Calcula taxas de reversão/sucesso de recursos do trabalhador
- Salva relatório em results/relatorio_cadeia_decisoes_json.md
"""

import os
import json
import re
from datetime import datetime
from collections import Counter

# Configurações gerais
data_path = "data/consolidated/all_decisions.json"
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

# Lê os dados JSON
print("Carregando dados do arquivo JSON...")
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total de registros carregados: {len(data)}")

# Função para padronizar resultados
RESULT_MAP = {
    'improcedente': 'Improcedente',
    'procedente': 'Procedente',
    'provido': 'Provido',
    'desprovido': 'Desprovido',
}

def normalize_result(res):
    if not res:
        return 'Desconhecido'
    res = str(res).strip().lower()
    for key in RESULT_MAP:
        if key in res:
            return RESULT_MAP[key]
    return res.capitalize()

# Função para obter ordem das instâncias
def get_instance_order(instance):
    if instance == 'Primeira Instância':
        return 1
    elif instance == 'Segunda Instância':
        return 2
    elif instance == 'TST':
        return 3
    return 99

# Normalização de números de processo
def normalize_process_number(num):
    """
    Normaliza números de processo para permitir correspondências entre instâncias.
    O padrão CNJ é NNNNNNN-DD.AAAA.J.TR.OOOO
    """
    if not num:
        return None
    
    # Remove caracteres não numéricos
    digits_only = re.sub(r'\D', '', str(num))
    
    # Para processos muito curtos
    if len(digits_only) < 7:
        return None
    
    # Extrai os primeiros 15 dígitos (contendo número sequencial, dígito verificador, 
    # ano e parte do código do tribunal), que devem ser consistentes entre instâncias
    if len(digits_only) >= 15:
        return digits_only[:15]
    
    # Para números mais curtos, usa o que tiver
    return digits_only

# Prepara os dados
print("Processando dados...")
processed_data = []
for decision in data:
    # Extrai campos relevantes
    instancia = decision.get('instancia')
    tribunal = decision.get('tribunal')
    numero_processo = decision.get('numero_processo')
    resultado = decision.get('resultado')
    data_julgamento = decision.get('data_julgamento')
    
    # Normaliza o número de processo
    numero_processo_norm = normalize_process_number(numero_processo)
    
    # Adiciona aos dados processados
    if numero_processo_norm and instancia and resultado:
        processed_data.append({
            'numero_processo': numero_processo,
            'numero_processo_norm': numero_processo_norm,
            'instancia': instancia,
            'instance_order': get_instance_order(instancia),
            'tribunal': tribunal,
            'resultado': resultado,
            'resultado_norm': normalize_result(resultado),
            'data_julgamento': data_julgamento,
            'orgao_julgador': decision.get('orgao_julgador', '')
        })

print(f"Registros processados: {len(processed_data)}")

# Estatísticas de instâncias
inst_counts = Counter(d['instancia'] for d in processed_data)
print("\nProcessos por instância:")
for inst, count in inst_counts.items():
    print(f"- {inst}: {count}")

# Agrupa por número de processo normalizado
process_groups = {}
for decision in processed_data:
    norm_num = decision['numero_processo_norm']
    if norm_num not in process_groups:
        process_groups[norm_num] = []
    process_groups[norm_num].append(decision)

# Analisa cadeias de decisões
cadeias = []
reversao_trt = 0
reversao_tst = 0
casos_totais = 0
casos_com_multiplas_instancias = 0
cadeias_exemplo = Counter()

print("\nAnalisando cadeias de decisões...")
for numero_norm, decisoes in process_groups.items():
    # Ordena por instância e data de julgamento
    decisoes_sorted = sorted(decisoes, key=lambda x: (x['instance_order'], x.get('data_julgamento', '')))
    
    # Analisa quantas instâncias diferentes temos
    instancias = set(d['instance_order'] for d in decisoes_sorted)
    instancias_list = [d['instance_order'] for d in decisoes_sorted]
    
    # Obtém resultados
    resultados = [d['resultado_norm'] for d in decisoes_sorted]
    tribunais = [d['tribunal'] for d in decisoes_sorted]
    numeros_originais = [d['numero_processo'] for d in decisoes_sorted]
    
    # Conta processos
    casos_totais += 1
    cadeia = ' -> '.join(resultados)
    cadeias_exemplo[cadeia] += 1
    
    # Verifica se temos decisões em múltiplas instâncias
    if len(instancias) > 1:
        casos_com_multiplas_instancias += 1
        
        # Debug: mostra exemplos de processos com múltiplas instâncias
        if casos_com_multiplas_instancias <= 5:  # Limita a 5 exemplos
            print(f"\nProcesso normalizado: {numero_norm}")
            print(f"Números originais: {numeros_originais}")
            print(f"Cadeia: {cadeia}")
            print(f"Instâncias: {instancias_list}")
            print(f"Tribunais: {tribunais}")
        
        # Análise de reversões no TRT
        if 1 in instancias and 2 in instancias:
            # Encontra índices das instâncias
            primeira_idx = next((i for i, d in enumerate(decisoes_sorted) if d['instance_order'] == 1), None)
            segunda_idx = next((i for i, d in enumerate(decisoes_sorted) if d['instance_order'] == 2), None)
            
            # Verifica se houve reversão no TRT
            if (primeira_idx is not None and segunda_idx is not None and
                resultados[primeira_idx] == 'Improcedente' and resultados[segunda_idx] == 'Provido'):
                reversao_trt += 1
                if casos_com_multiplas_instancias <= 10:  # Limita a 10 exemplos
                    print(f"REVERSÃO TRT - Processo: {numeros_originais}")
                    print(f"Instâncias: {instancias_list} | Resultados: {resultados}")
        
        # Análise de reversões no TST
        if 3 in instancias:
            # Encontra índices das instâncias
            primeira_idx = next((i for i, d in enumerate(decisoes_sorted) if d['instance_order'] == 1), None)
            segunda_idx = next((i for i, d in enumerate(decisoes_sorted) if d['instance_order'] == 2), None)
            tst_idx = next((i for i, d in enumerate(decisoes_sorted) if d['instance_order'] == 3), None)
            
            # Verifica se houve reversão completa (1ª → 2ª → TST)
            if (primeira_idx is not None and segunda_idx is not None and tst_idx is not None and
                resultados[primeira_idx] == 'Improcedente' and
                (resultados[segunda_idx] == 'Desprovido' or resultados[segunda_idx] == 'Improcedente') and
                resultados[tst_idx] == 'Provido'):
                reversao_tst += 1
                if casos_com_multiplas_instancias <= 15:  # Limita a 15 exemplos
                    print(f"REVERSÃO TST - Processo: {numeros_originais}")
                    print(f"Instâncias: {instancias_list} | Resultados: {resultados}")
    
    # Adiciona à lista de cadeias
    cadeias.append({
        'numero_processo': numeros_originais[0],  # Usa o primeiro número como referência
        'cadeia_resultados': cadeia,
        'tribunais': tribunais,
        'instancias': instancias_list
    })

# Relatório
print("\nGerando relatório...")
report_path = os.path.join(results_dir, 'relatorio_cadeia_decisoes_json.md')

with open(report_path, 'w', encoding='utf-8') as f:
    f.write('# Relatório de Cadeia de Decisões dos Processos (análise do JSON)\n\n')
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