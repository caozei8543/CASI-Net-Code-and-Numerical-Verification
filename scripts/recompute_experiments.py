#!/usr/bin/env python3
"""Compute event-metrics, bootstrap differences, ablation interactions and HEC-RAS table.

Reads submitted observation-level CSVs. No manuscript score is generated from thin air.
Use --strict to require all experiment CSVs; otherwise records NOT_VERIFIED status.
"""
import argparse,csv,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from casinet_repro.evaluate import per_event_metrics
from casinet_repro.bootstrap import paired_event_differences,bootstrap
from casinet_repro.ablation import summary_by_dataset
from casinet_repro.hydraulic_validation import evaluate_hydraulic

def read(name,folder):
    p=folder/name
    if not p.exists():return []
    with p.open(encoding='utf8',newline='') as f:return list(csv.DictReader(f))

def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs',default='data/measurements');p.add_argument('--output',default='outputs/recomputed.json');p.add_argument('--strict',action='store_true')
    a=p.parse_args();inp=pathlib.Path(a.inputs);out=ROOT/a.output if not pathlib.Path(a.output).is_absolute() else pathlib.Path(a.output)
    res={'status':'INCOMPLETE_UNLESS_ALL_INPUTS_PRESENT','analyses':{}}
    work={'event_confusions.csv':read('event_confusions.csv',inp),'ablation_per_event.csv':read('ablation_per_event.csv',inp),'hecras_reference_sites.csv':read('hecras_reference_sites.csv',inp)}
    for name,rs in work.items():
        if not rs:
            res['analyses'][name]={'status':'NOT_VERIFIED','reason':'No source measurement records supplied'}
            continue
        if name=='event_confusions.csv':
            mets=per_event_metrics([r for r in rs if r['split']=='test'])
            if not mets: raise ValueError('No test-partition confusion counts')
            byds={}
            for ds in sorted({r['dataset'] for r in mets}):
                subset=[r for r in mets if r['dataset']==ds]
                paired=paired_event_differences(subset)
                byds[ds]=bootstrap(paired) if len(paired)>1 else {'status':'INSUFFICIENT_EVENTS'}
            res['analyses'][name]={'status':'RECOMPUTED_FROM_INPUTS','paired_F1':byds,'n_records':len(rs)}
        elif name=='ablation_per_event.csv':
            res['analyses'][name]={'status':'RECOMPUTED_FROM_INPUTS','interaction':summary_by_dataset([r for r in rs if r['split']=='test']),'n_records':len(rs)}
        else:
            for r in rs:r['valid']=str(r['valid']).lower() in ('1','true','yes')
            res['analyses'][name]={'status':'RECOMPUTED_FROM_INPUTS','physical':evaluate_hydraulic(rs),'n_records':len(rs)}
    missing=[x for x,v in res['analyses'].items() if v['status']=='NOT_VERIFIED']
    res['status']='RECOMPUTED_NOT_EXTERNALLY_AUTHENTICATED' if not missing else 'INCOMPLETE'
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(res,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    print(json.dumps({'status':res['status'],'missing_inputs':missing,'output':str(out)},indent=2))
    if a.strict and missing:sys.exit(2)

if __name__=='__main__':main()
