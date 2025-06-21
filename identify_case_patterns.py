#!/usr/bin/env python3

import json
import os
import re
from collections import defaultdict, Counter

def main():
    # Load the consolidated data
    data_path = os.path.join('data', 'consolidated', 'all_decisions.json')
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Extract and analyze process number patterns
    first_instance_patterns = []
    second_instance_patterns = []
    tst_patterns = []
    
    # Sample process numbers for manual inspection
    samples = {
        'Primeira Instância': [],
        'Segunda Instância': [],
        'TST': []
    }
    
    # Count by tribunal and instance
    tribunal_counts = defaultdict(lambda: defaultdict(int))
    
    for decision in data:
        instance = decision.get('instancia', 'N/A')
        tribunal = decision.get('tribunal', 'N/A')
        num_proc = decision.get('numero_processo', '')
        
        tribunal_counts[tribunal][instance] += 1
        
        # Collect sample process numbers
        if len(samples[instance]) < 5 and num_proc:
            samples[instance].append((tribunal, num_proc))
        
        # Extract patterns
        if instance == 'Primeira Instância':
            first_instance_patterns.append(num_proc)
        elif instance == 'Segunda Instância':
            second_instance_patterns.append(num_proc)
        elif instance == 'TST':
            tst_patterns.append(num_proc)
    
    # Print tribunal and instance distribution
    print("=== Tribunal and Instance Counts ===")
    for tribunal in sorted(tribunal_counts.keys()):
        print(f"\n{tribunal}:")
        for instance, count in tribunal_counts[tribunal].items():
            print(f"  {instance}: {count}")
    
    # Print sample process numbers for manual inspection
    print("\n=== Sample Process Numbers by Instance ===")
    for instance, sample_list in samples.items():
        print(f"\n{instance}:")
        for tribunal, num_proc in sample_list:
            print(f"  {tribunal}: {num_proc}")
    
    # Attempt to find pattern transformations between instances
    print("\n=== Process Number Pattern Analysis ===")
    
    # Extract the first 7 digits for comparison
    print("\nFirst 7 digits frequency analysis:")
    first_inst_prefixes = Counter([p[:7] for p in first_instance_patterns if len(p) >= 7])
    second_inst_prefixes = Counter([p[:7] for p in second_instance_patterns if len(p) >= 7])
    tst_prefixes = Counter([p[:7] for p in tst_patterns if len(p) >= 7])
    
    print(f"First instance most common prefixes: {first_inst_prefixes.most_common(5)}")
    print(f"Second instance most common prefixes: {second_inst_prefixes.most_common(5)}")
    print(f"TST most common prefixes: {tst_prefixes.most_common(5)}")
    
    # Check for identical process numbers across instances
    print("\nLooking for exact matches between instances...")
    first_set = set(first_instance_patterns)
    second_set = set(second_instance_patterns)
    tst_set = set(tst_patterns)
    
    first_second_matches = first_set.intersection(second_set)
    second_tst_matches = second_set.intersection(tst_set)
    first_tst_matches = first_set.intersection(tst_set)
    
    print(f"Exact matches between first and second instances: {len(first_second_matches)}")
    print(f"Exact matches between second instance and TST: {len(second_tst_matches)}")
    print(f"Exact matches between first instance and TST: {len(first_tst_matches)}")
    
    # Extract year patterns
    year_pattern = re.compile(r'(\d{4})')
    years_first = Counter()
    years_second = Counter()
    years_tst = Counter()
    
    for num in first_instance_patterns:
        matches = year_pattern.findall(num)
        if matches:
            years_first[matches[0]] += 1
    
    for num in second_instance_patterns:
        matches = year_pattern.findall(num)
        if matches:
            years_second[matches[0]] += 1
    
    for num in tst_patterns:
        matches = year_pattern.findall(num)
        if matches:
            years_tst[matches[0]] += 1
    
    print("\nYear distribution in process numbers:")
    print(f"First instance years: {years_first.most_common(5)}")
    print(f"Second instance years: {years_second.most_common(5)}")
    print(f"TST years: {years_tst.most_common(5)}")
    
    # Extract the case part before the tribunal code
    print("\nLooking at case number core patterns...")
    
    def extract_case_core(num_proc):
        # Try to extract a numeric core from the process number
        # This is a simplified approach - might need refinement
        digits = re.sub(r'\D', '', num_proc)
        if len(digits) >= 14:  # CNJ standard has 14+ digits
            return digits[:14]
        return None
    
    first_cores = [extract_case_core(num) for num in first_instance_patterns]
    first_cores = [c for c in first_cores if c]
    
    second_cores = [extract_case_core(num) for num in second_instance_patterns]
    second_cores = [c for c in second_cores if c]
    
    tst_cores = [extract_case_core(num) for num in tst_patterns]
    tst_cores = [c for c in tst_cores if c]
    
    # Check for core matches
    first_cores_set = set(first_cores)
    second_cores_set = set(second_cores)
    tst_cores_set = set(tst_cores)
    
    first_second_core_matches = first_cores_set.intersection(second_cores_set)
    second_tst_core_matches = second_cores_set.intersection(tst_cores_set)
    first_tst_core_matches = first_cores_set.intersection(tst_cores_set)
    
    print(f"Core matches between first and second instances: {len(first_second_core_matches)}")
    print(f"Core matches between second instance and TST: {len(second_tst_core_matches)}")
    print(f"Core matches between first instance and TST: {len(first_tst_core_matches)}")
    
    # Print sample of matching case cores
    if first_second_core_matches:
        print("\nSample matched case cores between first and second instances:")
        for core in list(first_second_core_matches)[:5]:
            first_matches = [num for num in first_instance_patterns if core in re.sub(r'\D', '', num)]
            second_matches = [num for num in second_instance_patterns if core in re.sub(r'\D', '', num)]
            print(f"Core: {core}")
            print(f"  First: {first_matches[:2]}")
            print(f"  Second: {second_matches[:2]}")

if __name__ == '__main__':
    main()