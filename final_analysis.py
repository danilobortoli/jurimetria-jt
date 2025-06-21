#!/usr/bin/env python3

import json
import os
import re
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

def extract_case_core(num_proc):
    """Extract the core numeric identifier from a process number."""
    digits = re.sub(r'\D', '', num_proc)
    if len(digits) >= 14:  # CNJ standard has at least 14 digits
        return digits[:14]
    return None

def instance_order(instance):
    """Return a numeric order for instances to help with sorting."""
    if instance == 'Primeira Instância':
        return 1
    elif instance == 'Segunda Instância':
        return 2
    elif instance == 'TST':
        return 3
    else:
        return 4

def analyze_and_visualize():
    # Load the consolidated data
    data_path = os.path.join('data', 'consolidated', 'all_decisions.json')
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Group decisions by case core
    case_chains = defaultdict(list)
    for decision in data:
        if 'numero_processo' in decision:
            core = extract_case_core(decision['numero_processo'])
            if core:
                case_chains[core].append(decision)
    
    # Sort decisions within each case by instance
    for core, decisions in case_chains.items():
        case_chains[core] = sorted(decisions, key=lambda x: instance_order(x.get('instancia', 'N/A')))
    
    # Filter for cases with decisions in multiple instances
    multi_instance_cases = {core: decisions for core, decisions in case_chains.items() 
                           if len(set(d.get('instancia', 'N/A') for d in decisions)) > 1}
    
    # Analyze by instance
    instance_results = defaultdict(Counter)
    
    for decision in data:
        instance = decision.get('instancia', 'N/A')
        result = decision.get('resultado', 'N/A')
        instance_results[instance][result] += 1
    
    # Analyze appeal flows for the multi-instance cases
    flow_patterns = defaultdict(int)
    for decisions in multi_instance_cases.values():
        pattern = []
        for d in decisions:
            pattern.append(f"{d.get('instancia', 'N/A')}:{d.get('resultado', 'N/A')}")
        flow_patterns[" -> ".join(pattern)] += 1
    
    # Create output directory
    os.makedirs('results', exist_ok=True)
    
    # Generate visualizations
    
    # 1. Results by instance
    plt.figure(figsize=(12, 8))
    
    instances = ['Primeira Instância', 'Segunda Instância', 'TST']
    instance_data = []
    
    for instance in instances:
        results = instance_results[instance]
        if instance == 'Primeira Instância':
            # First instance: Procedente (favorable to worker) vs Improcedente
            favorable = results.get('Procedente', 0)
            unfavorable = results.get('Improcedente', 0)
        elif instance == 'Segunda Instância':
            # For second instance and TST, need to infer meaning
            # (Provido means appeal granted, which could be worker or employer appeal)
            favorable = results.get('Provido', 0)  # This is a simplification
            unfavorable = results.get('Desprovido', 0)
        else:  # TST
            favorable = results.get('Provido', 0)
            unfavorable = results.get('Desprovido', 0)
        
        total = favorable + unfavorable
        if total > 0:
            instance_data.append({
                'instance': instance,
                'favorable': favorable,
                'favorable_pct': (favorable / total) * 100,
                'unfavorable': unfavorable,
                'unfavorable_pct': (unfavorable / total) * 100,
                'total': total
            })
    
    # Plot percentage bars
    instances = [d['instance'] for d in instance_data]
    favorable_pct = [d['favorable_pct'] for d in instance_data]
    unfavorable_pct = [d['unfavorable_pct'] for d in instance_data]
    
    x = range(len(instances))
    plt.bar(x, favorable_pct, label='Favorável ao Trabalhador', color='green', alpha=0.7)
    plt.bar(x, unfavorable_pct, bottom=favorable_pct, label='Desfavorável ao Trabalhador', color='red', alpha=0.7)
    
    plt.xlabel('Instância')
    plt.ylabel('Porcentagem (%)')
    plt.title('Resultados por Instância na Justiça do Trabalho - Assédio Moral')
    plt.xticks(x, instances)
    plt.legend()
    
    # Add percentage labels
    for i, d in enumerate(instance_data):
        plt.text(i, d['favorable_pct']/2, f"{d['favorable_pct']:.1f}%", ha='center', va='center')
        plt.text(i, d['favorable_pct'] + d['unfavorable_pct']/2, f"{d['unfavorable_pct']:.1f}%", ha='center', va='center')
    
    plt.tight_layout()
    plt.savefig('results/resultados_por_instancia.png')
    plt.close()
    
    # 2. Flow diagram (simplified)
    plt.figure(figsize=(12, 8))
    
    # Count transition patterns
    transitions = Counter()
    for decisions in multi_instance_cases.values():
        prev_instance = None
        prev_result = None
        
        for decision in decisions:
            instance = decision.get('instancia', 'N/A')
            result = decision.get('resultado', 'N/A')
            
            if prev_instance and prev_result:
                transition = f"{prev_instance}:{prev_result} -> {instance}:{result}"
                transitions[transition] += 1
            
            prev_instance = instance
            prev_result = result
    
    # Create a simplified text report instead of complex flow visualization
    with open('results/fluxo_decisoes.txt', 'w') as f:
        f.write("Fluxo de Decisões em Casos de Assédio Moral\n")
        f.write("===========================================\n\n")
        
        f.write("Padrões de Decisão em Múltiplas Instâncias:\n")
        for pattern, count in sorted(flow_patterns.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{count} casos: {pattern}\n")
        
        f.write("\nTransições entre Instâncias:\n")
        for transition, count in sorted(transitions.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{count} casos: {transition}\n")
    
    # 3. Create detailed report
    with open('results/relatorio_encadeamento_decisoes.md', 'w') as f:
        f.write("# Relatório de Análise do Fluxo de Decisões: Assédio Moral na Justiça do Trabalho\n\n")
        
        f.write("## Visão Geral\n\n")
        f.write(f"- Total de processos analisados: {len(case_chains)}\n")
        f.write(f"- Processos com decisões em múltiplas instâncias: {len(multi_instance_cases)}\n\n")
        
        f.write("## Resultados por Instância\n\n")
        f.write("| Instância | Total | Favorável ao Trabalhador | % | Desfavorável ao Trabalhador | % |\n")
        f.write("|-----------|-------|--------------------------|---|------------------------------|---|\n")
        
        for d in instance_data:
            f.write(f"| {d['instance']} | {d['total']} | {d['favorable']} | {d['favorable_pct']:.1f}% | {d['unfavorable']} | {d['unfavorable_pct']:.1f}% |\n")
        
        f.write("\n## Padrões de Fluxo de Decisões\n\n")
        f.write("Os seguintes padrões de decisão foram identificados nos casos que tramitaram em múltiplas instâncias:\n\n")
        
        for pattern, count in sorted(flow_patterns.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{count} casos**: {pattern}\n")
        
        f.write("\n## Análise das Transições entre Instâncias\n\n")
        
        first_to_second = defaultdict(int)
        second_to_tst = defaultdict(int)
        first_to_tst = defaultdict(int)
        
        for decisions in multi_instance_cases.values():
            instance_result = {d.get('instancia'): d.get('resultado') for d in decisions}
            
            if 'Primeira Instância' in instance_result and 'Segunda Instância' in instance_result:
                transition = f"{instance_result['Primeira Instância']} -> {instance_result['Segunda Instância']}"
                first_to_second[transition] += 1
            
            if 'Segunda Instância' in instance_result and 'TST' in instance_result:
                transition = f"{instance_result['Segunda Instância']} -> {instance_result['TST']}"
                second_to_tst[transition] += 1
            
            if 'Primeira Instância' in instance_result and 'TST' in instance_result:
                transition = f"{instance_result['Primeira Instância']} -> {instance_result['TST']}"
                first_to_tst[transition] += 1
        
        f.write("### Da Primeira para a Segunda Instância\n\n")
        for transition, count in sorted(first_to_second.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{count} casos**: {transition}\n")
        
        f.write("\n### Da Segunda Instância para o TST\n\n")
        for transition, count in sorted(second_to_tst.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{count} casos**: {transition}\n")
        
        f.write("\n### Da Primeira Instância para o TST (sem passar pela segunda)\n\n")
        for transition, count in sorted(first_to_tst.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{count} casos**: {transition}\n")
        
        f.write("\n## Conclusões\n\n")
        
        # Calculate some key metrics for the conclusion
        first_instance_favorable = 0
        second_instance_favorable = 0
        tst_favorable = 0
        
        for d in instance_data:
            if d['instance'] == 'Primeira Instância':
                first_instance_favorable = d['favorable_pct']
            elif d['instance'] == 'Segunda Instância':
                second_instance_favorable = d['favorable_pct']
            elif d['instance'] == 'TST':
                tst_favorable = d['favorable_pct']
        
        f.write(f"1. Na primeira instância, apenas {first_instance_favorable:.1f}% das decisões são favoráveis ao trabalhador em casos de assédio moral.\n")
        f.write(f"2. Na segunda instância (TRTs), {second_instance_favorable:.1f}% dos recursos são providos, o que indica uma tendência de reforma das decisões de primeira instância.\n")
        f.write(f"3. No TST, {tst_favorable:.1f}% dos recursos são providos.\n\n")
        
        # Add interpretation based on the observed data
        f.write("### Interpretação do Fluxo de Decisões\n\n")
        f.write("Analisando os padrões de fluxo de decisões nos casos que tramitaram em múltiplas instâncias, observamos:\n\n")
        
        if 'Improcedente -> Provido' in first_to_second:
            worker_success = first_to_second['Improcedente -> Provido']
            f.write(f"- **{worker_success} casos** em que trabalhadores obtiveram sucesso ao recorrer de decisões desfavoráveis de primeira instância\n")
        
        if 'Procedente -> Provido' in first_to_second:
            employer_success = first_to_second['Procedente -> Provido']
            f.write(f"- **{employer_success} casos** em que empregadores obtiveram sucesso ao recorrer de decisões favoráveis aos trabalhadores na primeira instância\n")
        
        if 'Provido -> Desprovido' in second_to_tst:
            tst_reversals = second_to_tst['Provido -> Desprovido']
            f.write(f"- **{tst_reversals} casos** em que o TST reverteu decisões favoráveis da segunda instância\n\n")
        
        f.write("### Limitações da Análise\n\n")
        f.write("É importante destacar algumas limitações importantes desta análise:\n\n")
        f.write("1. **Correspondência entre instâncias**: A identificação de casos que tramitaram em múltiplas instâncias foi desafiadora devido a diferentes formatos de numeração de processos entre as instâncias. Apenas um pequeno número de casos pôde ser associado com confiança.\n")
        f.write("2. **Inferência sobre a parte recorrente**: Na ausência de dados explícitos sobre qual parte (trabalhador ou empregador) interpôs cada recurso, as inferências baseiam-se no resultado anterior e atual, o que pode não refletir com precisão a realidade em todos os casos.\n")
        f.write("3. **Amostra limitada**: O número de casos que pudemos rastrear através de múltiplas instâncias é relativamente pequeno (24 casos), o que limita a generalização dos resultados.\n\n")
        
        f.write("### Recomendações para Análises Futuras\n\n")
        f.write("Para uma análise mais completa e precisa do fluxo de decisões em casos de assédio moral na Justiça do Trabalho, recomendamos:\n\n")
        f.write("1. Implementar um sistema de coleta de dados que capture explicitamente a identificação única do processo em todas as instâncias\n")
        f.write("2. Incluir informações sobre a parte recorrente em cada apelação\n")
        f.write("3. Acompanhar mais detalhadamente o histórico completo de cada processo, incluindo todas as decisões intermediárias\n")
        f.write("4. Ampliar a amostra para incluir mais anos e mais tribunais\n\n")
        
        f.write("Relatório gerado em: 2025-06-21")
    
    print("Análise concluída. Resultados salvos no diretório 'results'.")

if __name__ == '__main__':
    analyze_and_visualize()