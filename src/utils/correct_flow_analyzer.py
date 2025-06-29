#!/usr/bin/env python3
"""
Analisador de Fluxo Correto - Interpreta corretamente os recursos trabalhistas
Aplicando a lógica: Procedência + Provimento = Trabalhador perdeu (empregador recorreu e ganhou)
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from .movement_analyzer import MovementAnalyzer

logger = logging.getLogger(__name__)

class CorrectFlowAnalyzer:
    """Analisa fluxos processuais com a lógica correta de recursos trabalhistas."""
    
    def __init__(self):
        self.movement_analyzer = MovementAnalyzer()
        
        # Códigos de movimento por instância
        self.primeira_instancia_codes = {
            219: {'nome': 'Procedência', 'favoravel_trabalhador': True},
            220: {'nome': 'Improcedência', 'favoravel_trabalhador': False},
            221: {'nome': 'Procedência em Parte', 'favoravel_trabalhador': True}
        }
        
        self.recurso_codes = {
            237: {'nome': 'Provimento', 'recurso_acolhido': True},
            238: {'nome': 'Provimento em Parte', 'recurso_acolhido': True},
            242: {'nome': 'Desprovimento', 'recurso_acolhido': False},
            236: {'nome': 'Negação de Seguimento', 'recurso_acolhido': False}
        }
        
        # Código de reforma de decisão - CRÍTICO para análise de mérito
        self.reforma_codes = {
            190: {'nome': 'Reforma de Decisão Anterior', 'indica_reforma': True}
        }
        
        # Tipos de mudança possíveis
        self.tipos_mudanca = {
            'reviravolta_favoravel': 'Trabalhador perdeu em 1ª e ganhou em recurso',
            'reviravolta_desfavoravel': 'Trabalhador ganhou em 1ª e perdeu em recurso',
            'manteve_favoravel': 'Trabalhador ganhou em 1ª e manteve em recurso',
            'manteve_desfavoravel': 'Trabalhador perdeu em 1ª e manteve em recurso',
            'reforma_explicita': 'Reforma explícita de decisão anterior (código 190)',
            'inferencia_trt': 'Inferência baseada em dados TRT e assuntos'
        }
    
    def analyze_process_flow(self, processo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analisa o fluxo completo de um processo aplicando a lógica correta.
        Agora com inferências aprimoradas para casos sem dados completos.
        
        Args:
            processo: Dados do processo
            
        Returns:
            Análise do fluxo ou None se não houver dados suficientes
        """
        numero = processo.get('numeroProcesso', '')
        movimentos = processo.get('movimentos', [])
        grau = processo.get('grau', '')
        tribunal = processo.get('tribunal', '')
        
        # Busca movimentos de primeira instância, recursos e reformas
        movs_primeira = []
        movs_recurso = []
        movs_reforma = []
        
        for movimento in movimentos:
            codigo = movimento.get('codigo')
            nome = movimento.get('nome', '')
            
            if codigo in self.primeira_instancia_codes:
                movs_primeira.append({
                    'codigo': codigo,
                    'nome': nome,
                    **self.primeira_instancia_codes[codigo]
                })
            elif codigo in self.recurso_codes:
                movs_recurso.append({
                    'codigo': codigo,
                    'nome': nome,
                    **self.recurso_codes[codigo]
                })
            elif codigo in self.reforma_codes:
                # Analisa reforma com complementos
                reforma_data = self.movement_analyzer.analyze_reforma_decisions([movimento])
                movs_reforma.append({
                    'codigo': codigo,
                    'nome': nome,
                    'reforma_data': reforma_data,
                    **self.reforma_codes[codigo]
                })
        
        # Se não tem dados de ambas as instâncias, tenta inferir
        # EXCETO se houver reforma explícita (código 190)
        if not movs_primeira or not movs_recurso:
            if movs_reforma:
                # Caso especial: tem reforma mas sem dados completos
                return self._interpret_reforma_only(numero, movs_reforma, grau, tribunal)
            
            # NOVA LÓGICA: Tenta inferir a partir de dados TRT sozinhos
            if grau in ['G2', 'GRAU_2'] and movs_recurso:
                return self._infer_from_trt_only(numero, processo, movs_recurso, grau, tribunal)
            
            return None
        
        # Pega o último movimento de cada tipo (mais recente)
        primeira = movs_primeira[-1]
        recurso = movs_recurso[-1]
        
        # Aplica a lógica correta dos recursos
        result = self._interpret_flow_logic(numero, primeira, recurso, grau, tribunal)
        
        # Adiciona informação de reforma se existir
        if movs_reforma:
            result['reformas_identificadas'] = movs_reforma
            result['tem_reforma_explicita'] = True
        
        return result
    
    def _interpret_flow_logic(self, numero: str, primeira: Dict, recurso: Dict, 
                            grau: str, tribunal: str) -> Dict[str, Any]:
        """
        Aplica a lógica correta de interpretação dos recursos.
        
        Lógica:
        - Se trabalhador ganhou em 1ª e recurso foi provido = Empregador recorreu e ganhou
        - Se trabalhador perdeu em 1ª e recurso foi provido = Trabalhador recorreu e ganhou
        """
        trabalhador_ganhou_primeira = primeira['favoravel_trabalhador']
        recurso_foi_provido = recurso['recurso_acolhido']
        
        # Determina quem recorreu e o resultado
        if trabalhador_ganhou_primeira:
            quem_recorreu = 'Empregador'
            if recurso_foi_provido:
                # Empregador recorreu e ganhou
                resultado_final = 'Trabalhador perdeu'
                tipo_mudanca = 'reviravolta_desfavoravel'
                final_favoravel = False
            else:
                # Empregador recorreu e perdeu
                resultado_final = 'Trabalhador manteve vitória'
                tipo_mudanca = 'manteve_favoravel'
                final_favoravel = True
        else:
            quem_recorreu = 'Trabalhador'
            if recurso_foi_provido:
                # Trabalhador recorreu e ganhou
                resultado_final = 'Trabalhador ganhou'
                tipo_mudanca = 'reviravolta_favoravel'
                final_favoravel = True
            else:
                # Trabalhador recorreu e perdeu
                resultado_final = 'Trabalhador manteve derrota'
                tipo_mudanca = 'manteve_desfavoravel'
                final_favoravel = False
        
        # Determina instância do recurso
        instancia_recurso = self.movement_analyzer.grau_mapping.get(grau, 'Instância Superior')
        
        return {
            'numero_processo': numero,
            'tribunal': tribunal,
            'grau': grau,
            'instancia_recurso': instancia_recurso,
            'primeira_instancia': {
                'resultado': primeira['nome'],
                'codigo': primeira['codigo'],
                'favoravel_trabalhador': trabalhador_ganhou_primeira
            },
            'recurso': {
                'resultado': recurso['nome'],
                'codigo': recurso['codigo'],
                'foi_provido': recurso_foi_provido,
                'instancia': instancia_recurso
            },
            'interpretacao': {
                'quem_recorreu': quem_recorreu,
                'resultado_final': resultado_final,
                'tipo_mudanca': tipo_mudanca,
                'descricao_mudanca': self.tipos_mudanca[tipo_mudanca],
                'final_favoravel_trabalhador': final_favoravel
            },
            'fluxo_resumo': f"1ª: {primeira['nome']} → {instancia_recurso}: {recurso['nome']} = {resultado_final}"
        }
    
    def _interpret_reforma_only(self, numero: str, movs_reforma: List[Dict], 
                               grau: str, tribunal: str) -> Dict[str, Any]:
        """
        Interpreta casos onde só há informação de reforma (código 190).
        
        Args:
            numero: Número do processo
            movs_reforma: Lista de movimentos de reforma
            grau: Grau do processo
            tribunal: Tribunal
            
        Returns:
            Análise da reforma identificada
        """
        reforma = movs_reforma[-1]  # Última reforma
        instancia_recurso = self.movement_analyzer.grau_mapping.get(grau, 'Instância Superior')
        
        reforma_data = reforma.get('reforma_data', {})
        complementos = []
        tipo_decisao_anterior = None
        
        if reforma_data.get('reformas_detalhadas'):
            primeira_reforma = reforma_data['reformas_detalhadas'][0]
            complementos = primeira_reforma.get('complementos', {})
            tipo_decisao_anterior = primeira_reforma.get('tipo_decisao_anterior')
        
        return {
            'numero_processo': numero,
            'tribunal': tribunal,
            'grau': grau,
            'instancia_recurso': instancia_recurso,
            'primeira_instancia': {
                'resultado': 'Não identificado diretamente',
                'codigo': None,
                'favoravel_trabalhador': None
            },
            'recurso': {
                'resultado': reforma['nome'],
                'codigo': reforma['codigo'],
                'foi_provido': True,  # Reforma implica em provimento
                'instancia': instancia_recurso
            },
            'interpretacao': {
                'quem_recorreu': 'Não determinado',
                'resultado_final': 'Decisão reformada',
                'tipo_mudanca': 'reforma_explicita',
                'descricao_mudanca': 'Reforma explícita de decisão anterior',
                'final_favoravel_trabalhador': None,
                'complementos_reforma': complementos,
                'tipo_decisao_anterior': tipo_decisao_anterior
            },
            'fluxo_resumo': f"Reforma: {reforma['nome']} em {instancia_recurso}",
            'reformas_identificadas': movs_reforma,
            'tem_reforma_explicita': True
        }
    
    def _infer_from_trt_only(self, numero: str, processo: Dict, movs_recurso: List[Dict],
                           grau: str, tribunal: str) -> Dict[str, Any]:
        """
        Infere resultado do trabalhador baseado APENAS em dados do TRT.
        Usa resultado explícito + padrões dos assuntos para determinar quem recorreu.
        
        Args:
            numero: Número do processo
            processo: Dados completos do processo
            movs_recurso: Movimentos de recurso encontrados
            grau: Grau do processo
            tribunal: Tribunal
            
        Returns:
            Análise inferida do fluxo
        """
        recurso = movs_recurso[-1]  # Último movimento de recurso
        resultado_campo = processo.get('resultado', '')
        assuntos = processo.get('assuntos', [])
        
        # Determina resultado do recurso
        recurso_foi_provido = recurso['recurso_acolhido']
        
        # NOVA LÓGICA: Infere quem provavelmente recorreu baseado nos assuntos
        provavel_recorrente = self._infer_appellant_from_subjects(assuntos)
        
        # Usa resultado explícito se disponível
        if resultado_campo and 'provid' in resultado_campo.lower():
            recurso_foi_provido = True
        elif resultado_campo and 'desprovid' in resultado_campo.lower():
            recurso_foi_provido = False
        
        # Determina resultado final baseado na inferência
        if provavel_recorrente == 'trabalhador':
            # Se trabalhador recorreu, provavelmente perdeu na 1ª instância
            if recurso_foi_provido:
                resultado_final = 'Trabalhador ganhou (recurso provido)'
                tipo_mudanca = 'reviravolta_favoravel'
                final_favoravel = True
            else:
                resultado_final = 'Trabalhador manteve derrota (recurso negado)'
                tipo_mudanca = 'manteve_desfavoravel'
                final_favoravel = False
        else:
            # Se empregador recorreu, provavelmente trabalhador ganhou na 1ª instância
            if recurso_foi_provido:
                resultado_final = 'Trabalhador perdeu (empregador ganhou recurso)'
                tipo_mudanca = 'reviravolta_desfavoravel'
                final_favoravel = False
            else:
                resultado_final = 'Trabalhador manteve vitória (recurso do empregador negado)'
                tipo_mudanca = 'manteve_favoravel'
                final_favoravel = True
        
        instancia_recurso = self.movement_analyzer.grau_mapping.get(grau, 'TRT')
        
        return {
            'numero_processo': numero,
            'tribunal': tribunal,
            'grau': grau,
            'instancia_recurso': instancia_recurso,
            'primeira_instancia': {
                'resultado': 'Inferido por contexto',
                'codigo': None,
                'favoravel_trabalhador': not (provavel_recorrente == 'trabalhador')
            },
            'recurso': {
                'resultado': recurso['nome'],
                'codigo': recurso['codigo'],
                'foi_provido': recurso_foi_provido,
                'instancia': instancia_recurso
            },
            'interpretacao': {
                'quem_recorreu': provavel_recorrente.title(),
                'resultado_final': resultado_final,
                'tipo_mudanca': tipo_mudanca,
                'descricao_mudanca': self.tipos_mudanca.get(tipo_mudanca, 'Inferência baseada em TRT'),
                'final_favoravel_trabalhador': final_favoravel,
                'metodo_inferencia': 'assuntos_e_resultado_trt',
                'confianca': self._calculate_inference_confidence(assuntos, resultado_campo)
            },
            'fluxo_resumo': f"Inferido: {provavel_recorrente.title()} → TRT: {recurso['nome']} = {resultado_final}",
            'dados_incompletos': True,
            'inferencia_trt': True
        }
    
    def _infer_appellant_from_subjects(self, assuntos: List[Dict]) -> str:
        """
        Infere quem provavelmente recorreu baseado nos assuntos do processo.
        
        Args:
            assuntos: Lista de assuntos do processo
            
        Returns:
            'trabalhador' ou 'empregador'
        """
        if not assuntos:
            return 'trabalhador'  # Default: assume trabalhador recorreu
        
        # Contadores para diferentes tipos de pedidos
        score_trabalhador = 0
        score_empregador = 0
        
        for assunto in assuntos:
            if isinstance(assunto, dict):
                nome = assunto.get('nome', '').lower()
                codigo = assunto.get('codigo', 0)
                
                # Padrões que indicam trabalhador como recorrente
                if any(termo in nome for termo in [
                    'salário', 'salarios', 'remuneração', 'verbas rescisórias',
                    'horas extras', 'adicional', 'indenização por dano',
                    'equiparação', 'diferenças salariais', 'gratificação',
                    'comissões', 'prêmios', 'participação nos lucros'
                ]):
                    score_trabalhador += 2
                
                # Padrões que indicam empregador como recorrente  
                elif any(termo in nome for termo in [
                    'justa causa', 'rescisão por justa causa', 'dispensa por justa causa',
                    'contribuição sindical', 'multa administrativa',
                    'reintegração', 'estabilidade', 'readmissão'
                ]):
                    score_empregador += 2
                
                # Assédio moral - contexto dependente, mas geralmente trabalhador
                elif 'assédio' in nome or 'dano moral' in nome:
                    score_trabalhador += 1
        
        # Retorna baseado no score
        if score_trabalhador > score_empregador:
            return 'trabalhador'
        elif score_empregador > score_trabalhador:
            return 'empregador'
        else:
            return 'trabalhador'  # Default em caso de empate
    
    def _calculate_inference_confidence(self, assuntos: List[Dict], resultado: str) -> str:
        """
        Calcula nível de confiança da inferência.
        
        Args:
            assuntos: Lista de assuntos
            resultado: Campo resultado do processo
            
        Returns:
            'alta', 'media' ou 'baixa'
        """
        confidence_score = 0
        
        # Resultado explícito aumenta confiança
        if resultado and ('provid' in resultado.lower() or 'desprovid' in resultado.lower()):
            confidence_score += 3
        
        # Quantidade e especificidade dos assuntos
        if len(assuntos) >= 3:
            confidence_score += 2
        elif len(assuntos) >= 1:
            confidence_score += 1
        
        # Assuntos específicos aumentam confiança
        for assunto in assuntos:
            if isinstance(assunto, dict):
                nome = assunto.get('nome', '').lower()
                if any(termo in nome for termo in [
                    'salário', 'horas extras', 'justa causa', 'indenização'
                ]):
                    confidence_score += 1
                    break
        
        if confidence_score >= 5:
            return 'alta'
        elif confidence_score >= 3:
            return 'media'
        else:
            return 'baixa'
    
    def analyze_dataset_flows(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa fluxos de todo o dataset aplicando a lógica correta.
        
        Args:
            data: Lista de processos
            
        Returns:
            Análise completa dos fluxos
        """
        fluxos_analisados = []
        fluxos_incompletos = 0
        
        for processo in data:
            analise = self.analyze_process_flow(processo)
            if analise:
                fluxos_analisados.append(analise)
            else:
                fluxos_incompletos += 1
        
        # Estatísticas dos fluxos
        stats = self._calculate_flow_statistics(fluxos_analisados)
        
        return {
            'total_processos': len(data),
            'fluxos_completos': len(fluxos_analisados),
            'fluxos_incompletos': fluxos_incompletos,
            'percentual_completos': (len(fluxos_analisados) / len(data) * 100) if data else 0,
            'estatisticas': stats,
            'fluxos_detalhados': fluxos_analisados
        }
    
    def _calculate_flow_statistics(self, fluxos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula estatísticas dos fluxos analisados."""
        if not fluxos:
            return {}
        
        # Conta por tipo de mudança
        tipos_mudanca = {}
        for fluxo in fluxos:
            tipo = fluxo['interpretacao']['tipo_mudanca']
            tipos_mudanca[tipo] = tipos_mudanca.get(tipo, 0) + 1
        
        # Conta por instância de recurso
        por_instancia = {}
        for fluxo in fluxos:
            instancia = fluxo['instancia_recurso']
            if instancia not in por_instancia:
                por_instancia[instancia] = {
                    'total': 0,
                    'favoravel': 0,
                    'desfavoravel': 0,
                    'reviravolta_favoravel': 0,
                    'reviravolta_desfavoravel': 0
                }
            
            stats_inst = por_instancia[instancia]
            stats_inst['total'] += 1
            
            if fluxo['interpretacao']['final_favoravel_trabalhador']:
                stats_inst['favoravel'] += 1
            else:
                stats_inst['desfavoravel'] += 1
            
            tipo = fluxo['interpretacao']['tipo_mudanca']
            if tipo == 'reviravolta_favoravel':
                stats_inst['reviravolta_favoravel'] += 1
            elif tipo == 'reviravolta_desfavoravel':
                stats_inst['reviravolta_desfavoravel'] += 1
        
        # Conta por tribunal
        por_tribunal = {}
        for fluxo in fluxos:
            tribunal = fluxo['tribunal']
            if tribunal not in por_tribunal:
                por_tribunal[tribunal] = {
                    'total': 0,
                    'favoravel': 0,
                    'desfavoravel': 0,
                    'tipos_mudanca': {}
                }
            
            stats_trib = por_tribunal[tribunal]
            stats_trib['total'] += 1
            
            if fluxo['interpretacao']['final_favoravel_trabalhador']:
                stats_trib['favoravel'] += 1
            else:
                stats_trib['desfavoravel'] += 1
            
            tipo = fluxo['interpretacao']['tipo_mudanca']
            stats_trib['tipos_mudanca'][tipo] = stats_trib['tipos_mudanca'].get(tipo, 0) + 1
        
        # Conta por ano (extraindo do número do processo)
        por_ano = {}
        for fluxo in fluxos:
            # Extrai ano do número do processo (formato: NNNNNNN-DD.AAAA.J.TR.OOOO)
            numero = fluxo['numero_processo']
            try:
                if len(numero) >= 15:
                    ano = numero[9:13]  # Posições 9-12 contêm o ano
                    if ano.isdigit():
                        if ano not in por_ano:
                            por_ano[ano] = {
                                'total': 0,
                                'favoravel': 0,
                                'desfavoravel': 0,
                                'tipos_mudanca': {}
                            }
                        
                        stats_ano = por_ano[ano]
                        stats_ano['total'] += 1
                        
                        if fluxo['interpretacao']['final_favoravel_trabalhador']:
                            stats_ano['favoravel'] += 1
                        else:
                            stats_ano['desfavoravel'] += 1
                        
                        tipo = fluxo['interpretacao']['tipo_mudanca']
                        stats_ano['tipos_mudanca'][tipo] = stats_ano['tipos_mudanca'].get(tipo, 0) + 1
            except:
                pass  # Ignora casos com número mal formado
        
        # Conta fluxos mais comuns
        fluxos_comuns = {}
        for fluxo in fluxos:
            resumo = fluxo['fluxo_resumo']
            fluxos_comuns[resumo] = fluxos_comuns.get(resumo, 0) + 1
        
        # Calcula percentuais
        total = len(fluxos)
        tipos_mudanca_percent = {k: (v/total)*100 for k, v in tipos_mudanca.items()}
        
        favoravel_final = sum(1 for f in fluxos if f['interpretacao']['final_favoravel_trabalhador'])
        taxa_sucesso_final = (favoravel_final / total * 100) if total > 0 else 0
        
        return {
            'total_fluxos': total,
            'tipos_mudanca': tipos_mudanca,
            'tipos_mudanca_percent': tipos_mudanca_percent,
            'por_instancia': por_instancia,
            'por_tribunal': por_tribunal,
            'por_ano': por_ano,
            'fluxos_mais_comuns': dict(sorted(fluxos_comuns.items(), key=lambda x: x[1], reverse=True)),
            'taxa_sucesso_final_trabalhador': taxa_sucesso_final,
            'favoravel_final': favoravel_final,
            'desfavoravel_final': total - favoravel_final
        }
    
    def generate_flow_report(self, analysis: Dict[str, Any]) -> str:
        """
        Gera relatório detalhado dos fluxos processuais.
        
        Args:
            analysis: Resultado da análise de fluxos
            
        Returns:
            Relatório em markdown
        """
        stats = analysis.get('estatisticas', {})
        
        report = f"""# Relatório de Fluxos Processuais - Lógica Correta de Recursos

## Resumo Geral

- **Total de processos analisados**: {analysis['total_processos']:,}
- **Fluxos completos identificados**: {analysis['fluxos_completos']:,} ({analysis['percentual_completos']:.1f}%)
- **Fluxos incompletos**: {analysis['fluxos_incompletos']:,}

## Resultado Final para o Trabalhador

- **Taxa de sucesso final**: {stats.get('taxa_sucesso_final_trabalhador', 0):.1f}%
- **Casos favoráveis**: {stats.get('favoravel_final', 0):,}
- **Casos desfavoráveis**: {stats.get('desfavoravel_final', 0):,}

## Tipos de Mudança Entre Instâncias

"""
        
        # Adiciona estatísticas de mudança
        tipos_mudanca = stats.get('tipos_mudanca_percent', {})
        for tipo, percent in sorted(tipos_mudanca.items(), key=lambda x: x[1], reverse=True):
            descricao = self.tipos_mudanca.get(tipo, tipo)
            count = stats.get('tipos_mudanca', {}).get(tipo, 0)
            report += f"- **{descricao}**: {count} casos ({percent:.1f}%)\n"
        
        report += f"""

## Análise por Instância de Recurso

"""
        
        # Adiciona análise por instância
        por_instancia = stats.get('por_instancia', {})
        for instancia, dados in por_instancia.items():
            total = dados['total']
            favoravel = dados['favoravel']
            reviravolta_fav = dados['reviravolta_favoravel']
            reviravolta_desfav = dados['reviravolta_desfavoravel']
            taxa_sucesso = (favoravel / total * 100) if total > 0 else 0
            
            report += f"""### {instancia}

- **Total de casos**: {total:,}
- **Taxa de sucesso**: {taxa_sucesso:.1f}%
- **Reviravoltas favoráveis**: {reviravolta_fav} casos
- **Reviravoltas desfavoráveis**: {reviravolta_desfav} casos

"""
        
        # Adiciona análise por tribunal
        report += f"""## Análise por Tribunal

"""
        
        por_tribunal = stats.get('por_tribunal', {})
        tribunais_ordenados = sorted(por_tribunal.items(), key=lambda x: x[1]['total'], reverse=True)
        
        for tribunal, dados in tribunais_ordenados[:10]:  # Top 10 tribunais
            total = dados['total']
            favoravel = dados['favoravel']
            taxa_sucesso = (favoravel / total * 100) if total > 0 else 0
            
            report += f"""### {tribunal}

- **Total de casos**: {total:,}
- **Taxa de sucesso**: {taxa_sucesso:.1f}%
- **Casos favoráveis**: {favoravel:,}
- **Casos desfavoráveis**: {dados['desfavoravel']:,}

"""
        
        # Adiciona análise por ano
        report += f"""## Análise Temporal (por Ano)

"""
        
        por_ano = stats.get('por_ano', {})
        anos_ordenados = sorted(por_ano.items())
        
        for ano, dados in anos_ordenados:
            total = dados['total']
            favoravel = dados['favoravel']
            taxa_sucesso = (favoravel / total * 100) if total > 0 else 0
            
            report += f"""### {ano}

- **Total de casos**: {total:,}
- **Taxa de sucesso**: {taxa_sucesso:.1f}%
- **Casos favoráveis**: {favoravel:,}
- **Casos desfavoráveis**: {dados['desfavoravel']:,}

"""
        
        # Adiciona seção específica sobre reformas (código 190)
        reformas_explicitas = sum(1 for f in analysis.get('fluxos_detalhados', []) 
                                if f.get('tem_reforma_explicita', False))
        
        if reformas_explicitas > 0:
            report += f"""## Análise de Reformas Explícitas (Código 190)

### Resumo das Reformas
- **Total de casos com reforma explícita**: {reformas_explicitas:,}
- **Percentual do dataset**: {(reformas_explicitas / stats.get('total_fluxos', 1) * 100):.1f}%

### Importância das Reformas Explícitas
As reformas identificadas pelo código 190 "Reforma de Decisão Anterior" representam casos onde:
1. **Cruzamento direto**: O movimento 190 + complementosTabelados identifica explicitamente o tipo da decisão reformada
2. **Maior precisão**: Elimina a necessidade de inferência temporal entre sentença original e novo julgamento
3. **Dados de complemento**: Acesso ao campo tipo_da_decisao_anterior quando disponível

### Cobertura e Limitações
- **Cobertura incompleta**: Alguns TRTs só passaram a preencher complementos após 2023
- **Processos antigos**: Casos anteriores a 2023 podem não conter o movimento 190
- **Variação entre tribunais**: Nem todos os TRTs implementaram consistentemente o código 190

"""
        
        report += f"""## Fluxos Mais Comuns

"""
        
        # Adiciona fluxos mais comuns
        fluxos_comuns = stats.get('fluxos_mais_comuns', {})
        for fluxo, count in list(fluxos_comuns.items())[:15]:
            percent = (count / stats.get('total_fluxos', 1) * 100)
            report += f"- **{fluxo}**: {count} casos ({percent:.1f}%)\n"
        
        report += f"""

## Interpretação dos Resultados

### Lógica Aplicada

1. **Procedência + Provimento** = Trabalhador perdeu (empregador recorreu e ganhou)
2. **Improcedência + Provimento** = Trabalhador ganhou (trabalhador recorreu e ganhou)
3. **Procedência + Desprovimento** = Trabalhador manteve vitória (empregador recorreu e perdeu)
4. **Improcedência + Desprovimento** = Trabalhador manteve derrota (trabalhador recorreu e perdeu)

### Principais Insights

"""
        
        # Adiciona insights baseados nos dados
        if tipos_mudanca.get('reviravolta_desfavoravel', 0) > tipos_mudanca.get('reviravolta_favoravel', 0):
            report += "- Os empregadores têm mais sucesso em recursos do que os trabalhadores\n"
        elif tipos_mudanca.get('reviravolta_favoravel', 0) > tipos_mudanca.get('reviravolta_desfavoravel', 0):
            report += "- Os trabalhadores têm mais sucesso em recursos do que os empregadores\n"
        
        manteve_favoravel = tipos_mudanca.get('manteve_favoravel', 0)
        manteve_desfavoravel = tipos_mudanca.get('manteve_desfavoravel', 0)
        
        if manteve_favoravel > manteve_desfavoravel:
            report += "- Trabalhadores que ganham em 1ª instância tendem a manter a vitória\n"
        else:
            report += "- Trabalhadores que perdem em 1ª instância tendem a manter a derrota\n"
        
        return report
    
    def get_flow_examples(self, analysis: Dict[str, Any], num_examples: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna exemplos representativos de diferentes tipos de fluxo.
        
        Args:
            analysis: Resultado da análise
            num_examples: Número de exemplos por tipo
            
        Returns:
            Lista de exemplos organizados por tipo
        """
        fluxos = analysis.get('fluxos_detalhados', [])
        
        # Agrupa por tipo de mudança
        por_tipo = {}
        for fluxo in fluxos:
            tipo = fluxo['interpretacao']['tipo_mudanca']
            if tipo not in por_tipo:
                por_tipo[tipo] = []
            por_tipo[tipo].append(fluxo)
        
        # Retorna exemplos de cada tipo
        exemplos = {}
        for tipo, casos in por_tipo.items():
            exemplos[tipo] = casos[:num_examples]
        
        return exemplos