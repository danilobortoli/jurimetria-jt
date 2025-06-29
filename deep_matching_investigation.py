#!/usr/bin/env python3
"""
Investigação Profunda do Matching de Processos
Analisa por que os dados G2 não estão sendo conectados às cadeias.
"""

import csv
from collections import defaultdict
import re
from datetime import datetime

class DeepMatchingInvestigator:
    """Investigador profundo de matching de processos."""
    
    def __init__(self):
        self.output_path = "matching_investigation_results"
        import os
        os.makedirs(self.output_path, exist_ok=True)
    
    def load_data(self, csv_file):
        """Carrega dados com foco em assédio moral."""
        print("📂 Carregando dados para investigação...")
        
        all_cases = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['eh_assedio_moral'] == 'True':
                    all_cases.append(row)
        
        print(f"✅ Carregados {len(all_cases):,} casos de assédio moral")
        return all_cases
    
    def analyze_number_patterns(self, cases):
        """Analisa padrões nos números processuais."""
        print("\n🔍 ANÁLISE DE PADRÕES NOS NÚMEROS PROCESSUAIS")
        print("=" * 60)
        
        patterns = {
            'G1': defaultdict(list),
            'G2': defaultdict(list), 
            'TST': defaultdict(list)
        }
        
        # Coleta amostras por grau
        for case in cases[:1000]:  # Primeiros 1000 para análise
            grau = case['grau']
            numero = case['numero_processo']
            
            if grau == 'G1':
                patterns['G1']['numbers'].append(numero)
                patterns['G1']['samples'].append(case)
            elif grau == 'G2':
                patterns['G2']['numbers'].append(numero)
                patterns['G2']['samples'].append(case)
            elif grau == 'SUP':
                patterns['TST']['numbers'].append(numero)
                patterns['TST']['samples'].append(case)
        
        # Analisa padrões
        for grau, data in patterns.items():
            if 'numbers' in data and data['numbers']:
                print(f"\n📋 PADRÃO {grau}:")
                print(f"  Quantidade analisada: {len(data['numbers'])}")
                
                # Mostra exemplos
                for i, numero in enumerate(data['numbers'][:5]):
                    print(f"  Exemplo {i+1}: {numero}")
                
                # Analisa estrutura
                if data['numbers']:
                    primeiro = data['numbers'][0]
                    print(f"  Tamanho típico: {len(primeiro)} caracteres")
                    print(f"  Contém letras: {'Sim' if any(c.isalpha() for c in primeiro) else 'Não'}")
                    
                    # Verifica padrões específicos
                    if grau == 'TST':
                        rr_count = sum(1 for n in data['numbers'] if 'RR' in n)
                        airr_count = sum(1 for n in data['numbers'] if 'AIRR' in n)
                        print(f"  Com 'RR': {rr_count}")
                        print(f"  Com 'AIRR': {airr_count}")
    
    def test_matching_algorithms(self, cases):
        """Testa diferentes algoritmos de matching."""
        print("\n🧪 TESTANDO ALGORITMOS DE MATCHING")
        print("=" * 50)
        
        # Organiza casos por grau
        by_grau = defaultdict(list)
        for case in cases:
            by_grau[case['grau']].append(case)
        
        print(f"G1: {len(by_grau['G1']):,} casos")
        print(f"G2: {len(by_grau['G2']):,} casos") 
        print(f"TST: {len(by_grau['SUP']):,} casos")
        
        # Testa diferentes algoritmos
        algorithms = [
            ('current', self.extract_case_core_current),
            ('full_digits', self.extract_full_digits),
            ('middle_section', self.extract_middle_section),
            ('year_sequential', self.extract_year_sequential),
            ('smart_core', self.extract_smart_core)
        ]
        
        results = {}
        
        for algo_name, algo_func in algorithms:
            print(f"\n🔬 Testando algoritmo: {algo_name}")
            
            # Aplica algoritmo em amostra pequena
            g1_sample = by_grau['G1'][:500]
            g2_sample = by_grau['G2'][:500]
            tst_sample = by_grau['SUP'][:500]
            
            # Cria índices
            g1_cores = {}
            g2_cores = {}
            tst_cores = {}
            
            for case in g1_sample:
                core = algo_func(case['numero_processo'])
                if core:
                    if core not in g1_cores:
                        g1_cores[core] = []
                    g1_cores[core].append(case)
            
            for case in g2_sample:
                core = algo_func(case['numero_processo'])
                if core:
                    if core not in g2_cores:
                        g2_cores[core] = []
                    g2_cores[core].append(case)
            
            for case in tst_sample:
                core = algo_func(case['numero_processo'])
                if core:
                    if core not in tst_cores:
                        tst_cores[core] = []
                    tst_cores[core].append(case)
            
            # Calcula matches
            g1_g2_matches = len(set(g1_cores.keys()) & set(g2_cores.keys()))
            g1_tst_matches = len(set(g1_cores.keys()) & set(tst_cores.keys()))
            g2_tst_matches = len(set(g2_cores.keys()) & set(tst_cores.keys()))
            g1_g2_tst_matches = len(set(g1_cores.keys()) & set(g2_cores.keys()) & set(tst_cores.keys()))
            
            results[algo_name] = {
                'g1_g2': g1_g2_matches,
                'g1_tst': g1_tst_matches,
                'g2_tst': g2_tst_matches,
                'g1_g2_tst': g1_g2_tst_matches,
                'total_g1': len(g1_cores),
                'total_g2': len(g2_cores),
                'total_tst': len(tst_cores)
            }
            
            print(f"  G1↔G2 matches: {g1_g2_matches}")
            print(f"  G1↔TST matches: {g1_tst_matches}")
            print(f"  G2↔TST matches: {g2_tst_matches}")
            print(f"  G1↔G2↔TST matches: {g1_g2_tst_matches}")
        
        return results
    
    def extract_case_core_current(self, numero_processo):
        """Algoritmo atual."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        if len(numbers_only) >= 20:
            return numbers_only[:7] + numbers_only[9:]
        return numbers_only
    
    def extract_full_digits(self, numero_processo):
        """Apenas todos os dígitos."""
        return ''.join(filter(str.isdigit, numero_processo))
    
    def extract_middle_section(self, numero_processo):
        """Seção do meio (sem ano e tribunal)."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        if len(numbers_only) >= 20:
            return numbers_only[7:15]  # Pega seção do meio
        return numbers_only
    
    def extract_year_sequential(self, numero_processo):
        """Ano + número sequencial."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        if len(numbers_only) >= 20:
            return numbers_only[9:13] + numbers_only[:7]  # Ano + sequencial
        return numbers_only
    
    def extract_smart_core(self, numero_processo):
        """Algoritmo inteligente baseado no padrão CNJ."""
        # Padrão CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
        # N=sequencial, D=dígito, A=ano, J=justiça, T=tribunal, O=origem
        
        # Remove tudo exceto dígitos
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        
        if len(numbers_only) >= 20:
            # Extrai: sequencial (7) + ano (4) + justiça (1)
            sequencial = numbers_only[:7]
            ano = numbers_only[9:13]
            justica = numbers_only[13:14]
            
            return sequencial + ano + justica
        
        return numbers_only
    
    def investigate_specific_cases(self, cases):
        """Investiga casos específicos para entender o problema."""
        print("\n🎯 INVESTIGAÇÃO DE CASOS ESPECÍFICOS")
        print("=" * 50)
        
        # Pega alguns casos G1 e procura seus possíveis G2/TST
        g1_cases = [c for c in cases if c['grau'] == 'G1'][:10]
        all_g2_cases = [c for c in cases if c['grau'] == 'G2']
        all_tst_cases = [c for c in cases if c['grau'] == 'SUP']
        
        for i, g1_case in enumerate(g1_cases):
            print(f"\n🔍 Caso {i+1} - Processo G1:")
            print(f"  Número: {g1_case['numero_processo']}")
            print(f"  Tribunal: {g1_case['tribunal']}")
            print(f"  Core atual: {self.extract_case_core_current(g1_case['numero_processo'])}")
            
            g1_numero = g1_case['numero_processo']
            g1_tribunal = g1_case['tribunal']
            g1_ano = g1_numero[9:13] if len(g1_numero) > 13 else ''
            
            # Busca G2 relacionados
            possible_g2 = []
            for g2_case in all_g2_cases:
                g2_numero = g2_case['numero_processo']
                g2_tribunal = g2_case['tribunal']
                g2_ano = g2_numero[9:13] if len(g2_numero) > 13 else ''
                
                # Critérios de matching
                same_tribunal = g1_tribunal == g2_tribunal
                same_year = g1_ano == g2_ano and g1_ano != ''
                
                if same_tribunal and same_year:
                    # Verifica similaridade dos números
                    g1_digits = ''.join(filter(str.isdigit, g1_numero))
                    g2_digits = ''.join(filter(str.isdigit, g2_numero))
                    
                    # Diferentes critérios de similaridade
                    core_match = self.extract_case_core_current(g1_numero) == self.extract_case_core_current(g2_numero)
                    smart_match = self.extract_smart_core(g1_numero) == self.extract_smart_core(g2_numero)
                    
                    if core_match or smart_match:
                        possible_g2.append({
                            'case': g2_case,
                            'core_match': core_match,
                            'smart_match': smart_match
                        })
            
            # Busca TST relacionados
            possible_tst = []
            for tst_case in all_tst_cases[:100]:  # Limita TST por performance
                tst_numero = tst_case['numero_processo']
                
                # Verifica se TST pode estar relacionado ao G1
                core_match = self.extract_case_core_current(g1_numero) == self.extract_case_core_current(tst_numero)
                smart_match = self.extract_smart_core(g1_numero) == self.extract_smart_core(tst_numero)
                
                if core_match or smart_match:
                    possible_tst.append({
                        'case': tst_case,
                        'core_match': core_match,
                        'smart_match': smart_match
                    })
            
            print(f"  Possíveis G2: {len(possible_g2)}")
            for j, g2_info in enumerate(possible_g2[:3]):
                g2_case = g2_info['case']
                print(f"    G2.{j+1}: {g2_case['numero_processo']} ({g2_case['tribunal']})")
                print(f"           Core: {g2_info['core_match']}, Smart: {g2_info['smart_match']}")
            
            print(f"  Possíveis TST: {len(possible_tst)}")
            for j, tst_info in enumerate(possible_tst[:3]):
                tst_case = tst_info['case']
                print(f"    TST.{j+1}: {tst_case['numero_processo']}")
                print(f"            Core: {tst_info['core_match']}, Smart: {tst_info['smart_match']}")
    
    def analyze_tribunal_patterns(self, cases):
        """Analisa padrões específicos por tribunal."""
        print("\n🏛️ ANÁLISE DE PADRÕES POR TRIBUNAL")
        print("=" * 50)
        
        by_tribunal_grau = defaultdict(lambda: defaultdict(list))
        
        for case in cases:
            tribunal = case['tribunal']
            grau = case['grau']
            by_tribunal_grau[tribunal][grau].append(case)
        
        # Foca nos tribunais com mais casos
        sorted_tribunals = sorted(by_tribunal_grau.items(), 
                                key=lambda x: sum(len(grau_cases) for grau_cases in x[1].values()), 
                                reverse=True)
        
        for tribunal, graus in sorted_tribunals[:5]:
            total_cases = sum(len(grau_cases) for grau_cases in graus.values())
            print(f"\n🏛️ {tribunal} (Total: {total_cases:,})")
            
            for grau, grau_cases in graus.items():
                print(f"  {grau}: {len(grau_cases):,} casos")
                
                if len(grau_cases) > 0:
                    exemplo = grau_cases[0]['numero_processo']
                    print(f"    Exemplo: {exemplo}")
    
    def generate_investigation_report(self, algo_results):
        """Gera relatório da investigação."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = f"""# Relatório de Investigação - Matching de Processos

