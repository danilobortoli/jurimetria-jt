#!/usr/bin/env python3
"""
Script para análise avançada do fluxo de processos de assédio moral 
através das instâncias da Justiça do Trabalho.

Este script implementa métodos mais sofisticados para rastrear o mesmo
processo através das diferentes instâncias (1ª instância, 2ª instância, TST).
"""

import json
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from tqdm import tqdm
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Set, Optional

# Diretório para salvar os resultados
RESULTS_DIR = 'resultados_fluxo'
os.makedirs(RESULTS_DIR, exist_ok=True)

# Configuração para visualizações
plt.style.use('ggplot')
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 18
})

def extrair_numero_processo(num_proc: str) -> Dict[str, str]:
    """
    Extrai os componentes de um número de processo no formato CNJ.
    
    Formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
    onde:
    - NNNNNNN: Número sequencial do processo
    - DD: Dígito verificador
    - AAAA: Ano de ajuizamento
    - J: Segmento da Justiça (8 para Trabalho)
    - TR: Tribunal
    - OOOO: Órgão de origem
    
    Returns:
        Dict com os componentes do número.
    """
    # Remover caracteres não numéricos para normalização inicial
    num_limpo = re.sub(r'\D', '', num_proc)
    
    # Tentar extrair os componentes usando regex para formato CNJ
    cnj_pattern = r'(\d{7})(\d{2})(\d{4})(\d)(\d{2})(\d{4})'
    match = re.search(cnj_pattern, num_limpo)
    
    if match:
        return {
            'sequencial': match.group(1),
            'digito': match.group(2),
            'ano': match.group(3),
            'segmento': match.group(4),
            'tribunal': match.group(5),
            'origem': match.group(6),
            'numero_completo': num_limpo
        }
    
    # Se não conseguir extrair no formato CNJ, retornar formato básico
    return {
        'numero_completo': num_limpo,
        'numero_simplificado': num_limpo[:14] if len(num_limpo) >= 14 else num_limpo
    }

def calcular_similaridade(num1: str, num2: str) -> float:
    """
    Calcula a similaridade entre dois números de processo.
    
    Args:
        num1: Primeiro número de processo
        num2: Segundo número de processo
    
    Returns:
        Pontuação de similaridade entre 0 e 1
    """
    # Extrair componentes
    comp1 = extrair_numero_processo(num1)
    comp2 = extrair_numero_processo(num2)
    
    # Se ambos têm componentes CNJ, comparar componentes
    if all(k in comp1 for k in ['sequencial', 'ano']) and all(k in comp2 for k in ['sequencial', 'ano']):
        # Maior peso para sequencial e ano iguais
        peso_total = 0
        pontuacao = 0
        
        # Sequencial (peso 5)
        if comp1['sequencial'] == comp2['sequencial']:
            pontuacao += 5
        peso_total += 5
        
        # Ano (peso 3)
        if comp1['ano'] == comp2['ano']:
            pontuacao += 3
        peso_total += 3
        
        # Segmento (peso 1)
        if 'segmento' in comp1 and 'segmento' in comp2:
            if comp1['segmento'] == comp2['segmento']:
                pontuacao += 1
        peso_total += 1
        
        # Tribunal e origem têm menor peso, pois mudam entre instâncias
        
        return pontuacao / peso_total
    
    # Caso contrário, usar comparação simplificada de substrings
    num1_clean = re.sub(r'\D', '', num1)
    num2_clean = re.sub(r'\D', '', num2)
    
    # Encontrar a maior substring comum
    len1, len2 = len(num1_clean), len(num2_clean)
    
    # Matriz para programação dinâmica
    matriz = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    max_len = 0
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if num1_clean[i-1] == num2_clean[j-1]:
                matriz[i][j] = matriz[i-1][j-1] + 1
                max_len = max(max_len, matriz[i][j])
    
    # Normalizar pelo tamanho do menor número
    return max_len / min(len1, len2)

