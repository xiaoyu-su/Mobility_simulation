"""Deterministic spatial imputation from mapped road nodes, never claimed GPS."""
import hashlib
import json
import numpy as np
from shapely.geometry import Point,shape
from shapely.ops import transform
from pyproj import CRS,Transformer


def node_pools(mapping,nodes,polygon_file=None,polygon_crs=None,network_crs=None):
    polygons=None
    if polygon_file is not None:
        data=json.loads(polygon_file.read_text())
        polygons={int(f['properties'].get('taxi_zone',f['properties'].get('zone_id'))):shape(f['geometry']) for f in data['features']}
        declared=polygon_crs or data.get('crs',{}).get('properties',{}).get('name','EPSG:4326')
        if CRS(declared)!=CRS(network_crs):
            project=Transformer.from_crs(declared,network_crs,always_xy=True).transform
            polygons={z:transform(project,g) for z,g in polygons.items()}
    positions=nodes.set_index('node_index')
    pools={}
    for zone,group in mapping.groupby('zone_id',sort=True):
        pool=sorted(int(n) for n in group.node_index)
        if polygons is not None:
            if zone not in polygons:raise ValueError(f'Missing zone polygon: {zone}')
            pool=[n for n in pool if polygons[zone].covers(Point(positions.loc[n,'pos_x'],positions.loc[n,'pos_y']))]
        if not pool:raise ValueError(f'No mapped road nodes within zone {zone}; verify polygon CRS')
        pools[int(zone)]=pool
    return pools


def mapped_nodes(rows,pools,seed,mode,centroids):
    rows=rows.copy()
    def choose(identity,role,zone,exclude=None):
        pool=pools[int(zone)]
        if exclude is not None:pool=[n for n in pool if n!=exclude]
        if not pool:raise ValueError(f'Intrazonal road imputation requires two eligible nodes in zone {zone}')
        digest=hashlib.sha256(f'market-road-v1/{seed}/{identity}/{role}'.encode()).digest()
        return pool[int.from_bytes(digest[:8],'big')%len(pool)]
    if mode=='centroid':
        rows['start']=rows.PULocationID.map(centroids);rows['end']=rows.DOLocationID.map(centroids)
    else:
        rows['start']=[choose(i,'origin',z) for i,z in zip(rows.trip_id,rows.PULocationID)]
        rows['end']=[choose(i,'destination',z,a if int(u)==int(z) else None)
                     for i,u,z,a in zip(rows.trip_id,rows.PULocationID,rows.DOLocationID,rows.start)]
    return rows


def causal_requests(observed,dt,patience):
    requests=observed[['request_id','start','end']].copy()
    requests['rq_time']=(np.ceil(observed.request_s/dt)*dt).astype(int)
    requests['latest_start_time']=observed.request_s+np.asarray(patience)
    if (requests.latest_start_time<requests.rq_time).any():
        raise ValueError('Patience deadline precedes causal grid admission; use a finer grid or sufficient patience')
    return requests
