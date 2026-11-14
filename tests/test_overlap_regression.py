"""Regression for cross-partition geographic/temporal leakage detection."""
import contextlib,csv,io,json,tempfile,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_provenance import audit

def test_cross_split_geotemporal_overlap_yields_error_without_crash():
    with tempfile.TemporaryDirectory() as td:
        base=pathlib.Path(td)/'inputs';base.mkdir()
        for template in ('reporting_units.csv','parent_events.csv','original_and_repaired_pairs.csv','benchmark_label_audit.csv'):
            with (ROOT/'templates'/template).open(newline='') as f:header=next(csv.reader(f))
            with (base/template).open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=header);writer.writeheader()
                if template=='reporting_units.csv':
                    for idx,split in enumerate(('train','test')):
                        writer.writerow({'reporting_unit_id':f'u{idx}','parent_event_uid':f'p{idx}',
                        'dataset':'CAU-Flood','split':split,'sar_acquired_utc':'2024-06-20T00:00:00Z',
                        'optical_original_acquired_utc':'2024-05-20T00:00:00Z',
                        'optical_used_acquired_utc':'2024-05-20T00:00:00Z',
                        'bbox_crs':'EPSG:4326','bbox_min_x':'110','bbox_min_y':'25',
                        'bbox_max_x':'110.1','bbox_max_y':'25.1',
                        'optical_replaced':'false','eligible_optical':'false','eligible_sar':'false'})
                elif template=='parent_events.csv':
                    for i,split in enumerate(('train','test')): writer.writerow({'parent_event_uid':f'p{i}','split':split,'reporting_unit_ids':f'u{i}','datasets_in_group':'CAU-Flood'})
                elif template=='original_and_repaired_pairs.csv':
                    for i,split in enumerate(('train','test')):writer.writerow({'reporting_unit_id':f'u{i}','parent_event_uid':f'p{i}','split':split,'dataset':'CAU-Flood'})
                else:writer.writerow({'label_audit_id':'audit','reporting_unit_id':'u0'})
        out=pathlib.Path(td)/'report'
        with contextlib.redirect_stdout(io.StringIO()):
            passed=audit(base,'submission',out,{'spatial_buffer_m':500,'temporal_window_days':14})
        assert not passed
        result=json.loads((out/'audit_report.json').read_text())
        assert any(e['code']=='UNRESOLVED_GEO_TIME_OVERLAP' for e in result['errors'])
