#!/usr/bin/env python3

import json
import os
import re
from collections import defaultdict

def normalize_process_number(num):
    """
    Normalize process numbers to help with matching across instances.
    First, remove all non-numeric characters, then apply pattern matching.
    """
    # Remove non-numeric characters
    digits_only = re.sub(r'\D', '', num)
    
    # Return the normalized string
    return digits_only

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

def infer_appellant(prev_result, current_result):
    """
    Infer which party likely filed the appeal based on previous and current results.
    
    Args:
        prev_result: Result of the previous instance (e.g., 'Procedente', 'Improcedente')
        current_result: Result of the current instance (e.g., 'Provido', 'Desprovido')
    
    Returns:
        'worker' if likely worker appeal, 'employer' if likely employer appeal
    """
    # In first instance, "Procedente" typically means favorable to worker
    # In appeals, "Provido" means the appeal was granted
    
    # Worker appealing unfavorable first instance decision
    if prev_result == 'Improcedente' and current_result == 'Provido':
        return 'worker'
    
    # Employer appealing favorable first instance decision
    elif prev_result == 'Procedente' and current_result == 'Provido':
        return 'employer'
    
    # Worker appealing, but appeal denied
    elif prev_result == 'Improcedente' and current_result == 'Desprovido':
        return 'worker'
    
    # Employer appealing, but appeal denied
    elif prev_result == 'Procedente' and current_result == 'Desprovido':
        return 'employer'
    
    # If pattern doesn't match, return unknown
    else:
        return 'unknown'

