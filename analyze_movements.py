#!/usr/bin/env python3
"""
Script para analisar o campo 'movimentos' dos arquivos JSON e extrair resultados
de processos de assédio moral, incluindo casos com apenas uma ocorrência.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
import pandas as pd
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MovementAnalyzer:
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.base_path = Path(__file__).parent
        self.output_path = self.base_path / "resultados_movimentos"
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Códigos de movimento importantes (TPU/CNJ)
        self.movimento_codes = {
            # Primeira instância
            219: "Procedência",
            220: "Improcedência",
            221: "Procedência em Parte",
            # Recursos
            237: "Provimento",
            242: "Desprovimento",
            236: "Negação de Seguimento",
            238: "Provimento em Parte",
            # Outros relevantes
            471: "Homologação de Acordo",
            466: "Extinção sem Resolução de Mérito",
            487: "Extinção com Resolução de Mérito"
        }
        
        # Mapeamento de grau para instância
        self.grau_mapping = {
            'G1': 'Primeira Instância',
            'G2': 'Segunda Instância',
            'GS': 'TST'  # Grau Superior
        }
        
    def load_json_files(self) -> List[Dict[str, Any]]:
        """Carrega todos os arquivos JSON do diretório especificado."""
        all_data = []
        json_files = list(self.data_path.glob("*.json"))
        
        logger.info(f"Encontrados {len(json_files)} arquivos JSON para processar")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
                    logger.info(f"Carregados dados de {file_path.name}")
            except Exception as e:
                logger.error(f"Erro ao carregar {file_path}: {str(e)}")
        
        return all_data
    
    def extract_result_from_movements(self, movimentos: List[Dict]) -> Optional[Tuple[str, int]]:
        """
        Extrai o resultado do processo analisando os movimentos.
        Retorna tupla (resultado, código) ou None se não encontrar.
        """
        if not movimentos:
            return None
        
        # Procura pelos códigos de movimento relevantes
        for mov in movimentos:
            codigo = mov.get('codigo')
            if codigo in self.movimento_codes:
                return (self.movimento_codes[codigo], codigo)
        
        return None
    
    def analyze_single_occurrence_cases(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Analisa casos que aparecem apenas uma vez na base de dados,
        extraindo resultado dos movimentos.
        """
        # Conta ocorrências de cada número de processo
        processo_counts = Counter()
        processo_data = defaultdict(list)
        
        for item in data:
            numero = item.get('numeroProcesso', '')
            if numero:
                processo_counts[numero] += 1
                processo_data[numero].append(item)
        
        # Identifica processos com apenas uma ocorrência
        single_occurrence = {num: data[0] for num, data in processo_data.items() 
                           if processo_counts[num] == 1}
        
        logger.info(f"Total de processos únicos: {len(processo_counts)}")
        logger.info(f"Processos com apenas uma ocorrência: {len(single_occurrence)}")
        
        # Analisa resultados dos casos únicos
        results_by_instance = defaultdict(lambda: defaultdict(int))
        detailed_results = []
        
        for numero, processo in single_occurrence.items():
            movimentos = processo.get('movimentos', [])
            grau = processo.get('grau', '')
            instancia = self.grau_mapping.get(grau, 'Desconhecida')
            
            # Extrai resultado dos movimentos
            resultado = self.extract_result_from_movements(movimentos)
            
            if resultado:
                resultado_nome, resultado_codigo = resultado
                results_by_instance[instancia][resultado_nome] += 1
                
                # Verifica se é caso de assédio moral
                assuntos = processo.get('assuntos', [])
                is_assedio = False
                if isinstance(assuntos, list):
                    for assunto in assuntos:
                        if isinstance(assunto, dict):
                            codigo = assunto.get('codigo')
                            nome = assunto.get('nome', '')
                            if codigo in [1723, 14175, 14018] or 'assédio moral' in nome.lower():
                                is_assedio = True
                                break
                
                detailed_results.append({
                    'numero_processo': numero,
                    'tribunal': processo.get('tribunal'),
                    'grau': grau,
                    'instancia': instancia,
                    'resultado': resultado_nome,
                    'resultado_codigo': resultado_codigo,
                    'is_assedio_moral': is_assedio,
                    'data_ajuizamento': processo.get('dataAjuizamento'),
                    'orgao_julgador': processo.get('orgaoJulgador', {}).get('nome'),
                    'num_movimentos': len(movimentos)
                })
            else:
                results_by_instance[instancia]['Sem Resultado Identificado'] += 1
        
        return {
            'total_single_occurrence': len(single_occurrence),
            'results_by_instance': dict(results_by_instance),
            'detailed_results': detailed_results
        }
    
    def analyze_case_chains(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Analisa o encadeamento de processos entre instâncias.
        """
        # Agrupa processos pelo número
        processo_chains = defaultdict(list)
        
        for item in data:
            numero = item.get('numeroProcesso', '')
            if numero:
                processo_chains[numero].append(item)
        
        # Analisa cadeias
        chain_patterns = defaultdict(int)
        detailed_chains = []
        
        for numero, chain in processo_chains.items():
            if len(chain) > 1:
                # Ordena por grau (G1 -> G2 -> GS)
                def grau_order(item):
                    grau = item.get('grau', 'G1')
                    if grau in ('G1', 'G2', 'GS'):
                        return ('G1', 'G2', 'GS').index(grau)
                    else:
                        return 999  # Coloca graus desconhecidos no final
                
                chain_sorted = sorted(chain, key=grau_order)
                
                # Cria padrão da cadeia
                pattern_parts = []
                chain_details = {
                    'numero_processo': numero,
                    'num_instancias': len(chain),
                    'instancias': []
                }
                
                for item in chain_sorted:
                    grau = item.get('grau', '')
                    instancia = self.grau_mapping.get(grau, 'Desconhecida')
                    movimentos = item.get('movimentos', [])
                    resultado = self.extract_result_from_movements(movimentos)
                    
                    if resultado:
                        resultado_nome, _ = resultado
                        pattern_parts.append(f"{instancia}:{resultado_nome}")
                        
                        chain_details['instancias'].append({
                            'instancia': instancia,
                            'resultado': resultado_nome,
                            'tribunal': item.get('tribunal'),
                            'data': item.get('dataAjuizamento')
                        })
                
                if pattern_parts:
                    pattern = ' -> '.join(pattern_parts)
                    chain_patterns[pattern] += 1
                    chain_details['pattern'] = pattern
                    detailed_chains.append(chain_details)
        
        return {
            'total_chains': len([c for c in processo_chains.values() if len(c) > 1]),
            'chain_patterns': dict(chain_patterns),
            'detailed_chains': detailed_chains[:100]  # Limita para não ficar muito grande
        }
    
    def generate_comprehensive_report(self, data: List[Dict]) -> None:
        """
        Gera um relatório completo analisando todos os aspectos dos movimentos.
        """
        logger.info("Iniciando análise compreensiva dos movimentos...")
        
        # 1. Análise de casos únicos
        single_occurrence = self.analyze_single_occurrence_cases(data)
        
        # 2. Análise de encadeamento
        chains = self.analyze_case_chains(data)
        
        # 3. Análise geral de movimentos
        all_movements = defaultdict(int)
        movement_by_instance = defaultdict(lambda: defaultdict(int))
        
        for item in data:
            grau = item.get('grau', '')
            instancia = self.grau_mapping.get(grau, 'Desconhecida')
            
            for mov in item.get('movimentos', []):
                codigo = mov.get('codigo')
                nome = mov.get('nome', '')
                
                if codigo in self.movimento_codes:
                    all_movements[f"{codigo} - {nome}"] += 1
                    movement_by_instance[instancia][f"{codigo} - {nome}"] += 1
        
        # Gera relatório
        report_path = self.output_path / "relatorio_analise_movimentos.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Análise Detalhada dos Movimentos Processuais - Assédio Moral\n\n")
            f.write(f"Data da análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Resumo geral
            f.write("## Resumo Geral\n\n")
            f.write(f"- Total de registros analisados: {len(data)}\n")
            f.write(f"- Processos únicos: {len(set(item.get('numeroProcesso', '') for item in data))}\n")
            f.write(f"- Processos com apenas uma ocorrência: {single_occurrence['total_single_occurrence']}\n")
            f.write(f"- Processos com múltiplas instâncias: {chains['total_chains']}\n\n")
            
            # Casos com apenas uma ocorrência
            f.write("## Análise de Casos com Apenas Uma Ocorrência\n\n")
            f.write("### Resultados por Instância\n\n")
            
            for instancia, resultados in single_occurrence['results_by_instance'].items():
                f.write(f"**{instancia}:**\n")
                total_inst = sum(resultados.values())
                for resultado, count in sorted(resultados.items(), key=lambda x: x[1], reverse=True):
                    percent = (count / total_inst * 100) if total_inst > 0 else 0
                    f.write(f"- {resultado}: {count} ({percent:.1f}%)\n")
                f.write("\n")
            
            # Padrões de encadeamento
            f.write("## Padrões de Encadeamento entre Instâncias\n\n")
            f.write("### Padrões mais comuns:\n\n")
            
            for pattern, count in sorted(chains['chain_patterns'].items(), 
                                       key=lambda x: x[1], reverse=True)[:20]:
                f.write(f"- {pattern}: {count} casos\n")
            
            # Movimentos importantes
            f.write("\n## Códigos de Movimento Importantes Encontrados\n\n")
            
            for mov, count in sorted(all_movements.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {mov}: {count} ocorrências\n")
            
            # Distribuição por instância
            f.write("\n## Distribuição de Movimentos por Instância\n\n")
            
            for instancia, movimentos in movement_by_instance.items():
                f.write(f"### {instancia}\n\n")
                for mov, count in sorted(movimentos.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {mov}: {count}\n")
                f.write("\n")
            
            # Exemplos de casos únicos
            f.write("## Exemplos de Casos com Apenas Uma Ocorrência\n\n")
            
            assedio_cases = [r for r in single_occurrence['detailed_results'] 
                           if r['is_assedio_moral']][:10]
            
            for caso in assedio_cases:
                f.write(f"**Processo {caso['numero_processo']}**\n")
                f.write(f"- Tribunal: {caso['tribunal']}\n")
                f.write(f"- Instância: {caso['instancia']}\n")
                f.write(f"- Resultado: {caso['resultado']}\n")
                f.write(f"- Órgão Julgador: {caso['orgao_julgador']}\n")
                f.write(f"- Número de movimentos: {caso['num_movimentos']}\n\n")
        
        # Salva dados detalhados em CSV
        if single_occurrence['detailed_results']:
            df_single = pd.DataFrame(single_occurrence['detailed_results'])
            df_single.to_csv(self.output_path / "casos_ocorrencia_unica.csv", 
                           index=False, encoding='utf-8')
            logger.info(f"Salvos {len(df_single)} casos únicos em CSV")
        
        logger.info(f"Relatório salvo em: {report_path}")
    
    def run_analysis(self):
        """Executa a análise completa."""
        # Carrega dados
        data = self.load_json_files()
        
        if not data:
            logger.error("Nenhum dado foi carregado")
            return
        
        # Gera relatório compreensivo
        self.generate_comprehensive_report(data)

def main():
    # Caminho para os dados
    data_path = "/Users/danilobortoli/Documents/Tese de doutorado da Andreia/Dados da segunda extração/raw"
    
    analyzer = MovementAnalyzer(data_path)
    analyzer.run_analysis()

if __name__ == "__main__":
    main()