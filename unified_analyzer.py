#!/usr/bin/env python3
"""
Analisador Unificado de Jurisprudência Trabalhista
Substitui múltiplos scripts redundantes com uma interface unificada.

Este script consolida funcionalidades de:
- analyze_case_chains.py, analyze_case_chains_fix.py, analyze_json_chains.py
- analyze_case_flow.py, track_case_chains.py, track_cases.py, final_analysis.py
- analyze.py, analyze_by_instance.py, analise_estatistica_tribunais.py
- enhanced_processor.py e funcionalidades de src/analysis/assedio_moral_analysis.py
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import json

# Importa módulos utilitários unificados
from src.utils.data_loader import DataLoader, extract_case_core, get_instance_order, filter_assedio_moral_cases
from src.utils.movement_analyzer import MovementAnalyzer
from src.utils.visualizations import JurimetriaVisualizer

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedJurimetricAnalyzer:
    """Analisador unificado que consolida toda funcionalidade de análise."""
    
    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)
            
        # Inicializa componentes
        self.data_loader = DataLoader(self.base_path)
        self.movement_analyzer = MovementAnalyzer()
        self.visualizer = JurimetriaVisualizer(self.base_path / "visualizations")
        
        # Paths de saída
        self.output_path = self.base_path / "analysis_results"
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def load_data(self, data_source: str = "consolidated", 
                  external_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Carrega dados de diferentes fontes.
        
        Args:
            data_source: 'consolidated', 'raw', ou 'external'
            external_path: Caminho externo se data_source='external'
            
        Returns:
            Lista de dados carregados
        """
        if data_source == "consolidated":
            return self.data_loader.load_consolidated_data()
        elif data_source == "raw":
            return self.data_loader.load_raw_json_files()
        elif data_source == "external" and external_path:
            return self.data_loader.load_raw_json_files(Path(external_path))
        else:
            logger.error(f"Fonte de dados não reconhecida: {data_source}")
            return []
    
    def analyze_basic_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Análise estatística básica (substitui analyze.py, analyze_by_instance.py).
        
        Args:
            data: Dados para análise
            
        Returns:
            Dicionário com estatísticas básicas
        """
        logger.info("Executando análise estatística básica...")
        
        total_cases = len(data)
        
        # Análise por tribunal
        tribunal_counts = {}
        # Análise por assunto
        assunto_counts = {}
        # Análise por classe
        classe_counts = {}
        # Análise por instância
        instancia_counts = {}
        
        for item in data:
            # Tribunal
            tribunal = item.get('tribunal', 'Desconhecido')
            tribunal_counts[tribunal] = tribunal_counts.get(tribunal, 0) + 1
            
            # Assuntos
            assuntos = item.get('assuntos', [])
            for assunto in assuntos:
                if isinstance(assunto, dict):
                    nome = assunto.get('nome', 'Desconhecido')
                    assunto_counts[nome] = assunto_counts.get(nome, 0) + 1
            
            # Classe
            classe = item.get('classe', {})
            if isinstance(classe, dict):
                nome_classe = classe.get('nome', 'Desconhecida')
                classe_counts[nome_classe] = classe_counts.get(nome_classe, 0) + 1
            
            # Instância
            grau = item.get('grau', '')
            instancia = self.movement_analyzer.grau_mapping.get(grau, 'Desconhecida')
            instancia_counts[instancia] = instancia_counts.get(instancia, 0) + 1
        
        return {
            'total_cases': total_cases,
            'tribunal_distribution': tribunal_counts,
            'assunto_distribution': assunto_counts,
            'classe_distribution': classe_counts,
            'instancia_distribution': instancia_counts
        }
    
    def analyze_case_chains(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Análise de encadeamento de casos (substitui múltiplos scripts de chain analysis).
        
        Args:
            data: Dados para análise
            
        Returns:
            Dicionário com análise de encadeamento
        """
        logger.info("Executando análise de encadeamento de casos...")
        
        # Agrupa processos pelo core do número
        process_groups = {}
        
        for item in data:
            numero_processo = item.get('numeroProcesso', '')
            if numero_processo:
                core = extract_case_core(numero_processo)
                if core not in process_groups:
                    process_groups[core] = []
                process_groups[core].append(item)
        
        # Analisa cadeias
        single_occurrence = 0
        multi_instance_chains = 0
        chain_patterns = {}
        detailed_chains = []
        
        for core, group in process_groups.items():
            if len(group) == 1:
                single_occurrence += 1
            else:
                multi_instance_chains += 1
                
                # Analisa padrão da cadeia
                pattern = self.movement_analyzer.get_case_chain_pattern(group)
                chain_patterns[pattern] = chain_patterns.get(pattern, 0) + 1
                
                # Adiciona detalhes da cadeia
                chain_detail = {
                    'core': core,
                    'num_instances': len(group),
                    'pattern': pattern,
                    'tribunals': list(set(item.get('tribunal', '') for item in group)),
                    'instances': []
                }
                
                for item in group:
                    grau = item.get('grau', '')
                    instancia = self.movement_analyzer.grau_mapping.get(grau, 'Desconhecida')
                    resultado = self.movement_analyzer.extract_result_from_movements(
                        item.get('movimentos', [])
                    )
                    
                    chain_detail['instances'].append({
                        'instancia': instancia,
                        'tribunal': item.get('tribunal', ''),
                        'resultado': resultado[0] if resultado else 'Sem Resultado',
                        'numero_processo': item.get('numeroProcesso', '')
                    })
                
                detailed_chains.append(chain_detail)
        
        return {
            'total_unique_cores': len(process_groups),
            'single_occurrence': single_occurrence,
            'multi_instance_chains': multi_instance_chains,
            'chain_patterns': chain_patterns,
            'detailed_chains': detailed_chains[:100]  # Limita para performance
        }
    
    def analyze_assedio_moral_cases(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Análise específica de casos de assédio moral.
        
        Args:
            data: Dados para análise
            
        Returns:
            Dicionário com análise de assédio moral
        """
        logger.info("Executando análise específica de assédio moral...")
        
        # Filtra casos de assédio moral
        assedio_cases = filter_assedio_moral_cases(data)
        
        if not assedio_cases:
            logger.warning("Nenhum caso de assédio moral encontrado")
            return {}
        
        logger.info(f"Encontrados {len(assedio_cases)} casos de assédio moral")
        
        # Análise de movimentos específica para assédio moral
        movement_analysis = self.movement_analyzer.analyze_movement_patterns(assedio_cases)
        
        # Análise de encadeamento específica
        chain_analysis = self.analyze_case_chains(assedio_cases)
        
        # Estatísticas básicas
        basic_stats = self.analyze_basic_statistics(assedio_cases)
        
        return {
            'total_assedio_cases': len(assedio_cases),
            'movement_analysis': movement_analysis,
            'chain_analysis': chain_analysis,
            'basic_statistics': basic_stats,
            'percentage_of_total': (len(assedio_cases) / len(data)) * 100
        }
    
    def generate_comprehensive_report(self, results: Dict[str, Any], 
                                    report_type: str = "complete") -> Path:
        """
        Gera relatório compreensivo da análise.
        
        Args:
            results: Resultados compilados
            report_type: Tipo do relatório ('complete', 'summary', 'assedio_only')
            
        Returns:
            Caminho do relatório gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_path / f"relatorio_{report_type}_{timestamp}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Relatório de Análise Jurisprudencial - {report_type.title()}\n\n")
            f.write(f"Data da análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Resumo executivo
            f.write("## Resumo Executivo\n\n")
            
            if 'basic_statistics' in results:
                basic = results['basic_statistics']
                f.write(f"- Total de casos analisados: {basic.get('total_cases', 0):,}\n")
                f.write(f"- Tribunais representados: {len(basic.get('tribunal_distribution', {}))}\n")
                f.write(f"- Classes processuais: {len(basic.get('classe_distribution', {}))}\n")
            
            if 'chain_analysis' in results:
                chains = results['chain_analysis']
                f.write(f"- Processos únicos: {chains.get('total_unique_cores', 0):,}\n")
                f.write(f"- Casos com múltiplas instâncias: {chains.get('multi_instance_chains', 0):,}\n")
            
            if 'assedio_analysis' in results:
                assedio = results['assedio_analysis']
                f.write(f"- Casos de assédio moral: {assedio.get('total_assedio_cases', 0):,}\n")
                if 'percentage_of_total' in assedio:
                    f.write(f"- Percentual de assédio moral: {assedio['percentage_of_total']:.1f}%\n")
            
            # Análise por instância
            if 'movement_analysis' in results.get('assedio_analysis', {}):
                mov_analysis = results['assedio_analysis']['movement_analysis']
                stats_by_instance = mov_analysis.get('stats_by_instance', {})
                
                f.write("\n## Análise por Instância\n\n")
                
                for instancia, stats in stats_by_instance.items():
                    f.write(f"### {instancia}\n\n")
                    f.write(f"Total de casos: {stats.get('total', 0):,}\n\n")
                    
                    contagens = stats.get('contagens', {})
                    percentuais = stats.get('percentuais', {})
                    
                    f.write("Resultados:\n")
                    for resultado in sorted(contagens.keys(), key=lambda x: contagens[x], reverse=True):
                        count = contagens[resultado]
                        percent = percentuais.get(resultado, 0)
                        f.write(f"- {resultado}: {count:,} casos ({percent:.1f}%)\n")
                    
                    # Taxa de sucesso
                    success_stats = stats.get('success_stats', {})
                    if success_stats:
                        taxa = success_stats.get('taxa_sucesso', 0)
                        f.write(f"\n**Taxa de sucesso do trabalhador: {taxa:.1f}%**\n")
                    
                    f.write("\n")
            
            # Padrões de encadeamento
            if 'chain_analysis' in results.get('assedio_analysis', {}):
                chain_analysis = results['assedio_analysis']['chain_analysis']
                patterns = chain_analysis.get('chain_patterns', {})
                
                if patterns:
                    f.write("## Padrões de Encadeamento Processual\n\n")
                    
                    sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:20]
                    
                    for pattern, count in sorted_patterns:
                        f.write(f"- {pattern}: {count} casos\n")
            
            # Distribuição por tribunal
            if 'basic_statistics' in results.get('assedio_analysis', {}):
                basic = results['assedio_analysis']['basic_statistics']
                tribunal_dist = basic.get('tribunal_distribution', {})
                
                if tribunal_dist:
                    f.write("\n## Distribuição por Tribunal\n\n")
                    
                    sorted_tribunals = sorted(tribunal_dist.items(), key=lambda x: x[1], reverse=True)
                    
                    for tribunal, count in sorted_tribunals[:20]:
                        f.write(f"- {tribunal}: {count:,} casos\n")
            
            # Metodologia
            f.write("\n## Metodologia\n\n")
            f.write("Esta análise utilizou os seguintes critérios:\n\n")
            f.write("### Códigos de Movimento (TPU/CNJ)\n\n")
            
            for codigo, nome in sorted(self.movement_analyzer.movement_codes.items()):
                f.write(f"- {codigo}: {nome}\n")
            
            f.write("\n### Códigos de Assunto para Assédio Moral\n\n")
            f.write("- 1723: Assédio Moral (Justiça do Trabalho)\n")
            f.write("- 14175: Assédio Moral (revisão 2022-2024)\n")
            f.write("- 14018: Assédio Moral (PJe unificado)\n")
            
        logger.info(f"Relatório salvo em: {report_path}")
        return report_path
    
    def generate_visualizations(self, results: Dict[str, Any]) -> List[Path]:
        """
        Gera visualizações dos resultados.
        
        Args:
            results: Resultados da análise
            
        Returns:
            Lista de caminhos dos arquivos gerados
        """
        generated_files = []
        
        # Visualização de resultados por instância
        if 'movement_analysis' in results.get('assedio_analysis', {}):
            mov_analysis = results['assedio_analysis']['movement_analysis']
            stats_by_instance = mov_analysis.get('stats_by_instance', {})
            
            if stats_by_instance:
                file_path = self.visualizer.plot_results_by_instance(
                    stats_by_instance,
                    "Resultados de Assédio Moral por Instância",
                    "assedio_moral_por_instancia.png"
                )
                generated_files.append(file_path)
                
                # Taxa de sucesso
                success_rates = {}
                for instancia, stats in stats_by_instance.items():
                    success_stats = stats.get('success_stats', {})
                    if success_stats:
                        success_rates[instancia] = success_stats.get('taxa_sucesso', 0)
                
                if success_rates:
                    file_path = self.visualizer.plot_success_rates_comparison(
                        success_rates,
                        "Taxa de Sucesso em Casos de Assédio Moral",
                        "taxa_sucesso_assedio_moral.png"
                    )
                    generated_files.append(file_path)
        
        # Distribuição por tribunal
        if 'basic_statistics' in results.get('assedio_analysis', {}):
            basic = results['assedio_analysis']['basic_statistics']
            tribunal_dist = basic.get('tribunal_distribution', {})
            
            if tribunal_dist:
                file_path = self.visualizer.plot_tribunal_distribution(
                    tribunal_dist,
                    "Distribuição de Casos de Assédio Moral por Tribunal",
                    "distribuicao_tribunais_assedio.png"
                )
                generated_files.append(file_path)
        
        # Padrões de fluxo
        if 'chain_analysis' in results.get('assedio_analysis', {}):
            chain_analysis = results['assedio_analysis']['chain_analysis']
            patterns = chain_analysis.get('chain_patterns', {})
            
            if patterns:
                file_path = self.visualizer.plot_flow_patterns(
                    patterns,
                    20,
                    "Padrões de Fluxo Processual - Assédio Moral",
                    "padroes_fluxo_assedio.png"
                )
                generated_files.append(file_path)
        
        return generated_files
    
    def save_processed_data(self, results: Dict[str, Any]) -> List[Path]:
        """
        Salva dados processados em diferentes formatos.
        
        Args:
            results: Resultados da análise
            
        Returns:
            Lista de caminhos dos arquivos salvos
        """
        saved_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salva resultados principais
        results_path = self.data_loader.save_data(
            [results], f"analysis_results_{timestamp}", "json"
        )
        saved_files.append(results_path)
        
        # Se há análise de assédio moral, salva dados específicos
        if 'assedio_analysis' in results:
            assedio_path = self.data_loader.save_data(
                [results['assedio_analysis']], f"assedio_moral_analysis_{timestamp}", "json"
            )
            saved_files.append(assedio_path)
        
        return saved_files
    
    def run_complete_analysis(self, data_source: str = "consolidated",
                            external_path: Optional[str] = None,
                            focus_assedio_moral: bool = True) -> Dict[str, Any]:
        """
        Executa análise completa unificada.
        
        Args:
            data_source: Fonte dos dados
            external_path: Caminho externo se necessário
            focus_assedio_moral: Se deve focar em análise de assédio moral
            
        Returns:
            Dicionário com todos os resultados
        """
        logger.info("Iniciando análise completa unificada...")
        
        # Carrega dados
        data = self.load_data(data_source, external_path)
        
        if not data:
            logger.error("Nenhum dado carregado")
            return {}
        
        results = {}
        
        # Análise estatística básica
        results['basic_statistics'] = self.analyze_basic_statistics(data)
        
        # Análise de encadeamento
        results['chain_analysis'] = self.analyze_case_chains(data)
        
        # Análise específica de assédio moral
        if focus_assedio_moral:
            results['assedio_analysis'] = self.analyze_assedio_moral_cases(data)
        
        # Análise de movimentos geral
        results['movement_analysis'] = self.movement_analyzer.analyze_movement_patterns(data)
        
        # Gera relatório
        report_path = self.generate_comprehensive_report(results)
        results['report_path'] = str(report_path)
        
        # Gera visualizações
        viz_files = self.generate_visualizations(results)
        results['visualization_files'] = [str(f) for f in viz_files]
        
        # Salva dados processados
        saved_files = self.save_processed_data(results)
        results['saved_files'] = [str(f) for f in saved_files]
        
        logger.info("Análise completa finalizada!")
        return results


