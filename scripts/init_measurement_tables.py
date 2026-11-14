#!/usr/bin/env python3
"""Copy empty, documented schemas to local input directory without inventing records."""
import argparse,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--dest',default='data/measurements');a=p.parse_args()
    dest=ROOT/a.dest;dest.mkdir(parents=True,exist_ok=True)
    for src in (ROOT/'templates').glob('*.csv'):
        if src.name in ('reporting_units.csv','parent_events.csv','original_and_repaired_pairs.csv','benchmark_label_audit.csv','reviewed_overlap_exceptions.csv'): continue
        target=dest/src.name
        if not target.exists():shutil.copyfile(src,target);print(f'CREATED {target.relative_to(ROOT)}')
        else:print(f'EXISTS {target.relative_to(ROOT)} (not overwritten)')
if __name__=='__main__':main()
