"""Image/hydrology logit fusion from paper Eqs (28)–(29)."""
import numpy as np
from scipy.special import expit,logit

def override_margin(max_abs_image_logit=4, gamma=.7, epsilon=.0025):
    llo=logit(expit(-max_abs_image_logit)**2)
    return float(gamma*logit(1-epsilon)-(1-gamma)*abs(llo))

def fuse(pre_logits,post_logits,p_hyd,support,gamma=.7,epsilon=.0025,max_abs_logit=4):
    a=np.asarray(pre_logits,dtype=float);b=np.asarray(post_logits,dtype=float)
    p=np.asarray(p_hyd,dtype=float);m=np.asarray(support,dtype=bool)
    if not(a.shape==b.shape==p.shape==m.shape):raise ValueError('shapes must match')
    if np.max(np.abs(a))>max_abs_logit+1e-7 or np.max(np.abs(b))>max_abs_logit+1e-7:
        raise ValueError('image logits not bounded as required')
    if (p<0).any() or (p>1).any():raise ValueError('physical change frequency must lie in [0,1]')
    if not (0<epsilon<.5) or not (0<=gamma<=1):raise ValueError('invalid fusion constants')
    img=logit(expit(b)*(1-expit(a)))
    hyd=logit(np.clip(p,epsilon,1-epsilon))
    combined=(1-gamma*m)*img+gamma*m*hyd
    return expit(combined)
