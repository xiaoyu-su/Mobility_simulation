"""Build immutable city bundles and run matched full physical policy experiments."""

import argparse
from pathlib import Path

from tools.city_av.build import build
from tools.city_av.run import experiment
from tools.city_av.summary import summarize


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='action',required=True)
    create=commands.add_parser('build')
    create.add_argument('--config',type=Path,required=True);create.add_argument('--data-root',type=Path,required=True)
    create.add_argument('--output',type=Path,required=True);create.add_argument('--fleet-multiplier',type=float,default=1)
    run=commands.add_parser('run')
    run.add_argument('--bundles',type=Path,nargs='+',required=True);run.add_argument('--policies',type=Path,required=True)
    run.add_argument('--seeds',type=int,nargs='+',required=True);run.add_argument('--output',type=Path,required=True)
    run.add_argument('--workers',type=int,default=1);run.add_argument('--timeout',type=int,default=7200)
    report=commands.add_parser('report');report.add_argument('--experiments',type=Path,nargs='+',required=True)
    report.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.action=='build':build(args.config,args.data_root,args.output,args.fleet_multiplier)
    elif args.action=='run':experiment(args)
    else:summarize(args.experiments,args.output)


if __name__=='__main__':main()
