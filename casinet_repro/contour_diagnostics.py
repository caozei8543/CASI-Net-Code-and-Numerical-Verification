"""Descriptive contour-test coverage/FRR/FCRR by terrain group.

Groupwise empirical rates are NOT group-conditional conformal guarantees.
Untested false candidates must count as not rejected in FCRR.
"""
from collections import defaultdict

def diagnostics(rows, group_key='terrain_group'):
    groups=defaultdict(list)
    for r in rows:groups[(r['state'],r.get(group_key,'all'))].append(r)
    out={}
    for group,rs in groups.items():
        genuine=[r for r in rs if r['is_genuine']]
        false=[r for r in rs if r['is_false']]
        eligible=[r for r in genuine if r['is_test_eligible']]
        testable=[r for r in rs if r['is_test_eligible']]
        events=defaultdict(list)
        for r in eligible: events[r['parent_event_uid']].append(r['rejected'])
        event_mean_frr=(sum(sum(e)/len(e) for e in events.values())/len(events)) if events else None
        out['/'.join(group)]={
            'n_all':len(rs),'n_genuine':len(genuine),'n_false':len(false),
            'n_testable':len(testable),'n_eligible_genuine':len(eligible),
            'frr_event_mean':event_mean_frr,
            'fcrr':sum(r['rejected'] for r in false)/len(false) if false else None,
            'coverage':len(testable)/len(rs) if rs else None,
        }
    return out
