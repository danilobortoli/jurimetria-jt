#!/usr/bin/env python3
"""
Maximizador de Conexões
Testa múltiplos algoritmos avançados para encontrar o maior número de conexões possível.
"""

import csv
from collections import defaultdict
import re
from datetime import datetime

class ConnectionMaximizer:
    """Maximiza conexões entre instâncias processuais."""
    
    def __init__(self):
        self.output_path = "max_connections_results"
        import os
        os.makedirs(self.output_path, exist_ok=True)
    
    def load_data(self, csv_file):
        """Carrega dados com foco em assédio moral."""
        print("📂 Carregando dados para maximização...")
        
        all_cases = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['eh_assedio_moral'] == 'True':
                    all_cases.append(row)
        
        print(f"✅ Carregados {len(all_cases):,} casos de assédio moral")
        return all_cases
    
    def algorithm_current(self, numero_processo):
        """Algoritmo atual."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        if len(numbers_only) >= 20:
            return numbers_only[:7] + numbers_only[9:]
        return numbers_only
    
    def algorithm_middle_section(self, numero_processo):
        """Seção do meio (atual melhor)."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        if len(numbers_only) >= 20:
            return numbers_only[7:15]
        return numbers_only
    
    def algorithm_full_digits(self, numero_processo):
        """Todos os dígitos."""
        return ''.join(filter(str.isdigit, numero_processo))
    
    def algorithm_smart_core(self, numero_processo):
        """Core inteligente baseado no padrão CNJ."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        if len(numbers_only) >= 20:
            sequencial = numbers_only[:7]
            ano = numbers_only[9:13]
            justica = numbers_only[13:14]
            return sequencial + ano + justica
        return numbers_only
    
    def algorithm_year_sequential(self, numero_processo):
        """Ano + número sequencial."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        if len(numbers_only) >= 20:
            return numbers_only[9:13] + numbers_only[:7]
        return numbers_only
    
    def algorithm_flexible_core(self, numero_processo):
        """Core flexível - múltiplas tentativas."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        cores = []
        
        if len(numbers_only) >= 20:
            # Tenta diferentes combinações
            cores.append(numbers_only[:7] + numbers_only[9:])  # Original
            cores.append(numbers_only[7:15])  # Middle section
            cores.append(numbers_only[:7] + numbers_only[13:17])  # Seq + Justice+Tribunal
            cores.append(numbers_only[:10])  # Primeiros 10
            cores.append(numbers_only[5:15])  # Do meio
            cores.append(numbers_only[9:13] + numbers_only[:7])  # Ano + Sequencial
        else:
            cores.append(numbers_only)
        
        return cores
    
    def algorithm_pattern_based(self, numero_processo):
        """Baseado em padrões específicos por tipo de número."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        
        # Detecta padrão
        if len(numbers_only) == 20:
            # Padrão CNJ completo: NNNNNNN-DD.AAAA.J.TR.OOOO
            sequencial = numbers_only[:7]
            ano = numbers_only[9:13]
            
            # Múltiplas estratégias
            return [
                sequencial + ano,  # Seq + Ano
                numbers_only[7:15],  # Meio
                sequencial + numbers_only[13:15],  # Seq + Tribunal
                numbers_only[:10],  # Primeiros 10
            ]
        elif len(numbers_only) > 20:
            # Número estendido - tenta diferentes seções
            return [
                numbers_only[:15],
                numbers_only[5:15],
                numbers_only[7:17],
                numbers_only[-15:],
            ]
        else:
            return [numbers_only]
    
    def algorithm_fuzzy_match(self, numero_processo):
        """Matching fuzzy - tolerante a pequenas diferenças."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        
        if len(numbers_only) >= 20:
            # Core principal
            core = numbers_only[7:15]
            
            # Variações para fuzzy matching
            variations = [core]
            
            # Remove últimos dígitos (pode ter diferença em tribunal/origem)
            if len(core) > 6:
                variations.append(core[:-1])
                variations.append(core[:-2])
            
            # Remove primeiros dígitos  
            if len(core) > 6:
                variations.append(core[1:])
                variations.append(core[2:])
            
            return variations
        
        return [numbers_only]
    
    def algorithm_context_aware(self, numero_processo, tribunal, grau):
        """Algoritmo consciente do contexto (tribunal e grau)."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        
        if len(numbers_only) >= 20:
            base_core = numbers_only[7:15]
            
            # Estratégias específicas por tribunal
            if 'TRT' in tribunal:
                trt_num = tribunal.replace('TRT', '')
                if trt_num.isdigit():
                    # Para TRTs, inclui número do tribunal na estratégia
                    cores = [
                        base_core,
                        base_core + trt_num,
                        numbers_only[:7] + trt_num,
                    ]
                else:
                    cores = [base_core]
            elif tribunal == 'TST':
                # Para TST, estratégia mais flexível
                cores = [
                    base_core,
                    numbers_only[:10],
                    numbers_only[5:13],
                ]
            else:
                cores = [base_core]
            
            return cores
        
        return [numbers_only]
    
    def test_advanced_algorithms(self, cases):
        """Testa algoritmos avançados de matching."""
        print("\n🧪 TESTANDO ALGORITMOS AVANÇADOS DE MATCHING")
        print("=" * 60)
        
        # Organiza casos por grau
        by_grau = defaultdict(list)
        for case in cases:
            by_grau[case['grau']].append(case)
        
        print(f"G1: {len(by_grau['G1']):,} casos")
        print(f"G2: {len(by_grau['G2']):,} casos") 
        print(f"TST: {len(by_grau['SUP']):,} casos")
        
        # Lista de algoritmos para testar
        algorithms = [
            ('current', self.algorithm_current),
            ('middle_section', self.algorithm_middle_section),
            ('full_digits', self.algorithm_full_digits),
            ('smart_core', self.algorithm_smart_core),
            ('year_sequential', self.algorithm_year_sequential),
        ]
        
        # Algoritmos com múltiplos cores
        multi_algorithms = [
            ('flexible_core', self.algorithm_flexible_core),
            ('pattern_based', self.algorithm_pattern_based),
            ('fuzzy_match', self.algorithm_fuzzy_match),
        ]
        
        results = {}
        
        # Testa algoritmos simples
        for algo_name, algo_func in algorithms:
            print(f"\n🔬 Testando algoritmo: {algo_name}")
            result = self.test_single_algorithm(algo_func, by_grau, algo_name)
            results[algo_name] = result
            self.print_algorithm_results(algo_name, result)
        
        # Testa algoritmos múltiplos
        for algo_name, algo_func in multi_algorithms:
            print(f"\n🔬 Testando algoritmo: {algo_name}")
            result = self.test_multi_algorithm(algo_func, by_grau, algo_name)
            results[algo_name] = result
            self.print_algorithm_results(algo_name, result)
        
        # Testa algoritmo contextual
        print(f"\n🔬 Testando algoritmo: context_aware")
        result = self.test_context_algorithm(by_grau)
        results['context_aware'] = result
        self.print_algorithm_results('context_aware', result)
        
        return results
    
    def test_single_algorithm(self, algo_func, by_grau, algo_name):
        """Testa um algoritmo simples."""
        # Usa sample para performance
        g1_sample = by_grau['G1'][:1000]
        g2_sample = by_grau['G2'][:1000]
        tst_sample = by_grau['SUP'][:1000]
        
        # Cria índices
        g1_cores = defaultdict(list)
        g2_cores = defaultdict(list)
        tst_cores = defaultdict(list)
        
        for case in g1_sample:
            core = algo_func(case['numero_processo'])
            if core:
                g1_cores[core].append(case)
        
        for case in g2_sample:
            core = algo_func(case['numero_processo'])
            if core:
                g2_cores[core].append(case)
        
        for case in tst_sample:
            core = algo_func(case['numero_processo'])
            if core:
                tst_cores[core].append(case)
        
        # Calcula matches
        g1_g2_matches = len(set(g1_cores.keys()) & set(g2_cores.keys()))
        g1_tst_matches = len(set(g1_cores.keys()) & set(tst_cores.keys()))
        g2_tst_matches = len(set(g2_cores.keys()) & set(tst_cores.keys()))
        g1_g2_tst_matches = len(set(g1_cores.keys()) & set(g2_cores.keys()) & set(tst_cores.keys()))
        
        return {
            'g1_g2': g1_g2_matches,
            'g1_tst': g1_tst_matches,
            'g2_tst': g2_tst_matches,
            'g1_g2_tst': g1_g2_tst_matches,
            'total_g1': len(g1_cores),
            'total_g2': len(g2_cores),
            'total_tst': len(tst_cores)
        }
    
    def test_multi_algorithm(self, algo_func, by_grau, algo_name):
        """Testa algoritmo que retorna múltiplos cores."""
        g1_sample = by_grau['G1'][:1000]
        g2_sample = by_grau['G2'][:1000]
        tst_sample = by_grau['SUP'][:1000]
        
        g1_cores = defaultdict(list)
        g2_cores = defaultdict(list)
        tst_cores = defaultdict(list)
        
        for case in g1_sample:
            cores = algo_func(case['numero_processo'])
            if isinstance(cores, list):
                for core in cores:
                    if core:
                        g1_cores[core].append(case)
            else:
                if cores:
                    g1_cores[cores].append(case)
        
        for case in g2_sample:
            cores = algo_func(case['numero_processo'])
            if isinstance(cores, list):
                for core in cores:
                    if core:
                        g2_cores[core].append(case)
            else:
                if cores:
                    g2_cores[cores].append(case)
        
        for case in tst_sample:
            cores = algo_func(case['numero_processo'])
            if isinstance(cores, list):
                for core in cores:
                    if core:
                        tst_cores[core].append(case)
            else:
                if cores:
                    tst_cores[cores].append(case)
        
        # Calcula matches
        g1_g2_matches = len(set(g1_cores.keys()) & set(g2_cores.keys()))
        g1_tst_matches = len(set(g1_cores.keys()) & set(tst_cores.keys()))
        g2_tst_matches = len(set(g2_cores.keys()) & set(tst_cores.keys()))
        g1_g2_tst_matches = len(set(g1_cores.keys()) & set(g2_cores.keys()) & set(tst_cores.keys()))
        
        return {
            'g1_g2': g1_g2_matches,
            'g1_tst': g1_tst_matches,
            'g2_tst': g2_tst_matches,
            'g1_g2_tst': g1_g2_tst_matches,
            'total_g1': len(set(g1_cores.keys())),
            'total_g2': len(set(g2_cores.keys())),
            'total_tst': len(set(tst_cores.keys()))
        }
    
    def test_context_algorithm(self, by_grau):
        """Testa algoritmo contextual."""
        g1_sample = by_grau['G1'][:1000]
        g2_sample = by_grau['G2'][:1000]
        tst_sample = by_grau['SUP'][:1000]
        
        g1_cores = defaultdict(list)
        g2_cores = defaultdict(list)
        tst_cores = defaultdict(list)
        
        for case in g1_sample:
            cores = self.algorithm_context_aware(
                case['numero_processo'], 
                case['tribunal'], 
                case['grau']
            )
            for core in cores:
                if core:
                    g1_cores[core].append(case)
        
        for case in g2_sample:
            cores = self.algorithm_context_aware(
                case['numero_processo'], 
                case['tribunal'], 
                case['grau']
            )
            for core in cores:
                if core:
                    g2_cores[core].append(case)
        
        for case in tst_sample:
            cores = self.algorithm_context_aware(
                case['numero_processo'], 
                case['tribunal'], 
                case['grau']
            )
            for core in cores:
                if core:
                    tst_cores[core].append(case)
        
        # Calcula matches
        g1_g2_matches = len(set(g1_cores.keys()) & set(g2_cores.keys()))
        g1_tst_matches = len(set(g1_cores.keys()) & set(tst_cores.keys()))
        g2_tst_matches = len(set(g2_cores.keys()) & set(tst_cores.keys()))
        g1_g2_tst_matches = len(set(g1_cores.keys()) & set(g2_cores.keys()) & set(tst_cores.keys()))
        
        return {
            'g1_g2': g1_g2_matches,
            'g1_tst': g1_tst_matches,
            'g2_tst': g2_tst_matches,
            'g1_g2_tst': g1_g2_tst_matches,
            'total_g1': len(set(g1_cores.keys())),
            'total_g2': len(set(g2_cores.keys())),
            'total_tst': len(set(tst_cores.keys()))
        }
    
    def print_algorithm_results(self, algo_name, result):
        """Imprime resultados do algoritmo."""
        print(f"  G1↔G2 matches: {result['g1_g2']}")
        print(f"  G1↔TST matches: {result['g1_tst']}")
        print(f"  G2↔TST matches: {result['g2_tst']}")
        print(f"  G1↔G2↔TST matches: {result['g1_g2_tst']}")
        
        # Calcula eficiência
        total_possible = min(result['total_g1'], result['total_g2'], result['total_tst'])
        if total_possible > 0:
            efficiency = (result['g1_g2_tst'] / total_possible) * 100
            print(f"  Eficiência: {efficiency:.1f}%")
    
    def generate_maximization_report(self, algo_results):
        """Gera relatório de maximização."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Encontra os melhores algoritmos
        best_g1_g2_tst = max(algo_results.items(), key=lambda x: x[1]['g1_g2_tst'])
        best_g1_g2 = max(algo_results.items(), key=lambda x: x[1]['g1_g2'])
        best_g2_tst = max(algo_results.items(), key=lambda x: x[1]['g2_tst'])
        
        report = f"""# Relatório de Maximização de Conexões

