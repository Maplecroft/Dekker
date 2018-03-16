#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH=/home/jpeel/projects/maplecroft/versions/current/:$DIR/../app
python $DIR/test.py
