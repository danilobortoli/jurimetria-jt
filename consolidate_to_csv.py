#!/usr/bin/env python3
"""
Consolidador de Dados JSON para CSV
Agrupa todos os processos em um único arquivo CSV para análise unificada.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys

def extract_case_core(numero_processo: str) -> str:
    """Extrai núcleo do número do processo - NÚMEROS DEVEM SER IDÊNTICOS."""
    numbers_only = ''.join(filter(str.isdigit, numero_processo))
    if len(numbers_only) >= 20:
        return numbers_only[:7] + numbers_only[9:]
    return numbers_only

def extract_year_from_number(numero_processo: str) -> Optional[str]:
    """Extrai ano do número do processo."""
    try:
        if len(numero_processo) >= 15:
            year = numero_processo[9:13]
            if year.isdigit() and 2000 <= int(year) <= 2030:
                return year
    except:
        pass
    return None

def extract_movement_results(movimentos: List[Dict]) -> Dict[str, Any]:
    """Extrai resultados dos movimentos."""
    primeira_instancia_codes = {219: 'Procedência', 220: 'Improcedência', 221: 'Procedência em Parte'}
    recurso_codes = {237: 'Provimento', 238: 'Provimento em Parte', 242: 'Desprovimento', 236: 'Negação de Seguimento'}
    
    results = {
        'tem_resultado_primeira': False,
        'resultado_primeira_codigo': None,
        'resultado_primeira_nome': '',
        'tem_resultado_recurso': False,
        'resultado_recurso_codigo': None,
        'resultado_recurso_nome': '',
        'total_movimentos': len(movimentos)
    }
    
    for movimento in movimentos:
        codigo = movimento.get('codigo')
        if codigo in primeira_instancia_codes:
            results['tem_resultado_primeira'] = True
            results['resultado_primeira_codigo'] = codigo
            results['resultado_primeira_nome'] = primeira_instancia_codes[codigo]
        elif codigo in recurso_codes:
            results['tem_resultado_recurso'] = True
            results['resultado_recurso_codigo'] = codigo
            results['resultado_recurso_nome'] = recurso_codes[codigo]
    
    return results

def extract_main_subjects(assuntos: List[Dict]) -> str:
    """Extrai principais assuntos do processo."""
    if not assuntos:
        return ''
    
    subjects = []
    for assunto in assuntos[:3]:  # Primeiros 3 assuntos
        if isinstance(assunto, dict):
            nome = assunto.get('nome', '')
            if nome:
                subjects.append(nome[:50])  # Limita tamanho
    
    return ' | '.join(subjects)

def is_assedio_moral(assuntos: List[Dict]) -> bool:
    """Verifica se é caso de assédio moral."""
    assedio_codes = [1723, 14175, 14018]
    
    for assunto in assuntos:
        if isinstance(assunto, dict):
            codigo = assunto.get('codigo')
            nome = assunto.get('nome', '').lower()
            
            if codigo in assedio_codes or 'assédio' in nome or 'assedio' in nome:
                return True
    return False

def consolidate_json_to_csv(external_path: str, output_file: str = None):
    """Consolida todos os JSONs em um único CSV."""
    
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"consolidated_data_{timestamp}.csv"
    
    print(f"🔄 Iniciando consolidação JSON → CSV...")
    print(f"📂 Diretório fonte: {external_path}")
    print(f"📝 Arquivo destino: {output_file}")
    
    json_files = list(Path(external_path).glob("*.json"))
    print(f"📁 Encontrados {len(json_files)} arquivos JSON")
    
    # Cabeçalhos do CSV
    headers = [
        'numero_processo',
        'numero_core',
        'ano_processo',
        'tribunal',
        'grau',
        'instancia_normalizada',
        'data_ajuizamento',
        'resultado_campo',
        'classe',
        'assuntos_principais',
        'eh_assedio_moral',
        'total_movimentos',
        'tem_resultado_primeira',
        'resultado_primeira_codigo',
        'resultado_primeira_nome',
        'tem_resultado_recurso', 
        'resultado_recurso_codigo',
        'resultado_recurso_nome',
        'arquivo_origem'
    ]
    
    total_processed = 0
    assedio_moral_count = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        for i, json_file in enumerate(json_files):
            if i % 20 == 0:
                print(f"  Processando arquivo {i+1}/{len(json_files)}... ({total_processed:,} processos)")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for processo in data:
                    numero = processo.get('numeroProcesso', '')
                    tribunal = processo.get('tribunal', '')
                    grau = processo.get('grau', '')
                    movimentos = processo.get('movimentos', [])
                    assuntos = processo.get('assuntos', [])
                    
                    # Extrai informações
                    core = extract_case_core(numero)
                    year = extract_year_from_number(numero)
                    movement_results = extract_movement_results(movimentos)
                    main_subjects = extract_main_subjects(assuntos)
                    is_assedio = is_assedio_moral(assuntos)
                    
                    if is_assedio:
                        assedio_moral_count += 1
                    
                    # Normaliza instância
                    instancia_map = {
                        'G1': 'Primeira Instância',
                        'GRAU_1': 'Primeira Instância', 
                        'G2': 'Segunda Instância',
                        'GRAU_2': 'Segunda Instância',
                        'GS': 'TST',
                        'SUP': 'TST'
                    }
                    instancia_normalizada = instancia_map.get(grau, grau)
                    
                    # Escreve linha no CSV
                    row = {
                        'numero_processo': numero,
                        'numero_core': core,
                        'ano_processo': year or '',
                        'tribunal': tribunal,
                        'grau': grau,
                        'instancia_normalizada': instancia_normalizada,
                        'data_ajuizamento': processo.get('dataAjuizamento', ''),
                        'resultado_campo': processo.get('resultado', ''),
                        'classe': processo.get('classe', {}).get('nome', '') if isinstance(processo.get('classe'), dict) else str(processo.get('classe', '')),
                        'assuntos_principais': main_subjects,
                        'eh_assedio_moral': is_assedio,
                        'total_movimentos': movement_results['total_movimentos'],
                        'tem_resultado_primeira': movement_results['tem_resultado_primeira'],
                        'resultado_primeira_codigo': movement_results['resultado_primeira_codigo'] or '',
                        'resultado_primeira_nome': movement_results['resultado_primeira_nome'],
                        'tem_resultado_recurso': movement_results['tem_resultado_recurso'],
                        'resultado_recurso_codigo': movement_results['resultado_recurso_codigo'] or '',
                        'resultado_recurso_nome': movement_results['resultado_recurso_nome'],
                        'arquivo_origem': json_file.name
                    }
                    
                    writer.writerow(row)
                    total_processed += 1
            
            except Exception as e:
                print(f"  ⚠️ Erro em {json_file.name}: {str(e)}")
    
    print(f"\n✅ Consolidação concluída!")
    print(f"📊 Total de processos: {total_processed:,}")
    print(f"🎯 Casos de assédio moral: {assedio_moral_count:,}")
    print(f"💾 Arquivo criado: {output_file}")
    
    # Gera estatísticas rápidas
    generate_csv_statistics(output_file)

def generate_csv_statistics(csv_file: str):
    """Gera estatísticas rápidas do CSV consolidado."""
    print(f"\n📈 Gerando estatísticas do arquivo consolidado...")
    
    stats = {
        'total_rows': 0,
        'by_tribunal': {},
        'by_grau': {},
        'by_year': {},
        'assedio_moral': 0,
        'with_primeira_result': 0,
        'with_recurso_result': 0,
        'cores_count': set()
    }
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            stats['total_rows'] += 1
            
            # Por tribunal
            tribunal = row['tribunal']
            stats['by_tribunal'][tribunal] = stats['by_tribunal'].get(tribunal, 0) + 1
            
            # Por grau  
            grau = row['grau']
            stats['by_grau'][grau] = stats['by_grau'].get(grau, 0) + 1
            
            # Por ano
            year = row['ano_processo']
            if year:
                stats['by_year'][year] = stats['by_year'].get(year, 0) + 1
            
            # Assédio moral
            if row['eh_assedio_moral'] == 'True':
                stats['assedio_moral'] += 1
            
            # Resultados
            if row['tem_resultado_primeira'] == 'True':
                stats['with_primeira_result'] += 1
            
            if row['tem_resultado_recurso'] == 'True':
                stats['with_recurso_result'] += 1
            
            # Cores únicos
            core = row['numero_core']
            if core:
                stats['cores_count'].add(core)
    
    # Imprime estatísticas
    print(f"\n📊 ESTATÍSTICAS DO CSV CONSOLIDADO:")
    print(f"=" * 50)
    print(f"Total de linhas: {stats['total_rows']:,}")
    print(f"Casos únicos (cores): {len(stats['cores_count']):,}")
    print(f"Assédio moral: {stats['assedio_moral']:,}")
    print(f"Com resultado 1ª instância: {stats['with_primeira_result']:,}")
    print(f"Com resultado recurso: {stats['with_recurso_result']:,}")
    
    print(f"\n🏛️ TOP 10 TRIBUNAIS:")
    sorted_tribunals = sorted(stats['by_tribunal'].items(), key=lambda x: x[1], reverse=True)
    for tribunal, count in sorted_tribunals[:10]:
        print(f"  {tribunal}: {count:,}")
    
    print(f"\n📊 POR GRAU:")
    for grau, count in sorted(stats['by_grau'].items()):
        print(f"  {grau}: {count:,}")
    
    print(f"\n📅 POR ANO:")
    for year, count in sorted(stats['by_year'].items()):
        print(f"  {year}: {count:,}")
    
    # Salva estatísticas em JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats_file = f"csv_statistics_{timestamp}.json"
    
    # Converte set para list para JSON
    stats['cores_list'] = list(stats['cores_count'])
    del stats['cores_count']
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Estatísticas salvas em: {stats_file}")

def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Consolidador JSON para CSV")
    parser.add_argument("--external-path", type=str,
                       default="/Users/danilobortoli/Documents/Tese de doutorado da Andreia/Dados da segunda extração/raw",
                       help="Caminho para dados externos")
    parser.add_argument("--output", type=str,
                       help="Nome do arquivo CSV de saída")
    
    args = parser.parse_args()
    
    consolidate_json_to_csv(args.external_path, args.output)

if __name__ == "__main__":
    main()