**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Objetivo
Encontrar o algoritmo que maximiza as conexões entre G1↔G2↔TST.

## 📊 Resultados dos Algoritmos

| Algoritmo | G1↔G2 | G1↔TST | G2↔TST | G1↔G2↔TST | Eficiência |
|-----------|-------|--------|--------|-----------|------------|
"""
        
        for algo_name, results in algo_results.items():
            total_possible = min(results['total_g1'], results['total_g2'], results['total_tst'])
            efficiency = (results['g1_g2_tst'] / total_possible * 100) if total_possible > 0 else 0
            
            report += f"| {algo_name} | {results['g1_g2']} | {results['g1_tst']} | {results['g2_tst']} | {results['g1_g2_tst']} | {efficiency:.1f}% |\n"
        
        report += f"""

## 🏆 Campeões por Categoria

### Máximas Conexões G1↔G2↔TST
**{best_g1_g2_tst[0]}**: {best_g1_g2_tst[1]['g1_g2_tst']} conexões

### Máximas Conexões G1↔G2  
**{best_g1_g2[0]}**: {best_g1_g2[1]['g1_g2']} conexões

### Máximas Conexões G2↔TST
**{best_g2_tst[0]}**: {best_g2_tst[1]['g2_tst']} conexões

## 💡 Recomendação Final

