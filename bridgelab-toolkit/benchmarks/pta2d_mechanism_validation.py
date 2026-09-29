"""PT-A2D bounded same-deal mechanism pilot. No auction-time expectation."""
from __future__ import annotations
import gzip,json
from pathlib import Path
from time import perf_counter
from statistics import mean,median
from bridge.models import Card,Seat,Suit,Hand
from bridge.deals import Deal,full_deck
from bridge.shortness_mechanism import (PlayPosition,MechanismOracle,DDSOptimalMoves,
    Restriction,Status,bounded_studied_paths)
from bridge.expected_ruffing_research import jsonable
from benchmarks.pta2c_target_validation import paired_metrics

FIXTURES={
 'two_ruff_capacity':(('2D 3D AC KC QC','AD KD AS KS 4C','2S 3S 2C 3C 8C','QD JD 5C 6C 9C'),'N'),
 'one_ruff':(('QC 9D 8S','2D 3D QS','TC 3S 7S','2C QD AD'),'W'),
 'zero_singleton':(('4C 5S AS','5C 6C QS','8C 3D 8S','4D TD JD'),'E'),
 'ambiguous_singleton':(('6C 9D KD','5C 4D 5D','JD 3S JS','3C 4C TD'),'S'),
 'crossruff_void':(('3D 3S TS','7C AC KD','4C JC 7S','5C 9C 6D'),'N'),
 'ruff_option_threat':(('QC 9D 8S JD','2D 3D QS KS','TC 3S 7S 4C','2C QD AD KD'),'W'),
}


def fixture(name):
    hands,leader=FIXTURES[name]
    return PlayPosition(tuple(frozenset(Card.parse(c) for c in h.split()) for h in hands),Seat(leader),Suit.SPADES)


def synthetic(names=None):
    rows=[]
    for name in (FIXTURES if names is None else names):
        p=fixture(name);start=perf_counter()
        o=MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,max_nodes=500000)
        a=o.analyze(p)
        assert a.status==Status.EXACT
        adapter=DDSOptimalMoves(10000)
        d=MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,dds=adapter,max_nodes=500000)
        if p.remaining_tricks<=4:
            b=d.analyze(p);assert a==b,(name,a,b)
        else:
            value,cards=adapter.optimal(p,Seat.SOUTH)
            assert a.optimum==value
            expected=o._optimal(p)[1]
            assert cards==expected
        restrictions=[]
        for policy in Restriction:
            r=MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,max_nodes=500000)
            result=r.restricted(p,policy,unrestricted=a.optimum)
            restrictions.append({'result':jsonable(result),'cost':r.statistics()})
        rows.append({'name':name,'cards':FIXTURES[name],'exact':jsonable(a),'cost':o.statistics(),
            'dds_crosscheck':'all optimal paths' if p.remaining_tricks<=4 else 'root value and every optimal first action',
            'dds_cost':{'calls':adapter.calls,'cache_hits':adapter.cache_hits,'seconds':adapter.seconds},
            'restricted':restrictions,'seconds':perf_counter()-start})
    return rows


def interval_comparison(rows,key):
    """Identified envelopes, not midpoint estimates or attained path extrema."""
    pairs=[(r['bounds']['minimum_lower_bound'],r['bounds']['maximum_upper_bound'],r['prior'][key],r['source'])
           for r in rows if r['prior'].get(key) is not None]
    if not pairs: return {'n':0}
    sign=lambda x:(x>0)-(x<0)
    lower=[lo-v for lo,hi,v,_ in pairs];upper=[hi-v for lo,hi,v,_ in pairs]
    signs=[({sign(x) for x in range(lo,hi+1)},sign(v)) for lo,hi,v,_ in pairs]
    return {'n':len(pairs),'mean_difference_envelope':[mean(lower),mean(upper)],
        'median_difference_envelope':[median(lower),median(upper)],'pearson':None,'spearman':None,
        'sign_disagreement_count_bounds':[sum(v not in opts for opts,v in signs),sum(any(x!=v for x in opts) for opts,v in signs)],
        'certain_large_disagreements':[source for lo,hi,v,source in pairs if max(lo-v,v-hi,0)>=1.5],
        'possible_large_disagreements':[source for lo,hi,v,source in pairs if max(abs(lo-v),abs(hi-v))>=1.5],
        'interpretation':'Unresolved envelopes; no midpoint, target point estimate, rank or correlation is inferred.'}


