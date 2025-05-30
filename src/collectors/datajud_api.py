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
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"dataAjuizamento": date_range}}
                    ],
                    "should": [
                        {"match_phrase": {"assuntos.nome": "ASSÉDIO MORAL"}},
                        {"match_phrase": {"movimentos.nome": "assédio moral"}},
                        {"match_phrase": {"movimentos.complementosTabelados.nome": "assédio moral"}}
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
        max_pages: int = 50  # Aumentado para coletar mais dados
    ) -> List[Dict[str, Any]]:
        """
        Busca todas as decisões no período especificado, paginando automaticamente
        
        Args:
            start_date: Data inicial
            end_date: Data final
            tribunal: Código do tribunal (ex: "TST", "TRT1", etc.)
            classe: Classe processual (opcional)
            assunto: Assunto (opcional)
            max_pages: Número máximo de páginas a buscar
        """
        if not tribunal or tribunal not in self.TRIBUNAL_ENDPOINTS:
            logger.error(f"Tribunal inválido ou não especificado: {tribunal}")
            return []
            
        all_decisions = []
        page = 1
        
        while page <= max_pages:
            logger.info(f"Buscando página {page} para {tribunal}")
            response = self.search_decisions(
                start_date=start_date,
                end_date=end_date,
                tribunal=tribunal,
                classe=classe,
                assunto=assunto,
                page=page
            )
            
            if not response or not response.get("content"):
                logger.info(f"Nenhum resultado encontrado na página {page}")
                break
                
            decisions = response["content"]
            all_decisions.extend(decisions)
            
            if not response.get("hasNext"):
                logger.info(f"Fim dos resultados para {tribunal}")
                break
                
            page += 1
            
        logger.info(f"Total de {len(all_decisions)} decisões encontradas para {tribunal}")
        return all_decisions 