**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Objetivo
Investigar por que os dados G2 (TRT como tribunal recursal) não estão sendo conectados às cadeias processuais G1→G2→TST.

## 🔍 Resultados dos Algoritmos de Matching

| Algoritmo | G1↔G2 | G1↔TST | G2↔TST | G1↔G2↔TST | Eficiência |
|-----------|-------|--------|--------|-----------|------------|
"""
        
        for algo_name, results in algo_results.items():
            total_possible = min(results['total_g1'], results['total_g2'], results['total_tst'])
            efficiency = (results['g1_g2_tst'] / total_possible * 100) if total_possible > 0 else 0
            
            report += f"| {algo_name} | {results['g1_g2']} | {results['g1_tst']} | {results['g2_tst']} | {results['g1_g2_tst']} | {efficiency:.1f}% |\n"
        
        # Encontra melhor algoritmo
        best_algo = max(algo_results.items(), key=lambda x: x[1]['g1_g2_tst'])
        
        # Calcula melhoria com segurança
        current_g1_g2_tst = algo_results['current']['g1_g2_tst']
        best_g1_g2_tst = best_algo[1]['g1_g2_tst']
        
        if current_g1_g2_tst > 0:
            improvement_percent = ((best_g1_g2_tst / current_g1_g2_tst) - 1) * 100
            improvement_text = f"- **Melhoria**: {improvement_percent:.1f}% mais matches"
        else:
            if best_g1_g2_tst > 0:
                improvement_text = f"- **Melhoria**: {best_g1_g2_tst} matches vs 0 (infinita)"
            else:
                improvement_text = "- **Melhoria**: Nenhuma"
        
        report += f"""

