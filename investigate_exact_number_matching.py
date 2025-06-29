#!/usr/bin/env python3
"""
Investigação de Matching por Números Exatos
Verifica por que não encontramos o mesmo número de processo nas três instâncias.
"""

import csv
from collections import defaultdict
import json

class ExactNumberMatcher:
    """Investiga matching exato de números processuais."""
    
    def __init__(self):
        self.output_path = "exact_matching_results"
        import os
        os.makedirs(self.output_path, exist_ok=True)
    
    def load_data(self, csv_file):
        """Carrega dados de assédio moral."""
        print("📂 Carregando dados para investigação de números exatos...")
        
        all_cases = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['eh_assedio_moral'] == 'True':
                    all_cases.append(row)
        
        print(f"✅ Carregados {len(all_cases):,} casos de assédio moral")
        return all_cases
    
    def investigate_exact_number_matches(self, cases):
        """Investiga matches por número exato."""
        print("\n🔍 INVESTIGAÇÃO DE NÚMEROS EXATOS")
        print("=" * 50)
        
        # Organiza por número de processo exato
        by_exact_number = defaultdict(list)
        for case in cases:
            numero = case['numero_processo']
            by_exact_number[numero].append(case)
        
        # Estatísticas
        total_numbers = len(by_exact_number)
        multi_instance_numbers = {num: cases for num, cases in by_exact_number.items() if len(cases) > 1}
        
        print(f"Total de números únicos: {total_numbers:,}")
        print(f"Números em múltiplas instâncias: {len(multi_instance_numbers):,}")
        
        # Analisa os casos de múltiplas instâncias
        chain_patterns = defaultdict(int)
        examples = defaultdict(list)
        
        print(f"\n📋 ANÁLISE DETALHADA DOS PRIMEIROS 20 CASOS MULTI-INSTÂNCIA:")
        print("=" * 60)
        
        for i, (numero, cases_list) in enumerate(list(multi_instance_numbers.items())[:20]):
            graus = [case['grau'] for case in cases_list]
            tribunais = [case['tribunal'] for case in cases_list]
            unique_graus = sorted(set(graus))
            chain_pattern = "→".join(unique_graus)
            
            chain_patterns[chain_pattern] += 1
            if len(examples[chain_pattern]) < 3:
                examples[chain_pattern].append((numero, cases_list))
            
            print(f"\n{i+1}. Número: {numero}")
            print(f"   Instâncias: {chain_pattern}")
            print(f"   Tribunais: {', '.join(set(tribunais))}")
            
            for case in cases_list:
                instancia = case.get('instancia_normalizada', 'N/A')
                arquivo = case.get('arquivo_origem', 'N/A')
                print(f"   - {case['grau']}: {case['tribunal']} | {instancia} | {arquivo}")
            
            # Verifica se é cadeia completa G1→G2→SUP
            if 'G1' in unique_graus and 'G2' in unique_graus and 'SUP' in unique_graus:
                print("   🎉 CADEIA COMPLETA G1→G2→TST!")
        
        # Resumo dos padrões
        print(f"\n📊 PADRÕES DE CADEIA ENCONTRADOS:")
        print("=" * 40)
        for pattern, count in sorted(chain_patterns.items(), key=lambda x: x[1], reverse=True):
            percent = (count / len(multi_instance_numbers)) * 100 if len(multi_instance_numbers) > 0 else 0
            print(f"  {pattern}: {count:,} ({percent:.1f}%)")
        
        # Conta cadeias completas
        complete_chains = chain_patterns.get('G1→G2→SUP', 0)
        print(f"\n🏆 CADEIAS COMPLETAS G1→G2→TST: {complete_chains}")
        
        return {
            'total_numbers': total_numbers,
            'multi_instance_count': len(multi_instance_numbers),
            'chain_patterns': dict(chain_patterns),
            'complete_chains': complete_chains,
            'examples': dict(examples)
        }
    
    def analyze_number_variations(self, cases):
        """Analisa variações sutis nos números."""
        print(f"\n🔍 ANÁLISE DE VARIAÇÕES SUTIS NOS NÚMEROS")
        print("=" * 50)
        
        # Agrupa por número base (removendo pequenas variações)
        base_numbers = defaultdict(list)
        
        for case in cases:
            numero = case['numero_processo']
            # Remove caracteres não numéricos e pontuação
            base = ''.join(filter(str.isdigit, numero))
            base_numbers[base].append(case)
        
        # Encontra casos onde o número base é igual mas há variações
        variations = {}
        for base, cases_list in base_numbers.items():
            if len(cases_list) > 1:
                # Verifica se há números diferentes com mesmo base
                different_numbers = set(case['numero_processo'] for case in cases_list)
                if len(different_numbers) > 1:
                    variations[base] = {
                        'numbers': list(different_numbers),
                        'cases': cases_list
                    }
        
        print(f"Números base com variações: {len(variations)}")
        
        if variations:
            print(f"\nPrimeiros 10 exemplos de variações:")
            for i, (base, info) in enumerate(list(variations.items())[:10]):
                print(f"\n{i+1}. Base: {base}")
                for num in info['numbers']:
                    cases_with_num = [c for c in info['cases'] if c['numero_processo'] == num]
                    graus = [c['grau'] for c in cases_with_num]
                    print(f"   {num}: {', '.join(set(graus))}")
        
        return len(variations)
    
    def investigate_tribunal_specific_patterns(self, cases):
        """Investiga padrões específicos por tribunal."""
        print(f"\n🏛️ INVESTIGAÇÃO POR TRIBUNAL")
        print("=" * 40)
        
        # Organiza por tribunal e grau
        tribunal_data = defaultdict(lambda: defaultdict(list))
        
        for case in cases:
            tribunal = case['tribunal']
            grau = case['grau']
            tribunal_data[tribunal][grau].append(case)
        
        # Foca nos principais tribunais
        main_tribunals = ['TRT2', 'TRT15', 'TRT4', 'TST']
        
        for tribunal in main_tribunals:
            if tribunal in tribunal_data:
                print(f"\n🏛️ {tribunal}:")
                for grau in ['G1', 'G2', 'SUP']:
                    if grau in tribunal_data[tribunal]:
                        count = len(tribunal_data[tribunal][grau])
                        print(f"  {grau}: {count:,} casos")
                        
                        # Mostra alguns números de exemplo
                        examples = tribunal_data[tribunal][grau][:3]
                        for ex in examples:
                            print(f"    Ex: {ex['numero_processo']}")
        
        # Verifica se TST tem números que também aparecem nos TRTs
        tst_numbers = set()
        trt_numbers = set()
        
        for case in cases:
            numero = case['numero_processo']
            if case['tribunal'] == 'TST':
                tst_numbers.add(numero)
            elif case['tribunal'].startswith('TRT'):
                trt_numbers.add(numero)
        
        common_numbers = tst_numbers & trt_numbers
        print(f"\n🔗 NÚMEROS COMUNS TST ↔ TRT: {len(common_numbers)}")
        
        if common_numbers:
            print("Primeiros 5 números comuns:")
            for i, numero in enumerate(list(common_numbers)[:5]):
                print(f"  {i+1}. {numero}")
                
                # Mostra onde aparece
                tst_cases = [c for c in cases if c['numero_processo'] == numero and c['tribunal'] == 'TST']
                trt_cases = [c for c in cases if c['numero_processo'] == numero and c['tribunal'].startswith('TRT')]
                
                print(f"     TST: {[c['grau'] for c in tst_cases]}")
                for trt_case in trt_cases:
                    print(f"     {trt_case['tribunal']}: {trt_case['grau']}")
        
        return len(common_numbers)
    
    def investigate_sampling_issue(self, cases):
        """Investiga se há problema de amostragem."""
        print(f"\n🎯 INVESTIGAÇÃO DE PROBLEMAS DE AMOSTRAGEM")
        print("=" * 50)
        
        # Verifica distribuição por arquivo de origem
        by_file = defaultdict(list)
        for case in cases:
            arquivo = case.get('arquivo_origem', 'unknown')
            by_file[arquivo].append(case)
        
        print(f"Número de arquivos de origem: {len(by_file)}")
        
        # Mostra distribuição
        sorted_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        print("\nTop 10 arquivos por número de casos:")
        for arquivo, casos in sorted_files:
            graus = [c['grau'] for c in casos]
            grau_counts = {g: graus.count(g) for g in set(graus)}
            print(f"  {arquivo}: {len(casos):,} casos | {grau_counts}")
        
        # Verifica se há arquivos TST separados dos TRT
        tst_files = [f for f in by_file.keys() if 'tst' in f.lower()]
        trt_files = [f for f in by_file.keys() if 'trt' in f.lower()]
        
        print(f"\nArquivos TST: {len(tst_files)}")
        print(f"Arquivos TRT: {len(trt_files)}")
        
        if tst_files:
            print("Arquivos TST encontrados:")
            for f in tst_files[:5]:
                print(f"  - {f}")
        
        return {
            'total_files': len(by_file),
            'tst_files': len(tst_files),
            'trt_files': len(trt_files)
        }
    
    def generate_investigation_report(self, exact_results, variations_count, common_numbers_count, sampling_results):
        """Gera relatório da investigação."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = f"""# Investigação de Matching por Números Exatos

