DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH=/home/jpeel/slots/maplecroft/versions/current:$DIR/..
python $DIR/test.py
