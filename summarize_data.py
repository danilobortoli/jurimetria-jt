#!/usr/bin/env python3

import json
import os

def main():
    # Load the consolidated data
    data_path = os.path.join('data', 'consolidated', 'all_decisions.json')
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Count decisions by tribunal
    tribunals = {}
    for d in data:
        if 'tribunal' in d:
            tribunals[d['tribunal']] = tribunals.get(d['tribunal'], 0) + 1
    
    # Print summary
    print('Total decisions:', len(data))
    print('By tribunal:')
    for t in sorted(tribunals.keys()):
        print(f'  {t}: {tribunals[t]} decisions')

if __name__ == '__main__':
    main()