#!/usr/bin/env python3
"""
Script para testar a conexão com a API do DataJud
"""

import os
import sys
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
        
        # Define período de teste (última semana)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"\nTestando busca de decisões:")
        print(f"- Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
        print(f"- Tribunal: TST")
        print(f"- Assunto: ASSÉDIO MORAL")
        
        # Tenta buscar decisões
        result = api.search_decisions(
            start_date=start_date,
            end_date=end_date,
            tribunal="TST",
            assunto="ASSÉDIO MORAL",
            page_size=5  # Busca apenas 5 resultados para teste
        )
        
        if result:
            print(f"\n✅ Busca realizada com sucesso!")
            print(f"- Total de resultados: {result.get('totalElements', 0)}")
            print(f"- Resultados nesta página: {len(result.get('content', []))}")
            
            # Mostra primeiro resultado (se houver)
            if result.get('content'):
                first = result['content'][0]
                print(f"\nPrimeiro resultado:")
                print(f"- ID: {first.get('id')}")
                print(f"- Tribunal: {first.get('tribunal')}")
                print(f"- Data: {first.get('dataJulgamento')}")
        else:
            print("❌ Nenhum resultado retornado")
            
    except Exception as e:
        print(f"❌ Erro ao testar API: {str(e)}")
        return False
    
    print("\n=== Teste concluído ===")
    return True

if __name__ == "__main__":
    success = test_datajud_api()
    sys.exit(0 if success else 1)