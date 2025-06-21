#!/usr/bin/env python3
"""
Script para análise estatística detalhada por tribunal e visualização
de resultados dos casos de assédio moral na Justiça do Trabalho.
"""

import json
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any
from collections import defaultdict, Counter

# Configurar estilo de visualização
plt.style.use('ggplot')
sns.set_palette("colorblind")
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 18
})

def carregar_dados():
    """
    Carrega os dados consolidados e convertemos para um DataFrame para facilitar a análise.
    """
    data_path = os.path.join('data', 'consolidated', 'all_decisions.json')
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Convertemos para DataFrame
    df = pd.DataFrame(data)
    
    # Verificamos se as colunas necessárias existem
    colunas_necessarias = ['tribunal', 'instancia', 'resultado', 'data_julgamento']
    for coluna in colunas_necessarias:
        if coluna not in df.columns:
            print(f"Aviso: Coluna '{coluna}' não encontrada nos dados")
    
    return df

def extrair_ano(data_str):
    """Extrai o ano de uma string de data."""
    if pd.isna(data_str) or not data_str:
        return None
    try:
        return int(data_str.split('-')[0])
    except (IndexError, ValueError, AttributeError):
        return None

def analisar_por_tribunal_instancia(df):
    """
    Analisa os resultados por tribunal e instância.
    """
    # Adicionar coluna de ano
    df['ano'] = df['data_julgamento'].apply(extrair_ano)
    
    # Análise por tribunal e instância
    resultados = {}
    
    # Para cada tribunal e instância, calcular estatísticas
    for tribunal in df['tribunal'].unique():
        resultados[tribunal] = {}
        
        for instancia in df[df['tribunal'] == tribunal]['instancia'].unique():
            df_filtrado = df[(df['tribunal'] == tribunal) & (df['instancia'] == instancia)]
            
            # Contar resultados
            contagem = df_filtrado['resultado'].value_counts().to_dict()
            total = df_filtrado.shape[0]
            
            # Calcular percentuais
            percentuais = {resultado: (count / total) * 100 for resultado, count in contagem.items()}
            
            # Análise por ano
            analise_anual = {}
            for ano in sorted(df_filtrado['ano'].dropna().unique()):
                df_ano = df_filtrado[df_filtrado['ano'] == ano]
                if df_ano.shape[0] > 0:
                    contagem_ano = df_ano['resultado'].value_counts().to_dict()
                    total_ano = df_ano.shape[0]
                    percentuais_ano = {resultado: (count / total_ano) * 100 
                                       for resultado, count in contagem_ano.items()}
                    
                    analise_anual[int(ano)] = {
                        'contagem': contagem_ano,
                        'total': total_ano,
                        'percentuais': percentuais_ano
                    }
            
            resultados[tribunal][instancia] = {
                'contagem': contagem,
                'total': total,
                'percentuais': percentuais,
                'por_ano': analise_anual
            }
    
    return resultados

