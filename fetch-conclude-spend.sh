#!/bin/bash

# Fetch
dit list \
    --all \
    --concluded \
    --where status open \
    --id-only \
    | xargs -n 1 dit fetch

# Conclude
dit list \
    --all \
    --where status closed \
    --id-only \
    | xargs -n 1 dit conclude

# Spend
previous_sunday=$(date --date 'last Sun -1 week' -Idate)

dit list \
    --all \
    --concluded \
    --from $previous_sunday \
    --id-only \
    | xargs -n 1 ./spend.py --from $previous_sunday
