#!/usr/bin/env python3
"""
Script para análise específica de casos de assédio moral na Justiça do Trabalho,
separando-os por instância e resultado conforme códigos de movimento da TPU/CNJ.
"""

import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

class AssedioMoralAnalysis:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.processed_data_path = self.base_path / "data" / "processed"
        self.analysis_output_path = self.base_path / "data" / "analysis"
        self.analysis_output_path.mkdir(parents=True, exist_ok=True)
        
        # Dicionário para mapear códigos de movimento para descrições
        self.movimento_descriptions = {
            219: "Procedência (1ª instância)",
            220: "Improcedência (1ª instância)",
            237: "Provimento (recurso acolhido)",
            242: "Desprovimento (recurso negado)",
            236: "Negação de seguimento (alternativa ao 242)"
        }
        
        # Descrições dos códigos de assunto para assédio moral
        self.assunto_descriptions = {
            1723: "Assédio Moral (Justiça do Trabalho - código tradicional)",
            14175: "Assédio Moral (Justiça Estadual/Federal/Militar - revisão 2022-2024)",
            14018: "Assédio Moral (Rótulo unificado do PJe)"
        }
        
    def load_data(self) -> pd.DataFrame:
        """
        Carrega os dados processados do CSV
        """
        csv_path = self.processed_data_path / "processed_decisions.csv"
        if not csv_path.exists():
            logger.error(f"Arquivo de dados processados não encontrado: {csv_path}")
            return pd.DataFrame()
        
        # Verificar o tamanho do arquivo para carregar de forma otimizada
        file_size_mb = csv_path.stat().st_size / (1024 * 1024)
        logger.info(f"Tamanho do arquivo CSV: {file_size_mb:.2f} MB")
        
        try:
            # Se o arquivo for muito grande, usa opções otimizadas de carregamento
            if file_size_mb > 500:  # Mais de 500MB
                logger.info("Arquivo muito grande, carregando com opções otimizadas...")
                # Carrega apenas as colunas necessárias para análise
                essential_columns = [
                    'tribunal', 'numero_processo', 'data_ajuizamento', 'data_julgamento',
                    'instancia', 'resultado', 'resultado_codigo', 'resultado_binario',
                    'orgao_julgador', 'assunto', 'assunto_codigo', 'mencao_laudo',
                    'duracao_dias'
                ]
                
                # Tenta detectar quais colunas existem no arquivo
                col_sample = pd.read_csv(csv_path, nrows=5)
                available_columns = [col for col in essential_columns if col in col_sample.columns]
                
                # Carrega o dataframe com as colunas disponíveis
                df = pd.read_csv(
                    csv_path, 
                    usecols=available_columns,
                    low_memory=True,
                    dtype={
                        'numero_processo': str,
                        'tribunal': str,
                        'resultado': str,
                        'instancia': str,
                        'assunto': str,
                        'orgao_julgador': str
                    }
                )
            else:
                # Carrega normalmente para arquivos menores
                df = pd.read_csv(csv_path)
                
            # Converte datas
            if 'data_ajuizamento' in df.columns:
                df['data_ajuizamento'] = pd.to_datetime(df['data_ajuizamento'], errors='coerce')
            if 'data_julgamento' in df.columns:
                df['data_julgamento'] = pd.to_datetime(df['data_julgamento'], errors='coerce')
                
            logger.info(f"Carregados {len(df)} registros de {csv_path}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo CSV: {str(e)}")
            # Tenta um método alternativo de carregamento
            logger.info("Tentando método alternativo de carregamento...")
            try:
                # Tenta carregar em chunks para arquivos muito grandes
                chunk_size = 100000
                chunks = []
                for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
                logger.info(f"Carregados {len(df)} registros em chunks de {csv_path}")
                return df
            except Exception as e2:
                logger.error(f"Falha no método alternativo: {str(e2)}")
                return pd.DataFrame()
    
    def filter_by_instancia(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Separa os dados por instância
        """
        # Filtra por instância
        primeira_instancia = df[df['instancia'] == 'Primeira Instância']
        segunda_instancia = df[df['instancia'] == 'Segunda Instância']
        tst = df[df['tribunal'] == 'TST']
        
        result = {
            'primeira_instancia': primeira_instancia,
            'segunda_instancia': segunda_instancia,
            'tst': tst
        }
        
        for key, value in result.items():
            logger.info(f"{key}: {len(value)} registros")
            
        return result
    
    def analyze_primeira_instancia(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analisa decisões de primeira instância (procedentes vs improcedentes)
        """
        if df.empty:
            return {}
            
        # Contagem por resultado
        result_counts = df['resultado'].value_counts().to_dict()
        
        # Percentuais
        total = len(df)
        result_percentages = {k: (v / total) * 100 for k, v in result_counts.items()}
        
        # Análise por tribunal
        by_tribunal = df.groupby(['tribunal', 'resultado']).size().unstack().fillna(0)
        
        # Duração média por resultado
        duration_by_result = df.groupby('resultado')['duracao_dias'].agg(['mean', 'median', 'std']).to_dict()
        
        # Influência do laudo pericial
        laudo_influence = pd.crosstab(
            df['resultado'], 
            df['mencao_laudo'],
            normalize='index'
        ).rename(columns={0: 'Sem Menção a Laudo', 1: 'Com Menção a Laudo'}).to_dict()
        
        # Análise por código de assunto
        if 'assunto_codigo' in df.columns:
            assunto_code_counts = df['assunto_codigo'].value_counts().to_dict()
            
            # Proporção de resultados por código de assunto
            assunto_results = {}
            
            for codigo in [1723, 14175, 14018]:
                if codigo in assunto_code_counts:
                    # Filtra apenas os processos com este código
                    codigo_df = df[df['assunto_codigo'] == codigo]
                    # Conta resultados
                    result_counts = codigo_df['resultado'].value_counts().to_dict()
                    total_codigo = len(codigo_df)
                    result_percentages = {k: (v / total_codigo) * 100 for k, v in result_counts.items()}
                    
                    assunto_results[codigo] = {
                        'nome': self.assunto_descriptions.get(codigo, f"Código {codigo}"),
                        'contagem': assunto_code_counts.get(codigo, 0),
                        'resultados': result_counts,
                        'percentuais': result_percentages
                    }
        else:
            assunto_results = {}
        
        return {
            'contagens': result_counts,
            'percentuais': result_percentages,
            'por_tribunal': by_tribunal,
            'duracao_media': duration_by_result,
            'influencia_laudo': laudo_influence,
            'por_codigo_assunto': assunto_results
        }
    
    def analyze_segunda_instancia(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analisa decisões de segunda instância (recursos providos vs desprovidos)
        """
        if df.empty:
            return {}
            
        # Contagem por resultado
        result_counts = df['resultado'].value_counts().to_dict()
        
        # Percentuais
        total = len(df)
        result_percentages = {k: (v / total) * 100 for k, v in result_counts.items()}
        
        # Análise por tribunal
        by_tribunal = df.groupby(['tribunal', 'resultado']).size().unstack().fillna(0)
        
        # Análise por código de assunto
        if 'assunto_codigo' in df.columns:
            assunto_code_counts = df['assunto_codigo'].value_counts().to_dict()
            
            # Proporção de resultados por código de assunto
            assunto_results = {}
            
            for codigo in [1723, 14175, 14018]:
                if codigo in assunto_code_counts:
                    # Filtra apenas os processos com este código
                    codigo_df = df[df['assunto_codigo'] == codigo]
                    # Conta resultados
                    result_counts = codigo_df['resultado'].value_counts().to_dict()
                    total_codigo = len(codigo_df)
                    result_percentages = {k: (v / total_codigo) * 100 for k, v in result_counts.items()}
                    
                    assunto_results[codigo] = {
                        'nome': self.assunto_descriptions.get(codigo, f"Código {codigo}"),
                        'contagem': assunto_code_counts.get(codigo, 0),
                        'resultados': result_counts,
                        'percentuais': result_percentages
                    }
        else:
            assunto_results = {}
        
        return {
            'contagens': result_counts,
            'percentuais': result_percentages,
            'por_tribunal': by_tribunal,
            'por_codigo_assunto': assunto_results
        }
    
    def analyze_tst(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analisa decisões do TST (recursos providos vs desprovidos)
        """
        if df.empty:
            return {}
            
        # Contagem por resultado
        result_counts = df['resultado'].value_counts().to_dict()
        
        # Percentuais
        total = len(df)
        result_percentages = {k: (v / total) * 100 for k, v in result_counts.items()}
        
        # Análise por órgão julgador
        by_orgao = df.groupby(['orgao_julgador', 'resultado']).size().unstack().fillna(0)
        
        # Análise por código de assunto
        if 'assunto_codigo' in df.columns:
            assunto_code_counts = df['assunto_codigo'].value_counts().to_dict()
            
            # Proporção de resultados por código de assunto
            assunto_results = {}
            
            for codigo in [1723, 14175, 14018]:
                if codigo in assunto_code_counts:
                    # Filtra apenas os processos com este código
                    codigo_df = df[df['assunto_codigo'] == codigo]
                    # Conta resultados
                    result_counts = codigo_df['resultado'].value_counts().to_dict()
                    total_codigo = len(codigo_df)
                    result_percentages = {k: (v / total_codigo) * 100 for k, v in result_counts.items()}
                    
                    assunto_results[codigo] = {
                        'nome': self.assunto_descriptions.get(codigo, f"Código {codigo}"),
                        'contagem': assunto_code_counts.get(codigo, 0),
                        'resultados': result_counts,
                        'percentuais': result_percentages
                    }
        else:
            assunto_results = {}
        
        return {
            'contagens': result_counts,
            'percentuais': result_percentages,
            'por_orgao': by_orgao,
            'por_codigo_assunto': assunto_results
        }
    
    def plot_results(
        self, 
        primeira_instancia: Dict[str, Any],
        segunda_instancia: Dict[str, Any],
        tst: Dict[str, Any]
    ):
        """
        Gera gráficos para visualização dos resultados
        """
        # Configuração de estilo
        sns.set(style="whitegrid")
        
        # Gráfico 1: Resultados por instância
        plt.figure(figsize=(12, 6))
        
        # Primeira instância
        primeira_data = primeira_instancia.get('percentuais', {})
        primeira_labels = list(primeira_data.keys())
        primeira_values = list(primeira_data.values())
        
        # Segunda instância
        segunda_data = segunda_instancia.get('percentuais', {})
        segunda_labels = list(segunda_data.keys())
        segunda_values = list(segunda_data.values())
        
        # TST
        tst_data = tst.get('percentuais', {})
        tst_labels = list(tst_data.keys())
        tst_values = list(tst_data.values())
        
        # Criação do gráfico
        width = 0.25
        x = np.arange(2)  # Resultados positivos e negativos
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Organiza os dados para o gráfico
        primeira_plot_values = [0, 0]
        for i, label in enumerate(primeira_labels):
            if "Procedente" in label:
                primeira_plot_values[0] = primeira_data.get(label, 0)
            elif "Improcedente" in label:
                primeira_plot_values[1] = primeira_data.get(label, 0)
                
        segunda_plot_values = [0, 0]
        for i, label in enumerate(segunda_labels):
            if "Provido" in label:
                segunda_plot_values[0] = segunda_data.get(label, 0)
            elif "Desprovido" in label:
                segunda_plot_values[1] = segunda_data.get(label, 0)
                
        tst_plot_values = [0, 0]
        for i, label in enumerate(tst_labels):
            if "Provido" in label:
                tst_plot_values[0] = tst_data.get(label, 0)
            elif "Desprovido" in label:
                tst_plot_values[1] = tst_data.get(label, 0)
        
        # Plotando as barras
        rects1 = ax.bar(x - width, primeira_plot_values, width, label='1ª Instância')
        rects2 = ax.bar(x, segunda_plot_values, width, label='2ª Instância (TRTs)')
        rects3 = ax.bar(x + width, tst_plot_values, width, label='TST')
        
        # Adiciona rótulos e título
        ax.set_ylabel('Percentual (%)')
        ax.set_title('Resultados por Instância em Casos de Assédio Moral')
        ax.set_xticks(x)
        ax.set_xticklabels(['Favorável ao Trabalhador', 'Desfavorável ao Trabalhador'])
        ax.legend()
        
        # Adiciona valores nas barras
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')
        
        autolabel(rects1)
        autolabel(rects2)
        autolabel(rects3)
        
        plt.tight_layout()
        plt.savefig(self.analysis_output_path / "resultados_por_instancia.png")
        
        # Gráfico 2: Distribuição por tribunal (primeira instância)
        if 'por_tribunal' in primeira_instancia and not primeira_instancia['por_tribunal'].empty:
            plt.figure(figsize=(15, 8))
            primeira_instancia['por_tribunal'].plot(kind='bar', stacked=True)
            plt.title('Resultados de Primeira Instância por Tribunal')
            plt.ylabel('Número de Processos')
            plt.xlabel('Tribunal')
            plt.tight_layout()
            plt.savefig(self.analysis_output_path / "primeira_instancia_por_tribunal.png")
        
        # Gráfico 3: Distribuição por tribunal (segunda instância)
        if 'por_tribunal' in segunda_instancia and not segunda_instancia['por_tribunal'].empty:
            plt.figure(figsize=(15, 8))
            segunda_instancia['por_tribunal'].plot(kind='bar', stacked=True)
            plt.title('Resultados de Segunda Instância por Tribunal')
            plt.ylabel('Número de Processos')
            plt.xlabel('Tribunal')
            plt.tight_layout()
            plt.savefig(self.analysis_output_path / "segunda_instancia_por_tribunal.png")
        
        # Gráfico 4: Influência do laudo pericial
        if 'influencia_laudo' in primeira_instancia:
            plt.figure(figsize=(10, 6))
            laudo_data = primeira_instancia['influencia_laudo']
            
            if isinstance(laudo_data, dict) and laudo_data:
                # Convertendo para DataFrame para facilitar a plotagem
                laudo_df = pd.DataFrame(laudo_data)
                laudo_df.plot(kind='bar')
                plt.title('Influência da Menção a Laudo Pericial no Resultado')
                plt.ylabel('Proporção')
                plt.xlabel('Resultado')
                plt.tight_layout()
                plt.savefig(self.analysis_output_path / "influencia_laudo_pericial.png")
    
    def generate_report(
        self, 
        df: pd.DataFrame,
        primeira_instancia_results: Dict[str, Any],
        segunda_instancia_results: Dict[str, Any],
        tst_results: Dict[str, Any]
    ):
        """
        Gera um relatório em formato markdown com os resultados da análise
        """
        report_path = self.analysis_output_path / "relatorio_assedio_moral.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Relatório de Análise: Assédio Moral na Justiça do Trabalho\n\n")
            
            f.write("## Visão Geral\n\n")
            f.write(f"- Total de processos analisados: {len(df)}\n")
            f.write(f"- Período: {df['data_ajuizamento'].min()} a {df['data_ajuizamento'].max()}\n")
            f.write(f"- Tribunais representados: {len(df['tribunal'].unique())}\n\n")
            
            # Primeira Instância
            f.write("## Primeira Instância\n\n")
            
            if primeira_instancia_results:
                contagens = primeira_instancia_results.get('contagens', {})
                percentuais = primeira_instancia_results.get('percentuais', {})
                
                f.write("### Resultados Gerais\n\n")
                for resultado, count in contagens.items():
                    percent = percentuais.get(resultado, 0)
                    f.write(f"- {resultado}: {count} processos ({percent:.1f}%)\n")
                
                f.write("\n### Duração Média dos Processos\n\n")
                duracao = primeira_instancia_results.get('duracao_media', {})
                for resultado, stats in duracao.items():
                    f.write(f"- {resultado}: {stats.get('mean', 0):.1f} dias em média (mediana: {stats.get('median', 0):.1f} dias)\n")
                
                f.write("\n### Influência de Laudo Pericial\n\n")
                f.write("Proporção de processos com menção a laudo pericial por resultado:\n\n")
                laudo = primeira_instancia_results.get('influencia_laudo', {})
                for resultado, values in laudo.items():
                    com_laudo = values.get('Com Menção a Laudo', 0) * 100
                    sem_laudo = values.get('Sem Menção a Laudo', 0) * 100
                    f.write(f"- {resultado}: {com_laudo:.1f}% com menção a laudo, {sem_laudo:.1f}% sem menção\n")
            else:
                f.write("Nenhum dado disponível para primeira instância.\n\n")
            
            # Segunda Instância
            f.write("\n## Segunda Instância (TRTs)\n\n")
            
            if segunda_instancia_results:
                contagens = segunda_instancia_results.get('contagens', {})
                percentuais = segunda_instancia_results.get('percentuais', {})
                
                f.write("### Resultados Gerais\n\n")
                for resultado, count in contagens.items():
                    percent = percentuais.get(resultado, 0)
                    f.write(f"- {resultado}: {count} processos ({percent:.1f}%)\n")
            else:
                f.write("Nenhum dado disponível para segunda instância.\n\n")
            
            # TST
            f.write("\n## Tribunal Superior do Trabalho (TST)\n\n")
            
            if tst_results:
                contagens = tst_results.get('contagens', {})
                percentuais = tst_results.get('percentuais', {})
                
                f.write("### Resultados Gerais\n\n")
                for resultado, count in contagens.items():
                    percent = percentuais.get(resultado, 0)
                    f.write(f"- {resultado}: {count} processos ({percent:.1f}%)\n")
            else:
                f.write("Nenhum dado disponível para o TST.\n\n")
            
            # Conclusões
            f.write("\n## Conclusões\n\n")
            
            f.write("### Taxas de Sucesso por Instância\n\n")
            
            primeira_taxa = 0
            if primeira_instancia_results and 'percentuais' in primeira_instancia_results:
                for resultado, percent in primeira_instancia_results['percentuais'].items():
                    if "Procedente" in resultado:
                        primeira_taxa = percent
            
            segunda_taxa = 0
            if segunda_instancia_results and 'percentuais' in segunda_instancia_results:
                for resultado, percent in segunda_instancia_results['percentuais'].items():
                    if "Provido" in resultado:
                        segunda_taxa = percent
            
            tst_taxa = 0
            if tst_results and 'percentuais' in tst_results:
                for resultado, percent in tst_results['percentuais'].items():
                    if "Provido" in resultado:
                        tst_taxa = percent
            
            f.write(f"- Taxa de sucesso em primeira instância: {primeira_taxa:.1f}%\n")
            f.write(f"- Taxa de sucesso em segunda instância: {segunda_taxa:.1f}%\n")
            f.write(f"- Taxa de sucesso no TST: {tst_taxa:.1f}%\n\n")
            
            f.write("### Observações Gerais\n\n")
            
            # Determinamos algumas observações baseadas nos dados
            if primeira_taxa > 50:
                f.write("- A maioria dos casos de assédio moral tem resultado favorável em primeira instância\n")
            else:
                f.write("- A minoria dos casos de assédio moral tem resultado favorável em primeira instância\n")
                
            if segunda_taxa > primeira_taxa:
                f.write("- As chances de reforma favorável ao trabalhador aumentam em segunda instância\n")
            else:
                f.write("- As chances de reforma favorável ao trabalhador diminuem em segunda instância\n")
                
            if 'influencia_laudo' in primeira_instancia_results:
                laudo = primeira_instancia_results.get('influencia_laudo', {})
                impacto_positivo = True
                for resultado, values in laudo.items():
                    if "Procedente" in resultado and values.get('Com Menção a Laudo', 0) < values.get('Sem Menção a Laudo', 0):
                        impacto_positivo = False
                
                if impacto_positivo:
                    f.write("- A presença de laudo pericial tende a aumentar as chances de procedência\n")
                else:
                    f.write("- A presença de laudo pericial não demonstrou impacto significativo nas chances de procedência\n")
            
            # Adiciona análise de códigos de assunto ao relatório
            f.write("\n## Análise por Código de Assunto do CNJ\n\n")
            
            # Primeira instância
            if primeira_instancia_results and 'por_codigo_assunto' in primeira_instancia_results:
                f.write("### Primeira Instância\n\n")
                for codigo, dados in primeira_instancia_results['por_codigo_assunto'].items():
                    f.write(f"**{dados['nome']} (Código {codigo})**\n\n")
                    f.write(f"- Total de processos: {dados['contagem']}\n")
                    for resultado, count in dados['resultados'].items():
                        percent = dados['percentuais'].get(resultado, 0)
                        f.write(f"- {resultado}: {count} processos ({percent:.1f}%)\n")
                    f.write("\n")
            
            # Segunda instância
            if segunda_instancia_results and 'por_codigo_assunto' in segunda_instancia_results:
                f.write("### Segunda Instância\n\n")
                for codigo, dados in segunda_instancia_results['por_codigo_assunto'].items():
                    f.write(f"**{dados['nome']} (Código {codigo})**\n\n")
                    f.write(f"- Total de processos: {dados['contagem']}\n")
                    for resultado, count in dados['resultados'].items():
                        percent = dados['percentuais'].get(resultado, 0)
                        f.write(f"- {resultado}: {count} processos ({percent:.1f}%)\n")
                    f.write("\n")
            
            # TST
            if tst_results and 'por_codigo_assunto' in tst_results:
                f.write("### TST\n\n")
                for codigo, dados in tst_results['por_codigo_assunto'].items():
                    f.write(f"**{dados['nome']} (Código {codigo})**\n\n")
                    f.write(f"- Total de processos: {dados['contagem']}\n")
                    for resultado, count in dados['resultados'].items():
                        percent = dados['percentuais'].get(resultado, 0)
                        f.write(f"- {resultado}: {count} processos ({percent:.1f}%)\n")
                    f.write("\n")
            
            f.write("\n## Notas Metodológicas\n\n")
            f.write("### Códigos de Movimento\n\n")
            f.write("Esta análise foi baseada nos seguintes códigos de movimentos processuais da Tabela Processual Unificada do CNJ:\n\n")
            f.write("- 219: Procedência (primeira instância)\n")
            f.write("- 220: Improcedência (primeira instância)\n")
            f.write("- 237: Provimento de recurso\n")
            f.write("- 242: Desprovimento de recurso\n")
            f.write("- 236: Negação de seguimento (alternativa ao 242 em alguns tribunais)\n\n")
            
            f.write("### Códigos de Assunto\n\n")
            f.write("Foram utilizados os seguintes códigos de assunto da Tabela Processual Unificada do CNJ:\n\n")
            f.write("- 1723: Assédio Moral (código tradicional da Justiça do Trabalho)\n")
            f.write("- 14175: Assédio Moral (introduzido na revisão de 2022-2024 para tribunais estaduais, federais e militares)\n")
            f.write("- 14018: Assédio Moral (rótulo unificado adotado nas versões mais recentes do PJe)\n\n")
            
            f.write("Relatório gerado em: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        logger.info(f"Relatório gerado em {report_path}")
        return report_path
    
    def run_analysis(self):
        """
        Executa toda a análise
        """
        # Carrega dados
        df = self.load_data()
        if df.empty:
            logger.error("Nenhum dado para analisar")
            return
        
        # Separa por instância
        dfs_by_instancia = self.filter_by_instancia(df)
        
        # Analisa cada instância
        primeira_instancia_results = self.analyze_primeira_instancia(dfs_by_instancia['primeira_instancia'])
        segunda_instancia_results = self.analyze_segunda_instancia(dfs_by_instancia['segunda_instancia'])
        tst_results = self.analyze_tst(dfs_by_instancia['tst'])
        
        # Gera visualizações
        self.plot_results(primeira_instancia_results, segunda_instancia_results, tst_results)
        
        # Gera relatório
        report_path = self.generate_report(
            df, 
            primeira_instancia_results, 
            segunda_instancia_results, 
            tst_results
        )
        
        return {
            'primeira_instancia': primeira_instancia_results,
            'segunda_instancia': segunda_instancia_results,
            'tst': tst_results,
            'report_path': report_path
        }

def main():
    analyzer = AssedioMoralAnalysis()
    results = analyzer.run_analysis()
    
    if results and 'report_path' in results:
        logger.info(f"Análise concluída. Relatório disponível em: {results['report_path']}")
    else:
        logger.error("Falha ao executar análise")

if __name__ == "__main__":
    main()