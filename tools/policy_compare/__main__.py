"""Run matched policies or compare sealed matching/city AV experiments."""
import argparse
from pathlib import Path
from tools.policy_compare.metrics import catalog
from tools.synthetic_market.build import json_write


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='action',required=True)
    run=commands.add_parser('run',help='Run a multi-policy matching specification and generate its KPI report')
    run.add_argument('--spec',type=Path,required=True);run.add_argument('--output',type=Path,required=True)
    analyze=commands.add_parser('report',help='Read-only analysis of sealed matching or city_av run manifests')
    analyze.add_argument('--experiments',type=Path,nargs='+',required=True);analyze.add_argument('--reference');analyze.add_argument('--output',type=Path,required=True)
    describe=commands.add_parser('catalog',help='Export all KPI units, preference directions, populations and clocks')
    describe.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.action=='run':
        from tools.policy_compare.run import run
        run(args.spec,args.output)
    elif args.action=='report':
        from tools.policy_compare.report import report
        report(args.experiments,args.output,args.reference)
    else:
        if args.output.exists():raise ValueError('Refusing to overwrite KPI catalog')
        json_write(args.output,catalog())


if __name__=='__main__':main()
