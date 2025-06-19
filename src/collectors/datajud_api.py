import logging
from typing import List, Dict, Any
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataJudAPI:
    # Endpoints específicos para cada tribunal
    TRIBUNAL_ENDPOINTS = {
        "TST": "https://api-publica.datajud.cnj.jus.br/api_publica_tst/_search",
        "TRT1": "https://api-publica.datajud.cnj.jus.br/api_publica_trt1/_search",
        "TRT2": "https://api-publica.datajud.cnj.jus.br/api_publica_trt2/_search",
        "TRT3": "https://api-publica.datajud.cnj.jus.br/api_publica_trt3/_search",
        "TRT4": "https://api-publica.datajud.cnj.jus.br/api_publica_trt4/_search",
        "TRT5": "https://api-publica.datajud.cnj.jus.br/api_publica_trt5/_search",
        "TRT6": "https://api-publica.datajud.cnj.jus.br/api_publica_trt6/_search",
        "TRT7": "https://api-publica.datajud.cnj.jus.br/api_publica_trt7/_search",
        "TRT8": "https://api-publica.datajud.cnj.jus.br/api_publica_trt8/_search",
        "TRT9": "https://api-publica.datajud.cnj.jus.br/api_publica_trt9/_search",
        "TRT10": "https://api-publica.datajud.cnj.jus.br/api_publica_trt10/_search",
        "TRT11": "https://api-publica.datajud.cnj.jus.br/api_publica_trt11/_search",
        "TRT12": "https://api-publica.datajud.cnj.jus.br/api_publica_trt12/_search",
        "TRT13": "https://api-publica.datajud.cnj.jus.br/api_publica_trt13/_search",
        "TRT14": "https://api-publica.datajud.cnj.jus.br/api_publica_trt14/_search",
        "TRT15": "https://api-publica.datajud.cnj.jus.br/api_publica_trt15/_search",
        "TRT16": "https://api-publica.datajud.cnj.jus.br/api_publica_trt16/_search",
        "TRT17": "https://api-publica.datajud.cnj.jus.br/api_publica_trt17/_search",
        "TRT18": "https://api-publica.datajud.cnj.jus.br/api_publica_trt18/_search",
        "TRT19": "https://api-publica.datajud.cnj.jus.br/api_publica_trt19/_search",
        "TRT20": "https://api-publica.datajud.cnj.jus.br/api_publica_trt20/_search",
        "TRT21": "https://api-publica.datajud.cnj.jus.br/api_publica_trt21/_search",
        "TRT22": "https://api-publica.datajud.cnj.jus.br/api_publica_trt22/_search",
        "TRT23": "https://api-publica.datajud.cnj.jus.br/api_publica_trt23/_search",
        "TRT24": "https://api-publica.datajud.cnj.jus.br/api_publica_trt24/_search",
    }
    
    # Nomes dos tribunais trabalhistas
    TRIBUNAL_NAMES = {
        "TST": "Tribunal Superior do Trabalho",
        "TRT1": "Tribunal Regional do Trabalho da 1ª Região (Rio de Janeiro)",
        "TRT2": "Tribunal Regional do Trabalho da 2ª Região (São Paulo)",
        "TRT3": "Tribunal Regional do Trabalho da 3ª Região (Minas Gerais)",
        "TRT4": "Tribunal Regional do Trabalho da 4ª Região (Rio Grande do Sul)",
        "TRT5": "Tribunal Regional do Trabalho da 5ª Região (Bahia)",
        "TRT6": "Tribunal Regional do Trabalho da 6ª Região (Pernambuco)",
        "TRT7": "Tribunal Regional do Trabalho da 7ª Região (Ceará)",
        "TRT8": "Tribunal Regional do Trabalho da 8ª Região (Pará e Amapá)",
        "TRT9": "Tribunal Regional do Trabalho da 9ª Região (Paraná)",
        "TRT10": "Tribunal Regional do Trabalho da 10ª Região (Distrito Federal e Tocantins)",
        "TRT11": "Tribunal Regional do Trabalho da 11ª Região (Amazonas e Roraima)",
        "TRT12": "Tribunal Regional do Trabalho da 12ª Região (Santa Catarina)",
        "TRT13": "Tribunal Regional do Trabalho da 13ª Região (Paraíba)",
        "TRT14": "Tribunal Regional do Trabalho da 14ª Região (Rondônia e Acre)",
        "TRT15": "Tribunal Regional do Trabalho da 15ª Região (Campinas)",
        "TRT16": "Tribunal Regional do Trabalho da 16ª Região (Maranhão)",
        "TRT17": "Tribunal Regional do Trabalho da 17ª Região (Espírito Santo)",
        "TRT18": "Tribunal Regional do Trabalho da 18ª Região (Goiás)",
        "TRT19": "Tribunal Regional do Trabalho da 19ª Região (Alagoas)",
        "TRT20": "Tribunal Regional do Trabalho da 20ª Região (Sergipe)",
        "TRT21": "Tribunal Regional do Trabalho da 21ª Região (Rio Grande do Norte)",
        "TRT22": "Tribunal Regional do Trabalho da 22ª Região (Piauí)",
        "TRT23": "Tribunal Regional do Trabalho da 23ª Região (Mato Grosso)",
        "TRT24": "Tribunal Regional do Trabalho da 24ª Região (Mato Grosso do Sul)",
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"APIKey {api_key}",  # Changed from Bearer to APIKey
            "Content-Type": "application/json"
        }
    
    def search_decisions(
        self,
        start_date: datetime,
        end_date: datetime,
        tribunal: str = None,
        classe: str = None,
        assunto: str = None,
        movimento_codigos: List[int] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Busca decisões no DataJud usando a API Elasticsearch
        
        Args:
            start_date: Data inicial
            end_date: Data final
            tribunal: Código do tribunal (opcional)
            classe: Classe processual (opcional)
            assunto: Assunto (opcional)
            movimento_codigos: Lista de códigos de movimento (opcional)
            page: Número da página
            page_size: Tamanho da página
        """
        if not tribunal or tribunal not in self.TRIBUNAL_ENDPOINTS:
            logger.error(f"Tribunal inválido ou não especificado: {tribunal}")
            return None
            
        endpoint = self.TRIBUNAL_ENDPOINTS[tribunal]
        
        # Formatação das datas para Elasticsearch
        date_range = {
            "gte": start_date.strftime("%Y-%m-%d"),
            "lte": end_date.strftime("%Y-%m-%d")
        }
        
        # Construção da query Elasticsearch otimizada para encontrar casos de assédio moral
        # Usando os códigos específicos da Tabela de Assuntos do CNJ para assédio moral:
        # 1723 - Tradicional da Justiça do Trabalho
        # 14175 - Introduzido na revisão de 2022-2024 para tribunais estaduais, federais e militares
        # 14018 - Rótulo unificado adotado nas versões mais recentes do PJe
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"dataAjuizamento": date_range}}
                    ],
                    "should": [
                        # Busca por nome
                        {"match_phrase": {"assuntos.nome": "ASSÉDIO MORAL"}},
                        {"match_phrase": {"movimentos.nome": "assédio moral"}},
                        {"match_phrase": {"movimentos.complementosTabelados.nome": "assédio moral"}},
                        
                        # Busca pelos códigos específicos da tabela CNJ
                        {"terms": {"assuntos.codigo": [1723, 14175, 14018]}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "from": (page - 1) * page_size,
            "size": page_size,
            "sort": [{"dataAjuizamento": {"order": "desc"}}]
        }
        
        # Adiciona filtros adicionais se necessário
        if classe:
            query["query"]["bool"]["must"].append({"match": {"classe.nome": classe}})
            
        # Filtra por códigos de movimento específicos (219, 220, 237, 242, 236)
        if movimento_codigos:
            movimento_filter = {
                "terms": {
                    "movimentos.codigo": movimento_codigos
                }
            }
            query["query"]["bool"]["must"].append(movimento_filter)
        
        if assunto and assunto != "ASSÉDIO MORAL":
            query["query"]["bool"]["must"].append({"match": {"assuntos.nome": assunto}})
            
        try:
            response = requests.post(endpoint, headers=self.headers, json=query)
            response.raise_for_status()
            result = response.json()
            
            # Formata a resposta para manter compatibilidade com o código existente
            hits = result.get("hits", {}).get("hits", [])
            total = result.get("hits", {}).get("total", {}).get("value", 0)
            
            formatted_result = {
                "content": [hit["_source"] for hit in hits],
                "totalElements": total,
                "page": page,
                "size": page_size,
                "hasNext": total > page * page_size
            }
            
            return formatted_result
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar decisões: {str(e)}")
            return None
    
    def get_decision_details(self, decision_id: str, tribunal: str) -> Dict[str, Any]:
        """
        Obtém detalhes de uma decisão específica
        
        Args:
            decision_id: ID do processo
            tribunal: Código do tribunal (ex: "TST", "TRT1", etc.)
        """
        if not tribunal or tribunal not in self.TRIBUNAL_ENDPOINTS:
            logger.error(f"Tribunal inválido ou não especificado: {tribunal}")
            return None
            
        endpoint = self.TRIBUNAL_ENDPOINTS[tribunal]
        
        # Consulta para buscar um documento específico pelo ID
        query = {
            "query": {
                "term": {
                    "_id": decision_id
                }
            }
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=query)
            response.raise_for_status()
            result = response.json()
            
            hits = result.get("hits", {}).get("hits", [])
            if hits:
                return hits[0]["_source"]
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar detalhes da decisão {decision_id}: {str(e)}")
            return None
    
    def get_all_decisions(
        self,
        start_date: datetime,
        end_date: datetime,
        tribunal: str = None,
        classe: str = None,
        assunto: str = None,
        movimento_codigos: List[int] = None,
        max_pages: int = 50,  # Aumentado para coletar mais dados
        max_results_per_query: int = 5000,  # Limite máximo de resultados por consulta
        date_chunk_size: int = 90  # Tamanho do intervalo de datas em dias (3 meses)
    ) -> List[Dict[str, Any]]:
        """
        Busca todas as decisões no período especificado, paginando automaticamente
        e dividindo em intervalos de data para evitar ultrapassar o limite de resultados
        
        Args:
            start_date: Data inicial
            end_date: Data final
            tribunal: Código do tribunal (ex: "TST", "TRT1", etc.)
            classe: Classe processual (opcional)
            assunto: Assunto (opcional)
            movimento_codigos: Lista de códigos de movimento (opcional)
            max_pages: Número máximo de páginas por intervalo de data
            max_results_per_query: Limite máximo de resultados que a API aceita por consulta
            date_chunk_size: Tamanho do intervalo de datas em dias
        """
        if not tribunal or tribunal not in self.TRIBUNAL_ENDPOINTS:
            logger.error(f"Tribunal inválido ou não especificado: {tribunal}")
            return []
        
        # Divide o período total em intervalos menores para evitar ultrapassar o limite de resultados
        all_decisions = []
        current_start_date = start_date
        
        logger.info(f"Iniciando coleta para {tribunal} de {start_date.strftime('%Y-%m-%d')} até {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Usando intervalos de {date_chunk_size} dias para não ultrapassar o limite de {max_results_per_query} resultados")
        
        interval_count = 1
        
        while current_start_date < end_date:
            # Define o fim do intervalo atual (até date_chunk_size dias depois ou até end_date, o que vier primeiro)
            current_end_date = min(current_start_date + timedelta(days=date_chunk_size), end_date)
            
            logger.info(f"Intervalo {interval_count}: {current_start_date.strftime('%Y-%m-%d')} a {current_end_date.strftime('%Y-%m-%d')}")
            
            # Busca decisões para o intervalo atual
            interval_decisions = []
            page = 1
            
            while page <= max_pages:
                logger.info(f"Buscando página {page} para {tribunal} (intervalo {current_start_date.strftime('%Y-%m-%d')} a {current_end_date.strftime('%Y-%m-%d')})")
                response = self.search_decisions(
                    start_date=current_start_date,
                    end_date=current_end_date,
                    tribunal=tribunal,
                    classe=classe,
                    assunto=assunto,
                    movimento_codigos=movimento_codigos,
                    page=page
                )
                
                if not response or not response.get("content"):
                    logger.info(f"Nenhum resultado encontrado na página {page} do intervalo atual")
                    break
                
                decisions = response["content"]
                interval_decisions.extend(decisions)
                
                # Verifica se estamos próximos do limite máximo de resultados
                if len(interval_decisions) >= max_results_per_query * 0.9:
                    logger.warning(f"Atingindo limite de resultados ({len(interval_decisions)} de {max_results_per_query}). "
                                 f"Reduzindo intervalo de datas para garantir coleta completa.")
                    
                    # Reduz o tamanho do intervalo para a próxima iteração
                    date_chunk_size = max(7, date_chunk_size // 2)  # Pelo menos 1 semana
                    logger.info(f"Novo tamanho de intervalo: {date_chunk_size} dias")
                    
                    # Se ainda temos mais páginas, mas estamos próximos do limite, paramos
                    # e deixamos para a próxima iteração com um intervalo menor
                    if response.get("hasNext"):
                        logger.info(f"Interrompendo coleta do intervalo atual para evitar perda de dados.")
                        break
                
                if not response.get("hasNext"):
                    logger.info(f"Fim dos resultados para o intervalo atual")
                    break
                
                page += 1
            
            logger.info(f"Coletados {len(interval_decisions)} decisões para o intervalo {interval_count}")
            all_decisions.extend(interval_decisions)
            
            # Avança para o próximo intervalo
            current_start_date = current_end_date + timedelta(days=1)
            interval_count += 1
            
            # Se o intervalo atual retornou poucos resultados, podemos aumentar o tamanho
            # do intervalo para a próxima iteração (até o máximo original)
            if len(interval_decisions) < max_results_per_query * 0.5:
                original_chunk_size = 90  # valor original
                date_chunk_size = min(original_chunk_size, date_chunk_size * 2)
                logger.info(f"Poucos resultados no intervalo atual. Aumentando para {date_chunk_size} dias")
        
        logger.info(f"Total geral: {len(all_decisions)} decisões encontradas para {tribunal}")
        return all_decisions 