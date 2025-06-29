#!/usr/bin/env python3
"""
Análise Completa de Fluxos Processuais
Aplica a lógica correta de recursos trabalhistas para interpretar resultados.
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys

# Adiciona o diretório src ao path
sys.path.append(str(Path(__file__).parent))

from src.utils.data_loader import DataLoader, filter_assedio_moral_cases
from src.utils.correct_flow_analyzer import CorrectFlowAnalyzer
from src.utils.visualizations import JurimetriaVisualizer

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteFlowAnalysis:
    """Análise completa de fluxos processuais com lógica correta."""
    
    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)
        
        self.data_loader = DataLoader(self.base_path)
        self.flow_analyzer = CorrectFlowAnalyzer()
        self.visualizer = JurimetriaVisualizer(self.base_path / "flow_analysis_results")
        
        self.output_path = self.base_path / "flow_analysis_results"
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def run_complete_analysis(self, data_source: str = "external", 
                            external_path: Optional[str] = None,
                            focus_assedio_moral: bool = True) -> Dict[str, Any]:
        """
        Executa análise completa de fluxos processuais.
        
        Args:
            data_source: Fonte dos dados
            external_path: Caminho externo se necessário
            focus_assedio_moral: Se deve focar em assédio moral
            
        Returns:
            Resultados da análise
        """
        logger.info("Iniciando análise completa de fluxos processuais...")
        
        # Carrega dados
        if data_source == "external" and external_path:
            data = self.data_loader.load_raw_json_files(Path(external_path))
        elif data_source == "consolidated":
            data = self.data_loader.load_consolidated_data()
        elif data_source == "raw":
            data = self.data_loader.load_raw_json_files()
        else:
            logger.error(f"Fonte de dados inválida: {data_source}")
            return {}
        
        if not data:
            logger.error("Nenhum dado carregado")
            return {}
        
        logger.info(f"Carregados {len(data)} processos")
        
        # Filtra casos de assédio moral se solicitado
        if focus_assedio_moral:
            data = filter_assedio_moral_cases(data)
            logger.info(f"Filtrados {len(data)} casos de assédio moral")
        
        # Executa análise de fluxos
        flow_analysis = self.flow_analyzer.analyze_dataset_flows(data)
        
        # Gera relatório
        report_content = self.flow_analyzer.generate_flow_report(flow_analysis)
        report_path = self._save_report(report_content)
        
        # Gera exemplos
        exemplos = self.flow_analyzer.get_flow_examples(flow_analysis, 5)
        
        # Salva dados detalhados
        data_path = self._save_detailed_data(flow_analysis)
        
        # Gera visualizações
        viz_files = self._generate_visualizations(flow_analysis)
        
        results = {
            'analysis': flow_analysis,
            'report_path': str(report_path),
            'data_path': str(data_path),
            'visualization_files': [str(f) for f in viz_files],
            'exemplos_por_tipo': exemplos,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("Análise completa finalizada!")
        return results
    
    def _save_report(self, report_content: str) -> Path:
        """Salva o relatório em arquivo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_path / f"relatorio_fluxos_corretos_{timestamp}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Relatório salvo em: {report_path}")
        return report_path
    
    def _save_detailed_data(self, analysis: Dict[str, Any]) -> Path:
        """Salva dados detalhados em JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_path = self.output_path / f"dados_fluxos_detalhados_{timestamp}.json"
        
        # Prepara dados para serialização
        import json
        
        # Remove objetos não serializáveis e prepara dados
        clean_analysis = {
            'resumo': {
                'total_processos': analysis['total_processos'],
                'fluxos_completos': analysis['fluxos_completos'],
                'percentual_completos': analysis['percentual_completos']
            },
            'estatisticas': analysis.get('estatisticas', {}),
            'exemplos_fluxos': analysis.get('fluxos_detalhados', [])[:50]  # Primeiros 50
        }
        
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(clean_analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Dados detalhados salvos em: {data_path}")
        return data_path
    
    def _generate_visualizations(self, analysis: Dict[str, Any]) -> List[Path]:
        """Gera visualizações dos resultados."""
        viz_files = []
        stats = analysis.get('estatisticas', {})
        
        if not stats:
            return viz_files
        
        try:
            # Gráfico de tipos de mudança
            tipos_mudanca = stats.get('tipos_mudanca', {})
            if tipos_mudanca:
                # Converte para nomes mais legíveis
                tipos_legivel = {
                    'reviravolta_favoravel': 'Reviravolta Favorável',
                    'reviravolta_desfavoravel': 'Reviravolta Desfavorável', 
                    'manteve_favoravel': 'Manteve Favorável',
                    'manteve_desfavoravel': 'Manteve Desfavorável'
                }
                
                dados_viz = {tipos_legivel.get(k, k): v for k, v in tipos_mudanca.items()}
                
                file_path = self.visualizer.plot_tribunal_distribution(
                    dados_viz,
                    "Tipos de Mudança Entre Instâncias",
                    "tipos_mudanca_fluxos.png"
                )
                viz_files.append(file_path)
            
            # Gráfico de taxa de sucesso por instância
            por_instancia = stats.get('por_instancia', {})
            if por_instancia:
                taxas_sucesso = {}
                for instancia, dados in por_instancia.items():
                    total = dados.get('total', 0)
                    favoravel = dados.get('favoravel', 0)
                    taxa = (favoravel / total * 100) if total > 0 else 0
                    taxas_sucesso[instancia] = taxa
                
                file_path = self.visualizer.plot_success_rates_comparison(
                    taxas_sucesso,
                    "Taxa de Sucesso por Instância de Recurso",
                    "taxa_sucesso_por_instancia_recurso.png"
                )
                viz_files.append(file_path)
            
            # Gráfico de taxa de sucesso por tribunal (top 10)
            por_tribunal = stats.get('por_tribunal', {})
            if por_tribunal:
                taxas_tribunal = {}
                tribunais_ordenados = sorted(por_tribunal.items(), key=lambda x: x[1]['total'], reverse=True)
                
                for tribunal, dados in tribunais_ordenados[:10]:
                    total = dados.get('total', 0)
                    favoravel = dados.get('favoravel', 0)
                    taxa = (favoravel / total * 100) if total > 0 else 0
                    taxas_tribunal[tribunal] = taxa
                
                file_path = self.visualizer.plot_success_rates_comparison(
                    taxas_tribunal,
                    "Taxa de Sucesso por Tribunal (Top 10)",
                    "taxa_sucesso_por_tribunal.png"
                )
                viz_files.append(file_path)
            
            # Gráfico temporal (por ano)
            por_ano = stats.get('por_ano', {})
            if por_ano:
                taxas_ano = {}
                for ano, dados in sorted(por_ano.items()):
                    total = dados.get('total', 0)
                    favoravel = dados.get('favoravel', 0)
                    taxa = (favoravel / total * 100) if total > 0 else 0
                    taxas_ano[ano] = taxa
                
                file_path = self.visualizer.plot_success_rates_comparison(
                    taxas_ano,
                    "Taxa de Sucesso por Ano",
                    "taxa_sucesso_por_ano.png"
                )
                viz_files.append(file_path)
            
            # Gráfico de fluxos mais comuns
            fluxos_comuns = stats.get('fluxos_mais_comuns', {})
            if fluxos_comuns:
                file_path = self.visualizer.plot_flow_patterns(
                    fluxos_comuns,
                    15,
                    "Fluxos Processuais Mais Comuns",
                    "fluxos_mais_comuns.png"
                )
                viz_files.append(file_path)
        
        except Exception as e:
            logger.error(f"Erro gerando visualizações: {str(e)}")
        
        return viz_files
    
    def print_summary(self, results: Dict[str, Any]) -> None:
        """Imprime resumo dos resultados."""
        analysis = results.get('analysis', {})
        stats = analysis.get('estatisticas', {})
        
        print(f"\n🎯 RESUMO DA ANÁLISE DE FLUXOS PROCESSUAIS")
        print(f"=" * 60)
        
        print(f"\n📊 DADOS GERAIS:")
        print(f"  Total de processos: {analysis.get('total_processos', 0):,}")
        print(f"  Fluxos completos: {analysis.get('fluxos_completos', 0):,}")
        print(f"  Percentual completo: {analysis.get('percentual_completos', 0):.1f}%")
        
        # Conta inferências TRT
        if stats:
            fluxos_detalhados = analysis.get('fluxos_detalhados', [])
            inferencias_trt = sum(1 for f in fluxos_detalhados if f.get('inferencia_trt', False))
            if inferencias_trt > 0:
                print(f"  Inferências TRT: {inferencias_trt:,} casos adicionais analisados")
        
        if stats:
            print(f"\n⚖️  RESULTADO FINAL PARA O TRABALHADOR:")
            taxa_sucesso = stats.get('taxa_sucesso_final_trabalhador', 0)
            print(f"  Taxa de sucesso: {taxa_sucesso:.1f}%")
            print(f"  Casos favoráveis: {stats.get('favoravel_final', 0):,}")
            print(f"  Casos desfavoráveis: {stats.get('desfavoravel_final', 0):,}")
            
            print(f"\n🔄 TIPOS DE MUDANÇA:")
            tipos_mudanca_percent = stats.get('tipos_mudanca_percent', {})
            for tipo, percent in sorted(tipos_mudanca_percent.items(), key=lambda x: x[1], reverse=True):
                count = stats.get('tipos_mudanca', {}).get(tipo, 0)
                print(f"  {tipo}: {count} casos ({percent:.1f}%)")
            
            print(f"\n🏛️  TOP 5 TRIBUNAIS:")
            por_tribunal = stats.get('por_tribunal', {})
            tribunais_ordenados = sorted(por_tribunal.items(), key=lambda x: x[1]['total'], reverse=True)
            for i, (tribunal, dados) in enumerate(tribunais_ordenados[:5], 1):
                taxa = (dados['favoravel'] / dados['total'] * 100) if dados['total'] > 0 else 0
                print(f"  {i}. {tribunal}: {dados['total']} casos ({taxa:.1f}% sucesso)")
            
            print(f"\n📅 DISTRIBUIÇÃO TEMPORAL:")
            por_ano = stats.get('por_ano', {})
            for ano, dados in sorted(por_ano.items())[-5:]:  # Últimos 5 anos
                taxa = (dados['favoravel'] / dados['total'] * 100) if dados['total'] > 0 else 0
                print(f"  {ano}: {dados['total']} casos ({taxa:.1f}% sucesso)")
            
            print(f"\n📋 FLUXOS MAIS COMUNS:")
            fluxos_comuns = stats.get('fluxos_mais_comuns', {})
            for i, (fluxo, count) in enumerate(list(fluxos_comuns.items())[:5], 1):
                total = stats.get('total_fluxos', 1)
                percent = (count / total * 100)
                print(f"  {i}. {fluxo}: {count} ({percent:.1f}%)")
        
        print(f"\n📁 ARQUIVOS GERADOS:")
        print(f"  Relatório: {results.get('report_path', 'N/A')}")
        print(f"  Dados: {results.get('data_path', 'N/A')}")
        print(f"  Visualizações: {len(results.get('visualization_files', []))} arquivos")

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Análise Completa de Fluxos Processuais com Lógica Correta")
    
    parser.add_argument("--data-source", choices=["consolidated", "raw", "external"],
                       default="external", help="Fonte dos dados")
    parser.add_argument("--external-path", type=str,
                       default="/Users/danilobortoli/Documents/Tese de doutorado da Andreia/Dados da segunda extração/raw",
                       help="Caminho externo para dados")
    parser.add_argument("--focus-assedio", action="store_true", default=True,
                       help="Focar em casos de assédio moral")
    parser.add_argument("--output-dir", type=str,
                       help="Diretório de saída personalizado")
    
    args = parser.parse_args()
    
    # Inicializa analisador
    base_path = Path(args.output_dir) if args.output_dir else None
    analyzer = CompleteFlowAnalysis(base_path)
    
    # Executa análise
    results = analyzer.run_complete_analysis(
        data_source=args.data_source,
        external_path=args.external_path,
        focus_assedio_moral=args.focus_assedio
    )
    
    if results:
        analyzer.print_summary(results)
    else:
        print("❌ Falha na análise")

if __name__ == "__main__":
    main()