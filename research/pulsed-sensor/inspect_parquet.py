"""Low-memory raw-data schema/coverage inventory; no scientific grading or fitting."""
import argparse
import hashlib
import json
from pathlib import Path
import pyarrow
import pyarrow.parquet as pq


def inspect(path):
    digest=hashlib.sha256();md5=hashlib.md5()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block);md5.update(block)
    if md5.hexdigest()!='7498e959c450654adc0ef5fb4a5fc3b5':raise ValueError('not the pinned repository file')
    parquet=pq.ParquetFile(path)
    names=parquet.schema_arrow.names
    grouping=['polymer_name','electrode_name','mix_id','step_index','step_type','nominal_current_uA']
    if not set(grouping+['time_s','potential_V','I_mA','file_id'])<=set(names):raise ValueError('expected schema columns missing')
    groups={};file_ids=set();missing={name:0 for name in names};rows=0
    for batch in parquet.iter_batches(batch_size=65536):
        rows+=batch.num_rows
        for name,column in zip(batch.schema.names,batch.columns):missing[name]+=column.null_count
        selected=batch.select(grouping+['file_id']).to_pydict()
        for i in range(batch.num_rows):
            key=tuple(selected[name][i] for name in grouping)
            groups[key]=groups.get(key,0)+1;file_ids.add(selected['file_id'][i])
    return {'source_doi':'10.5281/zenodo.20058832','file_bytes':path.stat().st_size,'sha256':digest.hexdigest(),'repository_md5_verified':True,
       'pyarrow_version':pyarrow.__version__,'rows':rows,'metadata_rows':parquet.metadata.num_rows,'row_groups':parquet.num_row_groups,
       'schema':str(parquet.schema_arrow.remove_metadata()),'columns':names,'null_counts':missing,'distinct_file_ids':len(file_ids),
       'protocol_coverage':[dict(zip(grouping,key),rows=count) for key,count in sorted(groups.items(),key=lambda pair:str(pair[0]))],
       'scope':'Full-file structural/coverage/null inventory only; finite values, timing, grouping leakage, physical assumptions and scientific task value not yet verified.',
       'model_calls':0,'scientific_acceptance':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('input',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    workspace=Path('/mnt/data/zhanglinfeng/workspace')
    if args.output.exists() or not args.output.resolve().is_relative_to(workspace) or not args.input.resolve().is_relative_to(workspace):raise ValueError('workspace input and fresh output required')
    result=inspect(args.input);args.output.write_text(json.dumps(result,indent=2)+'\n');args.output.chmod(0o600)
    print(json.dumps({key:result[key] for key in ('rows','metadata_rows','row_groups','distinct_file_ids','repository_md5_verified')}))
