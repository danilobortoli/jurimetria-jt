#!/usr/bin/env python3

import json
import os
from collections import Counter, defaultdict

def main():
    # Load the consolidated data
    data_path = os.path.join('data', 'consolidated', 'all_decisions.json')
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Initialize counters for each instance
    instance_results = defaultdict(Counter)
    instance_counts = Counter()
    
    # Group results by instance and tribunal
    tribunal_instance_results = defaultdict(lambda: defaultdict(Counter))
    
    # Analyze data
    for decision in data:
        instance = decision.get('instancia', 'N/A')
        tribunal = decision.get('tribunal', 'N/A')
        result = decision.get('resultado', 'N/A')
        
        instance_results[instance][result] += 1
        instance_counts[instance] += 1
        
        tribunal_instance_results[tribunal][instance][result] += 1
    
    # Print summary by instance
    print("=== Results by Instance ===")
    for instance, results in instance_results.items():
        print(f"\n{instance} ({instance_counts[instance]} decisions):")
        total = sum(results.values())
        for result, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100 if total > 0 else 0
            print(f"  - {result}: {count} ({percentage:.1f}%)")
    
    # Print detailed results by tribunal and instance
    print("\n\n=== Results by Tribunal and Instance ===")
    for tribunal in sorted(tribunal_instance_results.keys()):
        print(f"\n{tribunal}:")
        for instance, results in tribunal_instance_results[tribunal].items():
            print(f"  {instance} ({sum(results.values())} decisions):")
            total = sum(results.values())
            for result, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total) * 100 if total > 0 else 0
                print(f"    - {result}: {count} ({percentage:.1f}%)")

if __name__ == '__main__':
    main()