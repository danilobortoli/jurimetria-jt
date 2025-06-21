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

    def collect_from_tst(self, start_date=None, end_date=None) -> List[Dict[str, Any]]:
        """
        Coleta decisões do Tribunal Superior do Trabalho
        
        Args:
            start_date: Data inicial (opcional, padrão 2015-01-01)
            end_date: Data final (opcional, padrão 2024-12-31)
        """
        logger.info("Iniciando coleta de dados do TST...")
        
        # Define período de coleta (2015 a 2024) se não especificado
        if end_date is None:
            end_date = datetime(2024, 12, 31)  # Até o final de 2024
        if start_date is None:
            start_date = datetime(2015, 1, 1)  # A partir de 2015
            
        logger.info(f"Período de coleta: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
        
        # Códigos de movimento para recursos providos ou desprovidos
        # 237 = Provimento (recurso acolhido)
        # 242 = Desprovimento ("não-provimento/denegação" do recurso)
        # 236 = Negação de seguimento (alternativa ao 242 em alguns tribunais)
        movimento_codigos = [237, 242, 236]
        
        # Busca decisões do TST
        # Não usamos o parâmetro assunto pois estamos filtrando pelos códigos específicos
        # na query do Elasticsearch (1723, 14175, 14018)
        decisions = self.datajud.get_all_decisions(
            start_date=start_date,
            end_date=end_date,
            tribunal="TST",  # Código do TST
            movimento_codigos=movimento_codigos  # Códigos de movimento
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
            
            # Extrai os movimentos
            movimentos = decision.get("movimentos", [])
            movimentos.sort(key=lambda x: x.get("dataHora", ""), reverse=True)
            ultimo_movimento = movimentos[0] if movimentos else {}
            
            # Determina o relator (pode estar em complementos)
            relator = ""
            for movimento in movimentos:
                complementos = movimento.get("complementosNaoTabelados", [])
                for complemento in complementos:
                    if "relator" in complemento.get("descricao", "").lower():
                        relator = complemento.get("valor", "")
                        break
                if relator:
                    break
            
            # Tenta extrair o texto da decisão dos complementos
            texto_decisao = ""
            ementa = ""
            for movimento in movimentos:
                complementos = movimento.get("complementosTabelados", [])
                for complemento in complementos:
                    if "decisão" in complemento.get("descricao", "").lower():
                        texto_decisao = complemento.get("nome", "")
                    if "ementa" in complemento.get("descricao", "").lower():
                        ementa = complemento.get("nome", "")
            
            # Classifica o resultado com base nos códigos de movimento
            resultado = "Não classificado"
            resultado_codigo = None
            for movimento in movimentos:
                codigo = movimento.get("codigo")
                if codigo in [237]:  # Provimento (recurso acolhido)
                    resultado = "Provido"
                    resultado_codigo = codigo
                    break
                elif codigo in [242, 236]:  # Desprovimento ou Negação de seguimento
                    resultado = "Desprovido"
                    resultado_codigo = codigo
                    break
            
            # Extrai a data de julgamento do movimento que contém o resultado
            data_julgamento = ""
            for movimento in movimentos:
                if movimento.get("codigo") == resultado_codigo:
                    data_julgamento = movimento.get("dataHora", "")
                    break
            
            processed_decisions.append({
                "id": decision.get("id", ""),
                "tribunal": "TST",
                "numero_processo": decision.get("numeroProcesso", ""),
                "data_ajuizamento": decision.get("dataAjuizamento", ""),
                "data_julgamento": data_julgamento,
                "data_ultimo_movimento": ultimo_movimento.get("dataHora", ""),
                "ultimo_movimento": ultimo_movimento.get("nome", ""),
                "resultado": resultado,
                "resultado_codigo": resultado_codigo,
                "relator": relator,
                "classe": classe_nome,
                "assunto": assunto_texto,
                "assuntos": assuntos,  # Incluindo objeto assuntos completo com códigos
                "texto": texto_decisao,
                "ementa": ementa,
                "orgao_julgador": decision.get("orgaoJulgador", {}).get("nome", ""),
                "instancia": "TST"
            })
        
        return processed_decisions

    def collect_from_trt(self, region: int, start_date=None, end_date=None) -> List[Dict[str, Any]]:
        """
        Coleta decisões dos Tribunais Regionais do Trabalho
        
        Args:
            region: Número do TRT (1-24)
            start_date: Data inicial (opcional, padrão 2015-01-01)
            end_date: Data final (opcional, padrão 2024-12-31)
        """
        logger.info(f"Iniciando coleta de dados do TRT {region}...")
        
        # Define período de coleta (2015 a 2024) se não especificado
        if end_date is None:
            end_date = datetime(2024, 12, 31)  # Até o final de 2024
        if start_date is None:
            start_date = datetime(2015, 1, 1)  # A partir de 2015
            
        logger.info(f"Período de coleta: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
        
        # Formata o código do TRT (ex: 2 -> TRT2)
        tribunal_code = f"TRT{region}"
        
        # Primeiro coletamos decisões de primeira instância (sentenças)
        # 219 = Procedência
        # 220 = Improcedência
        primeira_instancia_codigos = [219, 220]
        
        primeira_instancia_decisions = self.datajud.get_all_decisions(
            start_date=start_date,
            end_date=end_date,
            tribunal=tribunal_code,
            # Não usamos o parâmetro assunto pois estamos filtrando pelos códigos específicos
            # na query do Elasticsearch (1723, 14175, 14018)
            movimento_codigos=primeira_instancia_codigos
        )
        
        # Depois coletamos decisões de segunda instância (recursos)
        # 237 = Provimento (recurso acolhido)
        # 242 = Desprovimento ("não-provimento/denegação" do recurso)
        # 236 = Negação de seguimento (alternativa ao 242 em alguns tribunais)
        segunda_instancia_codigos = [237, 242, 236]
        
        segunda_instancia_decisions = self.datajud.get_all_decisions(
            start_date=start_date,
            end_date=end_date,
            tribunal=tribunal_code,
            # Não usamos o parâmetro assunto pois estamos filtrando pelos códigos específicos
            # na query do Elasticsearch (1723, 14175, 14018)
            movimento_codigos=segunda_instancia_codigos
        )
        
        # Combina os resultados
        decisions = primeira_instancia_decisions + segunda_instancia_decisions
        
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
            
            # Extrai os movimentos
            movimentos = decision.get("movimentos", [])
            movimentos.sort(key=lambda x: x.get("dataHora", ""), reverse=True)
            ultimo_movimento = movimentos[0] if movimentos else {}
            
            # Determina o relator (pode estar em complementos)
            relator = ""
            for movimento in movimentos:
                complementos = movimento.get("complementosNaoTabelados", [])
                for complemento in complementos:
                    if "relator" in complemento.get("descricao", "").lower():
                        relator = complemento.get("valor", "")
                        break
                if relator:
                    break
            
            # Tenta extrair o texto da decisão dos complementos
            texto_decisao = ""
            ementa = ""
            for movimento in movimentos:
                complementos = movimento.get("complementosTabelados", [])
                for complemento in complementos:
                    if "decisão" in complemento.get("descricao", "").lower():
                        texto_decisao = complemento.get("nome", "")
                    if "ementa" in complemento.get("descricao", "").lower():
                        ementa = complemento.get("nome", "")
            
            # Determina a instância e classifica o resultado com base nos códigos de movimento
            instancia = "Não classificada"
            resultado = "Não classificado"
            resultado_codigo = None
            
            for movimento in movimentos:
                codigo = movimento.get("codigo")
                
                # Classificação de primeira instância
                if codigo in [219]:  # Procedência
                    instancia = "Primeira Instância"
                    resultado = "Procedente"
                    resultado_codigo = codigo
                    break
                elif codigo in [220]:  # Improcedência
                    instancia = "Primeira Instância"
                    resultado = "Improcedente"
                    resultado_codigo = codigo
                    break
                
                # Classificação de segunda instância
                elif codigo in [237]:  # Provimento (recurso acolhido)
                    instancia = "Segunda Instância"
                    resultado = "Provido"
                    resultado_codigo = codigo
                    break
                elif codigo in [242, 236]:  # Desprovimento ou Negação de seguimento
                    instancia = "Segunda Instância"
                    resultado = "Desprovido"
                    resultado_codigo = codigo
                    break
            
            # Extrai a data de julgamento do movimento que contém o resultado
            data_julgamento = ""
            for movimento in movimentos:
                if movimento.get("codigo") == resultado_codigo:
                    data_julgamento = movimento.get("dataHora", "")
                    break
            
            # Determina o tipo de órgão julgador para ajudar a confirmar a instância
            orgao_julgador = decision.get("orgaoJulgador", {}).get("nome", "")
            if instancia == "Não classificada" and orgao_julgador:
                if any(termo in orgao_julgador.lower() for termo in ["vara", "1ª instância", "primeira instância", "juízo"]):
                    instancia = "Primeira Instância"
                elif any(termo in orgao_julgador.lower() for termo in ["turma", "colegiado", "pleno", "2ª instância", "segunda instância"]):
                    instancia = "Segunda Instância"
            
            processed_decisions.append({
                "id": decision.get("id", ""),
                "tribunal": tribunal_code,
                "numero_processo": decision.get("numeroProcesso", ""),
                "data_ajuizamento": decision.get("dataAjuizamento", ""),
                "data_julgamento": data_julgamento,
                "data_ultimo_movimento": ultimo_movimento.get("dataHora", ""),
                "ultimo_movimento": ultimo_movimento.get("nome", ""),
                "instancia": instancia,
                "resultado": resultado,
                "resultado_codigo": resultado_codigo,
                "relator": relator,
                "classe": classe_nome,
                "assunto": assunto_texto,
                "assuntos": assuntos,  # Incluindo objeto assuntos completo com códigos
                "texto": texto_decisao,
                "ementa": ementa,
                "orgao_julgador": orgao_julgador
            })
        
        return processed_decisions

    def save_data(self, data: List[Dict[str, Any]], source: str):
        """
        Salva os dados coletados em formato JSON, detectando e evitando duplicatas
        """
        if not data:
            logger.warning(f"Nenhum dado para salvar de {source}")
            return
        
        # Verifica se existem arquivos anteriores deste mesmo tribunal
        existing_files = list(self.data_path.glob(f"{source}_*.json"))
        existing_data = []
        
        # Set para verificar números de processo já coletados
        existing_process_numbers = set()
        
        # Carrega dados existentes para verificar duplicatas
        if existing_files:
            logger.info(f"Encontrados {len(existing_files)} arquivos existentes para {source}")
            for file_path in existing_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        for item in file_data:
                            existing_process_numbers.add(item.get('numero_processo', ''))
                        existing_data.extend(file_data)
                except Exception as e:
                    logger.error(f"Erro ao carregar arquivo existente {file_path}: {str(e)}")
            
            logger.info(f"Carregados {len(existing_data)} registros existentes para {source}")
        
        # Filtra dados para remover duplicatas
        new_data = []
        duplicates = 0
        
        for item in data:
            numero_processo = item.get('numero_processo', '')
            if numero_processo and numero_processo not in existing_process_numbers:
                new_data.append(item)
                existing_process_numbers.add(numero_processo)
            else:
                duplicates += 1
        
        logger.info(f"Encontradas {duplicates} duplicatas em {len(data)} registros")
        
        # Salva apenas os novos dados
        if new_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{source}_{timestamp}.json"
            filepath = self.data_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Salvas {len(new_data)} novas decisões de {source} em {filepath}")
        else:
            logger.info(f"Nenhum novo registro para salvar de {source}")

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