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
        
        # Define período de coleta (desde 2016)
        end_date = datetime.now()
        start_date = datetime(2016, 1, 1)
        
        # Busca decisões do TST
        decisions = self.datajud.get_all_decisions(
            start_date=start_date,
            end_date=end_date,
            tribunal="TST",  # Código do TST
            assunto="ASSÉDIO MORAL"  # Assunto específico
        )
        
        # Processa e formata as decisões
        processed_decisions = []
        for decision in decisions:
            # Detalhes já estão incluídos na resposta
            # Extrai classe processual a partir do objeto classe
            classe_obj = decision.get("classe", {})
            classe_nome = classe_obj.get("nome", "") if isinstance(classe_obj, dict) else ""
            
            # Extrai assuntos
            assuntos = decision.get("assuntos", [])
            assunto_nomes = [a.get("nome", "") for a in assuntos if isinstance(a, dict)]
            assunto_texto = ", ".join(assunto_nomes)
            
            # Extrai o movimento mais recente (se houver)
            movimentos = decision.get("movimentos", [])
            movimentos.sort(key=lambda x: x.get("dataHora", ""), reverse=True)
            ultimo_movimento = movimentos[0] if movimentos else {}
            relator = ""
            
            # Tenta extrair o texto da decisão dos complementos
            texto_decisao = ""
            for movimento in movimentos:
                complementos = movimento.get("complementosTabelados", [])
                for complemento in complementos:
                    if "decisão" in complemento.get("descricao", "").lower():
                        texto_decisao = complemento.get("nome", "")
                        break
            
            processed_decisions.append({
                "id": decision.get("id", ""),
                "tribunal": "TST",
                "numero_processo": decision.get("numeroProcesso", ""),
                "data_ajuizamento": decision.get("dataAjuizamento", ""),
                "data_ultimo_movimento": ultimo_movimento.get("dataHora", ""),
                "ultimo_movimento": ultimo_movimento.get("nome", ""),
                "relator": relator,
                "classe": classe_nome,
                "assunto": assunto_texto,
                "texto": texto_decisao,
                "orgao_julgador": decision.get("orgaoJulgador", {}).get("nome", "")
            })
        
        return processed_decisions

    def collect_from_trt(self, region: int) -> List[Dict[str, Any]]:
        """
        Coleta decisões dos Tribunais Regionais do Trabalho
        """
        logger.info(f"Iniciando coleta de dados do TRT {region}...")
        
        # Define período de coleta (desde 2016)
        end_date = datetime.now()
        start_date = datetime(2016, 1, 1)
        
        # Formata o código do TRT (ex: 2 -> TRT2)
        tribunal_code = f"TRT{region}"
        
        # Busca decisões do TRT específico
        decisions = self.datajud.get_all_decisions(
            start_date=start_date,
            end_date=end_date,
            tribunal=tribunal_code,  # Código do TRT
            assunto="ASSÉDIO MORAL"  # Assunto específico
        )
        
        # Processa e formata as decisões
        processed_decisions = []
        for decision in decisions:
            # Detalhes já estão incluídos na resposta
            # Extrai classe processual a partir do objeto classe
            classe_obj = decision.get("classe", {})
            classe_nome = classe_obj.get("nome", "") if isinstance(classe_obj, dict) else ""
            
            # Extrai assuntos
            assuntos = decision.get("assuntos", [])
            assunto_nomes = [a.get("nome", "") for a in assuntos if isinstance(a, dict)]
            assunto_texto = ", ".join(assunto_nomes)
            
            # Extrai o movimento mais recente (se houver)
            movimentos = decision.get("movimentos", [])
            movimentos.sort(key=lambda x: x.get("dataHora", ""), reverse=True)
            ultimo_movimento = movimentos[0] if movimentos else {}
            relator = ""
            
            # Tenta extrair o texto da decisão dos complementos
            texto_decisao = ""
            for movimento in movimentos:
                complementos = movimento.get("complementosTabelados", [])
                for complemento in complementos:
                    if "decisão" in complemento.get("descricao", "").lower():
                        texto_decisao = complemento.get("nome", "")
                        break
            
            processed_decisions.append({
                "id": decision.get("id", ""),
                "tribunal": tribunal_code,
                "numero_processo": decision.get("numeroProcesso", ""),
                "data_ajuizamento": decision.get("dataAjuizamento", ""),
                "data_ultimo_movimento": ultimo_movimento.get("dataHora", ""),
                "ultimo_movimento": ultimo_movimento.get("nome", ""),
                "relator": relator,
                "classe": classe_nome,
                "assunto": assunto_texto,
                "texto": texto_decisao,
                "orgao_julgador": decision.get("orgaoJulgador", {}).get("nome", "")
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
        logger.info("=== Iniciando coleta de dados do TST ===")
        tst_decisions = collector.collect_from_tst()
        collector.save_data(tst_decisions, "tst")
        logger.info(f"Coletados {len(tst_decisions)} processos do TST")
        
        # Coleta e salva dados de cada TRT
        logger.info("=== Iniciando coleta de dados dos TRTs ===")
        for region in range(1, 25):
            try:
                logger.info(f"=== TRT {region} ===")
                trt_decisions = collector.collect_from_trt(region)
                collector.save_data(trt_decisions, f"trt{region}")
                logger.info(f"Coletados {len(trt_decisions)} processos do TRT{region}")
            except Exception as e:
                logger.error(f"Erro ao coletar dados do TRT {region}: {str(e)}")
                continue
        
        logger.info("=== Coleta de dados concluída ===")
        
    finally:
        collector.close()

if __name__ == "__main__":
    main() 