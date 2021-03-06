#!/bin/bash
# Copyright: Christoph Dittmann <github@christoph-d.de>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
# Creates vocabulary lists suitable for the quiz script.

JA="$(dirname "$0")"/lookup_one_line.sh

INPUT="$1"

if [[ ! $INPUT ]]; then
    echo 'Usage: create_vocab_list.sh word_list.txt > vocabulary/list.txt'
    echo 'word_list.txt should contain one word per line, in kanji.'
    exit 0
fi

TOTAL=$(wc -l "$INPUT")

C=0
SKIPPED=0
while read I; do
    FULL_LINE="$("$JA" "$I" | head -n 1)"
    if [[ $FULL_LINE = 'Unknown word.' ]] ||
        echo "$FULL_LINE" | grep -q '^\([^|]*\)|\1'; then
        let SKIPPED=$SKIPPED+1
    else
        echo "$FULL_LINE"
    fi
    let C=$C+1
    echo -ne "$C/$TOTAL\r" >&2
done < "$INPUT"

echo >&2
echo "Skipped $SKIPPED lines." >&2
