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
        """
        all_data = []
        for file_path in self.raw_data_path.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.extend(data)
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
            processed = self.process_text(item.get('texto', ''))
            processed.update({
                'id': item.get('id'),
                'tribunal': item.get('tribunal'),
                'data_julgamento': item.get('data_julgamento'),
                'relator': item.get('relator'),
                'classe': item.get('classe'),
                'assunto': item.get('assunto')
            })
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