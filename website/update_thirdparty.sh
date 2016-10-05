#!/bin/bash

set -e
set -x

DATATABLES='1.10.12'


wget https://cdn.datatables.net/${DATATABLES}/js/jquery.dataTables.min.js -O static/jquery.dataTables.min.js
wget https://cdn.datatables.net/${DATATABLES}/js/dataTables.bootstrap.min.js -O static/dataTables.bootstrap.min.js
wget https://cdn.datatables.net/${DATATABLES}/css/dataTables.bootstrap.min.css -O static/dataTables.bootstrap.min.css
