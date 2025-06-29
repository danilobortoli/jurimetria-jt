#!/usr/bin/env python3
"""
ULTRA COMPREHENSIVE G1 SEARCH
Busca COMPLETA e EXAUSTIVA de dados G1 em TODOS os arquivos TRT
"""

import json
import csv
import glob
from collections import defaultdict
from datetime import datetime
import re

class UltraComprehensiveG1Search:
    """Busca ultra-abrangente de dados G1 em TRTs."""
    
    def __init__(self):
        self.output_path = "ultra_g1_search_results"
        import os
        os.makedirs(self.output_path, exist_ok=True)
        
        # Códigos G1 conhecidos
        self.g1_codes = {
            219: 'Procedência',
            220: 'Improcedência', 
            221: 'Procedência em Parte',
            11: 'Sentença',
            861: 'Julgamento Procedente',
            862: 'Julgamento Improcedente',
            863: 'Julgamento Parcialmente Procedente',
            51: 'Decisão',
            132: 'Sentença Condenatória',
            133: 'Sentença Absolutória',
            134: 'Sentença Parcialmente Procedente'
        }
        
        # Códigos G2 conhecidos
        self.g2_codes = {
            237: 'Provimento',
            238: 'Provimento em Parte',
            242: 'Desprovimento',
            236: 'Negação de Seguimento',
            123: 'Acórdão',
            11009: 'Julgamento',
            804: 'Recurso'
        }
        
        # Padrões textuais para buscar
        self.g1_text_patterns = [
            r'procedência',
            r'improcedência', 
            r'procedente',
            r'improcedente',
            r'parcialmente procedente',
            r'primeira instância',
            r'sentença',
            r'juiz.*trabalho',
            r'vara.*trabalho',
            r'julgar.*procedente',
            r'julgar.*improcedente'
        ]
        
        # Cache para otimização
        self.trt_data_cache = {}
        self.g1_findings = defaultdict(list)
        
    def load_all_trt_files(self):
        """Carrega TODOS os arquivos TRT."""
        print("🔍 BUSCA ULTRA-ABRANGENTE DE DADOS G1")
        print("=" * 60)
        print("📂 Carregando TODOS os arquivos TRT...")
        
        trt_pattern = '/Users/danilobortoli/Documents/Tese de doutorado da Andreia/Dados da segunda extração/raw/trt*.json'
        trt_files = glob.glob(trt_pattern)
        
        print(f"📁 Encontrados {len(trt_files)} arquivos TRT")
        print("🚀 Iniciando análise COMPLETA...")
        
        all_trt_data = []
        files_processed = 0
        total_cases = 0
        
        for i, file_path in enumerate(trt_files):
            try:
                print(f"  📄 Processando {i+1:3d}/{len(trt_files)}: {file_path.split('/')[-1]}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Adiciona metadados de origem
                    for case in data:
                        case['_source_file'] = file_path.split('/')[-1]
                        case['_trt_region'] = self.extract_trt_region(file_path)
                    
                    all_trt_data.extend(data)
                    total_cases += len(data)
                    files_processed += 1
                
                if i % 50 == 0 and i > 0:
                    print(f"    ✅ Progresso: {i}/{len(trt_files)} arquivos, {total_cases:,} casos")
                    
            except Exception as e:
                print(f"    ❌ Erro em {file_path}: {e}")
        
        print(f"✅ Carregamento completo:")
        print(f"   - Arquivos processados: {files_processed:,}")
        print(f"   - Total de casos: {total_cases:,}")
        print(f"   - Média por arquivo: {total_cases/files_processed:.0f}")
        
        return all_trt_data
    
    def extract_trt_region(self, file_path):
        """Extrai região do TRT do nome do arquivo."""
        match = re.search(r'trt(\d+)', file_path.lower())
        return f"TRT{match.group(1)}" if match else "UNKNOWN"
    
    def deep_search_g1_data(self, case):
        """Busca profunda por dados G1 em um caso."""
        numero = case.get('numeroProcesso', '')
        movimentos = case.get('movimentos', [])
        trt_region = case.get('_trt_region', '')
        
        findings = {
            'numero': numero,
            'trt_region': trt_region,
            'g1_by_code': [],
            'g1_by_text': [],
            'g1_by_field': [],
            'movement_analysis': [],
            'total_movements': len(movimentos),
            'case_type': case.get('classe', {}).get('nome', ''),
            'assuntos': case.get('assuntos', [])
        }
        
        # 1. Busca por códigos G1 conhecidos
        for mov in movimentos:
            codigo = mov.get('codigo')
            nome = mov.get('nome', '')
            complemento = mov.get('complementosTabelados', [])
            
            if codigo in self.g1_codes:
                findings['g1_by_code'].append({
                    'codigo': codigo,
                    'nome': nome,
                    'resultado': self.g1_codes[codigo],
                    'data': mov.get('dataHora', ''),
                    'complemento': complemento
                })
            
            # 2. Busca textual por padrões G1
            for pattern in self.g1_text_patterns:
                if re.search(pattern, nome.lower()):
                    findings['g1_by_text'].append({
                        'codigo': codigo,
                        'nome': nome,
                        'pattern_match': pattern,
                        'data': mov.get('dataHora', ''),
                        'complemento': complemento
                    })
            
            # 3. Análise detalhada de movimentos
            findings['movement_analysis'].append({
                'codigo': codigo,
                'nome': nome,
                'data': mov.get('dataHora', ''),
                'has_complemento': len(complemento) > 0,
                'complemento_count': len(complemento)
            })
        
        # 4. Busca em outros campos
        for field in ['observacao', 'motivo', 'historico']:
            if field in case:
                field_text = str(case[field]).lower()
                for pattern in self.g1_text_patterns:
                    if re.search(pattern, field_text):
                        findings['g1_by_field'].append({
                            'field': field,
                            'pattern_match': pattern,
                            'content': case[field][:200]  # Primeiros 200 chars
                        })
        
        return findings
    
    def analyze_all_trt_cases(self, trt_data):
        """Analisa TODOS os casos TRT para dados G1."""
        print(f"\\n🔍 ANÁLISE ULTRA-PROFUNDA de {len(trt_data):,} casos TRT...")
        
        results = []
        stats = {
            'total_cases': 0,
            'cases_with_g1_codes': 0,
            'cases_with_g1_text': 0,
            'cases_with_g1_fields': 0,
            'cases_with_any_g1': 0,
            'by_trt_region': defaultdict(int),
            'by_case_type': defaultdict(int),
            'g1_code_frequency': defaultdict(int),
            'g1_text_pattern_frequency': defaultdict(int)
        }
        
        for i, case in enumerate(trt_data):
            if i % 5000 == 0:
                print(f"  🔍 Analisando caso {i+1:,}/{len(trt_data):,} ({(i/len(trt_data))*100:.1f}%)...")
            
            findings = self.deep_search_g1_data(case)
            results.append(findings)
            
            # Atualiza estatísticas
            stats['total_cases'] += 1
            stats['by_trt_region'][findings['trt_region']] += 1
            stats['by_case_type'][findings['case_type']] += 1
            
            has_g1_codes = len(findings['g1_by_code']) > 0
            has_g1_text = len(findings['g1_by_text']) > 0
            has_g1_fields = len(findings['g1_by_field']) > 0
            
            if has_g1_codes:
                stats['cases_with_g1_codes'] += 1
                for finding in findings['g1_by_code']:
                    stats['g1_code_frequency'][finding['codigo']] += 1
            
            if has_g1_text:
                stats['cases_with_g1_text'] += 1
                for finding in findings['g1_by_text']:
                    stats['g1_text_pattern_frequency'][finding['pattern_match']] += 1
            
            if has_g1_fields:
                stats['cases_with_g1_fields'] += 1
            
            if has_g1_codes or has_g1_text or has_g1_fields:
                stats['cases_with_any_g1'] += 1
        
        print("✅ Análise ultra-profunda concluída!")
        return results, stats
    
    def create_comprehensive_g1_database(self, results, stats):
        """Cria banco de dados abrangente de dados G1."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Relatório estatístico detalhado
        report = f"""# RELATÓRIO ULTRA-ABRANGENTE - DADOS G1 EM TRTs

**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Metodologia Ultra-Profunda

Esta análise examinou **TODOS** os {stats['total_cases']:,} casos TRT usando:
1. **Busca por códigos G1** conhecidos (219, 220, 221, etc.)
2. **Busca textual** por padrões linguísticos
3. **Busca em campos** adicionais (observação, motivo, histórico)
4. **Análise regional** por TRT
5. **Análise por tipo** de processo

## 📊 Descobertas Principais

### 🔍 Cobertura de Dados G1

- **Total de casos analisados**: {stats['total_cases']:,}
- **Casos com códigos G1**: {stats['cases_with_g1_codes']:,} ({(stats['cases_with_g1_codes']/stats['total_cases'])*100:.2f}%)
- **Casos com padrões textuais G1**: {stats['cases_with_g1_text']:,} ({(stats['cases_with_g1_text']/stats['total_cases'])*100:.2f}%)
- **Casos com G1 em outros campos**: {stats['cases_with_g1_fields']:,} ({(stats['cases_with_g1_fields']/stats['total_cases'])*100:.2f}%)
- **TOTAL com qualquer dado G1**: {stats['cases_with_any_g1']:,} ({(stats['cases_with_any_g1']/stats['total_cases'])*100:.2f}%)

### 🏛️ Análise por Região TRT

"""
        
        # Top TRTs por dados G1
        total_with_g1_by_region = defaultdict(int)
        for result in results:
            if len(result['g1_by_code']) > 0 or len(result['g1_by_text']) > 0 or len(result['g1_by_field']) > 0:
                total_with_g1_by_region[result['trt_region']] += 1
        
        sorted_regions = sorted(total_with_g1_by_region.items(), key=lambda x: x[1], reverse=True)
        
        for region, count in sorted_regions[:10]:
            total_region = stats['by_trt_region'][region]
            percent = (count / total_region) * 100 if total_region > 0 else 0
            report += f"- **{region}**: {count:,}/{total_region:,} ({percent:.1f}%)\\n"
        
        report += f"""

### 📋 Códigos G1 Mais Frequentes

"""
        
        for codigo, count in sorted(stats['g1_code_frequency'].items(), key=lambda x: x[1], reverse=True)[:10]:
            codigo_name = self.g1_codes.get(codigo, f'Código {codigo}')
            report += f"- **{codigo} ({codigo_name})**: {count:,} ocorrências\\n"
        
        report += f"""

### 🔤 Padrões Textuais Mais Encontrados

"""
        
        for pattern, count in sorted(stats['g1_text_pattern_frequency'].items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"- **'{pattern}'**: {count:,} ocorrências\\n"
        
        report += f"""

### 📊 Tipos de Processo com Mais Dados G1

"""
        
        # Análise por tipo de processo
        g1_by_case_type = defaultdict(int)
        for result in results:
            if len(result['g1_by_code']) > 0:
                g1_by_case_type[result['case_type']] += 1
        
        for case_type, count in sorted(g1_by_case_type.items(), key=lambda x: x[1], reverse=True)[:10]:
            if case_type:
                total_type = stats['by_case_type'][case_type]
                percent = (count / total_type) * 100 if total_type > 0 else 0
                report += f"- **{case_type}**: {count:,}/{total_type:,} ({percent:.1f}%)\\n"
        
        report += f"""

## 💡 Conclusões Ultra-Profundas

1. **Cobertura total**: {(stats['cases_with_any_g1']/stats['total_cases'])*100:.2f}% dos casos TRT contêm algum dado G1
2. **Códigos estruturados**: {(stats['cases_with_g1_codes']/stats['total_cases'])*100:.2f}% têm códigos G1 formais
3. **Dados textuais**: {(stats['cases_with_g1_text']/stats['total_cases'])*100:.2f}% têm padrões textuais G1
4. **Variação regional**: TRTs variam significativamente na preservação de dados G1
5. **Tipos específicos**: Alguns tipos de processo preservam mais dados G1

## 🎯 Impacto para Análise TST

Com esta descoberta, podemos analisar **{stats['cases_with_any_g1']:,} casos TST** com dados G1 reais,
representando **{(stats['cases_with_any_g1']/stats['total_cases'])*100:.2f}%** de cobertura total.

---
*Análise ultra-abrangente baseada em {stats['total_cases']:,} casos TRT*
"""
        
        # Salva relatório
        report_path = f"{self.output_path}/ultra_comprehensive_g1_report_{timestamp}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 2. CSV com TODOS os casos que têm dados G1
        csv_path = f"{self.output_path}/all_g1_cases_{timestamp}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'numero_processo', 'trt_region', 'case_type', 'total_movements',
                'g1_codes_count', 'g1_text_count', 'g1_fields_count',
                'primary_g1_code', 'primary_g1_result', 'primary_g1_date'
            ])
            
            for result in results:
                if len(result['g1_by_code']) > 0 or len(result['g1_by_text']) > 0 or len(result['g1_by_field']) > 0:
                    primary_g1 = result['g1_by_code'][0] if result['g1_by_code'] else None
                    
                    writer.writerow([
                        result['numero'],
                        result['trt_region'],
                        result['case_type'],
                        result['total_movements'],
                        len(result['g1_by_code']),
                        len(result['g1_by_text']),
                        len(result['g1_by_field']),
                        primary_g1['codigo'] if primary_g1 else '',
                        primary_g1['resultado'] if primary_g1 else '',
                        primary_g1['data'] if primary_g1 else ''
                    ])
        
        # 3. JSON detalhado com TODOS os achados
        json_path = f"{self.output_path}/ultra_detailed_findings_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'statistics': stats,
                'detailed_findings': results[:1000],  # Primeiros 1000 para não sobrecarregar
                'summary': {
                    'total_analyzed': stats['total_cases'],
                    'with_any_g1': stats['cases_with_any_g1'],
                    'coverage_percentage': (stats['cases_with_any_g1']/stats['total_cases'])*100
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\\n📊 RESULTADOS ULTRA-ABRANGENTES:")
        print("=" * 50)
        print(f"📄 Relatório: {report_path}")
        print(f"📊 CSV: {csv_path}")
        print(f"📋 JSON: {json_path}")
        
        print(f"\\n🎯 DESCOBERTAS PRINCIPAIS:")
        print(f"   Total analisado: {stats['total_cases']:,}")
        print(f"   Com dados G1: {stats['cases_with_any_g1']:,}")
        print(f"   Cobertura: {(stats['cases_with_any_g1']/stats['total_cases'])*100:.2f}%")
        
        return report_path, stats['cases_with_any_g1']
    
    def run_ultra_search(self):
        """Executa busca ultra-abrangente."""
        # Carrega TODOS os dados TRT
        trt_data = self.load_all_trt_files()
        
        # Análise ultra-profunda
        results, stats = self.analyze_all_trt_cases(trt_data)
        
        # Cria banco de dados abrangente
        report_path, total_g1_cases = self.create_comprehensive_g1_database(results, stats)
        
        return results, stats, report_path, total_g1_cases

def main():
    """Função principal."""
    searcher = UltraComprehensiveG1Search()
    searcher.run_ultra_search()

if __name__ == "__main__":
    main()