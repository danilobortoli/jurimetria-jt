#!/usr/bin/env python3
"""
Script para execução da coleta completa de dados de assédio moral
para todos os tribunais (TRT2-TRT24 e TST) e todos os anos (2015-2024).

Este script gerencia a coleta incremental para evitar timeouts e sobrecarga na API.
"""

import argparse
import datetime
import logging
import os
import subprocess
import sys
import time
from typing import List, Optional, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('coleta_completa.log')
    ]
)
logger = logging.getLogger(__name__)

# Constantes
ANOS = list(range(2015, 2025))  # 2015 até 2024
TRIBUNAIS_TRT = list(range(2, 25))  # TRT2 até TRT24
SLEEP_ENTRE_EXECUCOES = 30  # segundos de espera entre execuções
MAX_TENTATIVAS = 3  # máximo de tentativas em caso de falha

def executar_comando(comando: str) -> Tuple[int, str, str]:
    """
    Executa um comando shell e retorna o código de saída, stdout e stderr.
    """
    logger.info(f"Executando comando: {comando}")
    
    processo = subprocess.Popen(
        comando,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = processo.communicate()
    
    return processo.returncode, stdout, stderr

def executar_coleta(tribunal: str, ano: int, sleep: int = SLEEP_ENTRE_EXECUCOES) -> bool:
    """
    Executa a coleta para um tribunal e ano específicos.
    
    Args:
        tribunal: String com o nome do tribunal (ex: "TRT5" ou "TST")
        ano: Ano para coleta
        sleep: Tempo de espera em segundos após a execução
    
    Returns:
        bool: True se a coleta foi bem-sucedida, False caso contrário
    """
    if tribunal == "TST":
        comando = f"cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && python pipeline_assedio_moral.py --only-tst --year {ano}"
    else:
        trt_num = int(tribunal.replace("TRT", ""))
        comando = f"cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && python pipeline_assedio_moral.py --collect --start-tribunal {trt_num} --end-tribunal {trt_num} --year {ano}"
    
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        logger.info(f"Tentativa {tentativa}/{MAX_TENTATIVAS} - Coletando dados de {tribunal} para o ano {ano}")
        
        try:
            codigo, stdout, stderr = executar_comando(comando)
            
            if codigo == 0:
                logger.info(f"Coleta bem-sucedida para {tribunal} - {ano}")
                time.sleep(sleep)  # Aguarda antes da próxima execução
                return True
            else:
                logger.error(f"Erro na coleta para {tribunal} - {ano}: {stderr}")
                # Em caso de falha, aguarda mais tempo antes de tentar novamente
                time.sleep(sleep * 2)
        except Exception as e:
            logger.error(f"Exceção durante coleta para {tribunal} - {ano}: {str(e)}")
            time.sleep(sleep * 2)
    
    logger.error(f"Todas as tentativas falharam para {tribunal} - {ano}")
    return False

def executar_processamento() -> bool:
    """
    Executa as etapas de consolidação, processamento e análise.
    
    Returns:
        bool: True se todas as etapas foram bem-sucedidas, False caso contrário
    """
    etapas = [
        ("Consolidação", "python pipeline_assedio_moral.py --consolidate"),
        ("Processamento", "python pipeline_assedio_moral.py --process"),
        ("Análise", "python pipeline_assedio_moral.py --analyze")
    ]
    
    for nome, comando in etapas:
        logger.info(f"Iniciando etapa: {nome}")
        comando_completo = f"cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && {comando}"
        
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            logger.info(f"Tentativa {tentativa}/{MAX_TENTATIVAS} - {nome}")
            
            try:
                codigo, stdout, stderr = executar_comando(comando_completo)
                
                if codigo == 0:
                    logger.info(f"{nome} bem-sucedida")
                    break
                else:
                    logger.error(f"Erro na etapa {nome}: {stderr}")
                    time.sleep(SLEEP_ENTRE_EXECUCOES)
            except Exception as e:
                logger.error(f"Exceção durante {nome}: {str(e)}")
                time.sleep(SLEEP_ENTRE_EXECUCOES)
            
            if tentativa == MAX_TENTATIVAS:
                logger.error(f"Todas as tentativas falharam para a etapa {nome}")
                return False
    
    return True

def executar_analise_fluxo() -> bool:
    """
    Executa os scripts de análise de fluxo.
    
    Returns:
        bool: True se a análise foi bem-sucedida, False caso contrário
    """
    comandos = [
        "python analyze_case_flow.py",
        "python final_analysis.py"
    ]
    
    for comando in comandos:
        comando_completo = f"cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && {comando}"
        
        try:
            codigo, stdout, stderr = executar_comando(comando_completo)
            
            if codigo == 0:
                logger.info(f"Análise bem-sucedida: {comando}")
            else:
                logger.error(f"Erro na análise {comando}: {stderr}")
                return False
        except Exception as e:
            logger.error(f"Exceção durante análise {comando}: {str(e)}")
            return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Coleta completa de dados de assédio moral na Justiça do Trabalho")
    parser.add_argument("--ano-inicio", type=int, default=2015, help="Ano inicial para coleta")
    parser.add_argument("--ano-fim", type=int, default=2024, help="Ano final para coleta")
    parser.add_argument("--trt-inicio", type=int, default=2, help="Primeiro TRT para coleta")
    parser.add_argument("--trt-fim", type=int, default=24, help="Último TRT para coleta")
    parser.add_argument("--incluir-tst", action="store_true", help="Incluir coleta de dados do TST")
    parser.add_argument("--sleep", type=int, default=SLEEP_ENTRE_EXECUCOES, help="Tempo de espera entre execuções (em segundos)")
    parser.add_argument("--apenas-processar", action="store_true", help="Pular coleta e apenas processar/analisar dados existentes")
    args = parser.parse_args()
    
    # Definir intervalo de anos para coleta
    anos_coleta = list(range(args.ano_inicio, args.ano_fim + 1))
    
    # Definir tribunais para coleta
    tribunais_trt = [f"TRT{i}" for i in range(args.trt_inicio, args.trt_fim + 1)]
    tribunais = tribunais_trt + (["TST"] if args.incluir_tst else [])
    
    logger.info(f"Iniciando coleta completa em {datetime.datetime.now()}")
    logger.info(f"Anos: {anos_coleta}")
    logger.info(f"Tribunais: {tribunais}")
    
    if not args.apenas_processar:
        # Iterar sobre todos os tribunais e anos
        for tribunal in tribunais:
            logger.info(f"Iniciando coleta para {tribunal}")
            
            for ano in anos_coleta:
                sucesso = executar_coleta(tribunal, ano, args.sleep)
                if not sucesso:
                    logger.warning(f"Falha na coleta para {tribunal} - {ano}, continuando com próximo item")
    else:
        logger.info("Pulando etapa de coleta conforme solicitado")
    
    # Processar e analisar os dados coletados
    logger.info("Iniciando processamento dos dados coletados")
    sucesso_processamento = executar_processamento()
    
    if sucesso_processamento:
        logger.info("Processamento concluído com sucesso")
        
        # Executar análise de fluxo
        logger.info("Iniciando análise de fluxo de decisões")
        sucesso_analise = executar_analise_fluxo()
        
        if sucesso_analise:
            logger.info("Análise de fluxo concluída com sucesso")
        else:
            logger.error("Falha na análise de fluxo")
    else:
        logger.error("Falha no processamento dos dados")
    
    logger.info(f"Coleta completa finalizada em {datetime.datetime.now()}")

if __name__ == "__main__":
    main()