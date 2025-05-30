#!/usr/bin/env python3
"""
Script para testar a conexão com a API do DataJud
"""

import os
import sys
import requests
from dotenv import load_dotenv
from src.collectors.datajud_api import DataJudAPI
from datetime import datetime, timedelta

# Carrega variáveis de ambiente
load_dotenv()

def test_datajud_api():
    """Testa a conexão e funcionalidades básicas da API do DataJud"""
    
    print("=== Teste da API do DataJud ===\n")
    
    # Verifica se a API key está configurada
    api_key = os.getenv("DATAJUD_API_KEY")
    if not api_key:
        print("❌ ERRO: DATAJUD_API_KEY não encontrada no arquivo .env")
        print("Por favor, configure a API key no arquivo .env")
        return False
    
    print("✅ API key encontrada")
    
    try:
        # Inicializa a API
        api = DataJudAPI(api_key)
        print("✅ Cliente API inicializado")
        
        # Define período de teste (janeiro a junho de 2023)
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 6, 30)
        tribunal = "TST"  # Testamos com o TST
        
        print(f"\nTestando busca de decisões:")
        print(f"- Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
        print(f"- Tribunal: {tribunal}")
        print(f"- Assunto: ASSÉDIO MORAL")
        
        # Constrói uma query simplificada para testar acesso básico
        query = {
            "query": {
                "match_all": {}
            },
            "size": 5
        }
        
        # Tenta fazer a busca diretamente no endpoint do Elasticsearch
        endpoint = api.TRIBUNAL_ENDPOINTS[tribunal]
        response = requests.post(endpoint, headers=api.headers, json=query)
        
        if response.status_code == 200:
            result = response.json()
            hits = result.get('hits', {}).get('hits', [])
            total = result.get('hits', {}).get('total', {}).get('value', 0)
            
            print(f"\n✅ Busca realizada com sucesso!")
            print(f"- Total de resultados: {total}")
            print(f"- Resultados nesta página: {len(hits)}")
            
            # Mostra primeiro resultado (se houver)
            if hits:
                first = hits[0]['_source']
                print(f"\nPrimeiro resultado:")
                print(f"- ID: {hits[0].get('_id')}")
                print(f"- Número do Processo: {first.get('numeroProcesso')}")
                print(f"- Data: {first.get('dataAjuizamento')}")
                
                # Mostra algumas chaves disponíveis para ajudar a entender a estrutura
                print(f"\nChaves disponíveis no resultado:")
                for key in first.keys():
                    print(f"- {key}")
            else:
                print("\n⚠️ Nenhum processo encontrado com o termo 'assédio moral'")
        else:
            print(f"❌ Erro na requisição: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Erro ao testar API: {str(e)}")
        return False
    
    print("\n=== Teste concluído ===")
    return True

if __name__ == "__main__":
    success = test_datajud_api()
    sys.exit(0 if success else 1)