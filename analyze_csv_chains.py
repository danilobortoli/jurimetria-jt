#!/usr/bin/env python3
"""
Análise do CSV Consolidado para Identificar Cadeias Processuais
Verifica se mesmos casos estão distribuídos em arquivos diferentes.
"""

import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter
from datetime import datetime

def analyze_csv_chains(csv_file: str):
    """Analisa cadeias processuais no CSV consolidado."""
    
    print(f"🔍 Analisando cadeias processuais em: {csv_file}")
    
    # Carrega dados
    df = pd.read_csv(csv_file)
    print(f"📊 Carregados {len(df):,} registros")
    
    # Análise por número_core (casos relacionados)
    cores_analysis = df.groupby('numero_core').agg({
        'numero_processo': 'count',
        'grau': lambda x: list(x.unique()),
        'tribunal': lambda x: list(x.unique()),
        'arquivo_origem': lambda x: list(x.unique()),
        'instancia_normalizada': lambda x: list(x.unique()),
        'ano_processo': 'first'
    }).rename(columns={'numero_processo': 'count_instances'})
    
    # Filtra casos com múltiplas instâncias
    multi_instance = cores_analysis[cores_analysis['count_instances'] > 1]
    print(f"🔗 Casos com múltiplas instâncias: {len(multi_instance):,}")
    
    # Analisa distribuição de arquivos
    multi_files = multi_instance[multi_instance['arquivo_origem'].apply(len) > 1]
    print(f"📁 Casos em múltiplos arquivos: {len(multi_files):,}")
    
    # Estatísticas detalhadas
    print(f"\n📈 ANÁLISE DETALHADA:")
    print(f"=" * 50)
    
    # Distribuição por número de instâncias
    instance_counts = Counter(multi_instance['count_instances'])
    print(f"\n🔢 Distribuição por número de instâncias:")
    for count, cases in sorted(instance_counts.items()):
        print(f"  {count} instâncias: {cases:,} casos")
    
    # Casos com fluxo completo G1→G2→TST
    complete_flows = multi_instance[
        multi_instance['instancia_normalizada'].apply(
            lambda x: all(inst in x for inst in ['Primeira Instância', 'Segunda Instância', 'TST'])
        )
    ]
    print(f"\n⚖️ Fluxos completos (G1→G2→TST): {len(complete_flows):,}")
    
    # Casos apenas G1→TST (sem G2)
    g1_tst_only = multi_instance[
        multi_instance['instancia_normalizada'].apply(
            lambda x: 'Primeira Instância' in x and 'TST' in x and 'Segunda Instância' not in x
        )
    ]
    print(f"🔀 Fluxos G1→TST (sem G2): {len(g1_tst_only):,}")
    
    # Análise de arquivos cruzados
    print(f"\n📂 ANÁLISE DE DISTRIBUIÇÃO POR ARQUIVOS:")
    print(f"=" * 50)
    
    # Casos que estão em arquivos de tribunais diferentes
    cross_tribunal_cases = multi_files[
        multi_files['arquivo_origem'].apply(
            lambda files: len(set(f.split('_')[0] for f in files if '_' in f)) > 1
        )
    ]
    print(f"🏛️ Casos em arquivos de tribunais diferentes: {len(cross_tribunal_cases):,}")
    
    # Exemplos de casos distribuídos
    print(f"\n🔍 EXEMPLOS DE CASOS DISTRIBUÍDOS:")
    print(f"=" * 50)
    
    for i, (core, data) in enumerate(multi_files.head(10).iterrows()):
        print(f"\nCaso {i+1}: Core {core}")
        print(f"  Instâncias: {data['count_instances']}")
        print(f"  Graus: {', '.join(data['grau'])}")
        print(f"  Tribunais: {', '.join(data['tribunal'])}")
        print(f"  Arquivos: {', '.join(data['arquivo_origem'])}")
    
    # Análise de resultados por instância
    print(f"\n⚖️ ANÁLISE DE RESULTADOS:")
    print(f"=" * 50)
    
    # Filtra apenas casos de assédio moral
    df_assedio = df[df['eh_assedio_moral'] == True]
    
    # Estatísticas por instância
    by_instance = df_assedio.groupby('instancia_normalizada').agg({
        'tem_resultado_primeira': lambda x: sum(x == True),
        'tem_resultado_recurso': lambda x: sum(x == True),
        'numero_processo': 'count'
    }).rename(columns={'numero_processo': 'total_cases'})
    
    print("Por instância (apenas assédio moral):")
    for instance, data in by_instance.iterrows():
        print(f"  {instance}:")
        print(f"    Total: {data['total_cases']:,}")
        print(f"    Com resultado 1ª inst: {data['tem_resultado_primeira']:,}")
        print(f"    Com resultado recurso: {data['tem_resultado_recurso']:,}")
    
    # Salva resultados detalhados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Salva casos multi-instância
    multi_instance_file = f"casos_multiinstancia_{timestamp}.csv"
    multi_instance.to_csv(multi_instance_file)
    print(f"\n💾 Casos multi-instância salvos em: {multi_instance_file}")
    
    # Salva casos em múltiplos arquivos  
    multi_files_file = f"casos_multiplos_arquivos_{timestamp}.csv"
    multi_files.to_csv(multi_files_file)
    print(f"💾 Casos em múltiplos arquivos salvos em: {multi_files_file}")
    
    # Análise específica de cadeias completas
    analyze_complete_chains(df_assedio, complete_flows)
    
    return {
        'total_cases': len(df),
        'multi_instance_cases': len(multi_instance),
        'multi_file_cases': len(multi_files),
        'complete_flows': len(complete_flows),
        'g1_tst_only': len(g1_tst_only),
        'cross_tribunal_cases': len(cross_tribunal_cases)
    }

