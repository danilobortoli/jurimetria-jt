#!/usr/bin/env python3
"""
Script para consolidar múltiplos arquivos de coleta em um único arquivo JSON,
removendo duplicatas e organizando por tribunal e instância.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Set

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataConsolidator:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / "data" / "raw"
        self.consolidated_path = self.base_path / "data" / "consolidated"
        self.consolidated_path.mkdir(parents=True, exist_ok=True)
    
    def load_all_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Carrega todos os arquivos JSON da pasta raw e os organiza por tribunal
        """
        if not self.data_path.exists():
            logger.error(f"Pasta de dados brutos não encontrada: {self.data_path}")
            return {}
        
        all_files = list(self.data_path.glob("*.json"))
        logger.info(f"Encontrados {len(all_files)} arquivos para consolidação")
        
        # Agrupa arquivos por tribunal
        data_by_tribunal = {}
        
        for file_path in all_files:
            # Extrai tribunal do nome do arquivo (ex: tst_YYYYMMDD_HHMMSS.json -> tst)
            filename = file_path.name
            tribunal = filename.split('_')[0]
            
            # Inicializa lista para o tribunal se não existir
            if tribunal not in data_by_tribunal:
                data_by_tribunal[tribunal] = []
            
            # Carrega dados do arquivo
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Carregados {len(data)} registros de {file_path}")
                    data_by_tribunal[tribunal].extend(data)
            except Exception as e:
                logger.error(f"Erro ao carregar arquivo {file_path}: {str(e)}")
        
        return data_by_tribunal
    
    def remove_duplicates(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de uma lista de processos com base no número do processo
        """
        unique_data = []
        process_numbers: Set[str] = set()
        
        for item in data:
            numero_processo = item.get('numero_processo', '')
            if numero_processo and numero_processo not in process_numbers:
                unique_data.append(item)
                process_numbers.add(numero_processo)
        
        logger.info(f"Removidas {len(data) - len(unique_data)} duplicatas de {len(data)} registros")
        return unique_data
    
    def organize_by_instancia(self, data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organiza os dados por instância (primeira, segunda, TST)
        """
        organized_data = {
            "primeira_instancia": [],
            "segunda_instancia": [],
            "tst": []
        }
        
        for item in data:
            instancia = item.get('instancia', '')
            
            if instancia == 'TST' or item.get('tribunal') == 'TST':
                organized_data["tst"].append(item)
            elif instancia == 'Primeira Instância':
                organized_data["primeira_instancia"].append(item)
            elif instancia == 'Segunda Instância':
                organized_data["segunda_instancia"].append(item)
            else:
                # Tenta determinar a instância pelo tribunal e órgão julgador
                tribunal = item.get('tribunal', '')
                orgao_julgador = item.get('orgao_julgador', '').lower()
                
                if tribunal == 'TST':
                    organized_data["tst"].append(item)
                elif 'vara' in orgao_julgador or 'juiz' in orgao_julgador:
                    organized_data["primeira_instancia"].append(item)
                elif 'turma' in orgao_julgador or 'colegiado' in orgao_julgador:
                    organized_data["segunda_instancia"].append(item)
                else:
                    # Se não conseguiu determinar, coloca na segunda instância (mais comum)
                    organized_data["segunda_instancia"].append(item)
        
        # Registra contagens
        for key, value in organized_data.items():
            logger.info(f"{key}: {len(value)} registros")
        
        return organized_data
    
    def save_consolidated_data(self, data_by_tribunal: Dict[str, List[Dict[str, Any]]]):
        """
        Salva os dados consolidados em arquivos JSON separados por tribunal
        e em um único arquivo consolidado
        """
        # Salva arquivos consolidados por tribunal
        for tribunal, data in data_by_tribunal.items():
            # Remove duplicatas
            unique_data = self.remove_duplicates(data)
            
            # Organiza por instância
            organized_data = self.organize_by_instancia(unique_data)
            
            # Salva cada instância em um arquivo separado
            for instancia, instancia_data in organized_data.items():
                if instancia_data:
                    filepath = self.consolidated_path / f"{tribunal}_{instancia}.json"
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(instancia_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"Salvos {len(instancia_data)} registros em {filepath}")
        
        # Cria um único arquivo consolidado com todos os dados
        all_data = []
        for tribunal_data in data_by_tribunal.values():
            all_data.extend(tribunal_data)
        
        # Remove duplicatas do arquivo consolidado
        unique_all_data = self.remove_duplicates(all_data)
        
        # Salva arquivo consolidado geral
        consolidated_file = self.consolidated_path / "all_decisions.json"
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            json.dump(unique_all_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Arquivo consolidado completo salvo em {consolidated_file} com {len(unique_all_data)} registros")
    
    def consolidate(self):
        """
        Executa o processo completo de consolidação
        """
        # Carrega todos os arquivos
        data_by_tribunal = self.load_all_files()
        
        if not data_by_tribunal:
            logger.warning("Nenhum dado para consolidar")
            return
        
        # Salva dados consolidados
        self.save_consolidated_data(data_by_tribunal)
        
        logger.info("Consolidação concluída com sucesso")

def main():
    consolidator = DataConsolidator()
    consolidator.consolidate()

if __name__ == "__main__":
    main()