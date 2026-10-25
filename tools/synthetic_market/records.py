"""Stream source records without inventing unobserved request timestamps."""

from collections import Counter
import hashlib
from pathlib import Path

import pandas as pd

from src.misc.seeding import file_digest

REQUIRED = ['hvfhs_license_num','pickup_datetime','dropoff_datetime','PULocationID','DOLocationID']


def chunks(path,size):
    path = Path(path)
    if path.suffix == '.parquet':
        import pyarrow.parquet as pq
        source = pq.ParquetFile(path)
        names = source.schema.names
        missing = set(REQUIRED)-set(names)
        if missing:raise ValueError(f'Missing high-volume trip columns: {sorted(missing)}')
        columns = REQUIRED+(['request_datetime'] if 'request_datetime' in names else [])
        for batch in source.iter_batches(batch_size=size,columns=columns):yield batch.to_pandas()
    else:
        for batch in pd.read_csv(path,chunksize=size):
            missing = set(REQUIRED)-set(batch.columns)
            if missing:raise ValueError(f'Missing high-volume trip columns: {sorted(missing)}')
            yield batch


def stable_fraction(seed,identity):
    digest = hashlib.sha256(f'market-sample-v1/{seed}/{identity}'.encode()).digest()
    return int.from_bytes(digest[:8],'big')/2**64


def read_records(paths,dates,zones,seed,fraction,proxy_seconds=None,chunk_size=100000):
    """Retain source-row identity; identical zone/time tuples can be distinct rides."""
    if not 0 < fraction <= 1:raise ValueError('Sample fraction must lie in (0,1]')
    if proxy_seconds is not None and (not pd.notna(proxy_seconds) or not 0 <= proxy_seconds <= 86400):
        raise ValueError('Request-time proxy must be a finite duration in 0..86400 seconds')
    if chunk_size < 1:raise ValueError('Chunk size must be positive')
    output=[];counts=Counter();inputs={};seen=set()
    dates = {pd.Timestamp(d).strftime('%Y-%m-%d') for d in dates}
    for path in paths:
        path=Path(path).resolve();digest=file_digest(path)
        if digest in seen:raise ValueError('The same source bytes were supplied more than once')
        seen.add(digest);inputs[str(path)]=digest;offset=0
        for batch in chunks(path,chunk_size):
            batch=batch.copy();n=len(batch);counts['raw_rows']+=n
            batch['trip_id']=[f'{digest[:16]}:{i}' for i in range(offset,offset+n)];offset+=n
            for column in ['pickup_datetime','dropoff_datetime']:
                batch[column]=pd.to_datetime(batch[column],errors='coerce',format='mixed')
                if batch[column].dt.tz is not None:raise ValueError('TLC timestamps must be naive New York local wall times')
            observed = 'request_datetime' in batch.columns
            if not observed and proxy_seconds is None:
                raise ValueError('No request_datetime in source: explicitly supply a request-time proxy; observed waits are unavailable')
            batch['request_datetime']=(pd.to_datetime(batch.request_datetime,errors='coerce',format='mixed') if observed
                else batch.pickup_datetime-pd.to_timedelta(proxy_seconds,unit='s'))
            if batch.request_datetime.dt.tz is not None:raise ValueError('Request timestamps must be naive New York local wall times')
            batch['request_observed']=observed
            for column in ['PULocationID','DOLocationID']:
                batch[column]=pd.to_numeric(batch[column],errors='coerce')
            remaining=pd.Series(True,index=batch.index)
            conditions=[('invalid_time',batch[['request_datetime','pickup_datetime','dropoff_datetime']].notna().all(axis=1)
                         & (batch.request_datetime <= batch.pickup_datetime) & (batch.dropoff_datetime > batch.pickup_datetime)
                         & ((batch.dropoff_datetime-batch.pickup_datetime).dt.total_seconds() <= 86400)),
                        ('invalid_zone',batch.PULocationID.isin(zones)&batch.DOLocationID.isin(zones)),
                        ('intrazonal_unrepresented',batch.PULocationID.ne(batch.DOLocationID)),
                        ('invalid_license',batch.hvfhs_license_num.notna()),
                        ('other_date',batch.request_datetime.dt.strftime('%Y-%m-%d').isin(dates)),
                        ('not_sampled',batch.trip_id.map(lambda i:stable_fraction(seed,i)<fraction))]
            for reason,valid in conditions:
                counts[reason]+=int((remaining & ~valid).sum());remaining &= valid
            kept=batch.loc[remaining].copy();counts['retained']+=len(kept)
            if len(kept):
                kept['service_date']=kept.request_datetime.dt.strftime('%Y-%m-%d')
                midnight=kept.request_datetime.dt.normalize()
                for field,column in [('request_s','request_datetime'),('pickup_s','pickup_datetime'),('dropoff_s','dropoff_datetime')]:
                    kept[field]=(kept[column]-midnight).dt.total_seconds()
                kept['observed_wait_s']=(kept.pickup_s-kept.request_s).where(kept.request_observed)
                output.append(kept[['trip_id','service_date','PULocationID','DOLocationID','request_s','pickup_s','dropoff_s','request_observed','observed_wait_s']])
        if file_digest(path)!=digest:raise ValueError('Source trip input changed while it was being read')
    if not output:raise ValueError('No valid sampled trips remain for the selected dates/zones')
    result=pd.concat(output,ignore_index=True).sort_values('trip_id').reset_index(drop=True)
    if not result.trip_id.is_unique:raise ValueError('Source row identity collision')
    assert sum(v for k,v in counts.items() if k!='raw_rows')==counts['raw_rows']
    return result,dict(counts),inputs