**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Objetivo
Investigar por que não encontramos o mesmo número de processo nas três instâncias (G1→G2→TST).

## 📊 Resultados da Investigação

### Números Exatos
- **Total de números únicos**: {exact_results['total_numbers']:,}
- **Números em múltiplas instâncias**: {exact_results['multi_instance_count']:,}
- **Cadeias completas G1→G2→TST**: {exact_results['complete_chains']:,}

### Padrões de Cadeia Encontrados
"""
        
        for pattern, count in exact_results['chain_patterns'].items():
            percent = (count / exact_results['multi_instance_count']) * 100 if exact_results['multi_instance_count'] > 0 else 0
            report += f"- **{pattern}**: {count:,} ({percent:.1f}%)\n"
        
        report += f"""

### Problemas Identificados
- **Variações sutis nos números**: {variations_count:,}
- **Números comuns TST↔TRT**: {common_numbers_count:,}
- **Arquivos TST separados**: {sampling_results['tst_files']}
- **Arquivos TRT**: {sampling_results['trt_files']}

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
"""
        
        # Salva relatório
        report_path = f"{self.output_path}/exact_matching_report_{timestamp}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Salva dados detalhados
        data_path = f"{self.output_path}/detailed_data_{timestamp}.json"
        detailed_data = {
            'exact_results': exact_results,
            'variations_count': variations_count,
            'common_numbers_count': common_numbers_count,
            'sampling_results': sampling_results
        }
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(detailed_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo: {report_path}")
        return report_path
    
    def run_investigation(self, csv_file):
        """Executa investigação completa."""
        print("🔍 INVESTIGAÇÃO DE MATCHING POR NÚMEROS EXATOS")
        print("=" * 60)
        
        # Carrega dados
        cases = self.load_data(csv_file)
        
        # Investiga números exatos
        exact_results = self.investigate_exact_number_matches(cases)
        
        # Analisa variações
        variations_count = self.analyze_number_variations(cases)
        
        # Investiga padrões por tribunal
        common_numbers_count = self.investigate_tribunal_specific_patterns(cases)
        
        # Investiga problemas de amostragem
        sampling_results = self.investigate_sampling_issue(cases)
        
        # Gera relatório
        report_path = self.generate_investigation_report(
            exact_results, variations_count, common_numbers_count, sampling_results
        )
        
        print(f"\n📊 RESUMO FINAL:")
        print("=" * 30)
        print(f"Cadeias G1→G2→TST: {exact_results['complete_chains']:,}")
        print(f"Multi-instância: {exact_results['multi_instance_count']:,}")
        print(f"Números comuns TST↔TRT: {common_numbers_count:,}")
        
        return exact_results

def main():
    """Função principal."""
    investigator = ExactNumberMatcher()
    investigator.run_investigation("consolidated_all_data.csv")

if __name__ == "__main__":
    main()