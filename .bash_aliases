HVDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
alias hv-client='$HVDIR/hv_client.py '
alias hv-display='$HVDIR/hv_display.py '
alias hv-cli='ipython -i $HVDIR/cli.py -- $@'
# setup PYTHONPATH to a directory above HVDIR so the import work correctly
cd $HVDIR/..
export PYTHONPATH=`pwd`
source $HVDIR/venv/bin/activate
