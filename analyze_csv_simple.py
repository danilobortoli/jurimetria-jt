#!/usr/bin/env python3
"""
Análise Simples do CSV - Sem pandas
Verifica distribuição de casos por arquivos e cadeias.
"""

import csv
from collections import defaultdict, Counter
from datetime import datetime

def analyze_csv_distribution(csv_file: str):
    """Analisa distribuição de casos no CSV."""
    
    print(f"🔍 Analisando distribuição de casos em: {csv_file}")
    
    # Estruturas para análise
    by_core = defaultdict(list)
    by_tribunal = defaultdict(int)
    by_grau = defaultdict(int)
    by_arquivo = defaultdict(int)
    total_rows = 0
    assedio_cases = 0
    
    # Lê o CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            total_rows += 1
            
            core = row['numero_core']
            if core:
                by_core[core].append({
                    'numero': row['numero_processo'],
                    'tribunal': row['tribunal'],
                    'grau': row['grau'],
                    'instancia': row['instancia_normalizada'],
                    'arquivo': row['arquivo_origem'],
                    'tem_primeira': row['tem_resultado_primeira'] == 'True',
                    'tem_recurso': row['tem_resultado_recurso'] == 'True',
                    'resultado_primeira': row['resultado_primeira_nome'],
                    'resultado_recurso': row['resultado_recurso_nome']
                })
            
            # Estatísticas gerais
            by_tribunal[row['tribunal']] += 1
            by_grau[row['grau']] += 1
            by_arquivo[row['arquivo_origem']] += 1
            
            if row['eh_assedio_moral'] == 'True':
                assedio_cases += 1
    
    print(f"📊 Total de registros: {total_rows:,}")
    print(f"🎯 Casos de assédio moral: {assedio_cases:,}")
    print(f"🔗 Cores únicos: {len(by_core):,}")
    
    # Analisa cadeias multi-instância
    multi_instance = {core: cases for core, cases in by_core.items() if len(cases) > 1}
    print(f"⛓️ Cadeias multi-instância: {len(multi_instance):,}")
    
    # Analisa casos em múltiplos arquivos
    multi_file_cases = 0
    cross_tribunal_cases = 0
    
    for core, cases in multi_instance.items():
        arquivos = set(case['arquivo'] for case in cases)
        if len(arquivos) > 1:
            multi_file_cases += 1
            
            # Verifica se são de tribunais diferentes
            tribunais = set(case['tribunal'] for case in cases)
            if len(tribunais) > 1:
                cross_tribunal_cases += 1
    
    print(f"📁 Casos em múltiplos arquivos: {multi_file_cases:,}")
    print(f"🏛️ Casos em tribunais diferentes: {cross_tribunal_cases:,}")
    
    # Exemplos de casos distribuídos
    print(f"\n🔍 EXEMPLOS DE CASOS EM MÚLTIPLOS ARQUIVOS:")
    print("=" * 60)
    
    count = 0
    for core, cases in multi_instance.items():
        arquivos = set(case['arquivo'] for case in cases)
        if len(arquivos) > 1 and count < 10:
            count += 1
            print(f"\nCaso {count}: Core {core}")
            print(f"  Instâncias: {len(cases)}")
            
            for case in cases:
                print(f"    {case['grau']} ({case['instancia']}) - {case['tribunal']} - {case['arquivo']}")
    
    # Análise de fluxos completos
    print(f"\n⚖️ ANÁLISE DE FLUXOS COMPLETOS:")
    print("=" * 60)
    
    fluxos_completos = []
    fluxos_g1_tst = []
    
    for core, cases in multi_instance.items():
        instancias = [case['instancia'] for case in cases]
        
        # Fluxo completo G1→G2→TST
        if all(inst in instancias for inst in ['Primeira Instância', 'Segunda Instância', 'TST']):
            fluxos_completos.append((core, cases))
        
        # Fluxo G1→TST (sem G2)
        elif 'Primeira Instância' in instancias and 'TST' in instancias and 'Segunda Instância' not in instancias:
            fluxos_g1_tst.append((core, cases))
    
    print(f"🔄 Fluxos G1→G2→TST: {len(fluxos_completos):,}")
    print(f"🔀 Fluxos G1→TST: {len(fluxos_g1_tst):,}")
    
    # Analisa alguns fluxos completos
    if fluxos_completos:
        print(f"\n📊 ANÁLISE DE ALGUNS FLUXOS COMPLETOS:")
        print("=" * 60)
        
        resultados_determinaveis = 0
        trabalhador_vitorias = 0
        
        for i, (core, cases) in enumerate(fluxos_completos[:20]):
            # Ordena por grau
            cases_sorted = sorted(cases, key=lambda x: {'G1': 1, 'G2': 2, 'SUP': 3}.get(x['grau'], 4))
            
            g1_case = next((c for c in cases_sorted if c['instancia'] == 'Primeira Instância'), None)
            tst_case = next((c for c in cases_sorted if c['instancia'] == 'TST'), None)
            
            if g1_case and tst_case and g1_case['tem_primeira'] and tst_case['tem_recurso']:
                resultado_g1 = g1_case['resultado_primeira']
                resultado_tst = tst_case['resultado_recurso']
                
                # Aplica lógica correta
                trabalhador_ganhou_g1 = resultado_g1 in ['Procedência', 'Procedência em Parte']
                tst_provido = resultado_tst in ['Provimento', 'Provimento em Parte']
                
                if trabalhador_ganhou_g1:
                    trabalhador_venceu = not tst_provido  # Se TST proveu, empregador ganhou
                else:
                    trabalhador_venceu = tst_provido  # Se TST proveu, trabalhador ganhou
                
                resultados_determinaveis += 1
                if trabalhador_venceu:
                    trabalhador_vitorias += 1
                
                if i < 5:  # Mostra primeiros 5
                    status = "GANHOU" if trabalhador_venceu else "PERDEU"
                    print(f"\nFluxo {i+1} (Core: {core}):")
                    print(f"  G1: {resultado_g1} → TST: {resultado_tst} = Trabalhador {status}")
                    
                    # Mostra arquivos
                    arquivos = set(case['arquivo'] for case in cases)
                    print(f"  Arquivos: {', '.join(sorted(arquivos))}")
        
        if resultados_determinaveis > 0:
            taxa_sucesso = (trabalhador_vitorias / resultados_determinaveis) * 100
            print(f"\n📈 RESULTADOS (primeiros 20 fluxos):")
            print(f"  Determináveis: {resultados_determinaveis}")
            print(f"  Vitórias trabalhador: {trabalhador_vitorias}")
            print(f"  Taxa de sucesso: {taxa_sucesso:.1f}%")
    
    # Estatísticas por tribunal
    print(f"\n🏛️ TOP 15 TRIBUNAIS:")
    print("=" * 40)
    sorted_tribunals = sorted(by_tribunal.items(), key=lambda x: x[1], reverse=True)
    for tribunal, count in sorted_tribunals[:15]:
        percent = (count / total_rows) * 100
        print(f"  {tribunal:4}: {count:6,} ({percent:4.1f}%)")
    
    # Estatísticas por grau
    print(f"\n📊 POR GRAU:")
    print("=" * 30)
    for grau, count in sorted(by_grau.items()):
        percent = (count / total_rows) * 100
        print(f"  {grau:4}: {count:6,} ({percent:4.1f}%)")
    
    # Salva resumo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = {
        'timestamp': timestamp,
        'total_registros': total_rows,
        'cores_unicos': len(by_core),
        'cadeias_multiinstancia': len(multi_instance),
        'casos_multiplos_arquivos': multi_file_cases,
        'casos_tribunais_diferentes': cross_tribunal_cases,
        'fluxos_completos_g1_g2_tst': len(fluxos_completos),
        'fluxos_g1_tst': len(fluxos_g1_tst)
    }
    
    with open(f"analise_csv_summary_{timestamp}.json", 'w', encoding='utf-8') as f:
        import json
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resumo salvo em: analise_csv_summary_{timestamp}.json")
    
    return summary

def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Análise Simples do CSV")
    parser.add_argument("--csv-file", type=str,
                       default="consolidated_all_data.csv",
                       help="Arquivo CSV para análise")
    
    args = parser.parse_args()
    
    from pathlib import Path
    if not Path(args.csv_file).exists():
        print(f"❌ Arquivo não encontrado: {args.csv_file}")
        return
    
    analyze_csv_distribution(args.csv_file)

if __name__ == "__main__":
    main()