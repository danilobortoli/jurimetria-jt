#!/usr/bin/env python3
"""
Investigação de Números Idênticos
Analisa quantas conexões reais existem com números processuais idênticos.
"""

import csv
from collections import defaultdict

class IdenticalNumberInvestigator:
    """Investiga conexões com números processuais idênticos."""
    
    def __init__(self):
        self.output_path = "identical_investigation_results"
        import os
        os.makedirs(self.output_path, exist_ok=True)
    
    def load_data(self, csv_file):
        """Carrega dados de assédio moral."""
        print("📂 Carregando dados para investigação de números idênticos...")
        
        all_cases = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['eh_assedio_moral'] == 'True':
                    all_cases.append(row)
        
        print(f"✅ Carregados {len(all_cases):,} casos de assédio moral")
        return all_cases
    
    def extract_exact_core(self, numero_processo):
        """Extrai núcleo exato do número processual."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        if len(numbers_only) >= 20:
            return numbers_only[:7] + numbers_only[9:]
        return numbers_only
    
    def analyze_exact_matches(self, cases):
        """Analisa matches exatos entre instâncias."""
        print("\n🔍 ANÁLISE DE MATCHES EXATOS")
        print("=" * 50)
        
        # Organiza por core exato
        by_exact_core = defaultdict(list)
        for case in cases:
            core = self.extract_exact_core(case['numero_processo'])
            by_exact_core[core].append(case)
        
        # Estatísticas gerais
        total_cores = len(by_exact_core)
        multi_instance_cores = {core: cases for core, cases in by_exact_core.items() if len(cases) > 1}
        single_cores = {core: cases[0] for core, cases in by_exact_core.items() if len(cases) == 1}
        
        print(f"Total de cores únicos: {total_cores:,}")
        print(f"Cores com múltiplas instâncias: {len(multi_instance_cores):,}")
        print(f"Cores com instância única: {len(single_cores):,}")
        
        # Analisa tipos de cadeia
        chain_types = defaultdict(int)
        chain_examples = defaultdict(list)
        
        for core, cases in multi_instance_cores.items():
            graus = [case['grau'] for case in cases]
            unique_graus = sorted(set(graus))
            chain_signature = "→".join(unique_graus)
            
            chain_types[chain_signature] += 1
            if len(chain_examples[chain_signature]) < 5:
                chain_examples[chain_signature].append((core, cases))
        
        print(f"\n📊 TIPOS DE CADEIA ENCONTRADOS:")
        print("=" * 40)
        for chain_type, count in sorted(chain_types.items(), key=lambda x: x[1], reverse=True):
            percent = (count / len(multi_instance_cores)) * 100
            print(f"  {chain_type}: {count:,} ({percent:.1f}%)")
        
        # Foca em G1→G2→SUP
        g1_g2_sup_chains = []
        for core, cases in multi_instance_cores.items():
            graus = [case['grau'] for case in cases]
            if 'G1' in graus and 'G2' in graus and 'SUP' in graus:
                g1_g2_sup_chains.append((core, cases))
        
        print(f"\n🎯 CADEIAS COMPLETAS G1→G2→TST: {len(g1_g2_sup_chains):,}")
        
        # Análise detalhada das cadeias completas
        if g1_g2_sup_chains:
            print(f"\n🔍 ANÁLISE DETALHADA DAS PRIMEIRAS 10 CADEIAS G1→G2→TST:")
            print("=" * 60)
            
            for i, (core, cases) in enumerate(g1_g2_sup_chains[:10]):
                print(f"\n--- Cadeia {i+1}: Core {core} ---")
                
                # Organiza casos por grau
                g1_cases = [c for c in cases if c['grau'] == 'G1']
                g2_cases = [c for c in cases if c['grau'] == 'G2']
                sup_cases = [c for c in cases if c['grau'] == 'SUP']
                
                print(f"G1 ({len(g1_cases)}): ", end="")
                for case in g1_cases:
                    print(f"{case['numero_processo']} ({case['tribunal']}) ", end="")
                print()
                
                print(f"G2 ({len(g2_cases)}): ", end="")
                for case in g2_cases:
                    print(f"{case['numero_processo']} ({case['tribunal']}) ", end="")
                print()
                
                print(f"TST ({len(sup_cases)}): ", end="")
                for case in sup_cases:
                    print(f"{case['numero_processo']} ({case['tribunal']}) ", end="")
                print()
                
                # Verifica se números são realmente idênticos
                all_numbers = [case['numero_processo'] for case in cases]
                are_identical = len(set(all_numbers)) == 1
                print(f"Números idênticos: {'✅ SIM' if are_identical else '❌ NÃO'}")
                
                if not are_identical:
                    print("Números encontrados:")
                    for num in set(all_numbers):
                        print(f"  - {num}")
        
        return {
            'total_cores': total_cores,
            'multi_instance_cores': len(multi_instance_cores),
            'single_cores': len(single_cores),
            'chain_types': dict(chain_types),
            'g1_g2_sup_chains': len(g1_g2_sup_chains),
            'examples': dict(chain_examples)
        }
    
    def analyze_number_variations(self, cases):
        """Analisa variações nos números processuais."""
        print(f"\n🔍 ANÁLISE DE VARIAÇÕES NOS NÚMEROS:")
        print("=" * 50)
        
        # Agrupa por números completos
        by_full_number = defaultdict(list)
        for case in cases:
            by_full_number[case['numero_processo']].append(case)
        
        # Casos com mesmo número completo mas instâncias diferentes
        same_number_diff_instance = []
        for numero, cases_list in by_full_number.items():
            graus = [case['grau'] for case in cases_list]
            if len(set(graus)) > 1:  # Mesmo número, graus diferentes
                same_number_diff_instance.append((numero, cases_list))
        
        print(f"Números idênticos em instâncias diferentes: {len(same_number_diff_instance):,}")
        
        if same_number_diff_instance:
            print(f"\nPrimeiros 10 exemplos:")
            for i, (numero, cases_list) in enumerate(same_number_diff_instance[:10]):
                graus = [case['grau'] for case in cases_list]
                tribunais = [case['tribunal'] for case in cases_list]
                print(f"  {i+1}. {numero}")
                print(f"     Graus: {', '.join(set(graus))}")
                print(f"     Tribunais: {', '.join(set(tribunais))}")
        
        return len(same_number_diff_instance)
    
    def investigate_tst_numbers(self, cases):
        """Investiga especificamente os números dos casos TST."""
        print(f"\n🔍 INVESTIGAÇÃO ESPECÍFICA - NÚMEROS TST:")
        print("=" * 50)
        
        tst_cases = [case for case in cases if case['grau'] == 'SUP']
        print(f"Total de casos TST: {len(tst_cases):,}")
        
        # Analisa padrões nos números TST
        tst_patterns = defaultdict(int)
        for case in tst_cases:
            numero = case['numero_processo']
            if 'RR' in numero:
                tst_patterns['RR'] += 1
            elif 'AIRR' in numero:
                tst_patterns['AIRR'] += 1
            elif len(''.join(filter(str.isdigit, numero))) == 20:
                tst_patterns['Numérico 20 dígitos'] += 1
            else:
                tst_patterns['Outro'] += 1
        
        print("Padrões encontrados no TST:")
        for pattern, count in tst_patterns.items():
            percent = (count / len(tst_cases)) * 100
            print(f"  {pattern}: {count:,} ({percent:.1f}%)")
        
        # Exemplos de números TST
        print(f"\nExemplos de números TST:")
        for i, case in enumerate(tst_cases[:10]):
            print(f"  {i+1}. {case['numero_processo']}")
        
        return dict(tst_patterns)
    
    def generate_investigation_report(self, analysis_results, number_variations, tst_patterns):
        """Gera relatório da investigação."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = f"""# Investigação de Números Processuais Idênticos

