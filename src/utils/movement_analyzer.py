#!/usr/bin/env python3
"""
Módulo utilitário para análise de movimentos processuais.
Centraliza toda lógica relacionada aos códigos de movimento da TPU/CNJ.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MovementAnalyzer:
    """Classe para análise unificada de movimentos processuais."""
    
    def __init__(self):
        # Códigos de movimento da Tabela Processual Unificada (TPU/CNJ)
        self.movement_codes = {
            # Primeira instância - Mérito
            219: "Procedência",
            220: "Improcedência", 
            221: "Procedência em Parte",
            
            # Recursos - Segunda instância e superiores
            237: "Provimento",
            242: "Desprovimento",
            236: "Negação de Seguimento",
            238: "Provimento em Parte",
            
            # Reforma de decisões - CRÍTICO para análise de mérito
            190: "Reforma de Decisão Anterior",
            
            # Outros tipos relevantes
            471: "Homologação de Acordo",
            466: "Extinção sem Resolução de Mérito",
            487: "Extinção com Resolução de Mérito",
            
            # Códigos adicionais encontrados na base
            11009: "Sentença Publicada",
            123: "Juntada de Petição",
            246: "Recebimento dos Autos",
            51: "Audiência Designada"
        }
        
        # Mapeamento de grau para instância
        self.grau_mapping = {
            'G1': 'Primeira Instância',
            'G2': 'Segunda Instância', 
            'GS': 'TST',
            'GRAU_1': 'Primeira Instância',
            'GRAU_2': 'Segunda Instância'
        }
        
        # Códigos que indicam resultado favorável ao trabalhador
        self.favorable_codes = {
            'Primeira Instância': [219, 221],  # Procedência, Procedência em Parte
            'Segunda Instância': [237, 238],   # Provimento, Provimento em Parte
            'TST': [237, 238]                  # Provimento, Provimento em Parte
        }
        
        # Códigos que indicam resultado desfavorável ao trabalhador
        self.unfavorable_codes = {
            'Primeira Instância': [220],       # Improcedência
            'Segunda Instância': [242, 236],   # Desprovimento, Negação de Seguimento
            'TST': [242, 236]                  # Desprovimento, Negação de Seguimento
        }
    
    def extract_result_from_movements(self, movimentos: List[Dict]) -> Optional[Tuple[str, int]]:
        """
        Extrai o resultado principal do processo analisando os movimentos.
        
        Args:
            movimentos: Lista de movimentos do processo
            
        Returns:
            Tupla (nome_resultado, codigo) ou None se não encontrar
        """
        if not movimentos or not isinstance(movimentos, list):
            return None
        
        # Prioridade: códigos de mérito primeiro (190 adicionado para reformas)
        priority_codes = [190, 219, 220, 221, 237, 238, 242, 236]
        
        # Procura por códigos prioritários primeiro
        for priority_code in priority_codes:
            for movimento in movimentos:
                if isinstance(movimento, dict):
                    codigo = movimento.get('codigo')
                    if codigo == priority_code:
                        return (self.movement_codes[codigo], codigo)
        
        # Se não encontrou códigos prioritários, procura outros relevantes
        for movimento in movimentos:
            if isinstance(movimento, dict):
                codigo = movimento.get('codigo')
                if codigo in self.movement_codes:
                    return (self.movement_codes[codigo], codigo)
        
        return None
    
    def extract_complementos_data(self, movimento: Dict) -> Optional[Dict[str, Any]]:
        """
        Extrai dados dos complementosTabelados de um movimento.
        
        Args:
            movimento: Dicionário com dados do movimento
            
        Returns:
            Dicionário com dados dos complementos ou None se não houver
        """
        complementos = movimento.get('complementosTabelados', [])
        if not complementos:
            return None
        
        dados_complementos = {}
        for complemento in complementos:
            nome = complemento.get('nome', '')
            descricao = complemento.get('descricao', '')
            valor = complemento.get('valor')
            codigo = complemento.get('codigo')
            
            # Armazena dados relevantes dos complementos
            if nome or descricao:
                chave = descricao if descricao else nome
                dados_complementos[chave] = {
                    'valor': valor,
                    'codigo': codigo,
                    'nome': nome,
                    'descricao': descricao
                }
        
        return dados_complementos if dados_complementos else None
    
    def analyze_reforma_decisions(self, movimentos: List[Dict]) -> Dict[str, Any]:
        """
        Analisa movimentos de reforma de decisão (código 190).
        
        Args:
            movimentos: Lista de movimentos do processo
            
        Returns:
            Análise das reformas encontradas
        """
        reformas = []
        
        for movimento in movimentos:
            if movimento.get('codigo') == 190:
                complementos = self.extract_complementos_data(movimento)
                
                reforma_info = {
                    'codigo': 190,
                    'nome': movimento.get('nome', 'Reforma de Decisão Anterior'),
                    'dataHora': movimento.get('dataHora'),
                    'complementos': complementos
                }
                
                # Tenta identificar o tipo da decisão reformada
                if complementos:
                    for chave, dados in complementos.items():
                        if 'decisao' in chave.lower() or 'tipo' in chave.lower():
                            reforma_info['tipo_decisao_anterior'] = dados
                
                reformas.append(reforma_info)
        
        return {
            'total_reformas': len(reformas),
            'reformas_detalhadas': reformas,
            'tem_reforma': len(reformas) > 0
        }
    
    def classify_result_outcome(self, resultado_codigo: int, instancia: str) -> str:
        """
        Classifica o resultado como favorável, desfavorável ou neutro.
        
        Args:
            resultado_codigo: Código do movimento de resultado
            instancia: Instância do processo
            
        Returns:
            'favoravel', 'desfavoravel' ou 'neutro'
        """
        if resultado_codigo in self.favorable_codes.get(instancia, []):
            return 'favoravel'
        elif resultado_codigo in self.unfavorable_codes.get(instancia, []):
            return 'desfavoravel'
        else:
            return 'neutro'
    
    def calculate_success_rate(self, resultados: List[Dict[str, Any]], 
                             instancia: str) -> Dict[str, float]:
        """
        Calcula taxa de sucesso para uma instância específica.
        
        Args:
            resultados: Lista de resultados processados
            instancia: Nome da instância
            
        Returns:
            Dicionário com estatísticas de sucesso
        """
        total = len(resultados)
        if total == 0:
            return {'total': 0, 'favoravel': 0, 'desfavoravel': 0, 'neutro': 0,
                   'taxa_sucesso': 0.0}
        
        favoravel = 0
        desfavoravel = 0
        neutro = 0
        
        for resultado in resultados:
            codigo = resultado.get('resultado_codigo')
            if codigo:
                classificacao = self.classify_result_outcome(codigo, instancia)
                if classificacao == 'favoravel':
                    favoravel += 1
                elif classificacao == 'desfavoravel':
                    desfavoravel += 1
                else:
                    neutro += 1
        
        taxa_sucesso = (favoravel / total) * 100 if total > 0 else 0
        
        return {
            'total': total,
            'favoravel': favoravel,
            'desfavoravel': desfavoravel,
            'neutro': neutro,
            'taxa_sucesso': taxa_sucesso,
            'taxa_sucesso_percent': f"{taxa_sucesso:.1f}%"
        }
    
    def analyze_movement_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa padrões de movimentos em todo o dataset.
        
        Args:
            data: Lista de dados dos processos
            
        Returns:
            Dicionário com análise de padrões
        """
        movement_frequency = {}
        results_by_instance = {}
        
        for item in data:
            movimentos = item.get('movimentos', [])
            grau = item.get('grau', '')
            instancia = self.grau_mapping.get(grau, 'Desconhecida')
            
            # Conta frequência de movimentos
            for movimento in movimentos:
                if isinstance(movimento, dict):
                    codigo = movimento.get('codigo')
                    nome = movimento.get('nome', f'Código {codigo}')
                    
                    if codigo in self.movement_codes:
                        key = f"{codigo} - {self.movement_codes[codigo]}"
                        movement_frequency[key] = movement_frequency.get(key, 0) + 1
            
            # Analisa resultados por instância
            resultado = self.extract_result_from_movements(movimentos)
            if resultado:
                resultado_nome, resultado_codigo = resultado
                
                if instancia not in results_by_instance:
                    results_by_instance[instancia] = {}
                
                if resultado_nome not in results_by_instance[instancia]:
                    results_by_instance[instancia][resultado_nome] = []
                
                results_by_instance[instancia][resultado_nome].append({
                    'numero_processo': item.get('numeroProcesso', ''),
                    'resultado_codigo': resultado_codigo,
                    'tribunal': item.get('tribunal', '')
                })
        
        # Calcula estatísticas por instância
        stats_by_instance = {}
        for instancia, resultados in results_by_instance.items():
            all_results = []
            contagens = {}
            
            for resultado_nome, casos in resultados.items():
                contagens[resultado_nome] = len(casos)
                all_results.extend(casos)
            
            total = len(all_results)
            percentuais = {k: (v/total)*100 for k, v in contagens.items()} if total > 0 else {}
            
            success_stats = self.calculate_success_rate(all_results, instancia)
            
            stats_by_instance[instancia] = {
                'total': total,
                'contagens': contagens,
                'percentuais': percentuais,
                'success_stats': success_stats
            }
        
        return {
            'movement_frequency': movement_frequency,
            'stats_by_instance': stats_by_instance,
            'total_analyzed': len(data)
        }
    
    def get_case_chain_pattern(self, chain: List[Dict[str, Any]]) -> str:
        """
        Cria padrão de encadeamento para um grupo de processos relacionados.
        
        Args:
            chain: Lista de processos da mesma cadeia
            
        Returns:
            String representando o padrão de fluxo
        """
        # Ordena por grau
        def grau_order(item):
            grau = item.get('grau', 'G1')
            if grau in ('G1', 'G2', 'GS'):
                return ('G1', 'G2', 'GS').index(grau)
            else:
                return 999
        
        chain_sorted = sorted(chain, key=grau_order)
        
        pattern_parts = []
        for item in chain_sorted:
            grau = item.get('grau', '')
            instancia = self.grau_mapping.get(grau, 'Desconhecida')
            movimentos = item.get('movimentos', [])
            resultado = self.extract_result_from_movements(movimentos)
            
            if resultado:
                resultado_nome, _ = resultado
                pattern_parts.append(f"{instancia}:{resultado_nome}")
            else:
                pattern_parts.append(f"{instancia}:Sem Resultado")
        
        return ' -> '.join(pattern_parts)
    
    def is_assedio_moral_case(self, processo: Dict[str, Any]) -> bool:
        """
        Verifica se um processo é de assédio moral.
        
        Args:
            processo: Dados do processo
            
        Returns:
            True se for caso de assédio moral
        """
        assedio_codes = [1723, 14175, 14018]
        assuntos = processo.get('assuntos', [])
        
        if isinstance(assuntos, list):
            for assunto in assuntos:
                if isinstance(assunto, dict):
                    codigo = assunto.get('codigo')
                    nome = assunto.get('nome', '')
                    if codigo in assedio_codes or 'assédio moral' in nome.lower():
                        return True
        
        return False