def analyze_case_chains():
    # Load the consolidated data
    data_path = os.path.join('data', 'consolidated', 'all_decisions.json')
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Group decisions by normalized process number
    case_chains = defaultdict(list)
    for decision in data:
        if 'numero_processo' in decision and 'tribunal' in decision and 'instancia' in decision and 'resultado' in decision:
            # Skip cases with missing key information
            norm_num = normalize_process_number(decision['numero_processo'])
            # Only keep the first part of the number (up to 20 digits) to improve matching chances
            if len(norm_num) >= 20:
                norm_num = norm_num[:20]
            case_chains[norm_num].append(decision)
    
    # Sort decisions within each case by instance
    for norm_num, decisions in case_chains.items():
        case_chains[norm_num] = sorted(decisions, key=lambda x: instance_order(x.get('instancia', 'N/A')))
    
    # Count cases with decisions in multiple instances
    cases_with_multiple_instances = 0
    cases_with_all_three_instances = 0
    
    # Track worker and employer appeal success rates
    worker_appeals = {'success': 0, 'failure': 0}
    employer_appeals = {'success': 0, 'failure': 0}
    
    # Track success rates across the complete chain
    complete_chain_outcomes = {
        'worker_first_instance_victory': 0,  # Worker won in first instance
        'worker_second_instance_victory': 0,  # Worker won on appeal to TRT
        'worker_tst_victory': 0,             # Worker won at TST
        'worker_complete_victory': 0,        # Worker won at all three levels
        'worker_partial_victory': 0,         # Worker won at some level
        'worker_no_victory': 0               # Worker lost at all levels
    }
    
    # Analyze each case chain
    multi_instance_cases = []
    for norm_num, decisions in case_chains.items():
        if len(decisions) > 1:
            # Count cases with multiple instances
            cases_with_multiple_instances += 1
            instances = set(d.get('instancia', 'N/A') for d in decisions)
            
            if len(instances) >= 2:  # Only consider cases with at least 2 different instances
                multi_instance_cases.append(decisions)
                
                # Track complete chains
                has_first = any(d.get('instancia') == 'Primeira Instância' for d in decisions)
                has_second = any(d.get('instancia') == 'Segunda Instância' for d in decisions)
                has_tst = any(d.get('instancia') == 'TST' for d in decisions)
                
                if has_first and has_second and has_tst:
                    cases_with_all_three_instances += 1
                
                # Analyze chain of appeals
                prev_decision = None
                worker_won_first = False
                worker_won_second = False
                worker_won_tst = False
                
                for i, decision in enumerate(decisions):
                    instance = decision.get('instancia')
                    result = decision.get('resultado')
                    
                    # Track first instance outcome
                    if instance == 'Primeira Instância':
                        if result == 'Procedente':
                            worker_won_first = True
                            complete_chain_outcomes['worker_first_instance_victory'] += 1
                    
                    # If not first decision, analyze appeal outcome
                    if i > 0 and prev_decision:
                        prev_instance = prev_decision.get('instancia')
                        prev_result = prev_decision.get('resultado')
                        
                        # Only analyze appeals between consecutive instances
                        if ((prev_instance == 'Primeira Instância' and instance == 'Segunda Instância') or
                            (prev_instance == 'Segunda Instância' and instance == 'TST')):
                            
                            appellant = infer_appellant(prev_result, result)
                            
                            if appellant == 'worker':
                                if result == 'Provido':
                                    worker_appeals['success'] += 1
                                    if instance == 'Segunda Instância':
                                        worker_won_second = True
                                        complete_chain_outcomes['worker_second_instance_victory'] += 1
                                    elif instance == 'TST':
                                        worker_won_tst = True
                                        complete_chain_outcomes['worker_tst_victory'] += 1
                                else:  # Desprovido
                                    worker_appeals['failure'] += 1
                            
                            elif appellant == 'employer':
                                if result == 'Provido':
                                    employer_appeals['success'] += 1
                                    # If employer's appeal is successful, worker lost at this level
                                else:  # Desprovido
                                    employer_appeals['failure'] += 1
                                    # If employer's appeal fails, worker maintains victory from previous level
                                    if instance == 'Segunda Instância':
                                        worker_won_second = True
                                        complete_chain_outcomes['worker_second_instance_victory'] += 1
                                    elif instance == 'TST':
                                        worker_won_tst = True
                                        complete_chain_outcomes['worker_tst_victory'] += 1
                    
                    prev_decision = decision
                
                # Count overall outcomes for the case
                if worker_won_first and worker_won_second and worker_won_tst:
                    complete_chain_outcomes['worker_complete_victory'] += 1
                elif worker_won_first or worker_won_second or worker_won_tst:
                    complete_chain_outcomes['worker_partial_victory'] += 1
                else:
                    complete_chain_outcomes['worker_no_victory'] += 1
    
    # Print summary statistics
    print(f"Total unique cases: {len(case_chains)}")
    print(f"Cases with decisions in multiple instances: {cases_with_multiple_instances}")
    print(f"Cases with decisions in all three instances: {cases_with_all_three_instances}")
    
    # Print appeal success rates
    total_worker_appeals = worker_appeals['success'] + worker_appeals['failure']
    total_employer_appeals = employer_appeals['success'] + employer_appeals['failure']
    
    print("\nAppeal Success Rates:")
    if total_worker_appeals > 0:
        worker_success_rate = (worker_appeals['success'] / total_worker_appeals) * 100
        print(f"Worker appeals: {worker_success_rate:.1f}% ({worker_appeals['success']}/{total_worker_appeals})")
    else:
        print("No worker appeals identified")
    
    if total_employer_appeals > 0:
        employer_success_rate = (employer_appeals['success'] / total_employer_appeals) * 100
        print(f"Employer appeals: {employer_success_rate:.1f}% ({employer_appeals['success']}/{total_employer_appeals})")
    else:
        print("No employer appeals identified")
    
    # Print complete chain outcomes
    print("\nComplete Chain Outcomes:")
    print(f"Worker victories in first instance: {complete_chain_outcomes['worker_first_instance_victory']}")
    print(f"Worker victories in second instance: {complete_chain_outcomes['worker_second_instance_victory']}")
    print(f"Worker victories in TST: {complete_chain_outcomes['worker_tst_victory']}")
    print(f"Worker complete victories (all levels): {complete_chain_outcomes['worker_complete_victory']}")
    print(f"Worker partial victories (some level): {complete_chain_outcomes['worker_partial_victory']}")
    print(f"Worker no victories (all levels): {complete_chain_outcomes['worker_no_victory']}")
    
    # Print examples of multi-instance cases
    print("\nExamples of cases with decisions in multiple instances:")
    for i, case in enumerate(multi_instance_cases[:3]):  # Show first 3 examples
        print(f"\nCase {i+1}:")
        for decision in case:
            print(f"  - Instance: {decision.get('instancia', 'N/A')}, Tribunal: {decision.get('tribunal', 'N/A')}, Result: {decision.get('resultado', 'N/A')}")

if __name__ == '__main__':
    analyze_case_chains()