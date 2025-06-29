#!/usr/bin/env python3
"""
Script para coleta específica de dados TST de 2024
"""

import subprocess
import time
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coleta_tst_2024.log'),
        logging.StreamHandler()
    ]
)

def verificar_ambiente():
    """Verifica se o ambiente está configurado"""
    try:
        # Verifica se o pipeline existe
        import os
        if not os.path.exists('pipeline_assedio_moral.py'):
            logging.error("pipeline_assedio_moral.py não encontrado")
            return False
        
        logging.info("Ambiente verificado com sucesso")
        return True
    except Exception as e:
        logging.error(f"Erro ao verificar ambiente: {e}")
        return False

def executar_coleta_tst_2024():
    """Executa coleta específica do TST para 2024"""
    
    # Verifica ambiente primeiro
    if not verificar_ambiente():
        return False
    
    # Comando para executar a coleta
    comando = "python3 pipeline_assedio_moral.py --collect --only-tst --year 2024"
    
    logging.info("🚀 Iniciando coleta do TST para 2024")
    logging.info(f"Comando: {comando}")
    
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos de timeout
        )
        
        if resultado.returncode == 0:
            logging.info("✅ Coleta do TST para 2024 concluída com sucesso")
            logging.info(f"Output: {resultado.stdout}")
            return True
        else:
            logging.error(f"❌ Erro na coleta do TST para 2024")
            logging.error(f"Stderr: {resultado.stderr}")
            logging.error(f"Stdout: {resultado.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error("⏰ Timeout na coleta do TST para 2024 (>10 minutos)")
        return False
    except Exception as e:
        logging.error(f"💥 Erro inesperado na coleta do TST para 2024: {e}")
        return False

def executar_coleta_alternativa():
    """Tenta coleta alternativa caso o método principal falhe"""
    logging.info("🔄 Tentando método alternativo de coleta...")
    
    # Tenta sem parâmetros específicos
    comando = "python3 pipeline_assedio_moral.py --collect"
    
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if resultado.returncode == 0:
            logging.info("✅ Coleta alternativa concluída com sucesso")
            return True
        else:
            logging.error(f"❌ Coleta alternativa também falhou: {resultado.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"💥 Erro na coleta alternativa: {e}")
        return False

def main():
    """Função principal"""
    logging.info("=" * 60)
    logging.info("🎯 COLETA ESPECÍFICA TST 2024")
    logging.info("=" * 60)
    
    # Tenta coleta principal
    if executar_coleta_tst_2024():
        logging.info("🎉 Coleta de 2024 finalizada com sucesso!")
    else:
        logging.warning("⚠️ Coleta principal falhou, tentando método alternativo...")
        if executar_coleta_alternativa():
            logging.info("🎉 Coleta alternativa finalizada com sucesso!")
        else:
            logging.error("💀 Todas as tentativas de coleta falharam")
            
            # Lista arquivos disponíveis para debug
            logging.info("📁 Listando arquivos no diretório atual:")
            try:
                import os
                for arquivo in os.listdir('.'):
                    if arquivo.endswith('.py'):
                        logging.info(f"  - {arquivo}")
            except Exception as e:
                logging.error(f"Erro ao listar arquivos: {e}")

if __name__ == "__main__":
    main()