"""Full-file protocol/time audit; observations do not establish causal explanations."""
import hashlib,json,math
from pathlib import Path
from collections import Counter
import pyarrow.parquet as pq


def audit(path):
    parquet=pq.ParquetFile(path);by_step={};files={};concentrations=set()
    columns=['file_id','step_type','step_index','polymer_name','electrode_name','mix_id','Ca_M','Cb_M','Cg_M','time_s','potential_V','I_mA','nominal_current_uA']
    for batch in parquet.iter_batches(batch_size=65536,columns=columns):
        data=batch.to_pydict()
        for i in range(batch.num_rows):
            step=data['step_type'][i]
            stats=by_step.setdefault(step,{'rows':0,'null_current':0,'null_nominal_current':0,'nonfinite_time':0,'nonfinite_potential':0})
            stats['rows']+=1;stats['null_current']+=data['I_mA'][i] is None;stats['null_nominal_current']+=data['nominal_current_uA'][i] is None
            t=data['time_s'][i];v=data['potential_V'][i]
            stats['nonfinite_time']+=t is None or not math.isfinite(t)
            stats['nonfinite_potential']+=v is None or not math.isfinite(v)
            fid=data['file_id'][i]
            identity=tuple(data[k][i] for k in ('polymer_name','electrode_name','mix_id','step_index','step_type'))
            f=files.setdefault(fid,{'identity':identity,'rows':0,'last_time':None,'time_decreases':0,'time_duplicates':0,'identity_changes':0,'hash':hashlib.sha256()})
            f['identity_changes']+=identity!=f['identity'];f['rows']+=1
            if t is not None and math.isfinite(t):
                if f['last_time'] is not None:f['time_decreases']+=t<f['last_time'];f['time_duplicates']+=t==f['last_time']
                f['last_time']=t
            f['hash'].update(json.dumps([t,v,data['I_mA'][i]],separators=(',',':')).encode()+b'\n')
            concentrations.add(tuple(data[k][i] for k in ('mix_id','Ca_M','Cb_M','Cg_M')))
    hashes=Counter(f['hash'].hexdigest() for f in files.values())
    return {'rows_by_step':by_step,'files':len(files),'files_with_identity_changes':sum(f['identity_changes']>0 for f in files.values()),'files_with_time_decreases':sum(f['time_decreases']>0 for f in files.values()),'files_with_duplicate_adjacent_times':sum(f['time_duplicates']>0 for f in files.values()),'duplicate_time_potential_current_payload_groups':sum(n>1 for n in hashes.values()),'duplicate_selected_payloads':[[{'file_id':fid,'identity':list(f['identity']),'rows':f['rows']} for fid,f in files.items() if f['hash'].hexdigest()==sha] for sha,n in hashes.items() if n>1],'distinct_mix_concentration_combinations':len(concentrations),'concentration_combinations':[list(c) for c in sorted(concentrations,key=str)],'scope':'Stored row order per file; identical selected signal payloads only. No claim of acquisition chronology, independent experiments, calibration validity or absence of near duplicates.','model_calls':0,'scientific_acceptance':False}


if __name__=='__main__':
    w=Path('/mnt/data/zhanglinfeng/workspace');p=w/'.state/science-proposals/pulsed-sensor-v1'
    result=audit(p/'mixed_ion_raw_public.parquet');out=p/'protocol-audit-v2.json'
    if out.exists():raise ValueError('fresh output required')
    out.write_text(json.dumps(result,indent=2)+'\n');out.chmod(0o600);print(json.dumps(result))
