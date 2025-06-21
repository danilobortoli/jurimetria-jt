import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import spacy
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

class DataProcessor:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.raw_data_path = self.base_path / "data" / "raw"
        self.processed_data_path = self.base_path / "data" / "processed"
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
        
        # Carrega modelo do spaCy para processamento de texto
        try:
            self.nlp = spacy.load("pt_core_news_lg")
        except OSError:
            logger.info("Modelo spaCy não encontrado. Baixando...")
            spacy.cli.download("pt_core_news_lg")
            self.nlp = spacy.load("pt_core_news_lg")

    def load_raw_data(self) -> List[Dict[str, Any]]:
        """
        Carrega todos os dados brutos dos arquivos JSON
        Primeiro tenta carregar do arquivo consolidado, depois dos arquivos individuais
        """
        consolidated_path = self.base_path / "data" / "consolidated"
        consolidated_file = consolidated_path / "all_decisions.json"
        
        # Se existe arquivo consolidado, usa ele
        if consolidated_file.exists():
            try:
                with open(consolidated_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Carregados {len(data)} registros do arquivo consolidado {consolidated_file}")
                    return data
            except Exception as e:
                logger.error(f"Erro ao carregar arquivo consolidado: {str(e)}")
                logger.info("Tentando carregar arquivos individuais...")
        
        # Se não conseguiu carregar o consolidado, carrega os arquivos individuais
        all_data = []
        for file_path in self.raw_data_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Carregados {len(data)} registros de {file_path}")
                    all_data.extend(data)
            except Exception as e:
                logger.error(f"Erro ao carregar arquivo {file_path}: {str(e)}")
        
        return all_data

    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Processa o texto da decisão usando NLP
        """
        doc = self.nlp(text)
        
        # Extrai entidades relevantes
        entities = {
            'pessoas': [],
            'organizacoes': [],
            'datas': [],
            'valores': []
        }
        
        for ent in doc.ents:
            if ent.label_ == 'PER':
                entities['pessoas'].append(ent.text)
            elif ent.label_ == 'ORG':
                entities['organizacoes'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['datas'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['valores'].append(ent.text)
        
        # Análise de sentimento básica (pode ser melhorada)
        sentiment_score = 0
        positive_words = {'favorável', 'procedente', 'aceito', 'confirmado'}
        negative_words = {'improcedente', 'negado', 'desfavorável', 'rejeitado'}
        
        for token in doc:
            if token.text.lower() in positive_words:
                sentiment_score += 1
            elif token.text.lower() in negative_words:
                sentiment_score -= 1
        
        return {
            'entities': entities,
            'sentiment_score': sentiment_score,
            'word_count': len(doc),
            'sentence_count': len(list(doc.sents))
        }

    def process_data(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Processa todos os dados e retorna um DataFrame
        """
        processed_data = []
        
        for item in data:
            numero_processo = item.get('numero_processo', '')
            
            # Processa o texto da decisão usando NLP
            texto_analise = item.get('texto', '') + ' ' + item.get('ementa', '')
            processed = self.process_text(texto_analise)
            
            # Extrai o código de assunto (se disponível)
            assuntos = item.get('assuntos', [])
            assunto_codigo = None
            assunto_nome = item.get('assunto', '')
            
            # Verifica cada assunto buscando os códigos específicos de assédio moral
            codigos_assedio_moral = [1723, 14175, 14018]
            for assunto in assuntos:
                if isinstance(assunto, dict) and assunto.get('codigo') in codigos_assedio_moral:
                    assunto_codigo = assunto.get('codigo')
                    assunto_nome = assunto.get('nome', assunto_nome)
                    break
            
            # Adiciona campos dos metadados
            processed.update({
                'id': item.get('id'),
                'tribunal': item.get('tribunal'),
                'numero_processo': numero_processo,
                'data_ajuizamento': item.get('data_ajuizamento'),
                'data_julgamento': item.get('data_julgamento'),
                'instancia': item.get('instancia'),
                'resultado': item.get('resultado'),
                'resultado_codigo': item.get('resultado_codigo'),
                'relator': item.get('relator'),
                'classe': item.get('classe'),
                'assunto': assunto_nome,
                'assunto_codigo': assunto_codigo,
                'orgao_julgador': item.get('orgao_julgador')
            })
            
            # Codifica os resultados para facilitar a análise
            # Primeira instância: 1 = Procedente, 0 = Improcedente
            # Segunda instância ou TST: 1 = Provido, 0 = Desprovido
            resultado_binario = None
            
            if item.get('instancia') == 'Primeira Instância':
                if item.get('resultado') == 'Procedente':
                    resultado_binario = 1
                elif item.get('resultado') == 'Improcedente':
                    resultado_binario = 0
            elif item.get('instancia') in ['Segunda Instância', 'TST']:
                if item.get('resultado') == 'Provido':
                    resultado_binario = 1
                elif item.get('resultado') == 'Desprovido':
                    resultado_binario = 0
            
            processed['resultado_binario'] = resultado_binario
            
            # Verifica se há menção a laudo pericial no texto
            processed['mencao_laudo'] = 1 if any(termo in texto_analise.lower() 
                for termo in ['laudo pericial', 'perícia', 'perito', 'perita', 'laudo médico']) else 0
            
            # Calcula duração do processo (em dias)
            try:
                if item.get('data_ajuizamento') and item.get('data_julgamento'):
                    data_aj = pd.to_datetime(item.get('data_ajuizamento'))
                    data_julg = pd.to_datetime(item.get('data_julgamento'))
                    duracao = (data_julg - data_aj).days
                    processed['duracao_dias'] = duracao
            except Exception as e:
                logger.warning(f"Erro ao calcular duração do processo: {str(e)}")
            
            processed_data.append(processed)
        
        return pd.DataFrame(processed_data)

    def save_processed_data(self, df: pd.DataFrame):
        """
        Salva os dados processados em formato CSV
        """
        output_file = self.processed_data_path / "processed_decisions.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Dados processados salvos em {output_file}")

def main():
    processor = DataProcessor()
    
    # Carrega dados brutos
    raw_data = processor.load_raw_data()
    logger.info(f"Carregados {len(raw_data)} registros")
    
    # Processa dados
    processed_df = processor.process_data(raw_data)
    logger.info(f"Processados {len(processed_df)} registros")
    
    # Salva dados processados
    processor.save_processed_data(processed_df)

if __name__ == "__main__":
    main() 