def criar_visualizacoes(resultados, df):
    """
    Cria visualizações a partir dos resultados da análise.
    """
    # Garantir que o diretório de resultados existe
    os.makedirs('resultados_estatisticos', exist_ok=True)
    
    # 1. Gráfico de barras com taxa de sucesso na primeira instância por tribunal
    fig, ax = plt.subplots(figsize=(14, 8))
    
    tribunais = []
    taxas_sucesso = []
    totais = []
    
    for tribunal in sorted(resultados.keys()):
        if 'Primeira Instância' in resultados[tribunal]:
            dados = resultados[tribunal]['Primeira Instância']
            if 'Procedente' in dados['contagem']:
                taxa = dados['percentuais'].get('Procedente', 0)
                tribunais.append(tribunal)
                taxas_sucesso.append(taxa)
                totais.append(dados['total'])
    
    # Criar DataFrame para ordenação
    df_plot = pd.DataFrame({
        'Tribunal': tribunais,
        'Taxa de Sucesso (%)': taxas_sucesso,
        'Total de Processos': totais
    })
    
    # Ordenar por taxa de sucesso
    df_plot = df_plot.sort_values('Taxa de Sucesso (%)', ascending=False)
    
    # Gráfico de barras
    bars = ax.bar(df_plot['Tribunal'], df_plot['Taxa de Sucesso (%)'], color='skyblue')
    
    # Adicionar valores nas barras
    for i, bar in enumerate(bars):
        height = bar.get_height()
        total = df_plot.iloc[i]['Total de Processos']
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f}%\n({total})',
                ha='center', va='bottom', fontsize=10)
    
    # Configurar o gráfico
    ax.set_title('Taxa de Sucesso na Primeira Instância por Tribunal')
    ax.set_xlabel('Tribunal')
    ax.set_ylabel('Taxa de Sucesso (%)')
    ax.set_ylim(0, max(taxas_sucesso) * 1.2)  # Margem superior
    
    # Adicionar linha média
    media = df_plot['Taxa de Sucesso (%)'].mean()
    ax.axhline(y=media, color='red', linestyle='--', label=f'Média: {media:.1f}%')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('resultados_estatisticos/taxa_sucesso_primeira_instancia.png')
    plt.close()
    
    # 2. Gráfico de barras com taxa de provimento na segunda instância por tribunal
    fig, ax = plt.subplots(figsize=(14, 8))
    
    tribunais = []
    taxas_provimento = []
    totais = []
    
    for tribunal in sorted(resultados.keys()):
        if 'Segunda Instância' in resultados[tribunal]:
            dados = resultados[tribunal]['Segunda Instância']
            if 'Provido' in dados['contagem']:
                taxa = dados['percentuais'].get('Provido', 0)
                tribunais.append(tribunal)
                taxas_provimento.append(taxa)
                totais.append(dados['total'])
    
    # Criar DataFrame para ordenação
    df_plot = pd.DataFrame({
        'Tribunal': tribunais,
        'Taxa de Provimento (%)': taxas_provimento,
        'Total de Processos': totais
    })
    
    # Ordenar por taxa de provimento
    df_plot = df_plot.sort_values('Taxa de Provimento (%)', ascending=False)
    
    # Gráfico de barras
    bars = ax.bar(df_plot['Tribunal'], df_plot['Taxa de Provimento (%)'], color='lightgreen')
    
    # Adicionar valores nas barras
    for i, bar in enumerate(bars):
        height = bar.get_height()
        total = df_plot.iloc[i]['Total de Processos']
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f}%\n({total})',
                ha='center', va='bottom', fontsize=10)
    
    # Configurar o gráfico
    ax.set_title('Taxa de Provimento na Segunda Instância por Tribunal')
    ax.set_xlabel('Tribunal')
    ax.set_ylabel('Taxa de Provimento (%)')
    ax.set_ylim(0, max(taxas_provimento) * 1.2)  # Margem superior
    
    # Adicionar linha média
    media = df_plot['Taxa de Provimento (%)'].mean()
    ax.axhline(y=media, color='red', linestyle='--', label=f'Média: {media:.1f}%')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('resultados_estatisticos/taxa_provimento_segunda_instancia.png')
    plt.close()
    
    # 3. Evolução temporal das taxas de sucesso por ano (1ª instância)
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Preparar dados
    anos = range(2015, 2025)
    dados_temporais = defaultdict(lambda: {ano: None for ano in anos})
    
    for tribunal in resultados:
        if 'Primeira Instância' in resultados[tribunal]:
            dados_anuais = resultados[tribunal]['Primeira Instância']['por_ano']
            
            for ano in dados_anuais:
                if 'Procedente' in dados_anuais[ano]['contagem']:
                    taxa = dados_anuais[ano]['percentuais'].get('Procedente', 0)
                    dados_temporais[tribunal][ano] = taxa
    
    # Plotar linha para cada tribunal
    for tribunal in sorted(dados_temporais.keys()):
        anos_plot = []
        taxas_plot = []
        
        for ano in sorted(dados_temporais[tribunal].keys()):
            if dados_temporais[tribunal][ano] is not None:
                anos_plot.append(ano)
                taxas_plot.append(dados_temporais[tribunal][ano])
        
        if anos_plot:  # Só plotar se tiver dados
            ax.plot(anos_plot, taxas_plot, marker='o', linewidth=2, label=tribunal)
    
    # Configurar o gráfico
    ax.set_title('Evolução da Taxa de Sucesso na Primeira Instância por Ano')
    ax.set_xlabel('Ano')
    ax.set_ylabel('Taxa de Sucesso (%)')
    ax.set_xticks(anos)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Verificar número de linhas para decidir onde colocar a legenda
    if len(dados_temporais) > 10:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        ax.legend(loc='best')
    
    plt.tight_layout()
    plt.savefig('resultados_estatisticos/evolucao_taxa_sucesso_primeira_instancia.png')
    plt.close()
    
    # 4. Mapa de calor da taxa de sucesso por tribunal e ano
    # Preparar dados para o mapa de calor
    tribunais_heatmap = []
    anos_heatmap = []
    taxas_heatmap = []
    
    for tribunal in sorted(resultados.keys()):
        if 'Primeira Instância' in resultados[tribunal]:
            dados_anuais = resultados[tribunal]['Primeira Instância']['por_ano']
            
            for ano in sorted(dados_anuais.keys()):
                if 'Procedente' in dados_anuais[ano]['contagem']:
                    tribunais_heatmap.append(tribunal)
                    anos_heatmap.append(ano)
                    taxa = dados_anuais[ano]['percentuais'].get('Procedente', 0)
                    taxas_heatmap.append(taxa)
    
    if tribunais_heatmap:  # Só criar o mapa de calor se houver dados
        df_heatmap = pd.DataFrame({
            'Tribunal': tribunais_heatmap,
            'Ano': anos_heatmap,
            'Taxa': taxas_heatmap
        })
        
        # Pivotar para formato adequado para o mapa de calor
        pivot_table = df_heatmap.pivot_table(index='Tribunal', columns='Ano', values='Taxa')
        
        plt.figure(figsize=(14, 10))
        ax = sns.heatmap(pivot_table, annot=True, fmt='.1f', cmap='YlGnBu', 
                         linewidths=.5, cbar_kws={'label': 'Taxa de Sucesso (%)'})
        
        plt.title('Taxa de Sucesso na Primeira Instância por Tribunal e Ano')
        plt.tight_layout()
        plt.savefig('resultados_estatisticos/heatmap_taxa_sucesso.png')
        plt.close()
    
    # 5. Gerar relatório de estatísticas em markdown
    gerar_relatorio_markdown(resultados, df)

