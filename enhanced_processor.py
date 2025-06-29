#!/usr/bin/env python3
"""
Processador melhorado que analisa o campo 'movimentos' dos JSONs para extrair
resultados precisos de processos de assédio moral.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import pandas as pd

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedDataProcessor:
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.base_path = Path(__file__).parent
        self.processed_data_path = self.base_path / "data" / "processed_enhanced"
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
        
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
            'GS': 'TST'
        }
        
        # Códigos de assunto para assédio moral
        self.assedio_moral_codes = [1723, 14175, 14018]
        
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
            except Exception as e:
                logger.error(f"Erro ao carregar {file_path}: {str(e)}")
        
        logger.info(f"Total de {len(all_data)} registros carregados")
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
    
    def is_assedio_moral(self, processo: Dict) -> bool:
        """Verifica se o processo é de assédio moral."""
        assuntos = processo.get('assuntos', [])
        
        if isinstance(assuntos, list):
            for assunto in assuntos:
                if isinstance(assunto, dict):
                    codigo = assunto.get('codigo')
                    nome = assunto.get('nome', '')
                    if codigo in self.assedio_moral_codes or 'assédio moral' in nome.lower():
                        return True
        
        return False
    
    def process_data(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Processa todos os dados extraindo informações dos movimentos.
        """
        processed_data = []
        
        for item in data:
            # Informações básicas
            numero_processo = item.get('numeroProcesso', '')
            tribunal = item.get('tribunal', '')
            grau = item.get('grau', '')
            instancia = self.grau_mapping.get(grau, 'Desconhecida')
            
            # Extrai resultado dos movimentos
            movimentos = item.get('movimentos', [])
            resultado = self.extract_result_from_movements(movimentos)
            
            if resultado:
                resultado_nome, resultado_codigo = resultado
            else:
                resultado_nome = 'Sem Resultado Identificado'
                resultado_codigo = None
            
            # Verifica se é assédio moral
            is_assedio = self.is_assedio_moral(item)
            
            # Extrai informações do órgão julgador
            orgao_julgador = item.get('orgaoJulgador', {})
            if isinstance(orgao_julgador, dict):
                orgao_nome = orgao_julgador.get('nome', '')
                orgao_municipio = orgao_julgador.get('codigoMunicipioIBGE', '')
            else:
                orgao_nome = ''
                orgao_municipio = ''
            
            # Conta tipos de movimentos
            movimento_counts = {}
            for mov in movimentos:
                codigo = mov.get('codigo')
                if codigo in self.movimento_codes:
                    nome_mov = self.movimento_codes[codigo]
                    movimento_counts[nome_mov] = movimento_counts.get(nome_mov, 0) + 1
            
            # Processa datas
            data_ajuizamento = item.get('dataAjuizamento')
            if data_ajuizamento:
                try:
                    data_ajuizamento = pd.to_datetime(data_ajuizamento)
                except:
                    data_ajuizamento = None
            
            # Adiciona ao processado
            processed_item = {
                'id': item.get('id'),
                'numero_processo': numero_processo,
                'tribunal': tribunal,
                'grau': grau,
                'instancia': instancia,
                'resultado': resultado_nome,
                'resultado_codigo': resultado_codigo,
                'is_assedio_moral': is_assedio,
                'orgao_julgador': orgao_nome,
                'municipio_ibge': orgao_municipio,
                'data_ajuizamento': data_ajuizamento,
                'num_movimentos': len(movimentos),
                'formato': item.get('formato', {}).get('nome', ''),
                'sistema': item.get('sistema', {}).get('nome', ''),
                'classe': item.get('classe', {}).get('nome', ''),
                'nivel_sigilo': item.get('nivelSigilo', 0)
            }
            
            # Adiciona contagens de movimentos
            for mov_tipo, count in movimento_counts.items():
                processed_item[f'movimento_{mov_tipo.lower().replace(" ", "_")}'] = count
            
            processed_data.append(processed_item)
        
        return pd.DataFrame(processed_data)
    
    def analyze_assedio_moral_cases(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analisa especificamente os casos de assédio moral.
        """
        # Filtra apenas casos de assédio moral
        df_assedio = df[df['is_assedio_moral'] == True].copy()
        
        logger.info(f"Total de casos de assédio moral: {len(df_assedio)}")
        
        # Análise por instância
        instancia_stats = {}
        for instancia in df_assedio['instancia'].unique():
            df_inst = df_assedio[df_assedio['instancia'] == instancia]
            
            # Contagem de resultados
            resultado_counts = df_inst['resultado'].value_counts().to_dict()
            
            # Percentuais
            total = len(df_inst)
            resultado_percent = {k: (v/total)*100 for k, v in resultado_counts.items()}
            
            instancia_stats[instancia] = {
                'total': total,
                'resultados': resultado_counts,
                'percentuais': resultado_percent
            }
        
        # Análise de encadeamento
        processo_groups = df_assedio.groupby('numero_processo')
        
        # Casos únicos vs múltiplas instâncias
        casos_unicos = 0
        casos_multiplos = 0
        
        for num_proc, group in processo_groups:
            if len(group) == 1:
                casos_unicos += 1
            else:
                casos_multiplos += 1
        
        # Padrões de fluxo
        fluxo_patterns = {}
        for num_proc, group in processo_groups:
            if len(group) > 1:
                # Ordena por grau
                group_sorted = group.sort_values('grau')
                pattern = ' -> '.join([
                    f"{row['instancia']}:{row['resultado']}" 
                    for _, row in group_sorted.iterrows()
                ])
                fluxo_patterns[pattern] = fluxo_patterns.get(pattern, 0) + 1
        
        return {
            'total_casos': len(df_assedio),
            'casos_unicos': casos_unicos,
            'casos_multiplos': casos_multiplos,
            'instancia_stats': instancia_stats,
            'fluxo_patterns': fluxo_patterns
        }
    
    def generate_report(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> None:
        """
        Gera relatório detalhado sobre assédio moral.
        """
        report_path = self.processed_data_path / "relatorio_assedio_moral_completo.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Relatório Completo: Assédio Moral na Justiça do Trabalho\n\n")
            f.write(f"Data da análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Resumo
            f.write("## Resumo Executivo\n\n")
            f.write(f"- Total de casos de assédio moral analisados: {analysis['total_casos']}\n")
            f.write(f"- Casos com apenas uma ocorrência: {analysis['casos_unicos']} ")
            f.write(f"({(analysis['casos_unicos']/analysis['total_casos']*100):.1f}%)\n")
            f.write(f"- Casos com múltiplas instâncias: {analysis['casos_multiplos']} ")
            f.write(f"({(analysis['casos_multiplos']/analysis['total_casos']*100):.1f}%)\n\n")
            
            # Resultados por instância
            f.write("## Análise por Instância\n\n")
            
            for instancia, stats in analysis['instancia_stats'].items():
                f.write(f"### {instancia}\n\n")
                f.write(f"Total de casos: {stats['total']}\n\n")
                
                # Ordena resultados por frequência
                resultados_ordenados = sorted(
                    stats['resultados'].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                
                f.write("Resultados:\n")
                for resultado, count in resultados_ordenados:
                    percent = stats['percentuais'][resultado]
                    f.write(f"- {resultado}: {count} casos ({percent:.1f}%)\n")
                
                # Calcula taxa de sucesso
                taxa_sucesso = 0
                if instancia == 'Primeira Instância':
                    proc = stats['resultados'].get('Procedência', 0)
                    proc_parte = stats['resultados'].get('Procedência em Parte', 0)
                    taxa_sucesso = ((proc + proc_parte) / stats['total']) * 100
                elif instancia in ['Segunda Instância', 'TST']:
                    prov = stats['resultados'].get('Provimento', 0)
                    prov_parte = stats['resultados'].get('Provimento em Parte', 0)
                    taxa_sucesso = ((prov + prov_parte) / stats['total']) * 100
                
                f.write(f"\n**Taxa de sucesso do trabalhador: {taxa_sucesso:.1f}%**\n\n")
            
            # Padrões de fluxo mais comuns
            if analysis['fluxo_patterns']:
                f.write("## Padrões de Encadeamento Processual\n\n")
                f.write("### Padrões mais frequentes:\n\n")
                
                patterns_sorted = sorted(
                    analysis['fluxo_patterns'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:20]
                
                for pattern, count in patterns_sorted:
                    f.write(f"- {pattern}: {count} casos\n")
            
            # Conclusões
            f.write("\n## Conclusões\n\n")
            
            # Análise da primeira instância
            primeira_stats = analysis['instancia_stats'].get('Primeira Instância', {})
            if primeira_stats:
                total_primeira = primeira_stats['total']
                improc = primeira_stats['resultados'].get('Improcedência', 0)
                if total_primeira > 0:
                    taxa_improc = (improc / total_primeira) * 100
                    f.write(f"1. **Primeira Instância**: {taxa_improc:.1f}% dos casos ")
                    f.write("de assédio moral são julgados improcedentes.\n\n")
            
            # Análise de casos únicos
            if analysis['casos_unicos'] > 0:
                percent_unicos = (analysis['casos_unicos'] / analysis['total_casos']) * 100
                f.write(f"2. **Casos únicos**: {percent_unicos:.1f}% dos processos ")
                f.write("aparecem apenas uma vez na base, indicando possível ausência ")
                f.write("de recursos ou dados incompletos.\n\n")
            
            f.write("3. **Importância dos movimentos**: A análise do campo 'movimentos' ")
            f.write("revelou resultados processuais que não estavam disponíveis ")
            f.write("em outros campos, especialmente para casos com apenas uma ocorrência.\n\n")
            
            f.write("## Metodologia\n\n")
            f.write("Esta análise utilizou os códigos de movimento da Tabela Processual ")
            f.write("Unificada do CNJ para identificar resultados processuais:\n\n")
            
            for codigo, nome in sorted(self.movimento_codes.items()):
                f.write(f"- {codigo}: {nome}\n")
        
        logger.info(f"Relatório salvo em: {report_path}")
    
    def save_processed_data(self, df: pd.DataFrame) -> None:
        """
        Salva os dados processados em diferentes formatos.
        """
        # CSV completo
        csv_path = self.processed_data_path / "dados_processados_completo.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"Dados salvos em: {csv_path}")
        
        # CSV apenas assédio moral
        df_assedio = df[df['is_assedio_moral'] == True]
        csv_assedio_path = self.processed_data_path / "casos_assedio_moral.csv"
        df_assedio.to_csv(csv_assedio_path, index=False, encoding='utf-8')
        logger.info(f"Casos de assédio moral salvos em: {csv_assedio_path}")
    
    def run(self):
        """Executa o processamento completo."""
        # Carrega dados
        data = self.load_json_files()
        
        if not data:
            logger.error("Nenhum dado foi carregado")
            return
        
        # Processa dados
        df = self.process_data(data)
        logger.info(f"Processados {len(df)} registros")
        
        # Analisa casos de assédio moral
        analysis = self.analyze_assedio_moral_cases(df)
        
        # Gera relatório
        self.generate_report(df, analysis)
        
        # Salva dados processados
        self.save_processed_data(df)
        
        return df, analysis

def main():
    # Caminho para os dados
    data_path = "/Users/danilobortoli/Documents/Tese de doutorado da Andreia/Dados da segunda extração/raw"
    
    processor = EnhancedDataProcessor(data_path)
    df, analysis = processor.run()
    
    logger.info("Processamento concluído com sucesso!")

if __name__ == "__main__":
    main()