#!/usr/bin/env python3
"""
Script para executar o pipeline completo de análise de assédio moral na Justiça do Trabalho:
1. Coleta de dados da API do DataJud
2. Processamento dos dados coletados
3. Análise dos dados processados

Este script permite executar todo o pipeline ou apenas partes específicas,
conforme os parâmetros passados na linha de comando.
"""

import os
import sys
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_collection():
    """
    Executa a coleta de dados
    """
    logger.info("Iniciando coleta de dados...")
    try:
        from src.collectors.main import main as collect_main
        collect_main()
        logger.info("Coleta de dados concluída com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro durante a coleta de dados: {str(e)}")
        return False

def run_consolidation():
    """
    Executa a consolidação dos dados coletados
    """
    logger.info("Iniciando consolidação de dados...")
    try:
        from src.collectors.consolidate import main as consolidate_main
        consolidate_main()
        logger.info("Consolidação de dados concluída com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro durante a consolidação de dados: {str(e)}")
        return False

def run_processing():
    """
    Executa o processamento dos dados coletados
    """
    logger.info("Iniciando processamento de dados...")
    try:
        from src.processors.main import main as process_main
        process_main()
        logger.info("Processamento de dados concluído com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro durante o processamento de dados: {str(e)}")
        return False

def run_analysis():
    """
    Executa a análise dos dados processados
    """
    logger.info("Iniciando análise de dados...")
    try:
        from src.analysis.assedio_moral_analysis import main as analyze_main
        analyze_main()
        logger.info("Análise de dados concluída com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro durante a análise de dados: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Pipeline de análise de assédio moral na Justiça do Trabalho")
    
    parser.add_argument('--collect', action='store_true', help='Executar etapa de coleta de dados')
    parser.add_argument('--consolidate', action='store_true', help='Executar etapa de consolidação de dados')
    parser.add_argument('--process', action='store_true', help='Executar etapa de processamento de dados')
    parser.add_argument('--analyze', action='store_true', help='Executar etapa de análise de dados')
    parser.add_argument('--all', action='store_true', help='Executar todo o pipeline')
    parser.add_argument('--start-tribunal', type=int, help='Iniciar coleta a partir deste número de TRT (1-24)')
    parser.add_argument('--end-tribunal', type=int, help='Terminar coleta neste número de TRT (1-24)')
    parser.add_argument('--only-tst', action='store_true', help='Coletar apenas dados do TST')
    parser.add_argument('--sleep', type=int, default=0, help='Tempo de espera entre tribunais (em segundos)')
    
    args = parser.parse_args()
    
    # Se nenhum argumento for fornecido, exibe a ajuda
    if not (args.collect or args.consolidate or args.process or args.analyze or args.all):
        parser.print_help()
        return
    
    start_time = datetime.now()
    logger.info(f"Iniciando pipeline em {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = True
    
    # Executa as etapas conforme solicitado
    if args.all or args.collect:
        # Se tem parâmetros específicos para coleta, sobrescreve a função main
        if args.start_tribunal or args.end_tribunal or args.only_tst:
            from src.collectors.main import DataCollector, logger as collector_logger
            
            # Configuração de coletor personalizado
            collector = DataCollector()
            try:
                # Coleta do TST se não estiver desabilitado
                if not args.only_tst:
                    logger.info("=== Iniciando coleta de dados do TST ===")
                    tst_decisions = collector.collect_from_tst()
                    collector.save_data(tst_decisions, "tst")
                    logger.info(f"Coletados {len(tst_decisions)} processos do TST")
                
                # Coleta dos TRTs conforme faixa especificada
                start_trt = args.start_tribunal if args.start_tribunal else 1
                end_trt = args.end_tribunal if args.end_tribunal else 24
                
                logger.info(f"=== Iniciando coleta de dados dos TRTs ({start_trt} a {end_trt}) ===")
                for region in range(start_trt, end_trt + 1):
                    try:
                        logger.info(f"=== TRT {region} ===")
                        trt_decisions = collector.collect_from_trt(region)
                        collector.save_data(trt_decisions, f"trt{region}")
                        logger.info(f"Coletados {len(trt_decisions)} processos do TRT{region}")
                        
                        # Aguarda entre tribunais se solicitado
                        if args.sleep > 0:
                            logger.info(f"Aguardando {args.sleep} segundos antes do próximo tribunal...")
                            time.sleep(args.sleep)
                    except Exception as e:
                        logger.error(f"Erro ao coletar dados do TRT {region}: {str(e)}")
                        continue
                
                logger.info("=== Coleta de dados concluída ===")
                success = True
            finally:
                collector.close()
        else:
            # Executa a coleta padrão
            success = run_collection()
            
        if not success and args.all:
            logger.error("Coleta falhou, abortando pipeline")
            return
    
    # Consolidação dos dados coletados
    if (args.all and success) or args.consolidate:
        success = run_consolidation()
        if not success and args.all:
            logger.error("Consolidação falhou, abortando pipeline")
            return
    
    # Processamento dos dados
    if (args.all and success) or args.process:
        success = run_processing()
        if not success and args.all:
            logger.error("Processamento falhou, abortando pipeline")
            return
    
    # Análise dos dados processados
    if (args.all and success) or args.analyze:
        success = run_analysis()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info(f"Pipeline concluído em {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duração total: {duration}")
    
    if success:
        logger.info("Todas as etapas foram executadas com sucesso")
    else:
        logger.warning("Uma ou mais etapas apresentaram erros")

if __name__ == "__main__":
    main()