def run(output=Path('output/pta2d_mechanism')):
    if (output/'pilot.json').exists(): raise ValueError('completed pilot exists')
    output.mkdir(exist_ok=True,parents=True)
    started=perf_counter()
    small=synthetic(); print('synthetic complete',flush=True)
    old=json.loads(Path('output/pta2c_targets/pilot/summary.json').read_text(encoding='utf-8'))
    selected=[]
    for available in (True,False):
        selected.extend([r for r in old['rows'] if r['cohort']=='PTA2B_conditional' and
                         (r['exchange']['first_valid_delta'] is not None)==available][:3])
    stress=json.loads(Path('output/pta2c_targets/impossible_reference_census.json').read_text(encoding='utf-8'))
    for r in stress['cases']:
        selected.append({'source_deal_id':r['source'],'perspective':'S','studied_suit':1,'trump':3,
            'declarer':'N','label':r['hand'],'cohort':'extreme','exchange':{'first_valid_delta':None,'distribution':{'mean':None}},'candidates':[]})
    # Exact zero physical-ruff case, complete physical deal, no own trump.
    own=Hand.parse('-.AKQJT9876543.2.-');free=[c for c in full_deck() if c not in own.cards]
    deal=Deal(0,((Seat.SOUTH,own),(Seat.NORTH,Hand.from_cards(free[:13])),
        (Seat.EAST,Hand.from_cards(free[13:26])),(Seat.WEST,Hand.from_cards(free[26:]))))
    selected.append({'source_deal_id':deal.serialize(),'perspective':'S','studied_suit':1,'trump':3,
        'declarer':'N','label':'no_own_trump','cohort':'extreme','exchange':{'first_valid_delta':None,'distribution':{'mean':None}},'candidates':[]})
    rows=[]
    for row in selected:
        source=Deal.parse(row['source_deal_id']);p=Seat(row['perspective']);s=Suit(row['studied_suit']);t=Suit(row['trump'])
        position=PlayPosition.from_deal(source,Seat(row['declarer']),t)
        adapter=DDSOptimalMoves(128); start=perf_counter()
        bounds,cost=bounded_studied_paths(position,p,s,adapter,max_nodes=2500)
        if row.get('source_solver'): assert bounds.optimum==row['source_solver']['maximum_declarer_tricks']
        restrictions=[]
        # Restricted search feasibility pilot: fixed low budget, no DDS shortcut.
        for policy in Restriction:
            o=MechanismOracle(p,s,t,max_nodes=1500)
            result=o.restricted(position,policy,unrestricted=bounds.optimum)
            restrictions.append({'result':jsonable(result),'cost':o.statistics()})
        prior={'exchange_first':row['exchange']['first_valid_delta'],'exchange_mean':row['exchange']['distribution']['mean']}
        prior.update({r['target']:r['delta'] for r in row['candidates']})
        rows.append({'source':source.serialize(),'label':row['label'],'cohort':row['cohort'],
            'physical_features':{'own_trumps':source.hand(p).length(t),'partner_trumps':source.hand(p.partner()).length(t),
                'trump_length_role':'shorter' if source.hand(p).length(t)<source.hand(p.partner()).length(t) else 'longer' if source.hand(p).length(t)>source.hand(p.partner()).length(t) else 'equal',
                'own_studied_length':source.hand(p).length(s)},
            'prior':prior,'bounds':jsonable(bounds),'restricted':restrictions,
            'comparison_difference_envelopes':{k:None if v is None else [bounds.minimum_lower_bound-v,bounds.maximum_upper_bound-v] for k,v in prior.items()},
            'cost':{**cost,'dds_calls':adapter.calls,'dds_cache_hits':adapter.cache_hits,'dds_seconds':adapter.seconds,'seconds':perf_counter()-start}})
        print('source',row['label'],bounds.status.value,adapter.calls,flush=True)
    comparisons={}
    for key in sorted({k for r in rows for k in r['prior']}):
        # An ambiguous exact range is not replaced by its midpoint.
        values=[r['bounds']['minimum_lower_bound'] if r['bounds']['extrema_exact'] and
                r['bounds']['minimum_lower_bound']==r['bounds']['maximum_upper_bound'] else None for r in rows]
        comparisons[key]=paired_metrics(values,[r['prior'].get(key) for r in rows])
        comparisons[key]['reason_if_no_overlap']='No jointly exact scalar mechanism/prior values; interval envelopes retained, correlations not invented.'
    census={'total':0,'exchange_available':0,'exchange_unavailable':0,'physical_positions_valid':0}
    with gzip.open('output/pta2_erv/main/hypotheses.jsonl.gz','rt',encoding='utf-8') as stream:
        for i,line in enumerate(stream):
            if i>=10: break
            for effect in json.loads(line)['effects']:
                position=PlayPosition.from_deal(Deal.parse(effect['source_deal_id']),Seat.NORTH,Suit.SPADES)
                MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)._validate(position)
                census['total']+=1;census['physical_positions_valid']+=1
                census['exchange_available' if effect['status']=='evaluable' else 'exchange_unavailable']+=1
    result={'synthetic':small,'full_deals':rows,'comparisons':comparisons,'zero_dds_census':census,
        'interval_comparisons':{k:interval_comparison(rows,k) for k in comparisons},
        'adopted_target':None,'expectation_pilot':'not run: full-information target not adopted',
        'recommendation':'PT-A2E mechanism methodology required','wall_seconds':perf_counter()-started,
        'warning':'Ruff event counts, action restrictions and modified reward games are different estimands. Budget envelopes are not attained optimal-line extrema. No control deal is transformed.'}
    (output/'pilot.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':run()