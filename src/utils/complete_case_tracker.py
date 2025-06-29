#!/usr/bin/env python3
"""
Rastreador Completo de Casos - Extrai histórico completo de processos
incluindo dados de instâncias anteriores presentes nos movimentos.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from .movement_analyzer import MovementAnalyzer

logger = logging.getLogger(__name__)

class CompleteCaseTracker:
    """Rastreia histórico completo de processos através dos movimentos."""
    
    def __init__(self):
        self.movement_analyzer = MovementAnalyzer()
        
        # Códigos por instância
        self.codes_by_instance = {
            'primeira_instancia': [219, 220, 221],  # Procedência, Improcedência, Procedência em Parte
            'segunda_instancia': [237, 238, 242, 236],  # Provimento, Provimento em Parte, Desprovimento, Negação
            'tst': [237, 238, 242, 236]  # Mesmos códigos do TRT
        }
        
        # Mapeamento de resultados para entendimento humano
        self.result_interpretation = {
            219: {'nome': 'Procedência', 'favoravel': True, 'instancia': '1ª'},
            220: {'nome': 'Improcedência', 'favoravel': False, 'instancia': '1ª'},
            221: {'nome': 'Procedência em Parte', 'favoravel': True, 'instancia': '1ª'},
            237: {'nome': 'Provimento', 'favoravel': True, 'instancia': '2ª/TST'},
            238: {'nome': 'Provimento em Parte', 'favoravel': True, 'instancia': '2ª/TST'},
            242: {'nome': 'Desprovimento', 'favoravel': False, 'instancia': '2ª/TST'},
            236: {'nome': 'Negação de Seguimento', 'favoravel': False, 'instancia': '2ª/TST'}
        }
    
    def extract_complete_history(self, processo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai histórico completo de um processo, incluindo dados de instâncias
        anteriores presentes nos movimentos.
        
        Args:
            processo: Dados do processo
            
        Returns:
            Dicionário com histórico completo
        """
        numero = processo.get('numeroProcesso', '')
        grau_atual = processo.get('grau', '')
        tribunal_atual = processo.get('tribunal', '')
        movimentos = processo.get('movimentos', [])
        
        # Extrai todos os movimentos relevantes
        historico = {
            'numero_processo': numero,
            'grau_atual': grau_atual,
            'tribunal_atual': tribunal_atual,
            'instancia_atual': self.movement_analyzer.grau_mapping.get(grau_atual, 'Desconhecida'),
            'total_movimentos': len(movimentos),
            'resultados_por_instancia': {},
            'fluxo_completo': [],
            'tem_historico_completo': False,
            'trabalhador_venceu': None,
            'mudancas_resultado': []
        }
        
        # Busca movimentos por instância
        movimentos_primeira = []
        movimentos_segunda = []
        
        for movimento in movimentos:
            codigo = movimento.get('codigo')
            nome = movimento.get('nome', '')
            
            if codigo in self.codes_by_instance['primeira_instancia']:
                movimentos_primeira.append({
                    'codigo': codigo,
                    'nome': nome,
                    'interpretacao': self.result_interpretation.get(codigo, {})
                })
            elif codigo in self.codes_by_instance['segunda_instancia']:
                movimentos_segunda.append({
                    'codigo': codigo,
                    'nome': nome,
                    'interpretacao': self.result_interpretation.get(codigo, {})
                })
        
        # Processa resultados por instância
        if movimentos_primeira:
            historico['resultados_por_instancia']['primeira_instancia'] = movimentos_primeira
            historico['tem_historico_completo'] = True
        
        if movimentos_segunda:
            historico['resultados_por_instancia']['segunda_instancia_ou_tst'] = movimentos_segunda
        
        # Constrói fluxo completo
        fluxo = []
        
        # Adiciona primeira instância se encontrada
        if movimentos_primeira:
            for mov in movimentos_primeira:
                interpretacao = mov['interpretacao']
                fluxo.append({
                    'instancia': '1ª Instância',
                    'resultado': interpretacao.get('nome', mov['nome']),
                    'favoravel_trabalhador': interpretacao.get('favoravel', None),
                    'codigo': mov['codigo']
                })
        
        # Adiciona segunda instância/TST se encontrada
        if movimentos_segunda:
            instancia_nome = '2ª Instância' if grau_atual == 'G2' else 'TST'
            for mov in movimentos_segunda:
                interpretacao = mov['interpretacao']
                fluxo.append({
                    'instancia': instancia_nome,
                    'resultado': interpretacao.get('nome', mov['nome']),
                    'favoravel_trabalhador': interpretacao.get('favoravel', None),
                    'codigo': mov['codigo']
                })
        
        historico['fluxo_completo'] = fluxo
        
        # Determina resultado final e mudanças
        if fluxo:
            resultado_final = fluxo[-1]['favoravel_trabalhador']
            historico['trabalhador_venceu'] = resultado_final
            
            # Identifica mudanças de resultado
            if len(fluxo) > 1:
                for i in range(1, len(fluxo)):
                    resultado_anterior = fluxo[i-1]['favoravel_trabalhador']
                    resultado_atual = fluxo[i]['favoravel_trabalhador']
                    
                    if resultado_anterior != resultado_atual and resultado_anterior is not None and resultado_atual is not None:
                        mudanca = {
                            'de_instancia': fluxo[i-1]['instancia'],
                            'para_instancia': fluxo[i]['instancia'],
                            'resultado_anterior': resultado_anterior,
                            'resultado_novo': resultado_atual,
                            'tipo_mudanca': 'favoravel_para_desfavoravel' if resultado_anterior and not resultado_atual else 'desfavoravel_para_favoravel'
                        }
                        historico['mudancas_resultado'].append(mudanca)
        
        return historico
    
    def analyze_dataset_complete_tracking(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa dataset completo identificando casos com histórico completo.
        
        Args:
            data: Lista de processos
            
        Returns:
            Análise completa do dataset
        """
        casos_completos = []
        casos_parciais = []
        estatisticas = {
            'total_processos': len(data),
            'com_historico_primeira': 0,
            'com_historico_segunda': 0,
            'com_historico_completo': 0,
            'fluxos_identificados': {},
            'mudancas_resultado': {
                'total': 0,
                'favoravel_para_desfavoravel': 0,
                'desfavoravel_para_favoravel': 0
            }
        }
        
        for processo in data:
            historico = self.extract_complete_history(processo)
            
            if historico['tem_historico_completo']:
                casos_completos.append(historico)
                estatisticas['com_historico_completo'] += 1
            else:
                casos_parciais.append(historico)
            
            # Estatísticas por instância
            if historico['resultados_por_instancia'].get('primeira_instancia'):
                estatisticas['com_historico_primeira'] += 1
            
            if historico['resultados_por_instancia'].get('segunda_instancia_ou_tst'):
                estatisticas['com_historico_segunda'] += 1
            
            # Conta fluxos
            if historico['fluxo_completo']:
                fluxo_str = ' → '.join([f"{f['instancia']}:{f['resultado']}" for f in historico['fluxo_completo']])
                estatisticas['fluxos_identificados'][fluxo_str] = estatisticas['fluxos_identificados'].get(fluxo_str, 0) + 1
            
            # Conta mudanças
            if historico['mudancas_resultado']:
                estatisticas['mudancas_resultado']['total'] += len(historico['mudancas_resultado'])
                for mudanca in historico['mudancas_resultado']:
                    tipo = mudanca['tipo_mudanca']
                    estatisticas['mudancas_resultado'][tipo] += 1
        
        return {
            'estatisticas': estatisticas,
            'casos_completos': casos_completos,
            'casos_parciais': casos_parciais,
            'percentual_historico_completo': (estatisticas['com_historico_completo'] / len(data)) * 100 if data else 0
        }
    
    def generate_complete_tracking_report(self, analysis: Dict[str, Any]) -> str:
        """
        Gera relatório de rastreamento completo.
        
        Args:
            analysis: Resultado da análise
            
        Returns:
            Relatório em markdown
        """
        stats = analysis['estatisticas']
        
        report = f"""# Relatório de Rastreamento Completo de Casos

## Resumo Geral

- **Total de processos analisados**: {stats['total_processos']:,}
- **Processos com histórico de 1ª instância**: {stats['com_historico_primeira']:,} ({(stats['com_historico_primeira']/stats['total_processos']*100):.1f}%)
- **Processos com histórico de 2ª instância/TST**: {stats['com_historico_segunda']:,} ({(stats['com_historico_segunda']/stats['total_processos']*100):.1f}%)
- **Processos com histórico completo**: {stats['com_historico_completo']:,} ({analysis['percentual_historico_completo']:.1f}%)

## Mudanças de Resultado Entre Instâncias

- **Total de mudanças identificadas**: {stats['mudancas_resultado']['total']}
- **Favorável → Desfavorável**: {stats['mudancas_resultado']['favoravel_para_desfavoravel']} casos
- **Desfavorável → Favorável**: {stats['mudancas_resultado']['desfavoravel_para_favoravel']} casos

## Fluxos Processuais Mais Comuns

"""
        
        # Adiciona fluxos mais comuns
        fluxos_ordenados = sorted(stats['fluxos_identificados'].items(), key=lambda x: x[1], reverse=True)
        for fluxo, count in fluxos_ordenados[:20]:
            report += f"- **{fluxo}**: {count} casos\n"
        
        report += f"""

## Exemplos de Casos com Histórico Completo

"""
        
        # Adiciona exemplos de casos completos
        for i, caso in enumerate(analysis['casos_completos'][:10]):
            report += f"""
### Caso {i+1}: {caso['numero_processo']}

- **Instância atual**: {caso['instancia_atual']} ({caso['tribunal_atual']})
- **Resultado final**: {"Favorável" if caso['trabalhador_venceu'] else "Desfavorável" if caso['trabalhador_venceu'] is not None else "Indefinido"}

**Fluxo completo**:
"""
            for etapa in caso['fluxo_completo']:
                resultado_emoji = "✅" if etapa['favoravel_trabalhador'] else "❌" if etapa['favoravel_trabalhador'] is not None else "⚖️"
                report += f"- {resultado_emoji} **{etapa['instancia']}**: {etapa['resultado']}\n"
            
            if caso['mudancas_resultado']:
                report += "\n**Mudanças de resultado**:\n"
                for mudanca in caso['mudancas_resultado']:
                    tipo_emoji = "📈" if mudanca['tipo_mudanca'] == 'desfavoravel_para_favoravel' else "📉"
                    report += f"- {tipo_emoji} {mudanca['de_instancia']} → {mudanca['para_instancia']}\n"
        
        return report