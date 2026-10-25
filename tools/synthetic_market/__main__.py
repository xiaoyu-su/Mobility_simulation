"""Build a TLC-style input bundle or run audited full paired simulations."""

import argparse
from pathlib import Path

from tools.synthetic_market.build import build
from tools.synthetic_market.run import experiment


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='action',required=True)
    create=commands.add_parser('build')
    create.add_argument('--trips',type=Path,nargs='+',required=True)
    create.add_argument('--network',type=Path,required=True)
    create.add_argument('--zone-map',type=Path,required=True)
    create.add_argument('--network-type',choices=['NetworkBasic','NetworkBasicWithStore','NetworkTTMatrix'],default='NetworkBasicWithStore')
    create.add_argument('--data-kind',choices=['fixture','tlc_public'],required=True)
    create.add_argument('--target-date',default='2019-11-26')
    create.add_argument('--training-dates',nargs='+',default=['2019-11-05','2019-11-12','2019-11-19'])
    create.add_argument('--sample-fraction',type=float,default=.1)
    create.add_argument('--seed',type=int,default=0)
    create.add_argument('--request-time-proxy-seconds',type=float)
    create.add_argument('--patience-extra-seconds',type=int,default=300)
    create.add_argument('--start-seconds',type=int,default=25200)
    create.add_argument('--end-seconds',type=int,default=36000)
    create.add_argument('--resolution',type=int,default=900)
    create.add_argument('--time-step',type=int,default=60)
    create.add_argument('--chunk-size',type=int,default=100000)
    create.add_argument('--utilization',type=float,default=.58)
    create.add_argument('--fleet-size',type=int)
    create.add_argument('--full-time-share',type=float,default=.42)
    create.add_argument('--driver-model',choices=['off','classes'],default='off')
    create.add_argument('--future-value',action='store_true')
    create.add_argument('--dynamic-fleet',action='store_true')
    create.add_argument('--controller',choices=['PoolingIRSOnly','PoolingIRSAssignmentBatchOptimization','RidePoolingBatchAssignmentFleetcontrol'],default='PoolingIRSOnly')
    create.add_argument('--output',type=Path,required=True)
    run=commands.add_parser('run');run.add_argument('--bundle',type=Path,required=True)
    run.add_argument('--output',type=Path,required=True);run.add_argument('--seeds',type=int,nargs='+',required=True)
    run.add_argument('--timeout',type=int,default=300)
    args=parser.parse_args()
    if args.action=='build':build(args)
    else:experiment(args)


if __name__=='__main__':main()
