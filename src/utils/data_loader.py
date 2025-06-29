#!/usr/bin/env python3
"""
Módulo utilitário compartilhado para carregamento de dados.
Elimina redundâncias de carregamento de dados em múltiplos scripts.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class DataLoader:
    """Classe unificada para carregamento de dados."""
    
    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = base_path
            
        self.consolidated_path = self.base_path / "data" / "consolidated"
        self.raw_path = self.base_path / "data" / "raw" 
        self.processed_path = self.base_path / "data" / "processed"
        
    def load_consolidated_data(self, filename: str = "all_decisions.json") -> List[Dict[str, Any]]:
        """
        Carrega dados consolidados do arquivo JSON principal.
        
        Args:
            filename: Nome do arquivo JSON consolidado
            
        Returns:
            Lista de dicionários com os dados dos processos
        """
        file_path = self.consolidated_path / filename
        
        if not file_path.exists():
            logger.warning(f"Arquivo consolidado não encontrado: {file_path}")
            return []
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Carregados {len(data)} registros de {file_path}")
                return data
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo consolidado: {str(e)}")
            return []
    
    def load_raw_json_files(self, data_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Carrega todos os arquivos JSON brutos de um diretório.
        
        Args:
            data_path: Caminho opcional para os dados brutos
            
        Returns:
            Lista de dicionários com todos os dados carregados
        """
        if data_path is None:
            search_path = self.raw_path
        else:
            search_path = Path(data_path)
            
        if not search_path.exists():
            logger.error(f"Diretório não encontrado: {search_path}")
            return []
            
        all_data = []
        json_files = list(search_path.glob("*.json"))
        
        logger.info(f"Encontrados {len(json_files)} arquivos JSON em {search_path}")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
            except Exception as e:
                logger.error(f"Erro ao carregar {file_path}: {str(e)}")
                
        logger.info(f"Total de {len(all_data)} registros carregados")
        return all_data
    
    def load_processed_csv(self, filename: str = "processed_decisions.csv") -> pd.DataFrame:
        """
        Carrega dados processados de arquivo CSV.
        
        Args:
            filename: Nome do arquivo CSV processado
            
        Returns:
            DataFrame com os dados processados
        """
        file_path = self.processed_path / filename
        
        if not file_path.exists():
            logger.warning(f"Arquivo processado não encontrado: {file_path}")
            return pd.DataFrame()
            
        try:
            # Verifica tamanho do arquivo para carregamento otimizado
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            logger.info(f"Carregando arquivo CSV: {file_size_mb:.2f} MB")
            
            if file_size_mb > 500:  # Arquivos muito grandes
                logger.info("Arquivo grande detectado, usando carregamento otimizado...")
                df = pd.read_csv(file_path, low_memory=True)
            else:
                df = pd.read_csv(file_path)
                
            # Converte datas automaticamente
            date_columns = ['data_ajuizamento', 'data_julgamento']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    
            logger.info(f"Carregados {len(df)} registros de {file_path}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo CSV: {str(e)}")
            return pd.DataFrame()
    
    def save_data(self, data: List[Dict[str, Any]], filename: str, 
                  output_type: str = "json") -> Path:
        """
        Salva dados em formato JSON ou CSV.
        
        Args:
            data: Dados para salvar
            filename: Nome do arquivo
            output_type: Tipo de saída ('json' ou 'csv')
            
        Returns:
            Caminho do arquivo salvo
        """
        if output_type == "json":
            output_path = self.processed_path / f"{filename}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif output_type == "csv":
            output_path = self.processed_path / f"{filename}.csv"
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False, encoding='utf-8')
        else:
            raise ValueError(f"Tipo de saída não suportado: {output_type}")
            
        logger.info(f"Dados salvos em: {output_path}")
        return output_path


def extract_case_core(numero_processo: str) -> str:
    """
    Função utilitária para extrair o core de um número de processo.
    Elimina redundância presente em múltiplos scripts.
    
    Args:
        numero_processo: Número completo do processo
        
    Returns:
        Core do número do processo (sem dígitos verificadores)
    """
    if not numero_processo:
        return ""
        
    # Remove caracteres não numéricos
    numbers_only = ''.join(filter(str.isdigit, numero_processo))
    
    if len(numbers_only) >= 20:
        # Formato padrão CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
        # Core: NNNNNNN.AAAA.J.TR.OOOO (remove dígitos verificadores)
        return numbers_only[:7] + numbers_only[9:]
    
    return numbers_only


def get_instance_order() -> Dict[str, int]:
    """
    Retorna mapeamento padrão de ordem de instâncias.
    Elimina redundância presente em múltiplos scripts.
    
    Returns:
        Dicionário com ordem das instâncias
    """
    return {
        'Primeira Instância': 1,
        'Segunda Instância': 2, 
        'TST': 3,
        'Desconhecida': 4
    }


def filter_assedio_moral_cases(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtra casos de assédio moral dos dados.
    
    Args:
        data: Lista de dados dos processos
        
    Returns:
        Lista filtrada com apenas casos de assédio moral
    """
    assedio_codes = [1723, 14175, 14018]
    filtered_cases = []
    
    for item in data:
        assuntos = item.get('assuntos', [])
        is_assedio = False
        
        if isinstance(assuntos, list):
            for assunto in assuntos:
                if isinstance(assunto, dict):
                    codigo = assunto.get('codigo')
                    nome = assunto.get('nome', '')
                    if codigo in assedio_codes or 'assédio moral' in nome.lower():
                        is_assedio = True
                        break
        
        if is_assedio:
            filtered_cases.append(item)
    
    return filtered_cases