#!/usr/bin/env python3
"""
Investigação de Cruzamentos G1↔G2 e Cobertura Temporal TST
Verifica se existem casos que aparecem tanto em G1 quanto G2 e analisa cobertura temporal.
"""

import csv
from collections import defaultdict
import json
from datetime import datetime

class G1G2CrossingInvestigator:
    """Investiga cruzamentos entre G1 e G2 e cobertura temporal."""
    
    def __init__(self):
        self.output_path = "g1_g2_crossing_results"
        import os
        os.makedirs(self.output_path, exist_ok=True)
    
    def load_data(self, csv_file):
        """Carrega dados de assédio moral."""
        print("📂 Carregando dados para investigação de cruzamentos G1↔G2...")
        
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
    
    def investigate_g1_g2_crossings(self, cases):
        """Investiga cruzamentos entre G1 e G2."""
        print("\n🔍 INVESTIGAÇÃO DE CRUZAMENTOS G1↔G2")
        print("=" * 50)
        
        # Organiza casos por core e grau
        g1_cores = set()
        g2_cores = set()
        all_cores_by_grau = defaultdict(list)
        
        for case in cases:
            core = self.extract_exact_core(case['numero_processo'])
            grau = case['grau']
            
            all_cores_by_grau[grau].append(core)
            
            if grau == 'G1':
                g1_cores.add(core)
            elif grau == 'G2':
                g2_cores.add(core)
        
        # Encontra interseções
        g1_g2_intersection = g1_cores & g2_cores
        
        print(f"Cores únicos em G1: {len(g1_cores):,}")
        print(f"Cores únicos em G2: {len(g2_cores):,}")
        print(f"Cores que aparecem em AMBOS G1 e G2: {len(g1_g2_intersection):,}")
        
        if g1_g2_intersection:
            print(f"\n🎯 CASOS QUE APARECEM EM G1 E G2:")
            print("=" * 40)
            
            # Analisa os casos de interseção
            intersection_details = []
            for core in list(g1_g2_intersection)[:20]:  # Primeiros 20
                g1_cases = [c for c in cases if self.extract_exact_core(c['numero_processo']) == core and c['grau'] == 'G1']
                g2_cases = [c for c in cases if self.extract_exact_core(c['numero_processo']) == core and c['grau'] == 'G2']
                
                print(f"\nCore: {core}")
                print(f"  G1 ({len(g1_cases)}): ", end="")
                for case in g1_cases:
                    print(f"{case['numero_processo']} ({case['tribunal']}) ", end="")
                print()
                
                print(f"  G2 ({len(g2_cases)}): ", end="")
                for case in g2_cases:
                    print(f"{case['numero_processo']} ({case['tribunal']}) ", end="")
                print()
                
                # Verifica se há também TST
                tst_cases = [c for c in cases if self.extract_exact_core(c['numero_processo']) == core and c['grau'] == 'SUP']
                if tst_cases:
                    print(f"  TST ({len(tst_cases)}): ", end="")
                    for case in tst_cases:
                        print(f"{case['numero_processo']} ({case['tribunal']}) ", end="")
                    print()
                    print("  🎉 CADEIA COMPLETA G1→G2→TST ENCONTRADA!")
                
                intersection_details.append({
                    'core': core,
                    'g1_count': len(g1_cases),
                    'g2_count': len(g2_cases),
                    'tst_count': len(tst_cases),
                    'has_complete_chain': len(tst_cases) > 0
                })
            
            # Conta cadeias completas
            complete_chains = sum(1 for detail in intersection_details if detail['has_complete_chain'])
            print(f"\n🏆 CADEIAS COMPLETAS G1→G2→TST: {complete_chains}")
            
            return {
                'g1_cores': len(g1_cores),
                'g2_cores': len(g2_cores),
                'intersection': len(g1_g2_intersection),
                'intersection_details': intersection_details,
                'complete_chains': complete_chains
            }
        else:
            print("❌ Nenhum cruzamento encontrado entre G1 e G2")
            return {
                'g1_cores': len(g1_cores),
                'g2_cores': len(g2_cores),
                'intersection': 0,
                'intersection_details': [],
                'complete_chains': 0
            }
    
    def analyze_temporal_coverage(self, cases):
        """Analisa cobertura temporal dos dados."""
        print(f"\n📅 ANÁLISE DE COBERTURA TEMPORAL")
        print("=" * 50)
        
        # Extrai anos dos casos
        cases_by_year_grau = defaultdict(lambda: defaultdict(int))
        cases_by_year_tribunal = defaultdict(lambda: defaultdict(int))
        
        for case in cases:
            # Extrai ano do número do processo
            numero = case['numero_processo']
            try:
                if len(numero) >= 15:
                    year_str = numero[9:13]
                    if year_str.isdigit():
                        year = int(year_str)
                        if 2000 <= year <= 2030:
                            grau = case['grau']
                            tribunal = case['tribunal']
                            
                            cases_by_year_grau[year][grau] += 1
                            cases_by_year_tribunal[year][tribunal] += 1
            except:
                continue
        
        # Analisa cobertura por ano e grau
        print("📊 CASOS POR ANO E GRAU:")
        print("=" * 30)
        
        all_years = sorted(cases_by_year_grau.keys())
        print(f"Período coberto: {min(all_years)} - {max(all_years)}")
        print()
        
        print("| Ano | G1 | G2 | TST | Total |")
        print("|-----|----|----|-----|-------|")
        
        year_totals = {}
        for year in all_years:
            g1_count = cases_by_year_grau[year]['G1']
            g2_count = cases_by_year_grau[year]['G2']
            tst_count = cases_by_year_grau[year]['SUP']
            total = g1_count + g2_count + tst_count
            year_totals[year] = total
            
            print(f"| {year} | {g1_count:,} | {g2_count:,} | {tst_count:,} | {total:,} |")
        
        # Verifica lacunas na cobertura
        print(f"\n🔍 ANÁLISE DE LACUNAS:")
        print("=" * 30)
        
        expected_years = list(range(2014, 2026))  # 2014-2025
        missing_years = [year for year in expected_years if year not in all_years]
        low_coverage_years = [year for year in all_years if year_totals[year] < 100]
        
        if missing_years:
            print(f"Anos completamente ausentes: {missing_years}")
        else:
            print("✅ Todos os anos de 2014-2025 têm dados")
        
        if low_coverage_years:
            print(f"Anos com baixa cobertura (<100 casos): {low_coverage_years}")
        
        # Analisa especificamente TST por ano
        print(f"\n🏛️ COBERTURA TST POR ANO:")
        print("=" * 30)
        
        tst_by_year = {}
        for year in all_years:
            tst_count = cases_by_year_grau[year]['SUP']
            tst_by_year[year] = tst_count
            if tst_count > 0:
                print(f"{year}: {tst_count:,} casos TST")
        
        tst_years = [year for year in all_years if cases_by_year_grau[year]['SUP'] > 0]
        tst_missing = [year for year in expected_years if year not in tst_years]
        
        print(f"\nTST - Período coberto: {min(tst_years)} - {max(tst_years)}")
        if tst_missing:
            print(f"TST - Anos sem dados: {tst_missing}")
        else:
            print("✅ TST tem dados para todos os anos esperados")
        
        return {
            'all_years': all_years,
            'year_totals': year_totals,
            'missing_years': missing_years,
            'low_coverage_years': low_coverage_years,
            'tst_years': tst_years,
            'tst_missing': tst_missing,
            'tst_by_year': tst_by_year
        }
    
    def investigate_tribunal_distribution(self, cases):
        """Investiga distribuição por tribunal."""
        print(f"\n🏛️ DISTRIBUIÇÃO POR TRIBUNAL")
        print("=" * 40)
        
        tribunal_grau_count = defaultdict(lambda: defaultdict(int))
        
        for case in cases:
            tribunal = case['tribunal']
            grau = case['grau']
            tribunal_grau_count[tribunal][grau] += 1
        
        # Ordena tribunais por total de casos
        tribunal_totals = {}
        for tribunal, graus in tribunal_grau_count.items():
            tribunal_totals[tribunal] = sum(graus.values())
        
        sorted_tribunals = sorted(tribunal_totals.items(), key=lambda x: x[1], reverse=True)
        
        print("| Tribunal | G1 | G2 | TST | Total |")
        print("|----------|----|----|-----|-------|")
        
        for tribunal, total in sorted_tribunals[:15]:  # Top 15
            g1 = tribunal_grau_count[tribunal]['G1']
            g2 = tribunal_grau_count[tribunal]['G2']
            tst = tribunal_grau_count[tribunal]['SUP']
            print(f"| {tribunal} | {g1:,} | {g2:,} | {tst:,} | {total:,} |")
        
        return dict(tribunal_grau_count)
    
    def generate_investigation_report(self, crossing_results, temporal_results, tribunal_results):
        """Gera relatório da investigação."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = f"""# Investigação de Cruzamentos G1↔G2 e Cobertura Temporal

