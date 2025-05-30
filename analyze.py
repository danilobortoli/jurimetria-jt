#!/usr/bin/env python3
import json
import os

def analyze_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Arquivo: {os.path.basename(file_path)}")
        print(f"Total de registros: {len(data)}")
        
        # Contagens
        tribunais = {}
        assuntos = {}
        classes = {}
        orgaos = {}
        
        # Anos de ajuizamento
        anos = {}
        
        for item in data:
            # Tribunal
            tribunal = item.get('tribunal', '')
            if tribunal:
                tribunais[tribunal] = tribunais.get(tribunal, 0) + 1
            
            # Assunto
            assunto = item.get('assunto', '')
            if assunto:
                assuntos[assunto] = assuntos.get(assunto, 0) + 1
            
            # Classe
            classe = item.get('classe', '')
            if classe:
                classes[classe] = classes.get(classe, 0) + 1
            
            # Órgão julgador
            orgao = item.get('orgao_julgador', '')
            if orgao:
                orgaos[orgao] = orgaos.get(orgao, 0) + 1
            
            # Ano de ajuizamento
            data_aj = item.get('data_ajuizamento', '')
            if data_aj and len(data_aj) >= 4:
                ano = data_aj[:4]
                anos[ano] = anos.get(ano, 0) + 1
        
        # Exibe resultados
        print("\nTribunais:")
        for tribunal, count in tribunais.items():
            print(f"- {tribunal}: {count}")
        
        print("\nTop 5 Assuntos:")
        for assunto, count in sorted(assuntos.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"- {assunto}: {count}")
        
        print("\nTop 5 Classes Processuais:")
        for classe, count in sorted(classes.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"- {classe}: {count}")
        
        print("\nTop 5 Órgãos Julgadores:")
        for orgao, count in sorted(orgaos.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"- {orgao}: {count}")
        
        print("\nDistribuição por Ano:")
        for ano, count in sorted(anos.items()):
            print(f"- {ano}: {count}")
            
    except Exception as e:
        print(f"Erro ao analisar arquivo {file_path}: {e}")

def main():
    raw_dir = os.path.join(os.path.dirname(__file__), "data", "raw")
    for filename in os.listdir(raw_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(raw_dir, filename)
            analyze_file(file_path)
            print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()