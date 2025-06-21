#!/usr/bin/env python3

import json
import os
import re
from collections import defaultdict

def normalize_process_number(num):
    """Remove non-numeric characters to help with matching."""
    return re.sub(r'\D', '', num)

def main():
    # Load the consolidated data
    data_path = os.path.join('data', 'consolidated', 'all_decisions.json')
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Group decisions by normalized process number
    cases = defaultdict(list)
    for decision in data:
        if 'numero_processo' in decision:
            norm_num = normalize_process_number(decision['numero_processo'])
            cases[norm_num].append(decision)
    
    # Count cases with decisions in multiple instances
    cases_with_multiple_instances = 0
    cases_with_all_three_instances = 0
    
    for num, decisions in cases.items():
        instances = set(d.get('instancia', 'N/A') for d in decisions)
        if len(instances) > 1:
            cases_with_multiple_instances += 1
            if len(instances) == 3 or ('Primeira Instância' in instances and 'Segunda Instância' in instances and any('TST' in i for i in instances)):
                cases_with_all_three_instances += 1
    
    # Print summary
    print(f'Total unique cases: {len(cases)}')
    print(f'Cases with decisions in multiple instances: {cases_with_multiple_instances}')
    print(f'Cases with decisions in all three instances: {cases_with_all_three_instances}')
    
    # Show some examples of cases with all three instances
    print("\nExamples of cases with decisions in all three instances:")
    count = 0
    for num, decisions in cases.items():
        instances = set(d.get('instancia', 'N/A') for d in decisions)
        if len(instances) == 3 or ('Primeira Instância' in instances and 'Segunda Instância' in instances and any('TST' in i for i in instances)):
            if count < 3:  # Show only 3 examples
                print(f"\nCase {count+1}: Process number with pattern matching {decisions[0].get('numero_processo', 'N/A')}")
                for d in sorted(decisions, key=lambda x: {'Primeira Instância': 1, 'Segunda Instância': 2, 'TST': 3}.get(x.get('instancia', 'N/A'), 4)):
                    print(f"  - Instance: {d.get('instancia', 'N/A')}, Tribunal: {d.get('tribunal', 'N/A')}, Result: {d.get('resultado', 'N/A')}")
                count += 1

if __name__ == '__main__':
    main()