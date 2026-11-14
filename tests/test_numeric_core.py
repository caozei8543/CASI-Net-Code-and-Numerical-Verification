import math
import numpy as np
import pytest
from scipy import sparse
from casinet_repro.contour_calibration import calibrate,mc_pvalue,is_rejected
from casinet_repro.evaluate import confusion,metrics_from_counts
from casinet_repro.bootstrap import paired_event_differences,bootstrap
from casinet_repro.priority_flood import minimax_deficit,paired_change_frequency
from casinet_repro.pair_sampling import spatial_dem_errors,paired_terrain_and_anchors
from casinet_repro.surface_solver import grid_edges,solve_surface
from casinet_repro.fusion import fuse,override_margin
from casinet_repro.make_candidates import candidates,anchors,source_core
from casinet_repro.contour_crossfit import crossfit_statistic
from casinet_repro.hydraulic_validation import evaluate_hydraulic,CONFIGS
from casinet_repro.ablation import interaction_by_event

# Deterministic mathematical unit-test fixtures; no empirical observation records.
def test_confusion_miou():
    counts=confusion(np.array([[1,1],[0,0]]),np.array([[1,0],[1,0]]))
    assert counts==dict(tp=1,fp=1,tn=1,fn=1)
    m=metrics_from_counts(**counts)
    assert m['f1']==.5 and m['miou']==1/3 and m['oa']==.5

def test_conformal_order_statistic_and_strict_threshold():
    ps=[0.005*i for i in range(1,33)]
    chosen=[{'parent_event_uid':f'e{i}','p_value':p} for i,p in enumerate(ps)]
    result=calibrate(chosen,.1)
    assert (result['n'],result['k'])==(32,30)
    # k-th ascending of -log(p) corresponds to third-smallest p.
    assert math.isclose(result['reject_if_p_lt'],0.015,abs_tol=1e-12)
    assert not is_rejected(.015,result)
    assert is_rejected(.01,result)
    assert math.isclose(mc_pvalue([0.5,1.0],.6),2/3)

def test_paired_bootstrap_seed_repeatability():
    rows=[]
    for i in range(5):
        for seed in (2026,2027):
            for name,f1 in (('CASI-Net',.91+.01*i),('CISRMamba',.90+.01*i)):
                rows.append(dict(dataset='A',parent_event_uid=str(i),seed=seed,method=name,f1=f1))
    dif=paired_event_differences(rows)
    b1=bootstrap(dif,repeats=100,seed=2026);b2=bootstrap(dif,repeats=100,seed=2026)
    assert b1==b2 and b1['events_won']==5

def test_priority_flood_eight_connected_and_nested():
    source=np.zeros((3,3),bool);source[0,0]=True
    dem=np.array([[0,2,2],[2,0,2],[2,2,0]],float)
    d=minimax_deficit(source,dem)
    assert d[2,2]==0  # diagonal 8-connected traversal allowed
    z=np.repeat(dem[None,:,:],3,axis=0)
    w0=np.zeros_like(z);w1=np.ones_like(z)
    res=paired_change_frequency(z,w0,w1,source)
    assert np.all(res['p0_reach']<=res['p1_reach'])
    assert np.isclose(res['p_change'][2,2],0)

def test_dem_spatial_field_and_shared_anchor_component():
    sigma=np.ones((4,4))
    a=spatial_dem_errors(sigma,3,resolution_m=10,correlation_m=25,seed=4)
    b=spatial_dem_errors(sigma,3,resolution_m=10,correlation_m=25,seed=4)
    assert a.shape==(3,4,4) and np.array_equal(a,b)
    z=np.ones((4,4))*4
    dem,anchor=paired_terrain_and_anchors(z,{'optical':[4.],'sar':[4.]},
                          {'optical':[[1,1]],'sar':[[1,1]]},sigma,n=2,seed=4,
                          sigma_loc={'optical':0,'sar':0},sigma_repr={'optical':0,'sar':0},
                          resolution_m=10,correlation_m=25,nugget_m=0)
    assert np.allclose(anchor['optical'],anchor['sar'])
    assert np.allclose(anchor['optical'].ravel(),dem[:,1,1])

def test_solver_gradient_monotone_and_datum():
    B,edge=grid_edges(2,2,grid_m=90)
    A=sparse.eye(4,format='csr')
    z=np.array([1.,1.5,1.5,2.])
    kw=dict(A=A,z=z,sigma=np.ones(4),q=np.ones(4),B=B,edge_lengths=edge,
            gradient_max=.003,irls_max=25,admm_max=500,tol=3e-4)
    w,info=solve_surface(**kw,require_convergence=False)
    assert info.edge_violation_m<.002
    assert np.max(np.abs(B@w))<.272
    shifted,_=solve_surface(**{**kw,'z':z+7},require_convergence=False)
    assert np.allclose(shifted,w+7,atol=1e-8)
    flood,_=solve_surface(**{**kw,'z':z+.5},normal_lower=w,require_convergence=False)
    assert np.all(flood >= w-0.002)

def test_fusion_override_and_candidate_extraction():
    assert override_margin()>0
    a=np.array([[4.,-4.]]);b=np.array([[-4.,4.]])
    assert fuse(a,b,np.array([[1.,0.]]),np.ones((1,2),bool))[0,0]>.5
    prob=np.zeros((4,4));prob[1:3,1:3]=.9
    cand=candidates(prob,min_pixels=3)
    assert len(cand)==1
    anc=anchors(cand[0]['mask'],prob,np.ones((4,4)))
    assert anc.shape[1]==4 and np.all(anc[:,2]==1)
    assert source_core(cand[0]['mask'],prob,prob,np.ones((4,4),bool),min_size=4).sum()==4

def test_crossfit_buffer_excludes_neighbors():
    p=np.column_stack((np.arange(30)*20,np.zeros(30)))
    y=np.zeros(30);sig=np.ones(30)
    seen=[]
    def callback(train,test):
        seen.append((len(train),len(test)))
        return np.zeros(len(test))
    score=crossfit_statistic(p,y,sig,callback,n_arcs=5,exclusion_buffer_m=25,min_fit_anchors=2)
    assert score==0 and len(seen)==5

def test_hecras_metric_comparison_same_site_support():
    rows=[]
    for output in ('stage_rise','inundation_depth'):
        for cfg in CONFIGS:
            for i in range(3):
                rows.append(dict(parent_event_uid='flood',site_id=str(i),output_type=output,
                    configuration=cfg,valid=True,reference_m=float(i),pred_m=float(i)+.1,
                    lower90_m=float(i)-.2,upper90_m=float(i)+.2))
    result=evaluate_hydraulic(rows)
    assert result['stage_rise']['full_casinet']['n']==3
    assert math.isclose(result['stage_rise']['full_casinet']['picp90_percent'],100.)
    rows.pop()
    with pytest.raises(ValueError):evaluate_hydraulic(rows)

def test_two_factor_interaction():
    val={'full_casinet':94.91,'no_contour':94.57,'no_source':94.39,'no_both':94.23}
    records=[dict(dataset='CAU-Flood',parent_event_uid='ev',configuration=k,f1=v) for k,v in val.items()]
    assert np.isclose(interaction_by_event(records)[('CAU-Flood','ev')],0.18)