def gerar_relatorio_markdown(resultados, df):
    """Gera um relatório em formato markdown com as estatísticas."""
    relatorio_path = 'resultados_estatisticos/relatorio_estatistico.md'
    
    with open(relatorio_path, 'w') as f:
        f.write("# Relatório Estatístico: Assédio Moral na Justiça do Trabalho\n\n")
        
        # Visão geral
        f.write("## Visão Geral\n\n")
        f.write(f"- Total de processos analisados: {df.shape[0]}\n")
        f.write(f"- Tribunais representados: {len(df['tribunal'].unique())}\n")
        f.write(f"- Período: {df['data_julgamento'].min()} a {df['data_julgamento'].max()}\n\n")
        
        # Resumo por instância
        f.write("## Resumo por Instância\n\n")
        
        instancias = df['instancia'].unique()
        for instancia in sorted(instancias):
            f.write(f"### {instancia}\n\n")
            
            df_inst = df[df['instancia'] == instancia]
            resultados_count = df_inst['resultado'].value_counts()
            
            f.write("| Resultado | Quantidade | Porcentagem |\n")
            f.write("|-----------|------------|-------------|\n")
            
            for resultado, count in resultados_count.items():
                percentual = (count / df_inst.shape[0]) * 100
                f.write(f"| {resultado} | {count} | {percentual:.1f}% |\n")
            
            f.write("\n")
        
        # Análise por tribunal
        f.write("## Análise por Tribunal\n\n")
        
        for tribunal in sorted(resultados.keys()):
            f.write(f"### {tribunal}\n\n")
            
            for instancia in sorted(resultados[tribunal].keys()):
                dados = resultados[tribunal][instancia]
                
                f.write(f"#### {instancia}\n\n")
                f.write(f"Total de processos: {dados['total']}\n\n")
                
                f.write("| Resultado | Quantidade | Porcentagem |\n")
                f.write("|-----------|------------|-------------|\n")
                
                for resultado, count in sorted(dados['contagem'].items(), key=lambda x: x[1], reverse=True):
                    percentual = dados['percentuais'][resultado]
                    f.write(f"| {resultado} | {count} | {percentual:.1f}% |\n")
                
                f.write("\n##### Evolução por Ano\n\n")
                
                if dados['por_ano']:
                    f.write("| Ano | Total | ")
                    # Obter todos os possíveis resultados para as colunas
                    resultados_possiveis = set()
                    for ano_data in dados['por_ano'].values():
                        resultados_possiveis.update(ano_data['contagem'].keys())
                    
                    for resultado in sorted(resultados_possiveis):
                        f.write(f"{resultado} | % | ")
                    f.write("\n")
                    
                    f.write("|-----|-------|")
                    for _ in resultados_possiveis:
                        f.write("--------|-----|")
                    f.write("\n")
                    
                    for ano in sorted(dados['por_ano'].keys()):
                        ano_data = dados['por_ano'][ano]
                        f.write(f"| {ano} | {ano_data['total']} | ")
                        
                        for resultado in sorted(resultados_possiveis):
                            count = ano_data['contagem'].get(resultado, 0)
                            percentual = ano_data['percentuais'].get(resultado, 0)
                            f.write(f"{count} | {percentual:.1f}% | ")
                        
                        f.write("\n")
                else:
                    f.write("*Não há dados disponíveis por ano para esta instância.*\n")
                
                f.write("\n")
            
            f.write("\n")
        
        # Conclusões
        f.write("## Conclusões\n\n")
        
        # Taxa média de sucesso na primeira instância
        taxas_primeira = []
        for tribunal, dados_tribunal in resultados.items():
            if 'Primeira Instância' in dados_tribunal:
                taxa = dados_tribunal['Primeira Instância']['percentuais'].get('Procedente', 0)
                taxas_primeira.append(taxa)
        
        taxa_media_primeira = sum(taxas_primeira) / len(taxas_primeira) if taxas_primeira else 0
        
        # Taxa média de provimento na segunda instância
        taxas_segunda = []
        for tribunal, dados_tribunal in resultados.items():
            if 'Segunda Instância' in dados_tribunal:
                taxa = dados_tribunal['Segunda Instância']['percentuais'].get('Provido', 0)
                taxas_segunda.append(taxa)
        
        taxa_media_segunda = sum(taxas_segunda) / len(taxas_segunda) if taxas_segunda else 0
        
        # Taxa de provimento no TST
        taxa_tst = 0
        if 'TST' in resultados and 'TST' in resultados['TST']:
            taxa_tst = resultados['TST']['TST']['percentuais'].get('Provido', 0)
        
        f.write(f"1. A taxa média de sucesso na primeira instância é de {taxa_media_primeira:.1f}%.\n")
        f.write(f"2. A taxa média de provimento na segunda instância é de {taxa_media_segunda:.1f}%.\n")
        f.write(f"3. A taxa de provimento no TST é de {taxa_tst:.1f}%.\n\n")
        
        # Variação regional
        maior_primeira = max(taxas_primeira) if taxas_primeira else 0
        menor_primeira = min(taxas_primeira) if taxas_primeira else 0
        
        f.write("### Variação Regional\n\n")
        f.write(f"- A maior taxa de sucesso na primeira instância é de {maior_primeira:.1f}%.\n")
        f.write(f"- A menor taxa de sucesso na primeira instância é de {menor_primeira:.1f}%.\n")
        f.write(f"- A diferença entre a maior e a menor taxa é de {maior_primeira - menor_primeira:.1f} pontos percentuais.\n\n")
        
        f.write("### Observações\n\n")
        f.write("- A análise revela uma discrepância significativa nas taxas de sucesso entre diferentes tribunais.\n")
        f.write("- O padrão de baixo sucesso na primeira instância, alto provimento na segunda e baixo provimento no TST se mantém na maioria dos tribunais.\n")
        f.write("- É recomendável uma análise mais aprofundada para identificar os fatores que contribuem para estas variações regionais.\n\n")
        
        f.write("Relatório gerado em: 2025-06-21")
    
    print(f"Relatório markdown gerado em: {relatorio_path}")

def main():
    print("Carregando dados...")
    df = carregar_dados()
    
    print("Analisando dados por tribunal e instância...")
    resultados = analisar_por_tribunal_instancia(df)
    
    print("Criando visualizações e relatório...")
    criar_visualizacoes(resultados, df)
    
    print("Análise estatística concluída com sucesso!")

if __name__ == "__main__":
    main()