O algoritmo **{best_g1_g2_tst[0]}** deve ser implementado para maximizar as conexões G1↔G2↔TST.

## 🔧 Próximos Passos

1. Implementar algoritmo {best_g1_g2_tst[0]} em consolidate_to_csv.py
2. Re-executar análise completa
3. Validar resultados finais
"""
        
        # Salva relatório
        report_path = f"{self.output_path}/maximization_report_{timestamp}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Relatório salvo: {report_path}")
        return report_path, best_g1_g2_tst
    
    def run_maximization(self, csv_file):
        """Executa maximização completa."""
        print("🚀 MAXIMIZAÇÃO DE CONEXÕES")
        print("=" * 60)
        
        # Carrega dados
        cases = self.load_data(csv_file)
        
        # Testa algoritmos
        algo_results = self.test_advanced_algorithms(cases)
        
        # Gera relatório
        report_path, best_algo = self.generate_maximization_report(algo_results)
        
        # Resumo final
        print(f"\n🏆 CAMPEÃO: {best_algo[0]}")
        print(f"G1↔G2↔TST máximas: {best_algo[1]['g1_g2_tst']}")
        print(f"G1↔G2 máximas: {best_algo[1]['g1_g2']}")
        print(f"G2↔TST máximas: {best_algo[1]['g2_tst']}")
        
        return algo_results, best_algo

def main():
    """Função principal."""
    maximizer = ConnectionMaximizer()
    maximizer.run_maximization("consolidated_data_20250629_175829.csv")

if __name__ == "__main__":
    main()