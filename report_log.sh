#!/usr/bin/env bash
csv_out=$1
echo Log, Cycles, Instructions > $csv_out
for file in "${@: 2}"
do
  echo "`basename ${file}`, `tac ${file} | grep -m 1 instret | sed 's/^instret:\([[:digit:]]*\).*   \([[:digit:]]*\)$/\2, \1/g'`" >> $csv_out
done

column -s, -t < $csv_out
