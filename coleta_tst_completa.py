#!/usr/bin/env python3
"""
Script para coleta completa de dados do TST de 2015 a 2024
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
        logging.FileHandler('coleta_tst.log'),
        logging.StreamHandler()
    ]
)

def executar_coleta_tst(ano):
    """Executa coleta do TST para um ano específico"""
    comando = f"source venv/bin/activate && python pipeline_assedio_moral.py --collect --only-tst --year {ano}"
    
    logging.info(f"Iniciando coleta do TST para o ano {ano}")
    
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos de timeout
        )
        
        if resultado.returncode == 0:
            logging.info(f"Coleta do TST para {ano} concluída com sucesso")
            return True
        else:
            logging.error(f"Erro na coleta do TST para {ano}: {resultado.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error(f"Timeout na coleta do TST para {ano}")
        return False
    except Exception as e:
        logging.error(f"Erro inesperado na coleta do TST para {ano}: {e}")
        return False

def main():
    """Função principal"""
    anos = list(range(2015, 2025))  # 2015 a 2024
    
    logging.info(f"Iniciando coleta completa do TST para os anos: {anos}")
    
    sucessos = 0
    falhas = 0
    
    for ano in anos:
        if executar_coleta_tst(ano):
            sucessos += 1
        else:
            falhas += 1
        
        # Aguardar 30 segundos entre as coletas
        if ano < 2024:  # Não aguardar após o último ano
            logging.info("Aguardando 30 segundos antes da próxima coleta...")
            time.sleep(30)
    
    logging.info(f"Coleta completa finalizada!")
    logging.info(f"Sucessos: {sucessos}")
    logging.info(f"Falhas: {falhas}")

if __name__ == "__main__":
    main() 