#!/usr/bin/env python3
"""
Análise Avançada da Taxa de Sucesso de Recursos de Trabalhadores em Casos de Assédio Moral

Este script implementa uma análise sofisticada que:
1. Rastreia a cadeia completa de decisões (1ª instância -> 2ª instância -> TST)
2. Identifica corretamente quem interpôs cada recurso (trabalhador vs empregador)
3. Calcula taxas de sucesso específicas para recursos de trabalhadores
4. Considera as tags de movimento nos processos de segunda instância nos TRTs e no TST
5. Analisa padrões de reversão de decisões entre instâncias

A análise é baseada nos códigos de movimento da TPU/CNJ:
- 219: Procedência (1ª instância)
- 220: Improcedência (1ª instância) 
- 237: Provimento (recurso acolhido)
- 242: Desprovimento (recurso negado)
- 236: Negação de seguimento
"""

import json
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Set, Optional
from pathlib import Path

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

# Diretórios
RESULTS_DIR = Path('resultados_taxa_sucesso')
RESULTS_DIR.mkdir(exist_ok=True)

class AnaliseTaxaSucessoRecursos:
    def __init__(self):
        self.data_path = Path("data/consolidated/all_decisions.json")
        self.results_dir = RESULTS_DIR
        
        # Códigos de movimento da TPU/CNJ
        self.movimento_codigos = {
            219: "Procedência",
            220: "Improcedência", 
            237: "Provimento",
            242: "Desprovimento",
            236: "Negação de Seguimento"
        }
        
        # Mapeamento de resultados para análise
        self.resultado_mapping = {
            'Procedente': 'Procedente',
            'Improcedente': 'Improcedente',
            'Provido': 'Provido',
            'Desprovido': 'Desprovido',
            'Não Provido': 'Desprovido'
        }
    
    def load_data(self) -> List[Dict[str, Any]]:
        """Carrega os dados consolidados"""
        print("Carregando dados consolidados...")
        
        if not self.data_path.exists():
            print(f"Arquivo não encontrado: {self.data_path}")
            return []
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Carregados {len(data)} registros")
        return data
    
    def normalize_process_number(self, numero: str) -> str:
        """Normaliza número do processo para facilitar correspondência"""
        if not numero:
            return ""
        
        # Remove caracteres não numéricos
        numero_limpo = re.sub(r'\D', '', str(numero))
        
        # Para correspondência entre instâncias, usa os primeiros 16 dígitos (raiz CNJ)
        if len(numero_limpo) >= 16:
            return numero_limpo[:16]
        return numero_limpo
    
    def identify_appeal_chains(self, data: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Identifica cadeias completas de recursos para o mesmo processo
        """
        print("Identificando cadeias de recursos...")
        
        # Agrupa por número de processo normalizado
        processos_por_numero = defaultdict(list)
        
        for decisao in data:
            numero_norm = self.normalize_process_number(decisao.get('numero_processo', ''))
            if numero_norm:
                processos_por_numero[numero_norm].append(decisao)
        
        # Filtra apenas processos com múltiplas decisões
        cadeias = []
        for numero, decisoes in processos_por_numero.items():
            if len(decisoes) > 1:
                # Ordena por instância e data
                decisoes_ordenadas = self.sort_decisions_by_instance(decisoes)
                cadeias.append(decisoes_ordenadas)
        
        print(f"Identificadas {len(cadeias)} cadeias de recursos")
        return cadeias
    
    def sort_decisions_by_instance(self, decisoes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ordena decisões por instância e data"""
        ordem_instancia = {
            'Primeira Instância': 1,
            'Segunda Instância': 2, 
            'TST': 3
        }
        
        def sort_key(decisao):
            instancia = decisao.get('instancia', '')
            data = decisao.get('data_julgamento', '')
            return (ordem_instancia.get(instancia, 99), data)
        
        return sorted(decisoes, key=sort_key)
    
    def analyze_appeal_success(self, cadeias: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Analisa a taxa de sucesso de recursos de trabalhadores
        """
        print("Analisando taxa de sucesso de recursos...")
        
        # Contadores para análise
        estatisticas = {
            'total_cadeias': len(cadeias),
            'cadeias_completas': 0,  # 1ª -> 2ª -> TST
            'cadeias_parciais': 0,   # 1ª -> 2ª ou 2ª -> TST
            
            # Recursos de trabalhadores
            'recursos_trabalhador_trt': {'sucesso': 0, 'fracasso': 0, 'total': 0},
            'recursos_trabalhador_tst': {'sucesso': 0, 'fracasso': 0, 'total': 0},
            
            # Recursos de empregadores  
            'recursos_empregador_trt': {'sucesso': 0, 'fracasso': 0, 'total': 0},
            'recursos_empregador_tst': {'sucesso': 0, 'fracasso': 0, 'total': 0},
            
            # Padrões de fluxo
            'padroes_fluxo': Counter(),
            'transicoes': Counter(),
            
            # Análise por tribunal
            'por_tribunal': defaultdict(lambda: {
                'recursos_trabalhador': {'sucesso': 0, 'fracasso': 0, 'total': 0},
                'recursos_empregador': {'sucesso': 0, 'fracasso': 0, 'total': 0}
            })
        }
        
        for cadeia in cadeias:
            if len(cadeia) >= 3:
                estatisticas['cadeias_completas'] += 1
            elif len(cadeia) == 2:
                estatisticas['cadeias_parciais'] += 1
            
            # Analisa cada transição na cadeia
            self.analyze_chain_transitions(cadeia, estatisticas)
        
        # Calcula taxas de sucesso
        self.calculate_success_rates(estatisticas)
        
        return estatisticas
    
    def analyze_chain_transitions(self, cadeia: List[Dict[str, Any]], estatisticas: Dict[str, Any]):
        """Analisa as transições em uma cadeia de recursos"""
        
        # Identifica instâncias presentes
        instancias_presentes = [d.get('instancia', '') for d in cadeia]
        resultados = [d.get('resultado', '') for d in cadeia]
        tribunais = [d.get('tribunal', '') for d in cadeia]
        
        # Registra padrão de fluxo
        padrao = " -> ".join([f"{inst}:{res}" for inst, res in zip(instancias_presentes, resultados)])
        estatisticas['padroes_fluxo'][padrao] += 1
        
        # Analisa transições específicas
        for i in range(len(cadeia) - 1):
            decisao_atual = cadeia[i]
            decisao_seguinte = cadeia[i + 1]
            
            instancia_atual = decisao_atual.get('instancia', '')
            resultado_atual = decisao_atual.get('resultado', '')
            tribunal_atual = decisao_atual.get('tribunal', '')
            
            instancia_seguinte = decisao_seguinte.get('instancia', '')
            resultado_seguinte = decisao_seguinte.get('resultado', '')
            
            # Transição 1ª -> 2ª instância
            if instancia_atual == 'Primeira Instância' and instancia_seguinte == 'Segunda Instância':
                self.analyze_first_to_second_transition(
                    decisao_atual, decisao_seguinte, estatisticas
                )
            
            # Transição 2ª instância -> TST
            elif instancia_atual == 'Segunda Instância' and instancia_seguinte == 'TST':
                self.analyze_second_to_tst_transition(
                    cadeia, i, estatisticas
                )
    
    def analyze_first_to_second_transition(self, primeira: Dict[str, Any], segunda: Dict[str, Any], 
                                         estatisticas: Dict[str, Any]):
        """Analisa transição da primeira para a segunda instância"""
        
        resultado_primeira = primeira.get('resultado', '')
        resultado_segunda = segunda.get('resultado', '')
        tribunal = segunda.get('tribunal', '')
        
        # Se primeira instância foi improcedente e segunda foi provida = recurso do trabalhador com sucesso
        if resultado_primeira == 'Improcedente' and resultado_segunda == 'Provido':
            estatisticas['recursos_trabalhador_trt']['sucesso'] += 1
            estatisticas['recursos_trabalhador_trt']['total'] += 1
            estatisticas['por_tribunal'][tribunal]['recursos_trabalhador']['sucesso'] += 1
            estatisticas['por_tribunal'][tribunal]['recursos_trabalhador']['total'] += 1
        
        # Se primeira instância foi improcedente e segunda foi desprovida = recurso do trabalhador sem sucesso
        elif resultado_primeira == 'Improcedente' and resultado_segunda == 'Desprovido':
            estatisticas['recursos_trabalhador_trt']['fracasso'] += 1
            estatisticas['recursos_trabalhador_trt']['total'] += 1
            estatisticas['por_tribunal'][tribunal]['recursos_trabalhador']['fracasso'] += 1
            estatisticas['por_tribunal'][tribunal]['recursos_trabalhador']['total'] += 1
        
        # Se primeira instância foi procedente e segunda foi provida = recurso do empregador com sucesso
        elif resultado_primeira == 'Procedente' and resultado_segunda == 'Provido':
            estatisticas['recursos_empregador_trt']['sucesso'] += 1
            estatisticas['recursos_empregador_trt']['total'] += 1
            estatisticas['por_tribunal'][tribunal]['recursos_empregador']['sucesso'] += 1
            estatisticas['por_tribunal'][tribunal]['recursos_empregador']['total'] += 1
        
        # Se primeira instância foi procedente e segunda foi desprovida = recurso do empregador sem sucesso
        elif resultado_primeira == 'Procedente' and resultado_segunda == 'Desprovido':
            estatisticas['recursos_empregador_trt']['fracasso'] += 1
            estatisticas['recursos_empregador_trt']['total'] += 1
            estatisticas['por_tribunal'][tribunal]['recursos_empregador']['fracasso'] += 1
            estatisticas['por_tribunal'][tribunal]['recursos_empregador']['total'] += 1
    
    def analyze_second_to_tst_transition(self, cadeia: List[Dict[str, Any]], idx_segunda: int,
                                       estatisticas: Dict[str, Any]):
        """Analisa transição da segunda instância para o TST"""
        
        # Precisa do contexto da primeira instância para determinar quem recorreu
        if idx_segunda == 0:  # Não há primeira instância
            return
        
        primeira = cadeia[0]  # Primeira instância
        segunda = cadeia[idx_segunda]  # Segunda instância
        tst = cadeia[idx_segunda + 1]  # TST
        
        resultado_primeira = primeira.get('resultado', '')
        resultado_segunda = segunda.get('resultado', '')
        resultado_tst = tst.get('resultado', '')
        
        # Caso 1: Trabalhador perdeu na primeira, ganhou na segunda, empregador recorre ao TST
        if resultado_primeira == 'Improcedente' and resultado_segunda == 'Provido':
            if resultado_tst == 'Provido':  # Empregador ganha no TST
                estatisticas['recursos_empregador_tst']['sucesso'] += 1
                estatisticas['recursos_empregador_tst']['total'] += 1
            else:  # Empregador perde no TST
                estatisticas['recursos_empregador_tst']['fracasso'] += 1
                estatisticas['recursos_empregador_tst']['total'] += 1
        
        # Caso 2: Trabalhador perdeu na primeira e na segunda, recorre ao TST
        elif resultado_primeira == 'Improcedente' and resultado_segunda == 'Desprovido':
            if resultado_tst == 'Provido':  # Trabalhador ganha no TST
                estatisticas['recursos_trabalhador_tst']['sucesso'] += 1
                estatisticas['recursos_trabalhador_tst']['total'] += 1
            else:  # Trabalhador perde no TST
                estatisticas['recursos_trabalhador_tst']['fracasso'] += 1
                estatisticas['recursos_trabalhador_tst']['total'] += 1
        
        # Caso 3: Trabalhador ganhou na primeira, perdeu na segunda, recorre ao TST
        elif resultado_primeira == 'Procedente' and resultado_segunda == 'Provido':
            if resultado_tst == 'Provido':  # Trabalhador perde no TST
                estatisticas['recursos_trabalhador_tst']['fracasso'] += 1
                estatisticas['recursos_trabalhador_tst']['total'] += 1
            else:  # Trabalhador ganha no TST
                estatisticas['recursos_trabalhador_tst']['sucesso'] += 1
                estatisticas['recursos_trabalhador_tst']['total'] += 1
    
    def calculate_success_rates(self, estatisticas: Dict[str, Any]):
        """Calcula as taxas de sucesso"""
        
        # Taxa de sucesso de recursos de trabalhadores no TRT
        trt_trab = estatisticas['recursos_trabalhador_trt']
        if trt_trab['total'] > 0:
            trt_trab['taxa_sucesso'] = (trt_trab['sucesso'] / trt_trab['total']) * 100
        else:
            trt_trab['taxa_sucesso'] = 0
        
        # Taxa de sucesso de recursos de trabalhadores no TST
        tst_trab = estatisticas['recursos_trabalhador_tst']
        if tst_trab['total'] > 0:
            tst_trab['taxa_sucesso'] = (tst_trab['sucesso'] / tst_trab['total']) * 100
        else:
            tst_trab['taxa_sucesso'] = 0
        
        # Taxa de sucesso de recursos de empregadores no TRT
        trt_emp = estatisticas['recursos_empregador_trt']
        if trt_emp['total'] > 0:
            trt_emp['taxa_sucesso'] = (trt_emp['sucesso'] / trt_emp['total']) * 100
        else:
            trt_emp['taxa_sucesso'] = 0
        
        # Taxa de sucesso de recursos de empregadores no TST
        tst_emp = estatisticas['recursos_empregador_tst']
        if tst_emp['total'] > 0:
            tst_emp['taxa_sucesso'] = (tst_emp['sucesso'] / tst_emp['total']) * 100
        else:
            tst_emp['taxa_sucesso'] = 0
        
        # Taxas por tribunal
        for tribunal, dados in estatisticas['por_tribunal'].items():
            for tipo in ['recursos_trabalhador', 'recursos_empregador']:
                if dados[tipo]['total'] > 0:
                    dados[tipo]['taxa_sucesso'] = (dados[tipo]['sucesso'] / dados[tipo]['total']) * 100
                else:
                    dados[tipo]['taxa_sucesso'] = 0
    
    def create_visualizations(self, estatisticas: Dict[str, Any]):
        """Cria visualizações dos resultados"""
        print("Criando visualizações...")
        
        # 1. Taxa de sucesso de recursos por parte e instância
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Gráfico 1: Recursos de trabalhadores
        categorias = ['TRT', 'TST']
        taxas_trabalhador = [
            estatisticas['recursos_trabalhador_trt']['taxa_sucesso'],
            estatisticas['recursos_trabalhador_tst']['taxa_sucesso']
        ]
        totais_trabalhador = [
            estatisticas['recursos_trabalhador_trt']['total'],
            estatisticas['recursos_trabalhador_tst']['total']
        ]
        
        bars1 = ax1.bar(categorias, taxas_trabalhador, color='blue', alpha=0.7)
        ax1.set_title('Taxa de Sucesso de Recursos de Trabalhadores')
        ax1.set_ylabel('Taxa de Sucesso (%)')
        ax1.set_ylim(0, max(taxas_trabalhador) * 1.2 if taxas_trabalhador else 100)
        
        # Adiciona valores nas barras
        for i, bar in enumerate(bars1):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%\n({totais_trabalhador[i]})', ha='center', va='bottom')
        
        # Gráfico 2: Recursos de empregadores
        taxas_empregador = [
            estatisticas['recursos_empregador_trt']['taxa_sucesso'],
            estatisticas['recursos_empregador_tst']['taxa_sucesso']
        ]
        totais_empregador = [
            estatisticas['recursos_empregador_trt']['total'],
            estatisticas['recursos_empregador_tst']['total']
        ]
        
        bars2 = ax2.bar(categorias, taxas_empregador, color='red', alpha=0.7)
        ax2.set_title('Taxa de Sucesso de Recursos de Empregadores')
        ax2.set_ylabel('Taxa de Sucesso (%)')
        ax2.set_ylim(0, max(taxas_empregador) * 1.2 if taxas_empregador else 100)
        
        # Adiciona valores nas barras
        for i, bar in enumerate(bars2):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%\n({totais_empregador[i]})', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'taxa_sucesso_recursos.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Comparação entre trabalhadores e empregadores
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = np.arange(2)
        width = 0.35
        
        # Dados para comparação
        taxas_trabalhador = [estatisticas['recursos_trabalhador_trt']['taxa_sucesso'],
                           estatisticas['recursos_trabalhador_tst']['taxa_sucesso']]
        taxas_empregador = [estatisticas['recursos_empregador_trt']['taxa_sucesso'],
                          estatisticas['recursos_empregador_tst']['taxa_sucesso']]
        
        bars1 = ax.bar(x - width/2, taxas_trabalhador, width, label='Trabalhadores', color='blue', alpha=0.7)
        bars2 = ax.bar(x + width/2, taxas_empregador, width, label='Empregadores', color='red', alpha=0.7)
        
        ax.set_xlabel('Instância')
        ax.set_ylabel('Taxa de Sucesso (%)')
        ax.set_title('Comparação de Taxa de Sucesso de Recursos por Parte')
        ax.set_xticks(x)
        ax.set_xticklabels(['TRT', 'TST'])
        ax.legend()
        
        # Adiciona valores nas barras
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{height:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'comparacao_taxa_sucesso.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Padrões de fluxo mais comuns
        if estatisticas['padroes_fluxo']:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            padroes = list(estatisticas['padroes_fluxo'].keys())[:10]  # Top 10
            contagens = [estatisticas['padroes_fluxo'][p] for p in padroes]
            
            bars = ax.barh(range(len(padroes)), contagens, color='green', alpha=0.7)
            ax.set_yticks(range(len(padroes)))
            ax.set_yticklabels(padroes, fontsize=10)
            ax.set_xlabel('Número de Casos')
            ax.set_title('Padrões de Fluxo Mais Comuns')
            
            # Adiciona valores nas barras
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                       f'{width}', ha='left', va='center')
            
            plt.tight_layout()
            plt.savefig(self.results_dir / 'padroes_fluxo.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    def generate_report(self, estatisticas: Dict[str, Any]):
        """Gera relatório detalhado em markdown"""
        print("Gerando relatório...")
        
        report_path = self.results_dir / 'relatorio_taxa_sucesso_recursos.md'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Relatório de Análise da Taxa de Sucesso de Recursos: Assédio Moral na Justiça do Trabalho\n\n")
            
            f.write("## Metodologia\n\n")
            f.write("Esta análise considera a cadeia completa de decisões para identificar corretamente:\n\n")
            f.write("1. **Quem interpôs cada recurso**: Trabalhador ou empregador\n")
            f.write("2. **Taxa de sucesso específica**: Para recursos de trabalhadores vs empregadores\n")
            f.write("3. **Padrões de reversão**: Entre diferentes instâncias\n\n")
            
            f.write("### Códigos de Movimento Utilizados\n\n")
            f.write("A análise é baseada nos códigos de movimento da TPU/CNJ:\n\n")
            for codigo, descricao in self.movimento_codigos.items():
                f.write(f"- **{codigo}**: {descricao}\n")
            f.write("\n")
            
            # Visão geral
            f.write("## Visão Geral\n\n")
            f.write(f"- **Total de cadeias de recursos analisadas**: {estatisticas['total_cadeias']}\n")
            f.write(f"- **Cadeias completas** (1ª → 2ª → TST): {estatisticas['cadeias_completas']}\n")
            f.write(f"- **Cadeias parciais** (1ª → 2ª ou 2ª → TST): {estatisticas['cadeias_parciais']}\n\n")
            
            # Taxas de sucesso de recursos de trabalhadores
            f.write("## Taxa de Sucesso de Recursos de Trabalhadores\n\n")
            
            trt_trab = estatisticas['recursos_trabalhador_trt']
            tst_trab = estatisticas['recursos_trabalhador_tst']
            
            f.write("| Instância | Recursos com Sucesso | Recursos sem Sucesso | Total | Taxa de Sucesso |\n")
            f.write("|-----------|----------------------|----------------------|-------|----------------|\n")
            f.write(f"| TRT | {trt_trab['sucesso']} | {trt_trab['fracasso']} | {trt_trab['total']} | {trt_trab['taxa_sucesso']:.1f}% |\n")
            f.write(f"| TST | {tst_trab['sucesso']} | {tst_trab['fracasso']} | {tst_trab['total']} | {tst_trab['taxa_sucesso']:.1f}% |\n\n")
            
            # Taxas de sucesso de recursos de empregadores
            f.write("## Taxa de Sucesso de Recursos de Empregadores\n\n")
            
            trt_emp = estatisticas['recursos_empregador_trt']
            tst_emp = estatisticas['recursos_empregador_tst']
            
            f.write("| Instância | Recursos com Sucesso | Recursos sem Sucesso | Total | Taxa de Sucesso |\n")
            f.write("|-----------|----------------------|----------------------|-------|----------------|\n")
            f.write(f"| TRT | {trt_emp['sucesso']} | {trt_emp['fracasso']} | {trt_emp['total']} | {trt_emp['taxa_sucesso']:.1f}% |\n")
            f.write(f"| TST | {tst_emp['sucesso']} | {tst_emp['fracasso']} | {tst_emp['total']} | {tst_emp['taxa_sucesso']:.1f}% |\n\n")
            
            # Análise por tribunal
            f.write("## Análise por Tribunal\n\n")
            
            tribunais_ordenados = sorted(estatisticas['por_tribunal'].items(), 
                                       key=lambda x: x[1]['recursos_trabalhador']['total'], reverse=True)
            
            f.write("| Tribunal | Recursos Trabalhador | Taxa Sucesso | Recursos Empregador | Taxa Sucesso |\n")
            f.write("|----------|---------------------|--------------|---------------------|--------------|\n")
            
            for tribunal, dados in tribunais_ordenados:
                if dados['recursos_trabalhador']['total'] > 0 or dados['recursos_empregador']['total'] > 0:
                    f.write(f"| {tribunal} | {dados['recursos_trabalhador']['total']} | {dados['recursos_trabalhador']['taxa_sucesso']:.1f}% | {dados['recursos_empregador']['total']} | {dados['recursos_empregador']['taxa_sucesso']:.1f}% |\n")
            
            f.write("\n")
            
            # Padrões de fluxo
            f.write("## Padrões de Fluxo Mais Comuns\n\n")
            
            f.write("| Padrão de Fluxo | Número de Casos |\n")
            f.write("|----------------|------------------|\n")
            
            for padrao, count in estatisticas['padroes_fluxo'].most_common(15):
                f.write(f"| {padrao} | {count} |\n")
            
            f.write("\n")
            
            # Conclusões
            f.write("## Conclusões\n\n")
            
            # Taxa geral de sucesso de recursos de trabalhadores
            total_recursos_trabalhador = trt_trab['total'] + tst_trab['total']
            if total_recursos_trabalhador > 0:
                taxa_geral_trabalhador = ((trt_trab['sucesso'] + tst_trab['sucesso']) / total_recursos_trabalhador) * 100
                f.write(f"1. **Taxa geral de sucesso de recursos de trabalhadores**: {taxa_geral_trabalhador:.1f}% ({total_recursos_trabalhador} recursos analisados)\n\n")
            
            # Taxa geral de sucesso de recursos de empregadores
            total_recursos_empregador = trt_emp['total'] + tst_emp['total']
            if total_recursos_empregador > 0:
                taxa_geral_empregador = ((trt_emp['sucesso'] + tst_emp['sucesso']) / total_recursos_empregador) * 100
                f.write(f"2. **Taxa geral de sucesso de recursos de empregadores**: {taxa_geral_empregador:.1f}% ({total_recursos_empregador} recursos analisados)\n\n")
            
            # Comparação
            if total_recursos_trabalhador > 0 and total_recursos_empregador > 0:
                diferenca = taxa_geral_trabalhador - taxa_geral_empregador
                if diferenca > 0:
                    f.write(f"3. **Os recursos de trabalhadores têm {diferenca:.1f} pontos percentuais a mais de sucesso** em comparação com os recursos de empregadores.\n\n")
                else:
                    f.write(f"3. **Os recursos de empregadores têm {abs(diferenca):.1f} pontos percentuais a mais de sucesso** em comparação com os recursos de trabalhadores.\n\n")
            
            # Análise por instância
            if trt_trab['total'] > 0 and tst_trab['total'] > 0:
                diferenca_trt_tst = trt_trab['taxa_sucesso'] - tst_trab['taxa_sucesso']
                if diferenca_trt_tst > 0:
                    f.write(f"4. **Os recursos de trabalhadores têm maior sucesso no TRT** ({diferenca_trt_tst:.1f} pontos percentuais a mais que no TST).\n\n")
                else:
                    f.write(f"4. **Os recursos de trabalhadores têm maior sucesso no TST** ({abs(diferenca_trt_tst):.1f} pontos percentuais a mais que no TRT).\n\n")
            
            f.write("### Limitações da Análise\n\n")
            f.write("1. **Identificação de recursos**: A análise baseia-se na inferência de quem interpôs cada recurso com base no resultado anterior e atual.\n")
            f.write("2. **Correspondência entre instâncias**: A vinculação de processos entre instâncias pode não ser perfeita devido a diferentes formatos de numeração.\n")
            f.write("3. **Amostra limitada**: O número de casos que tramitaram em múltiplas instâncias pode ser limitado.\n\n")
            
            f.write(f"Relatório gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"Relatório salvo em: {report_path}")
        return report_path
    
    def run_analysis(self):
        """Executa a análise completa"""
        print("=== ANÁLISE AVANÇADA DA TAXA DE SUCESSO DE RECURSOS ===\n")
        
        # Carrega dados
        data = self.load_data()
        if not data:
            print("Nenhum dado encontrado para análise")
            return
        
        # Identifica cadeias de recursos
        cadeias = self.identify_appeal_chains(data)
        if not cadeias:
            print("Nenhuma cadeia de recursos identificada")
            return
        
        # Analisa taxa de sucesso
        estatisticas = self.analyze_appeal_success(cadeias)
        
        # Cria visualizações
        self.create_visualizations(estatisticas)
        
        # Gera relatório
        self.generate_report(estatisticas)
        
        print("\n=== ANÁLISE CONCLUÍDA ===")
        print(f"Resultados salvos em: {self.results_dir}")

def main():
    analyzer = AnaliseTaxaSucessoRecursos()
    analyzer.run_analysis()

if __name__ == "__main__":
    main() 