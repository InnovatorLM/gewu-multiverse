"""Second-method direct equality check, independent of signal-hash matching."""
import json
from pathlib import Path
import pyarrow.compute as pc
import pyarrow.parquet as pq


def confirm(parquet_path, groups):
    ids=[f['file_id'] for group in groups for f in group]
    columns=['file_id','time_s','potential_V','I_mA','control_mA','analog_in1_V','nominal_current_uA','step_index']
    table=pq.read_table(parquet_path,columns=columns,filters=[('file_id','in',ids)])
    results=[]
    for group in groups:
        frames=[table.filter(pc.equal(table['file_id'],f['file_id'])).drop(['file_id']).combine_chunks() for f in group]
        checked={name:all(frames[0][name].equals(frame[name]) for frame in frames[1:]) for name in frames[0].column_names}
        results.append({'conditions':[f['identity'] for f in group],'rows_per_file':[t.num_rows for t in frames],'exact_arrow_column_equality':checked})
    return results


if __name__=='__main__':
    w=Path('/mnt/data/zhanglinfeng/workspace');p=w/'.state/science-proposals/pulsed-sensor-v1'
    groups=json.loads((p/'protocol-audit-v2.json').read_text())['duplicate_selected_payloads']
    print(json.dumps(confirm(p/'mixed_ion_raw_public.parquet',groups),indent=2))