**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Objetivo
Verificar cruzamentos entre G1 e G2 e analisar cobertura temporal dos dados TST (2014-2025).

## 📊 Resultados - Cruzamentos G1↔G2

### Estatísticas Gerais
- **Cores únicos em G1**: {crossing_results['g1_cores']:,}
- **Cores únicos em G2**: {crossing_results['g2_cores']:,}
- **Cores em AMBOS G1 e G2**: {crossing_results['intersection']:,}
- **Cadeias completas G1→G2→TST**: {crossing_results['complete_chains']:,}

## 📅 Cobertura Temporal

### Período Total
- **Início**: {min(temporal_results['all_years'])}
- **Fim**: {max(temporal_results['all_years'])}
- **Anos com dados**: {len(temporal_results['all_years'])}

### Lacunas Identificadas
"""
        
        if temporal_results['missing_years']:
            report += f"- **Anos ausentes**: {temporal_results['missing_years']}\n"
        else:
            report += "- ✅ **Cobertura completa**: Todos os anos 2014-2025 presentes\n"
        
        if temporal_results['low_coverage_years']:
            report += f"- **Anos com baixa cobertura** (<100 casos): {temporal_results['low_coverage_years']}\n"
        
        report += f"""

### Cobertura TST Específica
- **TST - Período**: {min(temporal_results['tst_years'])} - {max(temporal_results['tst_years'])}
"""
        
        if temporal_results['tst_missing']:
            report += f"- **TST - Anos ausentes**: {temporal_results['tst_missing']}\n"
        else:
            report += "- ✅ **TST - Cobertura completa**: Dados para todos os anos esperados\n"
        
        report += f"""