def identificar_casos_relacionados(data: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    Identifica processos que provavelmente são o mesmo caso em diferentes instâncias.
    
    Args:
        data: Lista de decisões judiciais
    
    Returns:
        Lista de grupos de decisões relacionadas
    """
    print("Identificando casos relacionados...")
    
    # Agrupar por tribunal e instância
    casos_por_tribunal_instancia = defaultdict(list)
    for decisao in data:
        tribunal = decisao.get('tribunal', '')
        instancia = decisao.get('instancia', '')
        if tribunal and instancia:
            casos_por_tribunal_instancia[(tribunal, instancia)].append(decisao)
    
    # Criar dicionário com apenas o número do processo como chave para busca rápida
    num_processo_para_decisao = {}
    for decisao in data:
        num_proc = decisao.get('numero_processo', '')
        if num_proc:
            # Se houver colisão, manter a decisão mais recente
            if num_proc in num_processo_para_decisao:
                data_atual = decisao.get('data_julgamento', '')
                data_existente = num_processo_para_decisao[num_proc].get('data_julgamento', '')
                if data_atual > data_existente:
                    num_processo_para_decisao[num_proc] = decisao
            else:
                num_processo_para_decisao[num_proc] = decisao
    
    # Criar grupos iniciais baseados em números exatamente iguais
    grupos = []
    decisoes_processadas = set()
    
    # Primeiro passo: agrupar por números exatamente iguais
    for decisao in tqdm(data, desc="Agrupando processos idênticos"):
        num_proc = decisao.get('numero_processo', '')
        if not num_proc or id(decisao) in decisoes_processadas:
            continue
        
        grupo = [decisao]
        decisoes_processadas.add(id(decisao))
        
        # Procurar correspondências exatas (mesmo número em diferentes tribunais)
        for outra_decisao in data:
            if id(outra_decisao) not in decisoes_processadas and outra_decisao.get('numero_processo', '') == num_proc:
                grupo.append(outra_decisao)
                decisoes_processadas.add(id(outra_decisao))
        
        if len(grupo) > 1:  # Só adicionar grupos com mais de uma decisão
            grupos.append(grupo)
    
    # Segundo passo: tentar agrupar usando a similaridade para processos ainda não agrupados
    processos_primeira_instancia = [d for d in data if d.get('instancia') == 'Primeira Instância' 
                                   and id(d) not in decisoes_processadas]
    processos_segunda_instancia = [d for d in data if d.get('instancia') == 'Segunda Instância' 
                                  and id(d) not in decisoes_processadas]
    processos_tst = [d for d in data if d.get('instancia') == 'TST' 
                    and id(d) not in decisoes_processadas]
    
    # Tentar conectar processos de primeira instância com segunda instância
    for proc_primeira in tqdm(processos_primeira_instancia, desc="Conectando 1ª e 2ª instância"):
        num_proc_primeira = proc_primeira.get('numero_processo', '')
        if not num_proc_primeira:
            continue
        
        comp_primeira = extrair_numero_processo(num_proc_primeira)
        
        # Características importantes para correspondência
        ano_primeira = comp_primeira.get('ano', '')
        seq_primeira = comp_primeira.get('sequencial', '')
        
        melhores_correspondencias = []
        
        for proc_segunda in processos_segunda_instancia:
            num_proc_segunda = proc_segunda.get('numero_processo', '')
            if not num_proc_segunda:
                continue
            
            comp_segunda = extrair_numero_processo(num_proc_segunda)
            
            # Verificar se ano e sequencial correspondem
            if (comp_segunda.get('ano', '') == ano_primeira and 
                comp_segunda.get('sequencial', '') == seq_primeira):
                similaridade = 1.0  # Correspondência perfeita de componentes-chave
            else:
                # Calcular similaridade para casos sem correspondência perfeita
                similaridade = calcular_similaridade(num_proc_primeira, num_proc_segunda)
            
            if similaridade >= 0.8:  # Limiar de similaridade
                melhores_correspondencias.append((proc_segunda, similaridade))
        
        # Ordenar por similaridade e selecionar a melhor correspondência
        if melhores_correspondencias:
            melhores_correspondencias.sort(key=lambda x: x[1], reverse=True)
            melhor_proc_segunda, _ = melhores_correspondencias[0]
            
            # Criar novo grupo
            grupo = [proc_primeira, melhor_proc_segunda]
            decisoes_processadas.add(id(proc_primeira))
            decisoes_processadas.add(id(melhor_proc_segunda))
            
            # Tentar encontrar correspondência no TST
            num_proc_segunda = melhor_proc_segunda.get('numero_processo', '')
            comp_segunda = extrair_numero_processo(num_proc_segunda)
            
            melhores_correspondencias_tst = []
            
            for proc_tst in processos_tst:
                num_proc_tst = proc_tst.get('numero_processo', '')
                if not num_proc_tst:
                    continue
                
                similaridade = calcular_similaridade(num_proc_segunda, num_proc_tst)
                if similaridade >= 0.8:
                    melhores_correspondencias_tst.append((proc_tst, similaridade))
            
            # Adicionar melhor correspondência do TST, se existir
            if melhores_correspondencias_tst:
                melhores_correspondencias_tst.sort(key=lambda x: x[1], reverse=True)
                melhor_proc_tst, _ = melhores_correspondencias_tst[0]
                grupo.append(melhor_proc_tst)
                decisoes_processadas.add(id(melhor_proc_tst))
            
            grupos.append(grupo)
    
    # Tentar conectar pares de segunda instância e TST ainda não processados
    for proc_segunda in tqdm(processos_segunda_instancia, desc="Conectando 2ª instância e TST"):
        if id(proc_segunda) in decisoes_processadas:
            continue
        
        num_proc_segunda = proc_segunda.get('numero_processo', '')
        if not num_proc_segunda:
            continue
        
        comp_segunda = extrair_numero_processo(num_proc_segunda)
        
        melhores_correspondencias = []
        
        for proc_tst in processos_tst:
            if id(proc_tst) in decisoes_processadas:
                continue
                
            num_proc_tst = proc_tst.get('numero_processo', '')
            if not num_proc_tst:
                continue
            
            similaridade = calcular_similaridade(num_proc_segunda, num_proc_tst)
            if similaridade >= 0.8:
                melhores_correspondencias.append((proc_tst, similaridade))
        
        if melhores_correspondencias:
            melhores_correspondencias.sort(key=lambda x: x[1], reverse=True)
            melhor_proc_tst, _ = melhores_correspondencias[0]
            
            grupo = [proc_segunda, melhor_proc_tst]
            decisoes_processadas.add(id(proc_segunda))
            decisoes_processadas.add(id(melhor_proc_tst))
            
            grupos.append(grupo)
    
    # Ordenar decisões dentro de cada grupo por instância
    ordem_instancia = {'Primeira Instância': 1, 'Segunda Instância': 2, 'TST': 3}
    
    for i, grupo in enumerate(grupos):
        grupos[i] = sorted(grupo, key=lambda x: ordem_instancia.get(x.get('instancia', ''), 99))
    
    return grupos

def analisar_fluxo_decisoes(grupos_relacionados: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Analisa o fluxo de decisões nos grupos de casos relacionados.
    
    Args:
        grupos_relacionados: Lista de grupos de decisões relacionadas
    
    Returns:
        Dicionário com estatísticas e padrões de fluxo
    """
    print("Analisando fluxo de decisões...")
    
    # Contadores para diferentes padrões de fluxo
    padroes_fluxo = Counter()
    transicoes = Counter()
    
    # Taxas de sucesso por instância no fluxo
    taxas_sucesso = {
        'primeira_instancia': {'favoravel': 0, 'desfavoravel': 0},
        'segunda_instancia': {'favoravel': 0, 'desfavoravel': 0},
        'tst': {'favoravel': 0, 'desfavoravel': 0}
    }
    
    # Contadores para análise de recursos
    recursos_trabalhador = {'sucesso': 0, 'fracasso': 0}
    recursos_empregador = {'sucesso': 0, 'fracasso': 0}
    
    # Contadores para resultados finais
    resultados_finais = Counter()
    
    # Analisar cada grupo de decisões relacionadas
    for grupo in tqdm(grupos_relacionados, desc="Analisando fluxos"):
        # Ignorar grupos com apenas uma decisão
        if len(grupo) <= 1:
            continue
        
        # Classificar decisões por instância para fácil acesso
        decisoes_por_instancia = {}
        for decisao in grupo:
            instancia = decisao.get('instancia', '')
            if instancia:
                decisoes_por_instancia[instancia] = decisao
        
        # Construir o padrão de fluxo
        sequencia = []
        for decisao in grupo:
            instancia = decisao.get('instancia', '')
            resultado = decisao.get('resultado', '')
            if instancia and resultado:
                sequencia.append(f"{instancia}:{resultado}")
        
        padrao = " -> ".join(sequencia)
        padroes_fluxo[padrao] += 1
        
        # Analisar transições entre instâncias
        for i in range(len(grupo) - 1):
            decisao_atual = grupo[i]
            decisao_seguinte = grupo[i + 1]
            
            instancia_atual = decisao_atual.get('instancia', '')
            resultado_atual = decisao_atual.get('resultado', '')
            
            instancia_seguinte = decisao_seguinte.get('instancia', '')
            resultado_seguinte = decisao_seguinte.get('resultado', '')
            
            transicao = f"{instancia_atual}:{resultado_atual} -> {instancia_seguinte}:{resultado_seguinte}"
            transicoes[transicao] += 1
            
            # Analisar recursos com base nas transições
            if instancia_atual == 'Primeira Instância' and instancia_seguinte == 'Segunda Instância':
                # Recurso do trabalhador contra decisão desfavorável
                if resultado_atual == 'Improcedente':
                    if resultado_seguinte == 'Provido':
                        recursos_trabalhador['sucesso'] += 1
                    else:
                        recursos_trabalhador['fracasso'] += 1
                # Recurso do empregador contra decisão favorável ao trabalhador
                elif resultado_atual == 'Procedente':
                    if resultado_seguinte == 'Provido':
                        recursos_empregador['sucesso'] += 1
                    else:
                        recursos_empregador['fracasso'] += 1
            
            # Transições de segunda instância para TST
            elif instancia_atual == 'Segunda Instância' and instancia_seguinte == 'TST':
                # Aqui a análise é mais complexa, precisamos conhecer o histórico
                if 'Primeira Instância' in decisoes_por_instancia:
                    resultado_primeira = decisoes_por_instancia['Primeira Instância'].get('resultado', '')
                    
                    # Caso 1: Trabalhador ganhou em primeira, perdeu em segunda, recorre ao TST
                    if resultado_primeira == 'Procedente' and resultado_atual == 'Provido':
                        if resultado_seguinte == 'Provido':
                            recursos_trabalhador['sucesso'] += 1
                        else:
                            recursos_trabalhador['fracasso'] += 1
                    
                    # Caso 2: Trabalhador perdeu em primeira, ganhou em segunda, empregador recorre ao TST
                    elif resultado_primeira == 'Improcedente' and resultado_atual == 'Provido':
                        if resultado_seguinte == 'Desprovido':
                            recursos_empregador['fracasso'] += 1
                        else:
                            recursos_empregador['sucesso'] += 1
        
        # Classificar resultado em cada instância
        for instancia in ['Primeira Instância', 'Segunda Instância', 'TST']:
            if instancia in decisoes_por_instancia:
                decisao = decisoes_por_instancia[instancia]
                resultado = decisao.get('resultado', '')
                
                # Classificar como favorável ou desfavorável ao trabalhador
                if instancia == 'Primeira Instância':
                    if resultado == 'Procedente':
                        taxas_sucesso['primeira_instancia']['favoravel'] += 1
                    elif resultado == 'Improcedente':
                        taxas_sucesso['primeira_instancia']['desfavoravel'] += 1
                
                elif instancia == 'Segunda Instância':
                    # Para segunda instância, precisamos do contexto da primeira
                    if 'Primeira Instância' in decisoes_por_instancia:
                        resultado_primeira = decisoes_por_instancia['Primeira Instância'].get('resultado', '')
                        
                        # Se trabalhador perdeu na primeira e recurso foi provido, é favorável
                        if resultado_primeira == 'Improcedente' and resultado == 'Provido':
                            taxas_sucesso['segunda_instancia']['favoravel'] += 1
                        # Se trabalhador ganhou na primeira e recurso foi desprovido, é favorável
                        elif resultado_primeira == 'Procedente' and resultado == 'Desprovido':
                            taxas_sucesso['segunda_instancia']['favoravel'] += 1
                        # Outros casos são desfavoráveis
                        else:
                            taxas_sucesso['segunda_instancia']['desfavoravel'] += 1
                    else:
                        # Se não tivermos o contexto, usamos a regra geral
                        if resultado == 'Provido':
                            taxas_sucesso['segunda_instancia']['favoravel'] += 1
                        else:
                            taxas_sucesso['segunda_instancia']['desfavoravel'] += 1
                
                elif instancia == 'TST':
                    # Para o TST, a lógica é similar à segunda instância
                    if resultado == 'Provido':
                        taxas_sucesso['tst']['favoravel'] += 1
                    else:
                        taxas_sucesso['tst']['desfavoravel'] += 1
        
        # Classificar o resultado final (última instância do fluxo)
        ultima_decisao = grupo[-1]
        instancia_final = ultima_decisao.get('instancia', '')
        resultado_final = ultima_decisao.get('resultado', '')
        
        if instancia_final and resultado_final:
            chave_resultado = f"Final:{instancia_final}:{resultado_final}"
            resultados_finais[chave_resultado] += 1
    
    # Calcular as porcentagens de sucesso para cada instância
    for instancia, dados in taxas_sucesso.items():
        total = dados['favoravel'] + dados['desfavoravel']
        if total > 0:
            dados['porcentagem_favoravel'] = (dados['favoravel'] / total) * 100
        else:
            dados['porcentagem_favoravel'] = 0
    
    # Calcular taxas de sucesso dos recursos
    total_recursos_trabalhador = recursos_trabalhador['sucesso'] + recursos_trabalhador['fracasso']
    taxa_sucesso_trabalhador = 0
    if total_recursos_trabalhador > 0:
        taxa_sucesso_trabalhador = (recursos_trabalhador['sucesso'] / total_recursos_trabalhador) * 100
    
    total_recursos_empregador = recursos_empregador['sucesso'] + recursos_empregador['fracasso']
    taxa_sucesso_empregador = 0
    if total_recursos_empregador > 0:
        taxa_sucesso_empregador = (recursos_empregador['sucesso'] / total_recursos_empregador) * 100
    
    return {
        'padroes_fluxo': padroes_fluxo,
        'transicoes': transicoes,
        'taxas_sucesso': taxas_sucesso,
        'recursos': {
            'trabalhador': {
                'sucesso': recursos_trabalhador['sucesso'],
                'fracasso': recursos_trabalhador['fracasso'],
                'total': total_recursos_trabalhador,
                'taxa_sucesso': taxa_sucesso_trabalhador
            },
            'empregador': {
                'sucesso': recursos_empregador['sucesso'],
                'fracasso': recursos_empregador['fracasso'],
                'total': total_recursos_empregador,
                'taxa_sucesso': taxa_sucesso_empregador
            }
        },
        'resultados_finais': resultados_finais,
        'total_casos_relacionados': len(grupos_relacionados),
        'casos_multiplas_instancias': sum(1 for grupo in grupos_relacionados if len(grupo) > 1)
    }

def visualizar_resultados(resultados_analise: Dict[str, Any], grupos_relacionados: List[List[Dict[str, Any]]]):
    """
    Cria visualizações dos resultados da análise de fluxo.
    
    Args:
        resultados_analise: Resultados da análise de fluxo
        grupos_relacionados: Grupos de decisões relacionadas
    """
    print("Criando visualizações...")
    
    # 1. Gráfico de barras com taxas de sucesso por instância
    taxas_sucesso = resultados_analise['taxas_sucesso']
    
    instancias = ['primeira_instancia', 'segunda_instancia', 'tst']
    nomes_instancias = ['Primeira Instância', 'Segunda Instância', 'TST']
    taxas = [taxas_sucesso[inst]['porcentagem_favoravel'] for inst in instancias]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(nomes_instancias, taxas, color=['skyblue', 'lightgreen', 'salmon'])
    
    # Adicionar rótulos nas barras
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom')
    
    ax.set_title('Taxa de Sucesso do Trabalhador por Instância')
    ax.set_ylabel('Taxa de Sucesso (%)')
    ax.set_ylim(0, max(taxas) * 1.2)  # Margem superior
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'taxa_sucesso_por_instancia.png'))
    plt.close()
    
    # 2. Gráfico de barras com taxa de sucesso dos recursos
    recursos = resultados_analise['recursos']
    
    partes = ['Trabalhador', 'Empregador']
    taxas_sucesso_recursos = [
        recursos['trabalhador']['taxa_sucesso'],
        recursos['empregador']['taxa_sucesso']
    ]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(partes, taxas_sucesso_recursos, color=['blue', 'red'])
    
    # Adicionar números absolutos nas barras
    for i, bar in enumerate(bars):
        height = bar.get_height()
        if i == 0:  # Trabalhador
            sucesso = recursos['trabalhador']['sucesso']
            total = recursos['trabalhador']['total']
        else:  # Empregador
            sucesso = recursos['empregador']['sucesso']
            total = recursos['empregador']['total']
        
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%\n({sucesso}/{total})', ha='center', va='bottom')
    
    ax.set_title('Taxa de Sucesso de Recursos por Parte')
    ax.set_ylabel('Taxa de Sucesso (%)')
    ax.set_ylim(0, max(taxas_sucesso_recursos) * 1.2)  # Margem superior
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'taxa_sucesso_recursos.png'))
    plt.close()
    
    # 3. Grafo de fluxo das decisões
    transicoes = resultados_analise['transicoes']
    
    # Criar um grafo direcionado
    G = nx.DiGraph()
    
    # Adicionar nós e arestas baseados nas transições
    for transicao, count in transicoes.items():
        origem, destino = transicao.split(' -> ')
        G.add_edge(origem, destino, weight=count, label=str(count))
    
    # Criar uma visualização do grafo
    plt.figure(figsize=(14, 10))
    
    # Posicionar os nós em camadas
    pos = nx.spring_layout(G, k=0.5)  # k controla o espaçamento
    
    # Desenhar os nós
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color='lightblue', alpha=0.8)
    
    # Desenhar as arestas com espessura proporcional ao peso
    edge_widths = [G[u][v]['weight'] / 2 for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color='gray', arrows=True, arrowsize=20)
    
    # Adicionar rótulos aos nós
    nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
    
    # Adicionar rótulos às arestas
    edge_labels = {(u, v): G[u][v]['label'] for u, v in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    
    plt.title('Grafo de Fluxo de Decisões')
    plt.axis('off')  # Desativar eixos
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'grafo_fluxo_decisoes.png'))
    plt.close()
    
    # 4. Gráfico de sankey para visualizar o fluxo
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Preparar dados para o diagrama de Sankey
        nodes = []
        links = []
        
        # Identificar todos os nós únicos
        all_nodes = set()
        for transicao in transicoes:
            origem, destino = transicao.split(' -> ')
            all_nodes.add(origem)
            all_nodes.add(destino)
        
        # Criar mapeamento de nós para índices
        node_to_idx = {node: i for i, node in enumerate(all_nodes)}
        
        # Adicionar nós
        nodes = list(all_nodes)
        
        # Adicionar links
        for transicao, count in transicoes.items():
            origem, destino = transicao.split(' -> ')
            origem_idx = node_to_idx[origem]
            destino_idx = node_to_idx[destino]
            links.append((origem_idx, destino_idx, count))
        
        # Criar figura
        fig = make_subplots(rows=1, cols=1)
        
        # Adicionar diagrama de Sankey
        fig.add_trace(
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=nodes
                ),
                link=dict(
                    source=[link[0] for link in links],
                    target=[link[1] for link in links],
                    value=[link[2] for link in links]
                )
            )
        )
        
        fig.update_layout(title_text="Fluxo de Decisões", font_size=10)
        fig.write_html(os.path.join(RESULTS_DIR, 'sankey_fluxo_decisoes.html'))
    except ImportError:
        print("Biblioteca plotly não encontrada. Diagrama de Sankey não será gerado.")
    
    # 5. Gerar relatório markdown
    gerar_relatorio_markdown(resultados_analise, grupos_relacionados)

