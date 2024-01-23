#!/usr/bin/env bash
for filename in ./tests/*.HC; do
    python3 ./DolDoc/DolDoc.py l ${filename}
done