## 🏛️ Distribuição por Tribunal

### Top 10 Tribunais
"""
        
        # Adiciona top tribunais
        tribunal_totals = {}
        for tribunal, graus in tribunal_results.items():
            tribunal_totals[tribunal] = sum(graus.values())
        
        sorted_tribunals = sorted(tribunal_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for tribunal, total in sorted_tribunals:
            g1 = tribunal_results[tribunal]['G1']
            g2 = tribunal_results[tribunal]['G2']
            tst = tribunal_results[tribunal]['SUP']
            report += f"- **{tribunal}**: {total:,} (G1: {g1:,}, G2: {g2:,}, TST: {tst:,})\n"
        
        report += f"""

## 🚨 Conclusões

1. **Cruzamentos G1↔G2**: {crossing_results['intersection']:,} casos aparecem em ambas as instâncias
2. **Cadeias completas**: {crossing_results['complete_chains']:,} cadeias G1→G2→TST verdadeiras
3. **Cobertura temporal**: {'Completa' if not temporal_results['missing_years'] else 'Incompleta'}
4. **TST cobertura**: {'Completa' if not temporal_results['tst_missing'] else 'Incompleta'}

## 💡 Recomendações

1. {'Focar nos ' + str(crossing_results['intersection']) + ' cruzamentos G1↔G2 para análise completa' if crossing_results['intersection'] > 0 else 'Aceitar que não há cruzamentos significativos G1↔G2'}
2. {'Investigar lacunas nos anos: ' + str(temporal_results['missing_years']) if temporal_results['missing_years'] else 'Dados temporais estão completos'}
3. Validar qualidade dos dados nos anos de baixa cobertura
"""
        
        # Salva relatório
        report_path = f"{self.output_path}/g1_g2_crossing_report_{timestamp}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Salva dados detalhados em JSON
        data_path = f"{self.output_path}/detailed_data_{timestamp}.json"
        detailed_data = {
            'crossing_results': crossing_results,
            'temporal_results': temporal_results,
            'tribunal_results': tribunal_results
        }
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(detailed_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Relatório salvo: {report_path}")
        print(f"📊 Dados detalhados: {data_path}")
        
        return report_path
    
    def run_investigation(self, csv_file):
        """Executa investigação completa."""
        print("🔍 INVESTIGAÇÃO DE CRUZAMENTOS G1↔G2 E COBERTURA TEMPORAL")
        print("=" * 70)
        
        # Carrega dados
        cases = self.load_data(csv_file)
        
        # Investiga cruzamentos G1↔G2
        crossing_results = self.investigate_g1_g2_crossings(cases)
        
        # Analisa cobertura temporal
        temporal_results = self.analyze_temporal_coverage(cases)
        
        # Investiga distribuição por tribunal
        tribunal_results = self.investigate_tribunal_distribution(cases)
        
        # Gera relatório
        report_path = self.generate_investigation_report(crossing_results, temporal_results, tribunal_results)
        
        print(f"\n📊 RESUMO FINAL:")
        print("=" * 30)
        print(f"Cruzamentos G1↔G2: {crossing_results['intersection']:,}")
        print(f"Cadeias G1→G2→TST: {crossing_results['complete_chains']:,}")
        print(f"Cobertura temporal: {min(temporal_results['all_years'])}-{max(temporal_results['all_years'])}")
        print(f"Anos TST: {len(temporal_results['tst_years'])}")
        
        return crossing_results, temporal_results

def main():
    """Função principal."""
    investigator = G1G2CrossingInvestigator()
    investigator.run_investigation("consolidated_all_data.csv")

if __name__ == "__main__":
    main()