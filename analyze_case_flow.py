#!/usr/bin/env python3

import json
import os
import re
from collections import defaultdict

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

def analyze_case_flow():
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
    
    # Count outcomes and flow patterns
    outcome_patterns = defaultdict(int)
    
    for core, decisions in multi_instance_cases.items():
        # Extract the sequence of outcomes
        outcome_sequence = []
        for decision in decisions:
            instance = decision.get('instancia', 'N/A')
            result = decision.get('resultado', 'N/A')
            outcome_sequence.append(f"{instance}:{result}")
        
        # Create a pattern string from the sequence
        pattern = " -> ".join(outcome_sequence)
        outcome_patterns[pattern] += 1
    
    # Analyze the outcome patterns
    print(f"Total unique cases: {len(case_chains)}")
    print(f"Cases with decisions in multiple instances: {len(multi_instance_cases)}")
    
    # Print the most common outcome patterns
    print("\nMost Common Case Flow Patterns:")
    for i, (pattern, count) in enumerate(sorted(outcome_patterns.items(), key=lambda x: x[1], reverse=True)):
        if i < 20:  # Show top 20 patterns
            print(f"{count} cases: {pattern}")
    
    # Analyze specific transition patterns
    worker_favorable_transitions = 0
    employer_favorable_transitions = 0
    
    # Categorize first to second instance transitions
    first_to_second_transitions = {
        'improcedente_to_provido': 0,    # Worker favorable
        'improcedente_to_desprovido': 0, # Worker unfavorable
        'procedente_to_provido': 0,      # Employer favorable
        'procedente_to_desprovido': 0,   # Employer unfavorable
    }
    
    # Categorize second instance to TST transitions
    second_to_tst_transitions = {
        'provido_to_provido': 0,       # Depends on first instance
        'provido_to_desprovido': 0,    # Depends on first instance
        'desprovido_to_provido': 0,    # Depends on first instance
        'desprovido_to_desprovido': 0, # Depends on first instance
    }
    
    # Track complete case outcomes
    complete_case_outcomes = {
        'worker_won_all': 0,         # Worker won at all levels
        'worker_won_first_lost_rest': 0,  # Worker won first, lost appeals
        'worker_lost_first_won_second_lost_tst': 0,  # Worker lost, won appeal, lost at TST
        'worker_lost_first_won_rest': 0,  # Worker lost first, won appeals
        'worker_lost_first_second_won_tst': 0,  # Worker lost first & second, won at TST
        'worker_lost_all': 0,        # Worker lost at all levels
    }
    
    # Analyze case chains in detail
    for core, decisions in multi_instance_cases.items():
        instances = [d.get('instancia', 'N/A') for d in decisions]
        results = [d.get('resultado', 'N/A') for d in decisions]
        
        # Create dictionaries for easy lookup
        instance_result = {d.get('instancia', 'N/A'): d.get('resultado', 'N/A') for d in decisions}
        
        # Check for first to second instance transitions
        if 'Primeira Instância' in instances and 'Segunda Instância' in instances:
            first_result = instance_result['Primeira Instância']
            second_result = instance_result['Segunda Instância']
            
            if first_result == 'Improcedente' and second_result == 'Provido':
                first_to_second_transitions['improcedente_to_provido'] += 1
                worker_favorable_transitions += 1
            elif first_result == 'Improcedente' and second_result == 'Desprovido':
                first_to_second_transitions['improcedente_to_desprovido'] += 1
            elif first_result == 'Procedente' and second_result == 'Provido':
                first_to_second_transitions['procedente_to_provido'] += 1
                employer_favorable_transitions += 1
            elif first_result == 'Procedente' and second_result == 'Desprovido':
                first_to_second_transitions['procedente_to_desprovido'] += 1
        
        # Check for second instance to TST transitions
        if 'Segunda Instância' in instances and 'TST' in instances:
            second_result = instance_result['Segunda Instância']
            tst_result = instance_result['TST']
            
            if second_result == 'Provido' and tst_result == 'Provido':
                second_to_tst_transitions['provido_to_provido'] += 1
            elif second_result == 'Provido' and tst_result == 'Desprovido':
                second_to_tst_transitions['provido_to_desprovido'] += 1
            elif second_result == 'Desprovido' and tst_result == 'Provido':
                second_to_tst_transitions['desprovido_to_provido'] += 1
            elif second_result == 'Desprovido' and tst_result == 'Desprovido':
                second_to_tst_transitions['desprovido_to_desprovido'] += 1
        
        # Analyze complete case chains (all three instances)
        if set(instances) == {'Primeira Instância', 'Segunda Instância', 'TST'}:
            first_result = instance_result['Primeira Instância']
            second_result = instance_result['Segunda Instância']
            tst_result = instance_result['TST']
            
            # Worker won first instance
            if first_result == 'Procedente':
                # Check second instance (appeal likely from employer)
                if second_result == 'Desprovido':  # Employer appeal failed
                    # Check TST (appeal likely from employer)
                    if tst_result == 'Desprovido':  # Employer appeal failed again
                        complete_case_outcomes['worker_won_all'] += 1
                    else:  # Employer won at TST
                        complete_case_outcomes['worker_won_first_lost_rest'] += 1
                else:  # Employer appeal succeeded
                    # Check TST (appeal likely from worker)
                    if tst_result == 'Provido':  # Worker appeal succeeded
                        complete_case_outcomes['worker_won_all'] += 1
                    else:  # Worker appeal failed
                        complete_case_outcomes['worker_won_first_lost_rest'] += 1
            
            # Worker lost first instance
            else:
                # Check second instance (appeal likely from worker)
                if second_result == 'Provido':  # Worker appeal succeeded
                    # Check TST (appeal likely from employer)
                    if tst_result == 'Desprovido':  # Employer appeal succeeded
                        complete_case_outcomes['worker_lost_first_won_second_lost_tst'] += 1
                    else:  # Employer appeal failed
                        complete_case_outcomes['worker_lost_first_won_rest'] += 1
                else:  # Worker appeal failed
                    # Check TST (appeal likely from worker)
                    if tst_result == 'Provido':  # Worker appeal succeeded
                        complete_case_outcomes['worker_lost_first_second_won_tst'] += 1
                    else:  # Worker appeal failed again
                        complete_case_outcomes['worker_lost_all'] += 1
    
    # Print transition analysis
    print("\nFirst to Second Instance Transitions:")
    print(f"Worker favorable (Improcedente -> Provido): {first_to_second_transitions['improcedente_to_provido']}")
    print(f"Worker unfavorable (Improcedente -> Desprovido): {first_to_second_transitions['improcedente_to_desprovido']}")
    print(f"Employer favorable (Procedente -> Provido): {first_to_second_transitions['procedente_to_provido']}")
    print(f"Employer unfavorable (Procedente -> Desprovido): {first_to_second_transitions['procedente_to_desprovido']}")
    
    worker_appeal_success_rate = 0
    if first_to_second_transitions['improcedente_to_provido'] + first_to_second_transitions['improcedente_to_desprovido'] > 0:
        worker_appeal_success_rate = (first_to_second_transitions['improcedente_to_provido'] / 
                                    (first_to_second_transitions['improcedente_to_provido'] + 
                                     first_to_second_transitions['improcedente_to_desprovido'])) * 100
    
    employer_appeal_success_rate = 0
    if first_to_second_transitions['procedente_to_provido'] + first_to_second_transitions['procedente_to_desprovido'] > 0:
        employer_appeal_success_rate = (first_to_second_transitions['procedente_to_provido'] / 
                                      (first_to_second_transitions['procedente_to_provido'] + 
                                       first_to_second_transitions['procedente_to_desprovido'])) * 100
    
    print(f"\nWorker appeal success rate (first to second instance): {worker_appeal_success_rate:.1f}%")
    print(f"Employer appeal success rate (first to second instance): {employer_appeal_success_rate:.1f}%")
    
    # Print complete case outcomes
    print("\nComplete Case Outcomes (All Three Instances):")
    print(f"Worker won at all levels: {complete_case_outcomes['worker_won_all']}")
    print(f"Worker won first instance, lost appeals: {complete_case_outcomes['worker_won_first_lost_rest']}")
    print(f"Worker lost first, won second, lost at TST: {complete_case_outcomes['worker_lost_first_won_second_lost_tst']}")
    print(f"Worker lost first, won subsequent appeals: {complete_case_outcomes['worker_lost_first_won_rest']}")
    print(f"Worker lost first & second, won at TST: {complete_case_outcomes['worker_lost_first_second_won_tst']}")
    print(f"Worker lost at all levels: {complete_case_outcomes['worker_lost_all']}")
    
    # Print examples of matched cases
    print("\nExamples of cases with decisions in multiple instances:")
    for i, (core, decisions) in enumerate(list(multi_instance_cases.items())[:5]):
        print(f"\nCase {i+1} (Core: {core}):")
        for decision in decisions:
            print(f"  - Instance: {decision.get('instancia', 'N/A')}, Tribunal: {decision.get('tribunal', 'N/A')}, Result: {decision.get('resultado', 'N/A')}, Process Number: {decision.get('numero_processo', 'N/A')}")

if __name__ == '__main__':
    analyze_case_flow()