def analyze_complete_chains(df_assedio, complete_flows):
    """Analisa cadeias completas G1→G2→TST."""
    
    print(f"\n🎯 ANÁLISE DE CADEIAS COMPLETAS G1→G2→TST:")
    print(f"=" * 50)
    
    # Para cada cadeia completa, analisa o fluxo
    chain_results = []
    
    for core in complete_flows.index[:20]:  # Primeiros 20 para análise
        chain_data = df_assedio[df_assedio['numero_core'] == core].sort_values('grau')
        
        if len(chain_data) >= 3:  # G1, G2, TST
            g1_data = chain_data[chain_data['instancia_normalizada'] == 'Primeira Instância'].iloc[0]
            g2_data = chain_data[chain_data['instancia_normalizada'] == 'Segunda Instância'].iloc[0]
            tst_data = chain_data[chain_data['instancia_normalizada'] == 'TST'].iloc[0]
            
            # Extrai resultados
            resultado_g1 = g1_data['resultado_primeira_nome'] if g1_data['tem_resultado_primeira'] else 'Sem resultado'
            resultado_g2 = g2_data['resultado_recurso_nome'] if g2_data['tem_resultado_recurso'] else 'Sem resultado'
            resultado_tst = tst_data['resultado_recurso_nome'] if tst_data['tem_resultado_recurso'] else 'Sem resultado'
            
            # Determina resultado final (se possível)
            worker_won = None
            if resultado_g1 != 'Sem resultado' and resultado_tst != 'Sem resultado':
                trabalhador_ganhou_g1 = resultado_g1 in ['Procedência', 'Procedência em Parte']
                tst_provido = resultado_tst in ['Provimento', 'Provimento em Parte']
                
                if trabalhador_ganhou_g1:
                    worker_won = not tst_provido  # Se TST proveu, trabalhador perdeu
                else:
                    worker_won = tst_provido  # Se TST proveu, trabalhador ganhou
            
            chain_info = {
                'core': core,
                'g1_tribunal': g1_data['tribunal'],
                'g2_tribunal': g2_data['tribunal'], 
                'tst_tribunal': tst_data['tribunal'],
                'resultado_g1': resultado_g1,
                'resultado_g2': resultado_g2,
                'resultado_tst': resultado_tst,
                'worker_won': worker_won,
                'arquivos': f"{g1_data['arquivo_origem']} | {g2_data['arquivo_origem']} | {tst_data['arquivo_origem']}"
            }
            
            chain_results.append(chain_info)
    
    # Imprime exemplos
    print(f"Analisando {len(chain_results)} cadeias completas:")
    
    determinable_results = [c for c in chain_results if c['worker_won'] is not None]
    if determinable_results:
        worker_wins = sum(1 for c in determinable_results if c['worker_won'])
        success_rate = (worker_wins / len(determinable_results)) * 100
        
        print(f"\n📊 Resultados determináveis: {len(determinable_results)}")
        print(f"⚖️ Taxa de sucesso do trabalhador: {success_rate:.1f}%")
        print(f"✅ Vitórias: {worker_wins}")
        print(f"❌ Derrotas: {len(determinable_results) - worker_wins}")
    
    # Mostra exemplos
    print(f"\n🔍 EXEMPLOS DE CADEIAS COMPLETAS:")
    for i, chain in enumerate(chain_results[:5]):
        print(f"\nCadeia {i+1} (Core: {chain['core']}):")
        print(f"  G1 ({chain['g1_tribunal']}): {chain['resultado_g1']}")
        print(f"  G2 ({chain['g2_tribunal']}): {chain['resultado_g2']}")
        print(f"  TST: {chain['resultado_tst']}")
        if chain['worker_won'] is not None:
            resultado = "Trabalhador GANHOU" if chain['worker_won'] else "Trabalhador PERDEU"
            print(f"  Resultado final: {resultado}")
        print(f"  Arquivos: {chain['arquivos']}")

def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Análise de Cadeias no CSV")
    parser.add_argument("--csv-file", type=str,
                       default="consolidated_all_data.csv",
                       help="Arquivo CSV para análise")
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"❌ Arquivo não encontrado: {args.csv_file}")
        return
    
    analyze_csv_chains(args.csv_file)

if __name__ == "__main__":
    main()