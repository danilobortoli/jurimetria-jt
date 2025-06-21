#!/usr/bin/env python3
"""
Script de orquestração para executar todo o pipeline de jurimetria em etapas controladas:
1. Coleta de dados dos TRTs (1 a 24)
2. Coleta de dados do TST
3. Consolidação dos dados coletados
4. Processamento dos dados consolidados
5. Análise dos dados processados

Este script permite controlar melhor o fluxo, lidar com erros em cada etapa,
e fornecer um relatório de progresso detalhado.
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline_completo.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(command, description, max_retries=3, retry_delay=60):
    """
    Executa um comando com suporte a retentativas em caso de falha
    """
    logger.info(f"INICIANDO: {description}")
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            logger.info(f"Executando comando: {command}")
            start_time = datetime.now()
            
            # Executa o comando e captura a saída
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Imprime a saída em tempo real
            stdout, stderr = process.communicate()
            
            # Verifica o código de retorno
            if process.returncode != 0:
                logger.error(f"Comando falhou com código {process.returncode}")
                logger.error(f"Erro: {stderr}")
                
                retry_count += 1
                if retry_count <= max_retries:
                    logger.info(f"Tentativa {retry_count}/{max_retries}. Aguardando {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Todas as tentativas falharam para: {description}")
                    return False
            else:
                end_time = datetime.now()
                duration = end_time - start_time
                logger.info(f"CONCLUÍDO: {description} (duração: {duration})")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao executar {description}: {str(e)}")
            
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Tentativa {retry_count}/{max_retries}. Aguardando {retry_delay} segundos...")
                time.sleep(retry_delay)
                continue
            else:
                logger.error(f"Todas as tentativas falharam para: {description}")
                return False
    
    return False

def coletar_trts(start_trt=1, end_trt=24, batch_size=1, sleep_between_batches=300, year_start=2015, year_end=2024):
    """
    Coleta dados dos TRTs em lotes para evitar sobrecarga
    Com controle de ano para dividir as consultas e evitar timeout
    """
    logger.info(f"Iniciando coleta de dados dos TRTs ({start_trt} a {end_trt}) para os anos {year_start} a {year_end}")
    
    # Para cada tribunal
    for trt_num in range(start_trt, end_trt + 1):
        logger.info(f"Iniciando coleta para TRT {trt_num}")
        
        # Para cada ano
        for year in range(year_start, year_end + 1):
            logger.info(f"Coletando dados do ano {year} para TRT {trt_num}")
            
            command = f"cd {os.getcwd()} && source venv/bin/activate && python pipeline_assedio_moral.py --collect --start-tribunal {trt_num} --end-tribunal {trt_num} --year {year}"
            
            success = run_command(
                command=command,
                description=f"Coleta de dados do TRT {trt_num} para o ano {year}",
                max_retries=3
            )
            
            if not success:
                logger.warning(f"Falha na coleta do TRT {trt_num} para o ano {year}")
                # Continua com o próximo ano mesmo em caso de falha
            
            # Aguarda entre consultas para evitar sobrecarga na API
            logger.info(f"Aguardando 30 segundos antes da próxima consulta...")
            time.sleep(30)
        
        # Aguarda entre tribunais para evitar sobrecarga na API
        if trt_num < end_trt:  # Se não for o último tribunal
            logger.info(f"Aguardando {sleep_between_batches} segundos antes do próximo tribunal...")
            time.sleep(sleep_between_batches)
    
    logger.info("Coleta de dados dos TRTs concluída")
    return True

def coletar_tst():
    """
    Coleta dados do TST
    """
    logger.info("Iniciando coleta de dados do TST")
    
    command = f"cd {os.getcwd()} && source venv/bin/activate && python pipeline_assedio_moral.py --collect --only-tst"
    
    success = run_command(
        command=command,
        description="Coleta de dados do TST",
        max_retries=3
    )
    
    if not success:
        logger.error("Falha na coleta de dados do TST")
        return False
    
    logger.info("Coleta de dados do TST concluída")
    return True

def consolidar_dados():
    """
    Consolida os dados coletados
    """
    logger.info("Iniciando consolidação dos dados")
    
    command = f"cd {os.getcwd()} && source venv/bin/activate && python pipeline_assedio_moral.py --consolidate"
    
    success = run_command(
        command=command,
        description="Consolidação dos dados",
        max_retries=2
    )
    
    if not success:
        logger.error("Falha na consolidação dos dados")
        return False
    
    logger.info("Consolidação dos dados concluída")
    return True

def processar_dados():
    """
    Processa os dados consolidados
    """
    logger.info("Iniciando processamento dos dados")
    
    command = f"cd {os.getcwd()} && source venv/bin/activate && python pipeline_assedio_moral.py --process"
    
    success = run_command(
        command=command,
        description="Processamento dos dados",
        max_retries=2
    )
    
    if not success:
        logger.error("Falha no processamento dos dados")
        return False
    
    logger.info("Processamento dos dados concluído")
    return True

def analisar_dados():
    """
    Analisa os dados processados
    """
    logger.info("Iniciando análise dos dados")
    
    command = f"cd {os.getcwd()} && source venv/bin/activate && python pipeline_assedio_moral.py --analyze"
    
    success = run_command(
        command=command,
        description="Análise dos dados",
        max_retries=2
    )
    
    if not success:
        logger.error("Falha na análise dos dados")
        return False
    
    logger.info("Análise dos dados concluída")
    return True

def main():
    # Configuração dos argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Pipeline completo de jurimetria para assédio moral")
    
    parser.add_argument("--skip-trts", action="store_true", help="Pular a coleta de dados dos TRTs")
    parser.add_argument("--skip-tst", action="store_true", help="Pular a coleta de dados do TST")
    parser.add_argument("--skip-consolidation", action="store_true", help="Pular a consolidação dos dados")
    parser.add_argument("--skip-processing", action="store_true", help="Pular o processamento dos dados")
    parser.add_argument("--skip-analysis", action="store_true", help="Pular a análise dos dados")
    parser.add_argument("--start-trt", type=int, default=1, help="TRT inicial para coleta (1-24)")
    parser.add_argument("--end-trt", type=int, default=24, help="TRT final para coleta (1-24)")
    parser.add_argument("--batch-size", type=int, default=5, help="Número de TRTs por lote")
    parser.add_argument("--sleep", type=int, default=300, help="Tempo de espera entre lotes em segundos")
    parser.add_argument("--year-start", type=int, default=2015, help="Ano inicial para coleta")
    parser.add_argument("--year-end", type=int, default=2024, help="Ano final para coleta")
    
    args = parser.parse_args()
    
    # Registra início do pipeline
    start_time = datetime.now()
    logger.info(f"Iniciando pipeline completo em {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Valida os argumentos
    if args.start_trt < 1 or args.start_trt > 24:
        logger.error("TRT inicial deve estar entre 1 e 24")
        return False
    
    if args.end_trt < 1 or args.end_trt > 24 or args.end_trt < args.start_trt:
        logger.error("TRT final deve estar entre 1 e 24 e ser maior ou igual ao TRT inicial")
        return False
    
    # Executa as etapas do pipeline
    steps_results = {
        "TRTs": None,
        "TST": None,
        "Consolidação": None,
        "Processamento": None,
        "Análise": None
    }
    
    # 1. Coleta de dados dos TRTs
    if not args.skip_trts:
        steps_results["TRTs"] = coletar_trts(
            start_trt=args.start_trt,
            end_trt=args.end_trt,
            batch_size=args.batch_size,
            sleep_between_batches=args.sleep,
            year_start=args.year_start,
            year_end=args.year_end
        )
    else:
        logger.info("Coleta de dados dos TRTs ignorada")
        steps_results["TRTs"] = True
    
    # 2. Coleta de dados do TST
    if not args.skip_tst:
        steps_results["TST"] = coletar_tst()
    else:
        logger.info("Coleta de dados do TST ignorada")
        steps_results["TST"] = True
    
    # 3. Consolidação dos dados
    if not args.skip_consolidation:
        steps_results["Consolidação"] = consolidar_dados()
    else:
        logger.info("Consolidação dos dados ignorada")
        steps_results["Consolidação"] = True
    
    # 4. Processamento dos dados
    if not args.skip_processing and steps_results["Consolidação"]:
        steps_results["Processamento"] = processar_dados()
    else:
        if args.skip_processing:
            logger.info("Processamento dos dados ignorado")
            steps_results["Processamento"] = True
        else:
            logger.error("Processamento dos dados ignorado devido a falha na consolidação")
            steps_results["Processamento"] = False
    
    # 5. Análise dos dados
    if not args.skip_analysis and steps_results["Processamento"]:
        steps_results["Análise"] = analisar_dados()
    else:
        if args.skip_analysis:
            logger.info("Análise dos dados ignorada")
            steps_results["Análise"] = True
        else:
            logger.error("Análise dos dados ignorada devido a falha no processamento")
            steps_results["Análise"] = False
    
    # Registra fim do pipeline
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info(f"Pipeline completo concluído em {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duração total: {duration}")
    
    # Gera relatório de resultados
    logger.info("===== RELATÓRIO DE RESULTADOS =====")
    for step, result in steps_results.items():
        status = "✅ Sucesso" if result else "❌ Falha" if result is False else "⏭️ Ignorado"
        logger.info(f"{step}: {status}")
    
    # Verifica se todas as etapas foram bem-sucedidas
    all_success = all(result for result in steps_results.values() if result is not None)
    
    if all_success:
        logger.info("PIPELINE CONCLUÍDO COM SUCESSO!")
        return True
    else:
        logger.warning("PIPELINE CONCLUÍDO COM FALHAS!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)