def main():
    """Função principal com interface de linha de comando."""
    parser = argparse.ArgumentParser(description="Analisador Unificado de Jurisprudência Trabalhista")
    
    parser.add_argument("--data-source", choices=["consolidated", "raw", "external"],
                       default="consolidated", help="Fonte dos dados")
    parser.add_argument("--external-path", type=str, 
                       help="Caminho externo para dados (se data-source=external)")
    parser.add_argument("--focus-assedio", action="store_true", default=True,
                       help="Focar em análise de assédio moral")
    parser.add_argument("--output-dir", type=str,
                       help="Diretório de saída personalizado")
    
    args = parser.parse_args()
    
    # Inicializa analisador
    base_path = Path(args.output_dir) if args.output_dir else None
    analyzer = UnifiedJurimetricAnalyzer(base_path)
    
    # Executa análise
    results = analyzer.run_complete_analysis(
        data_source=args.data_source,
        external_path=args.external_path,
        focus_assedio_moral=args.focus_assedio
    )
    
    if results:
        print(f"\n✅ Análise concluída com sucesso!")
        print(f"📊 Relatório: {results.get('report_path', 'N/A')}")
        print(f"📈 Visualizações: {len(results.get('visualization_files', []))} arquivos")
        print(f"💾 Dados salvos: {len(results.get('saved_files', []))} arquivos")
    else:
        print("❌ Falha na análise")

if __name__ == "__main__":
    main()