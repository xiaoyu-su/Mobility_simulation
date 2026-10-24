"""One restored window per fresh process, with an isolated output directory."""

import argparse
import json
from pathlib import Path

from tools.windowed_eval.runtime import run_task


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job',type=Path,required=True)
    args=parser.parse_args()
    run_task(json.loads(args.job.read_text()))


if __name__=='__main__':main()
