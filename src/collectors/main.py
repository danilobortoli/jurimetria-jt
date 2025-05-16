import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

from .datajud_api import DataJudAPI

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

class DataCollector:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / "data" / "raw"
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializa API do DataJud
        api_key = os.getenv("DATAJUD_API_KEY")
        if not api_key:
            raise ValueError("DATAJUD_API_KEY não encontrada nas variáveis de ambiente")
        self.datajud = DataJudAPI(api_key)
        
        # Configuração do Selenium (mantido para possíveis coletas adicionais)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

    def collect_from_tst(self) -> List[Dict[str, Any]]:
        """
        Coleta decisões do Tribunal Superior do Trabalho
        """
        logger.info("Iniciando coleta de dados do TST...")
        
        # Define período de coleta (últimos 6 meses)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        # Busca decisões do TST
        decisions = self.datajud.get_all_decisions(
            start_date=start_date,
            end_date=end_date,
            tribunal="TST",  # Código do TST
            classe="RECURSO DE REVISTA",  # Classe específica para assédio moral
            assunto="ASSÉDIO MORAL"  # Assunto específico
        )
        
        # Processa e formata as decisões
        processed_decisions = []
        for decision in decisions:
            # Obtém detalhes completos da decisão
            details = self.datajud.get_decision_details(decision["id"])
            if details:
                processed_decisions.append({
                    "id": decision["id"],
                    "tribunal": "TST",
                    "data_julgamento": decision["dataJulgamento"],
                    "relator": decision.get("relator", ""),
                    "classe": decision.get("classe", ""),
                    "assunto": decision.get("assunto", ""),
                    "texto": details.get("texto", ""),
                    "url": details.get("url", "")
                })
        
        return processed_decisions

    def collect_from_trt(self, region: int) -> List[Dict[str, Any]]:
        """
        Coleta decisões dos Tribunais Regionais do Trabalho
        """
        logger.info(f"Iniciando coleta de dados do TRT {region}...")
        
        # Define período de coleta (últimos 6 meses)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        # Formata o código do TRT (ex: 2 -> TRT2)
        tribunal_code = f"TRT{region}"
        
        # Busca decisões do TRT específico
        decisions = self.datajud.get_all_decisions(
            start_date=start_date,
            end_date=end_date,
            tribunal=tribunal_code,  # Código do TRT
            classe="RECURSO ORDINÁRIO",  # Classe específica para assédio moral
            assunto="ASSÉDIO MORAL"  # Assunto específico
        )
        
        # Processa e formata as decisões
        processed_decisions = []
        for decision in decisions:
            # Obtém detalhes completos da decisão
            details = self.datajud.get_decision_details(decision["id"])
            if details:
                processed_decisions.append({
                    "id": decision["id"],
                    "tribunal": tribunal_code,
                    "data_julgamento": decision["dataJulgamento"],
                    "relator": decision.get("relator", ""),
                    "classe": decision.get("classe", ""),
                    "assunto": decision.get("assunto", ""),
                    "texto": details.get("texto", ""),
                    "url": details.get("url", "")
                })
        
        return processed_decisions

    def save_data(self, data: List[Dict[str, Any]], source: str):
        """
        Salva os dados coletados em formato JSON
        """
        if not data:
            logger.warning(f"Nenhum dado para salvar de {source}")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}_{timestamp}.json"
        filepath = self.data_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Salvas {len(data)} decisões de {source} em {filepath}")

    def close(self):
        """
        Fecha o driver do Selenium
        """
        self.driver.quit()

def main():
    collector = DataCollector()
    try:
        # Coleta e salva dados do TST
        tst_decisions = collector.collect_from_tst()
        collector.save_data(tst_decisions, "tst")
        
        # Coleta e salva dados de cada TRT
        for region in range(1, 25):
            try:
                trt_decisions = collector.collect_from_trt(region)
                collector.save_data(trt_decisions, f"trt{region}")
            except Exception as e:
                logger.error(f"Erro ao coletar dados do TRT {region}: {str(e)}")
                continue
        
    finally:
        collector.close()

if __name__ == "__main__":
    main() 