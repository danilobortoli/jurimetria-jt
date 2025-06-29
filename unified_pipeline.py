#!/usr/bin/env python3
"""
Pipeline Unificado para Análise Jurisprudencial
Substitui e consolida: pipeline_assedio_moral.py, run_pipeline_completo.py, run_sistema_completo.py

Este script orquestra todo o fluxo de coleta, processamento e análise de dados.
"""

import argparse
import subprocess
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedPipeline:
    """Pipeline unificado para todo o fluxo de análise jurisprudencial."""
    
    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)
            
        self.log_path = self.base_path / "logs"
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # Define componentes do pipeline
        self.components = {
            'collection': {
                'script': 'src/collectors/main.py',
                'description': 'Coleta de dados via API DataJud',
                'required': False
            },
            'consolidation': {
                'script': 'src/collectors/consolidate.py', 
                'description': 'Consolidação de arquivos JSON',
                'required': False
            },
            'processing': {
                'script': 'src/processors/main.py',
                'description': 'Processamento com NLP',
                'required': False
            },
            'analysis': {
                'script': 'unified_analyzer.py',
                'description': 'Análise unificada completa',
                'required': True
            }
        }
    
    def run_command(self, command: List[str], component_name: str,
                   timeout: int = 3600, retry_count: int = 2) -> bool:
        """
        Executa um comando com retry e logging.
        
        Args:
            command: Lista com comando e argumentos
            component_name: Nome do componente para logging
            timeout: Timeout em segundos
            retry_count: Número de tentativas
            
        Returns:
            True se sucesso, False se falha
        """
        for attempt in range(retry_count + 1):
            try:
                logger.info(f"Executando {component_name} (tentativa {attempt + 1})...")
                logger.info(f"Comando: {' '.join(command)}")
                
                # Prepara arquivos de log
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = self.log_path / f"{component_name}_{timestamp}.log"
                
                with open(log_file, 'w') as f:
                    result = subprocess.run(
                        command,
                        cwd=self.base_path,
                        timeout=timeout,
                        stdout=f,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                
                if result.returncode == 0:
                    logger.info(f"✅ {component_name} executado com sucesso")
                    return True
                else:
                    logger.error(f"❌ {component_name} falhou com código {result.returncode}")
                    
                    # Mostra últimas linhas do log em caso de erro
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            if lines:
                                logger.error("Últimas linhas do log:")
                                for line in lines[-10:]:
                                    logger.error(f"  {line.strip()}")
                    except:
                        pass
                        
            except subprocess.TimeoutExpired:
                logger.error(f"⏰ {component_name} expirou após {timeout} segundos")
            except Exception as e:
                logger.error(f"💥 Erro executando {component_name}: {str(e)}")
            
            if attempt < retry_count:
                logger.info(f"🔄 Tentando novamente em 5 segundos...")
                import time
                time.sleep(5)
        
        logger.error(f"❌ {component_name} falhou após {retry_count + 1} tentativas")
        return False
    
    def check_prerequisites(self) -> bool:
        """
        Verifica pré-requisitos do pipeline.
        
        Returns:
            True se todos os pré-requisitos estão OK
        """
        logger.info("Verificando pré-requisitos...")
        
        # Verifica se Python está funcionando
        try:
            result = subprocess.run([sys.executable, "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Python: {result.stdout.strip()}")
            else:
                logger.error("❌ Python não está funcionando corretamente")
                return False
        except Exception as e:
            logger.error(f"❌ Erro verificando Python: {str(e)}")
            return False
        
        # Verifica se os scripts principais existem
        missing_scripts = []
        for component, config in self.components.items():
            script_path = self.base_path / config['script']
            if config['required'] and not script_path.exists():
                missing_scripts.append(config['script'])
        
        if missing_scripts:
            logger.error(f"❌ Scripts obrigatórios não encontrados: {missing_scripts}")
            return False
        
        # Verifica estrutura de diretórios
        required_dirs = ['src', 'data']
        for dir_name in required_dirs:
            dir_path = self.base_path / dir_name
            if not dir_path.exists():
                logger.info(f"📁 Criando diretório: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ Pré-requisitos verificados")
        return True
    
    def run_data_collection(self, config: Dict[str, Any]) -> bool:
        """
        Executa coleta de dados.
        
        Args:
            config: Configurações da coleta
            
        Returns:
            True se sucesso
        """
        if not config.get('enable_collection', False):
            logger.info("⏭️  Coleta de dados desabilitada")
            return True
            
        command = [sys.executable, self.components['collection']['script']]
        
        # Adiciona parâmetros específicos da coleta
        if config.get('tribunais'):
            command.extend(['--tribunais'] + config['tribunais'])
        if config.get('data_inicio'):
            command.extend(['--data-inicio', config['data_inicio']])
        if config.get('data_fim'):
            command.extend(['--data-fim', config['data_fim']])
            
        return self.run_command(command, 'collection', timeout=7200)  # 2 horas
    
    def run_consolidation(self, config: Dict[str, Any]) -> bool:
        """
        Executa consolidação de dados.
        
        Args:
            config: Configurações da consolidação
            
        Returns:
            True se sucesso
        """
        if not config.get('enable_consolidation', True):
            logger.info("⏭️  Consolidação desabilitada")
            return True
            
        command = [sys.executable, self.components['consolidation']['script']]
        
        # Adiciona parâmetros específicos
        if config.get('input_path'):
            command.extend(['--input-path', config['input_path']])
        if config.get('remove_duplicates', True):
            command.append('--remove-duplicates')
            
        return self.run_command(command, 'consolidation', timeout=3600)  # 1 hora
    
    def run_processing(self, config: Dict[str, Any]) -> bool:
        """
        Executa processamento de dados.
        
        Args:
            config: Configurações do processamento
            
        Returns:
            True se sucesso
        """
        if not config.get('enable_processing', True):
            logger.info("⏭️  Processamento desabilitado")
            return True
            
        command = [sys.executable, self.components['processing']['script']]
        
        # Adiciona parâmetros específicos
        if config.get('enable_nlp', True):
            command.append('--enable-nlp')
        if config.get('batch_size'):
            command.extend(['--batch-size', str(config['batch_size'])])
            
        return self.run_command(command, 'processing', timeout=7200)  # 2 horas
    
    def run_analysis(self, config: Dict[str, Any]) -> bool:
        """
        Executa análise unificada.
        
        Args:
            config: Configurações da análise
            
        Returns:
            True se sucesso
        """
        command = [sys.executable, self.components['analysis']['script']]
        
        # Adiciona parâmetros específicos
        data_source = config.get('data_source', 'consolidated')
        command.extend(['--data-source', data_source])
        
        if config.get('external_path'):
            command.extend(['--external-path', config['external_path']])
            
        if config.get('focus_assedio_moral', True):
            command.append('--focus-assedio')
            
        return self.run_command(command, 'analysis', timeout=3600)  # 1 hora
    
    def generate_pipeline_report(self, results: Dict[str, bool], 
                               config: Dict[str, Any]) -> Path:
        """
        Gera relatório de execução do pipeline.
        
        Args:
            results: Resultados de cada etapa
            config: Configuração utilizada
            
        Returns:
            Caminho do relatório
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.log_path / f"pipeline_report_{timestamp}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Relatório de Execução do Pipeline\n\n")
            f.write(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Status das etapas
            f.write("## Status das Etapas\n\n")
            
            success_count = 0
            total_count = 0
            
            for component, config_comp in self.components.items():
                if component in results:
                    total_count += 1
                    status = "✅ Sucesso" if results[component] else "❌ Falha"
                    if results[component]:
                        success_count += 1
                else:
                    status = "⏭️ Pulada"
                
                f.write(f"- **{config_comp['description']}**: {status}\n")
            
            # Resumo
            f.write(f"\n## Resumo\n\n")
            f.write(f"- Etapas executadas: {total_count}\n")
            f.write(f"- Sucessos: {success_count}\n")
            f.write(f"- Falhas: {total_count - success_count}\n")
            f.write(f"- Taxa de sucesso: {(success_count/total_count*100):.1f}%\n" if total_count > 0 else "")
            
            # Configuração utilizada
            f.write(f"\n## Configuração Utilizada\n\n")
            f.write("```json\n")
            f.write(json.dumps(config, indent=2, ensure_ascii=False))
            f.write("\n```\n")
            
        logger.info(f"Relatório do pipeline salvo em: {report_path}")
        return report_path
    
    def run_pipeline(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """
        Executa pipeline completo.
        
        Args:
            config: Configuração do pipeline
            
        Returns:
            Dicionário com resultados de cada etapa
        """
        logger.info("🚀 Iniciando pipeline unificado...")
        
        # Verifica pré-requisitos
        if not self.check_prerequisites():
            logger.error("❌ Pré-requisitos não atendidos")
            return {}
        
        results = {}
        
        # Executa etapas do pipeline
        pipeline_steps = [
            ('collection', self.run_data_collection),
            ('consolidation', self.run_consolidation), 
            ('processing', self.run_processing),
            ('analysis', self.run_analysis)
        ]
        
        for step_name, step_function in pipeline_steps:
            if step_name in config and config.get(f'enable_{step_name}', True):
                logger.info(f"📋 Executando: {self.components[step_name]['description']}")
                results[step_name] = step_function(config)
                
                if not results[step_name]:
                    if config.get('stop_on_error', True):
                        logger.error(f"⛔ Pipeline interrompido devido a falha em {step_name}")
                        break
                    else:
                        logger.warning(f"⚠️  Continuando apesar da falha em {step_name}")
            else:
                logger.info(f"⏭️  Pulando: {self.components[step_name]['description']}")
        
        # Gera relatório do pipeline
        report_path = self.generate_pipeline_report(results, config)
        
        # Resumo final
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count and total_count > 0:
            logger.info(f"🎉 Pipeline concluído com sucesso! ({success_count}/{total_count})")
        else:
            logger.warning(f"⚠️  Pipeline concluído com {success_count}/{total_count} sucessos")
        
        return results


def load_config_file(config_path: str) -> Dict[str, Any]:
    """
    Carrega configuração de arquivo JSON.
    
    Args:
        config_path: Caminho para arquivo de configuração
        
    Returns:
        Dicionário com configuração
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro carregando configuração: {str(e)}")
        return {}


def create_default_config() -> Dict[str, Any]:
    """
    Cria configuração padrão do pipeline.
    
    Returns:
        Configuração padrão
    """
    return {
        'enable_collection': False,  # Desabilitado por padrão
        'enable_consolidation': True,
        'enable_processing': False,  # Opcional
        'enable_analysis': True,
        'data_source': 'external',
        'external_path': '/Users/danilobortoli/Documents/Tese de doutorado da Andreia/Dados da segunda extração/raw',
        'focus_assedio_moral': True,
        'stop_on_error': False,
        'remove_duplicates': True
    }


def main():
    """Função principal com interface de linha de comando."""
    parser = argparse.ArgumentParser(description="Pipeline Unificado de Análise Jurisprudencial")
    
    parser.add_argument("--config", type=str,
                       help="Arquivo de configuração JSON")
    parser.add_argument("--data-source", choices=["consolidated", "raw", "external"],
                       default="external", help="Fonte dos dados")
    parser.add_argument("--external-path", type=str,
                       default="/Users/danilobortoli/Documents/Tese de doutorado da Andreia/Dados da segunda extração/raw",
                       help="Caminho externo para dados")
    parser.add_argument("--enable-collection", action="store_true",
                       help="Habilita coleta de dados")
    parser.add_argument("--enable-processing", action="store_true", 
                       help="Habilita processamento com NLP")
    parser.add_argument("--disable-consolidation", action="store_true",
                       help="Desabilita consolidação")
    parser.add_argument("--continue-on-error", action="store_true",
                       help="Continua pipeline mesmo com erros")
    
    args = parser.parse_args()
    
    # Carrega configuração
    if args.config:
        config = load_config_file(args.config)
    else:
        config = create_default_config()
    
    # Sobrescreve com argumentos da linha de comando
    if args.data_source:
        config['data_source'] = args.data_source
    if args.external_path:
        config['external_path'] = args.external_path
    if args.enable_collection:
        config['enable_collection'] = True
    if args.enable_processing:
        config['enable_processing'] = True
    if args.disable_consolidation:
        config['enable_consolidation'] = False
    if args.continue_on_error:
        config['stop_on_error'] = False
    
    # Inicializa e executa pipeline
    pipeline = UnifiedPipeline()
    results = pipeline.run_pipeline(config)
    
    # Status final
    if results:
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            print(f"\n✅ Pipeline executado com sucesso! ({success_count}/{total_count})")
            sys.exit(0)
        else:
            print(f"\n⚠️  Pipeline concluído com {success_count}/{total_count} sucessos")
            sys.exit(1)
    else:
        print("\n❌ Pipeline falhou")
        sys.exit(1)


if __name__ == "__main__":
    main()