def gerar_relatorio_markdown(resultados_analise: Dict[str, Any], grupos_relacionados: List[List[Dict[str, Any]]]):
    """
    Gera um relatório em formato markdown com os resultados da análise.
    
    Args:
        resultados_analise: Resultados da análise de fluxo
        grupos_relacionados: Grupos de decisões relacionadas
    """
    relatorio_path = os.path.join(RESULTS_DIR, 'relatorio_fluxo_decisoes.md')
    
    with open(relatorio_path, 'w') as f:
        f.write("# Relatório de Análise de Fluxo de Decisões: Assédio Moral na Justiça do Trabalho\n\n")
        
        # Visão geral
        f.write("## Visão Geral\n\n")
        f.write(f"- Total de casos analisados: {resultados_analise['total_casos_relacionados']}\n")
        f.write(f"- Casos com decisões em múltiplas instâncias: {resultados_analise['casos_multiplas_instancias']}\n\n")
        
        # Taxas de sucesso por instância
        f.write("## Taxas de Sucesso por Instância\n\n")
        f.write("| Instância | Favorável ao Trabalhador | Desfavorável ao Trabalhador | Taxa de Sucesso |\n")
        f.write("|-----------|--------------------------|------------------------------|----------------|\n")
        
        taxas_sucesso = resultados_analise['taxas_sucesso']
        for instancia, nome_formatado in zip(['primeira_instancia', 'segunda_instancia', 'tst'],
                                           ['Primeira Instância', 'Segunda Instância', 'TST']):
            dados = taxas_sucesso[instancia]
            f.write(f"| {nome_formatado} | {dados['favoravel']} | {dados['desfavoravel']} | {dados['porcentagem_favoravel']:.1f}% |\n")
        
        # Taxas de sucesso de recursos
        f.write("\n## Taxas de Sucesso de Recursos\n\n")
        f.write("| Parte | Recursos com Sucesso | Recursos sem Sucesso | Total | Taxa de Sucesso |\n")
        f.write("|-------|----------------------|----------------------|-------|----------------|\n")
        
        recursos = resultados_analise['recursos']
        f.write(f"| Trabalhador | {recursos['trabalhador']['sucesso']} | {recursos['trabalhador']['fracasso']} | {recursos['trabalhador']['total']} | {recursos['trabalhador']['taxa_sucesso']:.1f}% |\n")
        f.write(f"| Empregador | {recursos['empregador']['sucesso']} | {recursos['empregador']['fracasso']} | {recursos['empregador']['total']} | {recursos['empregador']['taxa_sucesso']:.1f}% |\n")
        
        # Padrões de fluxo mais comuns
        f.write("\n## Padrões de Fluxo Mais Comuns\n\n")
        
        padroes_fluxo = resultados_analise['padroes_fluxo']
        f.write("| Padrão de Fluxo | Ocorrências |\n")
        f.write("|----------------|-------------|\n")
        
        for padrao, count in padroes_fluxo.most_common(15):  # Top 15
            f.write(f"| {padrao} | {count} |\n")
        
        # Transições mais comuns
        f.write("\n## Transições Mais Comuns\n\n")
        
        transicoes = resultados_analise['transicoes']
        f.write("| Transição | Ocorrências |\n")
        f.write("|-----------|-------------|\n")
        
        for transicao, count in transicoes.most_common(15):  # Top 15
            f.write(f"| {transicao} | {count} |\n")
        
        # Resultados finais
        f.write("\n## Resultados Finais\n\n")
        
        resultados_finais = resultados_analise['resultados_finais']
        f.write("| Resultado Final | Ocorrências |\n")
        f.write("|----------------|-------------|\n")
        
        for resultado, count in resultados_finais.most_common():
            f.write(f"| {resultado} | {count} |\n")
        
        # Exemplos de casos
        f.write("\n## Exemplos de Casos\n\n")
        
        # Mostrar alguns exemplos de casos com fluxo completo
        casos_completos = [g for g in grupos_relacionados 
                          if len(set(d.get('instancia', '') for d in g)) >= 2]
        
        for i, caso in enumerate(casos_completos[:5]):  # Mostrar até 5 exemplos
            f.write(f"### Caso {i+1}\n\n")
            
            for decisao in caso:
                instancia = decisao.get('instancia', 'N/A')
                tribunal = decisao.get('tribunal', 'N/A')
                resultado = decisao.get('resultado', 'N/A')
                numero = decisao.get('numero_processo', 'N/A')
                data = decisao.get('data_julgamento', 'N/A')
                
                f.write(f"- **{instancia} ({tribunal})**: {resultado}\n")
                f.write(f"  - Número do processo: {numero}\n")
                f.write(f"  - Data de julgamento: {data}\n\n")
        
        # Conclusões
        f.write("\n## Conclusões\n\n")
        
        # Calcular estatísticas para conclusões
        total_primeira = (taxas_sucesso['primeira_instancia']['favoravel'] + 
                         taxas_sucesso['primeira_instancia']['desfavoravel'])
        taxa_sucesso_primeira = taxas_sucesso['primeira_instancia']['porcentagem_favoravel']
        
        total_segunda = (taxas_sucesso['segunda_instancia']['favoravel'] + 
                        taxas_sucesso['segunda_instancia']['desfavoravel'])
        taxa_sucesso_segunda = taxas_sucesso['segunda_instancia']['porcentagem_favoravel']
        
        total_tst = taxas_sucesso['tst']['favoravel'] + taxas_sucesso['tst']['desfavoravel']
        taxa_sucesso_tst = taxas_sucesso['tst']['porcentagem_favoravel']
        
        taxa_recursos_trabalhador = recursos['trabalhador']['taxa_sucesso']
        taxa_recursos_empregador = recursos['empregador']['taxa_sucesso']
        
        f.write(f"1. Na primeira instância, apenas {taxa_sucesso_primeira:.1f}% das decisões são favoráveis ao trabalhador em casos de assédio moral (com base em {total_primeira} decisões).\n\n")
        
        f.write(f"2. Na segunda instância, {taxa_sucesso_segunda:.1f}% das decisões são favoráveis ao trabalhador (com base em {total_segunda} decisões).\n\n")
        
        f.write(f"3. No TST, {taxa_sucesso_tst:.1f}% das decisões são favoráveis ao trabalhador (com base em {total_tst} decisões).\n\n")
        
        f.write(f"4. Recursos interpostos por trabalhadores têm uma taxa de sucesso de {taxa_recursos_trabalhador:.1f}%, enquanto recursos de empregadores têm uma taxa de sucesso de {taxa_recursos_empregador:.1f}%.\n\n")
        
        f.write("### Padrão de Decisões\n\n")
        f.write("A análise revela um padrão claro nas decisões de assédio moral na Justiça do Trabalho:\n\n")
        
        if taxa_sucesso_primeira < 30 and taxa_sucesso_segunda > 70 and taxa_sucesso_tst < 30:
            f.write("- Um \"efeito sanfona\" onde a primeira instância tende a ser desfavorável ao trabalhador, a segunda instância tende a reformar essas decisões em favor do trabalhador, e o TST tende a reverter novamente para decisões desfavoráveis.\n\n")
        elif taxa_sucesso_primeira < 30:
            f.write("- A primeira instância apresenta uma tendência significativa de decisões desfavoráveis ao trabalhador em casos de assédio moral.\n\n")
        
        if taxa_recursos_trabalhador > taxa_recursos_empregador:
            f.write("- Os recursos interpostos por trabalhadores têm maior taxa de sucesso do que os recursos interpostos por empregadores, sugerindo uma tendência de correção nas instâncias superiores.\n\n")
        else:
            f.write("- Os recursos interpostos por empregadores têm maior taxa de sucesso do que os recursos interpostos por trabalhadores, indicando uma possível vantagem para os empregadores nas instâncias recursais.\n\n")
        
        f.write("### Limitações da Análise\n\n")
        f.write("1. **Identificação de casos relacionados**: A metodologia para relacionar o mesmo processo em diferentes instâncias pode não ser perfeita, devido à falta de padronização nos números de processo.\n\n")
        f.write("2. **Inferência sobre a parte recorrente**: Na ausência de dados explícitos sobre qual parte interpôs cada recurso, as inferências baseiam-se no resultado anterior e atual.\n\n")
        f.write("3. **Amostra limitada**: O número de casos em que foi possível rastrear o fluxo completo é relativamente pequeno em comparação com o total de decisões.\n\n")
        
        f.write("### Recomendações\n\n")
        f.write("1. Implementar um sistema de coleta de dados que capture explicitamente a identificação única do processo em todas as instâncias.\n\n")
        f.write("2. Incluir informações sobre a parte recorrente em cada apelação.\n\n")
        f.write("3. Ampliar a análise para incluir informações textuais das decisões, para compreender melhor os fundamentos jurídicos que levam a essas tendências de decisão.\n\n")
        
        f.write("Relatório gerado em: 2025-06-21")
    
    print(f"Relatório markdown gerado em: {relatorio_path}")