## 📊 Análise dos Resultados

### Algoritmo Atual (current)
- **G1↔G2 matches**: {algo_results['current']['g1_g2']}
- **G1↔TST matches**: {algo_results['current']['g1_tst']}
- **G1↔G2↔TST matches**: {algo_results['current']['g1_g2_tst']}

### Melhor Algoritmo ({best_algo[0]})
- **G1↔G2↔TST matches**: {best_algo[1]['g1_g2_tst']}
{improvement_text}

## 🚨 Problemas Identificados

1. **Algoritmo de extração inadequado**: O método atual pode não estar capturando corretamente o núcleo comum dos processos
2. **Fragmentação real dos dados**: Possivelmente os dados G2 não estão completos no dataset
3. **Diferenças na numeração**: G2 pode usar numeração diferente de G1 no mesmo tribunal

## 💡 Recomendações

1. **Implementar algoritmo '{best_algo[0]}'**: Mostrou {best_algo[1]['g1_g2_tst']} matches vs {algo_results['current']['g1_g2_tst']} do atual
2. **Investigar missing data**: Verificar se dados G2 estão realmente ausentes
3. **Análise manual**: Validar matches encontrados manualmente

## 🔧 Próximos Passos

1. Aplicar melhor algoritmo na análise completa
2. Investigar casos onde matching falha
3. Validar resultados com especialista jurídico
"""
        
        # Salva relatório
        report_path = f"{self.output_path}/investigation_report_{timestamp}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Relatório salvo: {report_path}")
        return report_path
    
    def run_investigation(self, csv_file):
        """Executa investigação completa."""
        print("🔍 INVESTIGAÇÃO PROFUNDA DO MATCHING")
        print("=" * 60)
        
        # Carrega dados
        cases = self.load_data(csv_file)
        
        # Analisa padrões nos números
        self.analyze_number_patterns(cases)
        
        # Testa algoritmos
        algo_results = self.test_matching_algorithms(cases)
        
        # Investiga casos específicos
        self.investigate_specific_cases(cases)
        
        # Analisa padrões por tribunal
        self.analyze_tribunal_patterns(cases)
        
        # Gera relatório
        report_path = self.generate_investigation_report(algo_results)
        
        # Resumo final
        print(f"\n📊 RESUMO DA INVESTIGAÇÃO:")
        print("=" * 40)
        
        best_algo = max(algo_results.items(), key=lambda x: x[1]['g1_g2_tst'])
        current_matches = algo_results['current']['g1_g2_tst']
        best_matches = best_algo[1]['g1_g2_tst']
        
        print(f"Algoritmo atual: {current_matches} matches G1↔G2↔TST")
        print(f"Melhor algoritmo ({best_algo[0]}): {best_matches} matches")
        
        if best_matches > current_matches:
            if current_matches > 0:
                improvement = ((best_matches / current_matches) - 1) * 100
                print(f"Melhoria: {improvement:.1f}%")
            else:
                print(f"Melhoria: {best_matches} matches vs 0 (infinita)")
        elif best_matches == current_matches:
            print("Nenhuma melhoria encontrada")
        
        return algo_results, best_algo

def main():
    """Função principal."""
    investigator = DeepMatchingInvestigator()
    investigator.run_investigation("consolidated_all_data.csv")

if __name__ == "__main__":
    main()