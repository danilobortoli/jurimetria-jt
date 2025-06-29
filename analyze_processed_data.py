#!/usr/bin/env python3
"""
Script independente para análise detalhada dos dados processados de assédio moral na Justiça do Trabalho.
- Lê o arquivo data/processed/processed_decisions.csv
- Gera estatísticas descritivas por tribunal, ano, resultado, valores, duração, etc.
- Salva gráficos em results/
- Imprime resumo no terminal
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configurações gerais
data_path = "data/processed/processed_decisions.csv"
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

# Lê os dados processados
df = pd.read_csv(data_path)

# Converte datas para datetime
for col in ["data_ajuizamento", "data_julgamento"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# Extrai ano do ajuizamento
if "data_ajuizamento" in df.columns:
    df["ano_ajuizamento"] = df["data_ajuizamento"].dt.year

# Estatísticas gerais
print("\n===== ESTATÍSTICAS GERAIS =====")
print(f"Total de processos: {len(df)}")
print(f"Período: {df['ano_ajuizamento'].min()} a {df['ano_ajuizamento'].max()}")
print(f"Tribunais analisados: {df['tribunal'].nunique()} ({', '.join(sorted(df['tribunal'].unique()))})")

# Distribuição por tribunal
tb_tribunal = df['tribunal'].value_counts().sort_index()
print("\nProcessos por tribunal:")
print(tb_tribunal)

# Distribuição por ano
tb_ano = df['ano_ajuizamento'].value_counts().sort_index()
print("\nProcessos por ano de ajuizamento:")
print(tb_ano)

# Distribuição por resultado
if "resultado" in df.columns:
    tb_resultado = df['resultado'].value_counts()
    print("\nDistribuição por resultado:")
    print(tb_resultado)

# Duração dos processos
if "duracao_dias" in df.columns:
    print("\nDuração dos processos (em dias):")
    print(df['duracao_dias'].describe())

# Gráficos
sns.set(style="whitegrid")

# 1. Processos por tribunal
plt.figure(figsize=(12,6))
tb_tribunal.plot(kind='bar')
plt.title('Processos por Tribunal')
plt.ylabel('Quantidade')
plt.xlabel('Tribunal')
plt.tight_layout()
plt.savefig(os.path.join(results_dir, 'processos_por_tribunal.png'))
plt.close()

# 2. Processos por ano
plt.figure(figsize=(12,6))
tb_ano.plot(kind='bar')
plt.title('Processos por Ano de Ajuizamento')
plt.ylabel('Quantidade')
plt.xlabel('Ano')
plt.tight_layout()
plt.savefig(os.path.join(results_dir, 'processos_por_ano.png'))
plt.close()

# 3. Distribuição por resultado
if "resultado" in df.columns:
    plt.figure(figsize=(10,5))
    tb_resultado.plot(kind='bar')
    plt.title('Distribuição por Resultado')
    plt.ylabel('Quantidade')
    plt.xlabel('Resultado')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'distribuicao_por_resultado.png'))
    plt.close()

# 4. Duração dos processos
if "duracao_dias" in df.columns:
    plt.figure(figsize=(10,5))
    sns.histplot(df['duracao_dias'].dropna(), bins=50, kde=True)
    plt.title('Distribuição da Duração dos Processos (dias)')
    plt.xlabel('Dias')
    plt.ylabel('Frequência')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'distribuicao_duracao_processos.png'))
    plt.close()

# Relatório em Markdown
report_path = os.path.join(results_dir, 'relatorio_analise_processados.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('# Relatório de Análise Detalhada dos Dados Processados\n\n')
    f.write(f'**Total de processos:** {len(df)}\n\n')
    f.write(f'**Período:** {df["ano_ajuizamento"].min()} a {df["ano_ajuizamento"].max()}\n\n')
    f.write(f'**Tribunais analisados:** {df["tribunal"].nunique()} ({", ".join(sorted(df["tribunal"].unique()))})\n\n')

    f.write('## Processos por tribunal\n')
    f.write(tb_tribunal.to_markdown() + '\n\n')

    f.write('## Processos por ano de ajuizamento\n')
    f.write(tb_ano.to_markdown() + '\n\n')

    if "resultado" in df.columns:
        f.write('## Distribuição por resultado\n')
        f.write(tb_resultado.to_markdown() + '\n\n')

    if "duracao_dias" in df.columns:
        f.write('## Estatísticas de duração dos processos (em dias)\n')
        f.write(df['duracao_dias'].describe().to_markdown() + '\n\n')

    f.write('## Gráficos gerados\n')
    f.write('- ![Processos por Tribunal](processos_por_tribunal.png)\n')
    f.write('- ![Processos por Ano de Ajuizamento](processos_por_ano.png)\n')
    if "resultado" in df.columns:
        f.write('- ![Distribuição por Resultado](distribuicao_por_resultado.png)\n')
    if "duracao_dias" in df.columns:
        f.write('- ![Distribuição da Duração dos Processos](distribuicao_duracao_processos.png)\n')

print(f"\nRelatório salvo em: {report_path}")

print("Análise detalhada concluída!") 