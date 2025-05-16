import logging
from typing import List, Dict, Any
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataJudAPI:
    BASE_URL = "https://api-publica.datajud.cnj.jus.br/api/v1"  # URL correta da API pública do DataJud
    
    # Códigos dos tribunais trabalhistas
    TRIBUNALS = {
        "TST": "TST",  # Tribunal Superior do Trabalho
        "TRT1": "TRT1",  # 1ª Região (Rio de Janeiro)
        "TRT2": "TRT2",  # 2ª Região (São Paulo)
        "TRT3": "TRT3",  # 3ª Região (Minas Gerais)
        "TRT4": "TRT4",  # 4ª Região (Rio Grande do Sul)
        "TRT5": "TRT5",  # 5ª Região (Bahia)
        "TRT6": "TRT6",  # 6ª Região (Pernambuco)
        "TRT7": "TRT7",  # 7ª Região (Ceará)
        "TRT8": "TRT8",  # 8ª Região (Pará e Amapá)
        "TRT9": "TRT9",  # 9ª Região (Paraná)
        "TRT10": "TRT10",  # 10ª Região (Distrito Federal e Tocantins)
        "TRT11": "TRT11",  # 11ª Região (Amazonas e Roraima)
        "TRT12": "TRT12",  # 12ª Região (Santa Catarina)
        "TRT13": "TRT13",  # 13ª Região (Paraíba)
        "TRT14": "TRT14",  # 14ª Região (Rondônia e Acre)
        "TRT15": "TRT15",  # 15ª Região (Campinas)
        "TRT16": "TRT16",  # 16ª Região (Maranhão)
        "TRT17": "TRT17",  # 17ª Região (Espírito Santo)
        "TRT18": "TRT18",  # 18ª Região (Goiás)
        "TRT19": "TRT19",  # 19ª Região (Alagoas)
        "TRT20": "TRT20",  # 20ª Região (Sergipe)
        "TRT21": "TRT21",  # 21ª Região (Rio Grande do Norte)
        "TRT22": "TRT22",  # 22ª Região (Piauí)
        "TRT23": "TRT23",  # 23ª Região (Mato Grosso)
        "TRT24": "TRT24",  # 24ª Região (Mato Grosso do Sul)
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
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
        Busca decisões no DataJud
        
        Args:
            start_date: Data inicial
            end_date: Data final
            tribunal: Código do tribunal (opcional)
            classe: Classe processual (opcional)
            assunto: Assunto (opcional)
            page: Número da página
            page_size: Tamanho da página
        """
        endpoint = f"{self.BASE_URL}/pesquisa/metadados-processos"  # Endpoint correto para buscar processos
        
        params = {
            "dataInicial": start_date.strftime("%Y-%m-%d"),
            "dataFinal": end_date.strftime("%Y-%m-%d"),
            "page": page,
            "size": page_size,
            "tipoTribunal": "TRIBUNAL_DO_TRABALHO"  # Filtra apenas tribunais trabalhistas
        }
        
        if tribunal and tribunal in self.TRIBUNALS:
            params["siglaTribunal"] = self.TRIBUNALS[tribunal]  # Parâmetro correto para sigla do tribunal
        if classe:
            params["classe"] = classe
        if assunto:
            params["assunto"] = assunto
            
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar decisões: {str(e)}")
            return None
    
    def get_decision_details(self, decision_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de uma decisão específica
        """
        endpoint = f"{self.BASE_URL}/processos/{decision_id}"  # Endpoint para detalhes do processo
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar detalhes da decisão {decision_id}: {str(e)}")
            return None
    
    def get_all_decisions(
        self,
        start_date: datetime,
        end_date: datetime,
        tribunal: str = None,
        classe: str = None,
        assunto: str = None
    ) -> List[Dict[str, Any]]:
        """
        Busca todas as decisões no período especificado, paginando automaticamente
        """
        all_decisions = []
        page = 1
        
        while True:
            response = self.search_decisions(
                start_date=start_date,
                end_date=end_date,
                tribunal=tribunal,
                classe=classe,
                assunto=assunto,
                page=page
            )
            
            if not response or not response.get("content"):
                break
                
            decisions = response["content"]
            all_decisions.extend(decisions)
            
            if not response.get("hasNext"):
                break
                
            page += 1
            
        return all_decisions 