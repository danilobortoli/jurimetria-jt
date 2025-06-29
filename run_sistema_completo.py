#!/usr/bin/env python3
"""
Script principal para execução do sistema completo de análise de assédio moral na Justiça do Trabalho.

Este script orquestra todos os componentes do sistema:
1. Coleta de dados de todos os tribunais (TRT2-TRT24 + TST) de 2015 a 2024
2. Processamento e consolidação dos dados
3. Análise estatística por tribunal
4. Análise avançada do fluxo de decisões
5. Análise avançada da taxa de sucesso de recursos
6. Geração de relatórios e visualizações
"""

import argparse
import datetime
import logging
import os
import subprocess
import sys
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sistema_completo.log')
    ]
)
logger = logging.getLogger(__name__)

def executar_comando(comando, descricao=None, timeout=None):
    """
    Executa um comando e registra o resultado.
    
    Args:
        comando: Comando a ser executado
        descricao: Descrição opcional do comando
        timeout: Timeout opcional em segundos
    
    Returns:
        bool: True se o comando foi bem-sucedido, False caso contrário
    """
    if descricao:
        logger.info(f"Executando: {descricao}")
    else:
        logger.info(f"Executando comando: {comando}")
    
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        logger.info(f"Comando concluído com sucesso: {resultado.returncode}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao executar comando: {e}")
        logger.error(f"Saída de erro: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Comando excedeu o tempo limite de {timeout} segundos")
        return False
    except Exception as e:
        logger.error(f"Exceção ao executar comando: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Sistema completo de análise de assédio moral na Justiça do Trabalho")
    parser.add_argument("--pular-coleta", action="store_true", help="Pular etapa de coleta de dados")
    parser.add_argument("--pular-processamento", action="store_true", help="Pular etapa de processamento e consolidação")
    parser.add_argument("--pular-analise-estatistica", action="store_true", help="Pular etapa de análise estatística")
    parser.add_argument("--pular-analise-fluxo", action="store_true", help="Pular etapa de análise de fluxo")
    parser.add_argument("--pular-analise-taxa-sucesso", action="store_true", help="Pular etapa de análise de taxa de sucesso")
    parser.add_argument("--ano-inicio", type=int, default=2015, help="Ano inicial para coleta")
    parser.add_argument("--ano-fim", type=int, default=2024, help="Ano final para coleta")
    parser.add_argument("--trt-inicio", type=int, default=2, help="Primeiro TRT para coleta")
    parser.add_argument("--trt-fim", type=int, default=24, help="Último TRT para coleta")
    parser.add_argument("--incluir-tst", action="store_true", help="Incluir coleta de dados do TST")
    args = parser.parse_args()
    
    # Registrar início da execução
    logger.info(f"Iniciando sistema completo em {datetime.datetime.now()}")
    logger.info(f"Argumentos: {args}")
    
    # Etapa 1: Coleta de dados
    if not args.pular_coleta:
        logger.info("==== Iniciando Etapa 1: Coleta de dados ====")
        
        comando_coleta = f"cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && python run_coleta_completa.py"
        comando_coleta += f" --ano-inicio {args.ano_inicio} --ano-fim {args.ano_fim}"
        comando_coleta += f" --trt-inicio {args.trt_inicio} --trt-fim {args.trt_fim}"
        
        if args.incluir_tst:
            comando_coleta += " --incluir-tst"
        
        if not executar_comando(comando_coleta, "Coleta de dados"):
            logger.error("Falha na etapa de coleta de dados")
            # Continuar mesmo com falha, pois pode ter coletado alguns dados
    else:
        logger.info("Etapa de coleta de dados ignorada conforme solicitado")
    
    # Etapa 2: Processamento e consolidação
    if not args.pular_processamento:
        logger.info("==== Iniciando Etapa 2: Processamento e consolidação ====")
        
        # Consolidação
        logger.info("Executando consolidação dos dados")
        if not executar_comando(
            "cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && python pipeline_assedio_moral.py --consolidate",
            "Consolidação dos dados",
            timeout=600  # 10 minutos
        ):
            logger.error("Falha na consolidação dos dados")
            return
        
        # Processamento
        logger.info("Executando processamento dos dados")
        if not executar_comando(
            "cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && python pipeline_assedio_moral.py --process",
            "Processamento dos dados",
            timeout=1800  # 30 minutos
        ):
            logger.error("Falha no processamento dos dados")
            return
        
        # Análise básica
        logger.info("Executando análise básica dos dados")
        if not executar_comando(
            "cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && python pipeline_assedio_moral.py --analyze",
            "Análise básica dos dados",
            timeout=600  # 10 minutos
        ):
            logger.error("Falha na análise básica dos dados")
            return
    else:
        logger.info("Etapa de processamento e consolidação ignorada conforme solicitado")
    
    # Etapa 3: Análise estatística por tribunal
    if not args.pular_analise_estatistica:
        logger.info("==== Iniciando Etapa 3: Análise estatística por tribunal ====")
        
        if not executar_comando(
            "cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && python analise_estatistica_tribunais.py",
            "Análise estatística por tribunal",
            timeout=1200  # 20 minutos
        ):
            logger.error("Falha na análise estatística por tribunal")
            # Continuar mesmo com falha
    else:
        logger.info("Etapa de análise estatística ignorada conforme solicitado")
    
    # Etapa 4: Análise avançada do fluxo de decisões
    if not args.pular_analise_fluxo:
        logger.info("==== Iniciando Etapa 4: Análise avançada do fluxo de decisões ====")
        
        if not executar_comando(
            "cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && python analise_fluxo_avancada.py",
            "Análise avançada do fluxo de decisões",
            timeout=3600  # 60 minutos
        ):
            logger.error("Falha na análise avançada do fluxo de decisões")
            # Continuar mesmo com falha
    else:
        logger.info("Etapa de análise de fluxo ignorada conforme solicitado")
    
    # Etapa 5: Análise avançada da taxa de sucesso de recursos
    if not args.pular_analise_taxa_sucesso:
        logger.info("==== Iniciando Etapa 5: Análise avançada da taxa de sucesso de recursos ====")
        
        if not executar_comando(
            "cd /Users/danilobortoli/jurimetria-jt && source venv/bin/activate && python analise_taxa_sucesso_avancada.py",
            "Análise avançada da taxa de sucesso de recursos",
            timeout=1800  # 30 minutos
        ):
            logger.error("Falha na análise avançada da taxa de sucesso de recursos")
            # Continuar mesmo com falha
    else:
        logger.info("Etapa de análise de taxa de sucesso ignorada conforme solicitado")
    
    # Etapa 6: Gerar relatório final integrado
    logger.info("==== Iniciando Etapa 6: Geração de relatório final integrado ====")
    
    # Verifica se os diretórios de resultados existem
    resultados_estatisticos_existem = os.path.exists('resultados_estatisticos')
    resultados_fluxo_existem = os.path.exists('resultados_fluxo')
    resultados_taxa_sucesso_existem = os.path.exists('resultados_taxa_sucesso_avancada')
    
    if resultados_estatisticos_existem and resultados_fluxo_existem:
        # Criar diretório para relatório final
        os.makedirs('relatorio_final', exist_ok=True)
        
        # Copiar os arquivos relevantes para o diretório do relatório final
        comandos_copia = [
            "cp resultados_estatisticos/*.png relatorio_final/",
            "cp resultados_estatisticos/relatorio_estatistico.md relatorio_final/",
            "cp resultados_fluxo/*.png relatorio_final/",
            "cp resultados_fluxo/relatorio_fluxo_decisoes.md relatorio_final/",
            "cp data/analysis/relatorio_assedio_moral.md relatorio_final/relatorio_basico.md"
        ]
        
        # Adicionar arquivos da análise de taxa de sucesso se existirem
        if resultados_taxa_sucesso_existem:
            comandos_copia.extend([
                "cp resultados_taxa_sucesso_avancada/*.png relatorio_final/",
                "cp resultados_taxa_sucesso_avancada/relatorio_taxa_sucesso_avancada.md relatorio_final/"
            ])
        
        for comando in comandos_copia:
            executar_comando(comando, "Copiando arquivos para relatório final")
        
        # Criar relatório integrado
        with open('relatorio_final/README.md', 'w') as f:
            f.write("# Análise de Assédio Moral na Justiça do Trabalho\n\n")
            f.write("## Sumário\n\n")
            f.write("1. [Relatório Básico](relatorio_basico.md)\n")
            f.write("2. [Relatório Estatístico por Tribunal](relatorio_estatistico.md)\n")
            f.write("3. [Relatório de Fluxo de Decisões](relatorio_fluxo_decisoes.md)\n")
            if resultados_taxa_sucesso_existem:
                f.write("4. [Relatório de Taxa de Sucesso de Recursos](relatorio_taxa_sucesso_avancada.md)\n")
            f.write("\n")
            
            f.write("## Visualizações\n\n")
            f.write("### Análise Estatística por Tribunal\n\n")
            f.write("![Taxa de Sucesso na Primeira Instância por Tribunal](taxa_sucesso_primeira_instancia.png)\n\n")
            f.write("![Evolução da Taxa de Sucesso](evolucao_taxa_sucesso_primeira_instancia.png)\n\n")
            f.write("![Heatmap de Taxa de Sucesso](heatmap_taxa_sucesso.png)\n\n")
            
            f.write("### Análise de Fluxo de Decisões\n\n")
            f.write("![Taxa de Sucesso por Instância](taxa_sucesso_por_instancia.png)\n\n")
            f.write("![Taxa de Sucesso de Recursos](taxa_sucesso_recursos.png)\n\n")
            
            if resultados_taxa_sucesso_existem:
                f.write("### Análise Avançada de Taxa de Sucesso de Recursos\n\n")
                f.write("![Taxa de Sucesso de Recursos Avançada](taxa_sucesso_recursos.png)\n\n")
                f.write("![Comparação de Taxa de Sucesso](comparacao_taxa_sucesso.png)\n\n")
                f.write("![Padrões de Fluxo](padroes_fluxo.png)\n\n")
            
            f.write("## Principais Descobertas\n\n")
            f.write("### Taxa de Sucesso na Primeira Instância\n")
            f.write("- Análise detalhada por tribunal e período temporal\n")
            f.write("- Identificação de padrões regionais e temporais\n\n")
            
            f.write("### Fluxo de Decisões entre Instâncias\n")
            f.write("- Análise de reversão de decisões entre 1ª e 2ª instâncias\n")
            f.write("- Padrões de recursos para o TST\n")
            f.write("- Taxa de sucesso de recursos por parte (trabalhador vs empregador)\n\n")
            
            if resultados_taxa_sucesso_existem:
                f.write("### Taxa de Sucesso de Recursos Avançada\n")
                f.write("- Análise baseada em códigos de movimento da TPU/CNJ\n")
                f.write("- Identificação precisa de quem interpôs cada recurso\n")
                f.write("- Cadeias completas de recursos (1ª → 2ª → TST)\n")
                f.write("- Padrões de fluxo mais comuns\n\n")
            
            f.write("## Metodologia\n\n")
            f.write("### Coleta de Dados\n")
            f.write("- Dados coletados de todos os TRTs (2-24) e TST\n")
            f.write("- Período: 2015-2024\n")
            f.write("- Filtros: casos de assédio moral\n\n")
            
            f.write("### Processamento\n")
            f.write("- Consolidação e normalização dos dados\n")
            f.write("- Identificação de cadeias de recursos\n")
            f.write("- Análise de códigos de movimento\n\n")
            
            f.write("### Análise\n")
            f.write("- Estatística descritiva por tribunal\n")
            f.write("- Análise de fluxo entre instâncias\n")
            f.write("- Taxa de sucesso de recursos com identificação de partes\n\n")
            
            f.write(f"Relatório gerado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info("Relatório final integrado gerado com sucesso")
        logger.info("Arquivos disponíveis em: relatorio_final/")
    else:
        logger.warning("Alguns diretórios de resultados não foram encontrados")
        if not resultados_estatisticos_existem:
            logger.warning("Diretório 'resultados_estatisticos' não encontrado")
        if not resultados_fluxo_existem:
            logger.warning("Diretório 'resultados_fluxo' não encontrado")
        if not resultados_taxa_sucesso_existem:
            logger.warning("Diretório 'resultados_taxa_sucesso_avancada' não encontrado")
    
    logger.info(f"Sistema completo finalizado em {datetime.datetime.now()}")

if __name__ == "__main__":
    main()