**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Objetivo
Investigar quantas conexões reais existem quando exigimos números processuais idênticos entre G1→G2→TST.

## 📊 Resultados da Análise

### Estatísticas Gerais
- **Total de cores únicos**: {analysis_results['total_cores']:,}
- **Cores com múltiplas instâncias**: {analysis_results['multi_instance_cores']:,}
- **Cores com instância única**: {analysis_results['single_cores']:,}

### Cadeias G1→G2→TST com Números Idênticos
- **Total encontrado**: {analysis_results['g1_g2_sup_chains']:,}

### Tipos de Cadeia Processual
"""
        
        for chain_type, count in analysis_results['chain_types'].items():
            percent = (count / analysis_results['multi_instance_cores']) * 100 if analysis_results['multi_instance_cores'] > 0 else 0
            report += f"- **{chain_type}**: {count:,} ({percent:.1f}%)\n"
        
        report += f"""

### Números Idênticos em Instâncias Diferentes
- **Total**: {number_variations:,}

### Padrões nos Números TST
"""
        
        for pattern, count in tst_patterns.items():
            report += f"- **{pattern}**: {count:,}\n"
        
        report += f"""

## 🚨 Conclusões

1. **Cadeias G1→G2→TST verdadeiras**: {analysis_results['g1_g2_sup_chains']:,}
2. **Realidade dos dados**: A maioria dos casos são instâncias isoladas
3. **Números TST**: Seguem padrões específicos diferentes de G1/G2

## 💡 Recomendações

1. **Aceitar a realidade dos dados**: Há poucas cadeias completas verdadeiras
2. **Focar na análise correta**: Usar apenas conexões com números idênticos
3. **Investigar processos isolados**: Muitos casos são únicos por natureza
"""
        
        # Salva relatório
        report_path = f"{self.output_path}/identical_investigation_{timestamp}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Relatório salvo: {report_path}")
        return report_path
    
    def run_investigation(self, csv_file):
        """Executa investigação completa."""
        print("🔍 INVESTIGAÇÃO DE NÚMEROS PROCESSUAIS IDÊNTICOS")
        print("=" * 60)
        
        # Carrega dados
        cases = self.load_data(csv_file)
        
        # Analisa matches exatos
        analysis_results = self.analyze_exact_matches(cases)
        
        # Analisa variações nos números
        number_variations = self.analyze_number_variations(cases)
        
        # Investiga números TST
        tst_patterns = self.investigate_tst_numbers(cases)
        
        # Gera relatório
        report_path = self.generate_investigation_report(analysis_results, number_variations, tst_patterns)
        
        print(f"\n📊 RESUMO FINAL:")
        print("=" * 30)
        print(f"Cadeias G1→G2→TST verdadeiras: {analysis_results['g1_g2_sup_chains']:,}")
        print(f"Números idênticos multi-instância: {number_variations:,}")
        
        return analysis_results

def main():
    """Função principal."""
    investigator = IdenticalNumberInvestigator()
    investigator.run_investigation("consolidated_all_data.csv")

if __name__ == "__main__":
    main()