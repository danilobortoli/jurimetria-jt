#!/usr/bin/env python3
"""
Módulo utilitário compartilhado para visualizações.
Padroniza e elimina redundâncias de código de visualização.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class JurimetriaVisualizer:
    """Classe unificada para visualizações jurisprudenciais."""
    
    def __init__(self, output_path: Optional[Path] = None, style: str = 'whitegrid'):
        if output_path is None:
            self.output_path = Path(__file__).parent.parent.parent / "visualizations"
        else:
            self.output_path = Path(output_path)
            
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Configuração padrão de estilo
        sns.set_style(style)
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 10
        
        # Paleta de cores padrão
        self.colors = sns.color_palette("husl", 8)
        
    def plot_results_by_instance(self, stats_by_instance: Dict[str, Dict], 
                                title: str = "Resultados por Instância",
                                filename: str = "resultados_por_instancia.png") -> Path:
        """
        Plota resultados comparados por instância.
        
        Args:
            stats_by_instance: Estatísticas organizadas por instância
            title: Título do gráfico
            filename: Nome do arquivo de saída
            
        Returns:
            Caminho do arquivo salvo
        """
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Organiza dados para plotagem
        instancias = list(stats_by_instance.keys())
        resultados_unicos = set()
        
        # Coleta todos os tipos de resultado
        for stats in stats_by_instance.values():
            resultados_unicos.update(stats.get('percentuais', {}).keys())
        
        resultados_unicos = sorted(list(resultados_unicos))
        
        # Cria matriz de dados
        data_matrix = []
        for resultado in resultados_unicos:
            row = []
            for instancia in instancias:
                percent = stats_by_instance[instancia].get('percentuais', {}).get(resultado, 0)
                row.append(percent)
            data_matrix.append(row)
        
        # Plota barras agrupadas
        x = np.arange(len(instancias))
        width = 0.8 / len(resultados_unicos)
        
        for i, (resultado, percentuais) in enumerate(zip(resultados_unicos, data_matrix)):
            offset = (i - len(resultados_unicos)/2) * width + width/2
            bars = ax.bar(x + offset, percentuais, width, 
                         label=resultado, color=self.colors[i % len(self.colors)])
            
            # Adiciona valores nas barras
            for j, bar in enumerate(bars):
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                           f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel('Instância')
        ax.set_ylabel('Percentual (%)')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(instancias, rotation=45, ha='right')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        output_file = self.output_path / filename
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Gráfico salvo em: {output_file}")
        return output_file
    
    def plot_success_rates_comparison(self, success_rates: Dict[str, float],
                                    title: str = "Taxa de Sucesso por Instância",
                                    filename: str = "taxas_sucesso.png") -> Path:
        """
        Plota comparação de taxas de sucesso.
        
        Args:
            success_rates: Dicionário com taxas de sucesso por instância
            title: Título do gráfico
            filename: Nome do arquivo
            
        Returns:
            Caminho do arquivo salvo
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        instancias = list(success_rates.keys())
        taxas = list(success_rates.values())
        
        bars = ax.bar(instancias, taxas, color=self.colors[:len(instancias)])
        
        # Adiciona valores nas barras
        for bar, taxa in zip(bars, taxas):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{taxa:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylabel('Taxa de Sucesso (%)')
        ax.set_title(title)
        ax.set_ylim(0, max(taxas) * 1.2)
        
        # Adiciona linha de referência em 50%
        ax.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50%')
        ax.legend()
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        output_file = self.output_path / filename
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Gráfico salvo em: {output_file}")
        return output_file
    
    def plot_tribunal_distribution(self, tribunal_stats: Dict[str, Any],
                                  title: str = "Distribuição por Tribunal",
                                  filename: str = "distribuicao_tribunais.png") -> Path:
        """
        Plota distribuição de casos por tribunal.
        
        Args:
            tribunal_stats: Estatísticas por tribunal
            title: Título do gráfico
            filename: Nome do arquivo
            
        Returns:
            Caminho do arquivo salvo
        """
        if isinstance(tribunal_stats, dict):
            tribunais = list(tribunal_stats.keys())
            counts = list(tribunal_stats.values())
        else:
            # Assume que é um Series do pandas
            tribunais = tribunal_stats.index.tolist()
            counts = tribunal_stats.values.tolist()
        
        fig, ax = plt.subplots(figsize=(15, 8))
        
        bars = ax.bar(tribunais, counts, color=self.colors[0])
        
        # Adiciona valores nas barras
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                   f'{count}', ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel('Tribunal')
        ax.set_ylabel('Número de Casos')
        ax.set_title(title)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        output_file = self.output_path / filename
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Gráfico salvo em: {output_file}")
        return output_file
    
    def plot_flow_patterns(self, patterns: Dict[str, int], top_n: int = 20,
                          title: str = "Padrões de Fluxo Processual",
                          filename: str = "padroes_fluxo.png") -> Path:
        """
        Plota os padrões de fluxo processual mais comuns.
        
        Args:
            patterns: Dicionário com padrões e suas frequências
            top_n: Número de padrões principais a mostrar
            title: Título do gráfico
            filename: Nome do arquivo
            
        Returns:
            Caminho do arquivo salvo
        """
        # Seleciona top N padrões
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        if not sorted_patterns:
            logger.warning("Nenhum padrão de fluxo encontrado")
            return self.output_path / filename
        
        patterns_names, frequencies = zip(*sorted_patterns)
        
        fig, ax = plt.subplots(figsize=(15, 10))
        
        # Trunca nomes muito longos
        truncated_names = [name[:50] + "..." if len(name) > 50 else name 
                          for name in patterns_names]
        
        bars = ax.barh(range(len(frequencies)), frequencies, 
                      color=self.colors[0], alpha=0.7)
        
        # Adiciona valores nas barras
        for i, (bar, freq) in enumerate(zip(bars, frequencies)):
            width = bar.get_width()
            ax.text(width + max(frequencies)*0.01, bar.get_y() + bar.get_height()/2.,
                   f'{freq}', ha='left', va='center', fontsize=9)
        
        ax.set_yticks(range(len(truncated_names)))
        ax.set_yticklabels(truncated_names, fontsize=8)
        ax.set_xlabel('Número de Casos')
        ax.set_title(title)
        
        plt.tight_layout()
        
        output_file = self.output_path / filename
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Gráfico salvo em: {output_file}")
        return output_file
    
    def plot_time_series(self, df: pd.DataFrame, date_column: str = 'data_ajuizamento',
                        title: str = "Evolução Temporal dos Casos",
                        filename: str = "evolucao_temporal.png") -> Path:
        """
        Plota série temporal de casos.
        
        Args:
            df: DataFrame com dados
            date_column: Nome da coluna de data
            title: Título do gráfico
            filename: Nome do arquivo
            
        Returns:
            Caminho do arquivo salvo
        """
        if date_column not in df.columns:
            logger.error(f"Coluna {date_column} não encontrada")
            return self.output_path / filename
        
        # Filtra dados válidos
        df_valid = df[df[date_column].notna()].copy()
        
        if df_valid.empty:
            logger.warning("Nenhum dado temporal válido encontrado")
            return self.output_path / filename
        
        # Agrupa por mês/ano
        df_valid['periodo'] = df_valid[date_column].dt.to_period('M')
        counts = df_valid['periodo'].value_counts().sort_index()
        
        fig, ax = plt.subplots(figsize=(15, 6))
        
        ax.plot(counts.index.astype(str), counts.values, 
               marker='o', linewidth=2, markersize=4, color=self.colors[0])
        
        ax.set_xlabel('Período')
        ax.set_ylabel('Número de Casos')
        ax.set_title(title)
        
        # Rotaciona labels do eixo X
        plt.xticks(rotation=45, ha='right')
        
        # Adiciona grade
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_file = self.output_path / filename
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Gráfico salvo em: {output_file}")
        return output_file
    
    def create_summary_dashboard(self, stats: Dict[str, Any], 
                               filename: str = "dashboard_summary.png") -> Path:
        """
        Cria um dashboard resumo com múltiplos gráficos.
        
        Args:
            stats: Dicionário com estatísticas compiladas
            filename: Nome do arquivo
            
        Returns:
            Caminho do arquivo salvo
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 15))
        
        # Gráfico 1: Resultados por instância (se disponível)
        if 'resultados_por_instancia' in stats:
            instancia_data = stats['resultados_por_instancia']
            self._plot_mini_results_by_instance(ax1, instancia_data)
        
        # Gráfico 2: Taxa de sucesso (se disponível)
        if 'taxas_sucesso' in stats:
            self._plot_mini_success_rates(ax2, stats['taxas_sucesso'])
        
        # Gráfico 3: Distribuição por tribunal (se disponível)
        if 'distribuicao_tribunais' in stats:
            self._plot_mini_tribunal_dist(ax3, stats['distribuicao_tribunais'])
        
        # Gráfico 4: Top padrões de fluxo (se disponível)
        if 'padroes_fluxo' in stats:
            self._plot_mini_flow_patterns(ax4, stats['padroes_fluxo'])
        
        plt.suptitle('Dashboard de Análise Jurisprudencial', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        output_file = self.output_path / filename
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Dashboard salvo em: {output_file}")
        return output_file
    
    def _plot_mini_results_by_instance(self, ax, data):
        """Helper para gráfico mini de resultados por instância."""
        # Implementação simplificada para o dashboard
        pass
    
    def _plot_mini_success_rates(self, ax, data):
        """Helper para gráfico mini de taxas de sucesso."""
        pass
    
    def _plot_mini_tribunal_dist(self, ax, data):
        """Helper para gráfico mini de distribuição por tribunal."""
        pass
    
    def _plot_mini_flow_patterns(self, ax, data):
        """Helper para gráfico mini de padrões de fluxo."""
        pass