def main():
    # Carregar dados
    print("Carregando dados...")
    data_path = os.path.join('data', 'consolidated', 'all_decisions.json')
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Identificar casos relacionados
    grupos_relacionados = identificar_casos_relacionados(data)
    
    # Salvar grupos para referência futura
    grupos_path = os.path.join(RESULTS_DIR, 'grupos_relacionados.json')
    
    # Criar uma versão simplificada para salvar (apenas IDs e informações essenciais)
    grupos_simplificados = []
    for grupo in grupos_relacionados:
        grupo_simplificado = []
        for decisao in grupo:
            grupo_simplificado.append({
                'numero_processo': decisao.get('numero_processo', ''),
                'tribunal': decisao.get('tribunal', ''),
                'instancia': decisao.get('instancia', ''),
                'resultado': decisao.get('resultado', ''),
                'data_julgamento': decisao.get('data_julgamento', '')
            })
        grupos_simplificados.append(grupo_simplificado)
    
    with open(grupos_path, 'w') as f:
        json.dump(grupos_simplificados, f, indent=2)
    
    # Analisar fluxo de decisões
    resultados_analise = analisar_fluxo_decisoes(grupos_relacionados)
    
    # Salvar resultados da análise
    resultados_path = os.path.join(RESULTS_DIR, 'resultados_analise.json')
    
    # Converter Counter para dicionários para serialização
    resultados_serializaveis = dict(resultados_analise)
    resultados_serializaveis['padroes_fluxo'] = dict(resultados_analise['padroes_fluxo'])
    resultados_serializaveis['transicoes'] = dict(resultados_analise['transicoes'])
    resultados_serializaveis['resultados_finais'] = dict(resultados_analise['resultados_finais'])
    
    with open(resultados_path, 'w') as f:
        json.dump(resultados_serializaveis, f, indent=2)
    
    # Visualizar resultados
    visualizar_resultados(resultados_analise, grupos_relacionados)
    
    print(f"Análise concluída. Resultados salvos em {RESULTS_DIR}")

if __name__ == "__main__":
    main()