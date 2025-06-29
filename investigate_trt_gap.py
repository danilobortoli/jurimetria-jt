#!/usr/bin/env python3
"""
Investigação: Onde estão os TRTs?
Verifica se os processos realmente pulam do G1 para TST ou se há dados faltando.
"""

import csv
from collections import defaultdict

def investigate_trt_gap(csv_file: str):
    """Investiga a ausência de dados TRT nas cadeias."""
    
    print("🔍 INVESTIGANDO A AUSÊNCIA DOS TRTs")
    print("=" * 50)
    
    # Carrega dados
    all_cases = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['eh_assedio_moral'] == 'True':
                all_cases.append(row)
    
    # Organiza por core
    by_core = defaultdict(list)
    for case in all_cases:
        core = case['numero_core']
        if core:
            by_core[core].append(case)
    
    # Analisa cadeias multi-instância
    multi_chains = {core: cases for core, cases in by_core.items() if len(cases) > 1}
    
    print(f"📊 Total de cadeias multi-instância: {len(multi_chains):,}")
    
    # Classifica tipos de cadeia
    chain_types = {
        'G1_only': 0,
        'G2_only': 0, 
        'TST_only': 0,
        'G1_G2': 0,
        'G1_TST': 0,
        'G2_TST': 0,
        'G1_G2_TST': 0,
        'other': 0
    }
    
    examples = {
        'G1_TST': [],
        'G2_TST': [],
        'G1_G2_TST': [],
        'missing_G2': []
    }
    
    for core, cases in multi_chains.items():
        graus = [case['grau'] for case in cases]
        unique_graus = list(set(graus))
        
        # Classifica tipo de cadeia
        has_g1 = any(g in ['G1'] for g in unique_graus)
        has_g2 = any(g in ['G2'] for g in unique_graus) 
        has_tst = any(g in ['SUP'] for g in unique_graus)
        
        if has_g1 and has_g2 and has_tst:
            chain_types['G1_G2_TST'] += 1
            if len(examples['G1_G2_TST']) < 5:
                examples['G1_G2_TST'].append((core, cases))
        elif has_g1 and has_tst and not has_g2:
            chain_types['G1_TST'] += 1
            if len(examples['G1_TST']) < 10:
                examples['G1_TST'].append((core, cases))
                examples['missing_G2'].append((core, cases))
        elif has_g2 and has_tst and not has_g1:
            chain_types['G2_TST'] += 1
            if len(examples['G2_TST']) < 5:
                examples['G2_TST'].append((core, cases))
        elif has_g1 and has_g2 and not has_tst:
            chain_types['G1_G2'] += 1
        else:
            chain_types['other'] += 1
    
    print("\n📊 TIPOS DE CADEIA ENCONTRADOS:")
    print("=" * 40)
    for chain_type, count in chain_types.items():
        percent = (count / len(multi_chains)) * 100
        print(f"  {chain_type}: {count:,} ({percent:.1f}%)")
    
    # Foca nos casos G1→TST (sem G2)
    print(f"\n🚨 CASOS G1→TST (SEM G2): {chain_types['G1_TST']:,}")
    print("=" * 50)
    
    # Analisa alguns exemplos em detalhe
    print("\n🔍 ANÁLISE DETALHADA DE CASOS G1→TST:")
    print("=" * 50)
    
    for i, (core, cases) in enumerate(examples['G1_TST'][:5]):
        print(f"\nCaso {i+1}: Core {core}")
        
        for case in sorted(cases, key=lambda x: x['grau']):
            numero = case['numero_processo']
            grau = case['grau']
            tribunal = case['tribunal']
            arquivo = case['arquivo_origem']
            instancia = case['instancia_normalizada']
            
            print(f"  {grau} ({instancia}): {numero}")
            print(f"    Tribunal: {tribunal}")
            print(f"    Arquivo: {arquivo}")
            
            # Verifica se número sugere recurso
            if grau == 'SUP':
                # Analisa o número do processo TST para ver se indica recurso
                if 'RR' in numero or 'AIRR' in numero:
                    print(f"    ⚠️  RECURSO DE REVISTA detectado no número!")
    
    # Investigação específica: busca por padrões nos números
    print(f"\n🔍 INVESTIGAÇÃO DE NÚMEROS PROCESSUAIS:")
    print("=" * 50)
    
    # Analisa números dos casos G1→TST
    g1_tst_numbers = []
    for core, cases in examples['missing_G2'][:10]:
        case_info = {
            'core': core,
            'g1_number': '',
            'tst_number': '',
            'g1_tribunal': '',
            'tst_tribunal': 'TST'
        }
        
        for case in cases:
            if case['grau'] == 'G1':
                case_info['g1_number'] = case['numero_processo']
                case_info['g1_tribunal'] = case['tribunal']
            elif case['grau'] == 'SUP':
                case_info['tst_number'] = case['numero_processo']
        
        g1_tst_numbers.append(case_info)
    
    for i, info in enumerate(g1_tst_numbers):
        print(f"\nCaso {i+1}:")
        print(f"  G1:  {info['g1_number']} ({info['g1_tribunal']})")
        print(f"  TST: {info['tst_number']}")
        
        # Verifica padrões
        g1_num = info['g1_number']
        tst_num = info['tst_number']
        
        if 'RR' in tst_num:
            print(f"  📝 TST é Recurso de Revista (RR)")
        if 'AIRR' in tst_num:
            print(f"  📝 TST é Agravo de Instrumento em RR")
        
        # Verifica se número base é similar
        g1_clean = ''.join(filter(str.isdigit, g1_num))
        tst_clean = ''.join(filter(str.isdigit, tst_num))
        
        if len(g1_clean) >= 15 and len(tst_clean) >= 15:
            g1_core_num = g1_clean[5:15]  # Núcleo do processo
            tst_core_num = tst_clean[5:15] if len(tst_clean) > 15 else tst_clean[3:13]
            
            if g1_core_num == tst_core_num:
                print(f"  ✅ Núcleos dos números COINCIDEM")
            else:
                print(f"  ❌ Núcleos DIFERENTES: G1={g1_core_num} vs TST={tst_core_num}")
    
    # Busca por casos G2 isolados que poderiam ser da mesma cadeia
    print(f"\n🔍 BUSCA POR G2 ISOLADOS QUE PODERIAM SER DAS MESMAS CADEIAS:")
    print("=" * 60)
    
    # Casos G2 que não estão em cadeias multi-instância
    single_cases = {core: cases[0] for core, cases in by_core.items() if len(cases) == 1}
    g2_singles = {core: case for core, case in single_cases.items() if case['grau'] == 'G2'}
    
    print(f"G2 isolados encontrados: {len(g2_singles):,}")
    
    # Verifica se algum G2 isolado poderia pertencer às cadeias G1→TST
    potential_matches = 0
    for core_g1_tst, cases_g1_tst in examples['missing_G2'][:5]:
        g1_case = next(c for c in cases_g1_tst if c['grau'] == 'G1')
        g1_tribunal = g1_case['tribunal']
        
        print(f"\nBuscando G2 para cadeia {core_g1_tst} (G1 do {g1_tribunal}):")
        
        # Busca G2s do mesmo tribunal
        matching_g2s = []
        for core_g2, case_g2 in list(g2_singles.items())[:100]:  # Primeiros 100
            if case_g2['tribunal'] == g1_tribunal:
                # Verifica se números são relacionados
                g1_num = g1_case['numero_processo'] 
                g2_num = case_g2['numero_processo']
                
                # Extrai anos
                g1_year = g1_num[9:13] if len(g1_num) > 13 else ''
                g2_year = g2_num[9:13] if len(g2_num) > 13 else ''
                
                if g1_year == g2_year and g1_year:
                    matching_g2s.append((core_g2, case_g2))
        
        if matching_g2s:
            print(f"  Possíveis G2 relacionados: {len(matching_g2s)}")
            for core_g2, case_g2 in matching_g2s[:3]:
                print(f"    {case_g2['numero_processo']} (Core: {core_g2})")
            potential_matches += len(matching_g2s)
    
    print(f"\n📊 RESUMO DA INVESTIGAÇÃO:")
    print("=" * 40)
    print(f"Cadeias G1→TST (sem G2): {chain_types['G1_TST']:,}")
    print(f"Cadeias G1→G2→TST: {chain_types['G1_G2_TST']:,}")
    print(f"G2 isolados: {len(g2_singles):,}")
    print(f"Possíveis G2 não vinculados: {potential_matches}")
    
    # Conclusão
    print(f"\n💡 CONCLUSÕES:")
    print("=" * 30)
    if chain_types['G1_TST'] > chain_types['G1_G2_TST'] * 10:
        print("🚨 PROBLEMA IDENTIFICADO:")
        print("  - Muitos casos 'pulam' do G1 para TST")
        print("  - Dados de G2 (TRT) provavelmente FALTANDO")
        print("  - Algoritmo de matching pode estar falhando")
        print("  - Núcleos dos números podem não estar corretos")
    else:
        print("✅ Distribuição normal de fluxos processuais")

def main():
    """Função principal."""
    investigate_trt_gap("consolidated_all_data.csv")

if __name__ == "__main__":
    main()