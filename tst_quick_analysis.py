#!/usr/bin/env python3
"""
Análise Rápida de Processos TST - Apenas Estatísticas Essenciais
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import sys

# Adiciona o diretório src ao path
sys.path.append(str(Path(__file__).parent))

from src.utils.movement_analyzer import MovementAnalyzer

def extract_case_core(numero_processo: str) -> str:
    """Extrai núcleo do número do processo."""
    numbers_only = ''.join(filter(str.isdigit, numero_processo))
    if len(numbers_only) >= 20:
        return numbers_only[:7] + numbers_only[9:]
    return numbers_only

def quick_tst_analysis(external_path: str):
    """Análise rápida focada em TST."""
    print("🔍 Iniciando análise rápida TST...")
    
    # Códigos de movimento
    primeira_instancia_codes = {219, 220, 221}
    recurso_codes = {237, 238, 242, 236}
    
    # Contadores
    total_processos = 0
    tst_cases = 0
    tst_with_history = 0
    multi_instance_chains = set()
    
    # Análise por arquivo
    json_files = list(Path(external_path).glob("*.json"))
    print(f"📁 Encontrados {len(json_files)} arquivos JSON")
    
    # Processa apenas casos TST e multi-instância
    all_cases_by_core = {}
    
    for i, json_file in enumerate(json_files):
        if i % 50 == 0:
            print(f"  Processando arquivo {i+1}/{len(json_files)}...")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for processo in data:
                total_processos += 1
                
                # Verifica se é TST
                tribunal = processo.get('tribunal', '').upper()
                grau = processo.get('grau', '').upper()
                numero = processo.get('numeroProcesso', '')
                
                if tribunal == 'TST' or grau in ['GS', 'SUP']:
                    tst_cases += 1
                    
                    # Verifica se tem histórico nos movimentos
                    movimentos = processo.get('movimentos', [])
                    has_primeira = any(m.get('codigo') in primeira_instancia_codes for m in movimentos)
                    has_recurso = any(m.get('codigo') in recurso_codes for m in movimentos)
                    
                    if has_primeira and has_recurso:
                        tst_with_history += 1
                
                # Adiciona ao tracking de multi-instância
                core = extract_case_core(numero)
                if core:
                    if core not in all_cases_by_core:
                        all_cases_by_core[core] = []
                    all_cases_by_core[core].append({
                        'grau': grau,
                        'tribunal': tribunal,
                        'numero': numero
                    })
        
        except Exception as e:
            print(f"  ⚠️ Erro em {json_file.name}: {str(e)}")
    
    # Conta cadeias multi-instância
    multi_instance_count = sum(1 for core, cases in all_cases_by_core.items() if len(cases) > 1)
    tst_in_chains = sum(1 for core, cases in all_cases_by_core.items() 
                       if len(cases) > 1 and any(c['tribunal'] == 'TST' or c['grau'] in ['GS', 'SUP'] 
                                               for c in cases))
    
    # Resultados
    print("\n📊 RESULTADOS DA ANÁLISE RÁPIDA TST:")
    print("=" * 50)
    print(f"Total de processos analisados: {total_processos:,}")
    print(f"Casos TST identificados: {tst_cases:,} ({tst_cases/total_processos*100:.1f}%)")
    print(f"TST com histórico completo: {tst_with_history:,}")
    print(f"\n🔗 CADEIAS PROCESSUAIS:")
    print(f"Cadeias únicas identificadas: {len(all_cases_by_core):,}")
    print(f"Cadeias multi-instância: {multi_instance_count:,}")
    print(f"Cadeias com TST: {tst_in_chains:,}")
    
    # Salva sumário
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = {
        'timestamp': timestamp,
        'total_processos': total_processos,
        'tst_cases': tst_cases,
        'tst_with_history': tst_with_history,
        'total_chains': len(all_cases_by_core),
        'multi_instance_chains': multi_instance_count,
        'tst_in_chains': tst_in_chains
    }
    
    output_path = Path("tst_analysis_results")
    output_path.mkdir(exist_ok=True)
    
    with open(output_path / f"sumario_tst_{timestamp}.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Análise concluída! Sumário salvo em: tst_analysis_results/sumario_tst_{timestamp}.json")
    
    return summary

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Análise Rápida TST")
    parser.add_argument("--external-path", type=str,
                       default="/Users/danilobortoli/Documents/Tese de doutorado da Andreia/Dados da segunda extração/raw",
                       help="Caminho para dados externos")
    
    args = parser.parse_args()
    
    quick_tst_analysis(args.external_path)