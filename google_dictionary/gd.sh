#!/bin/bash
# Copyright: Christoph Dittmann <github@christoph-d.de>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
# This script performs a Google dictionary lookup for english words.
#

URL="http://google.com/dictionary?aq=f&langpair=en%7Cen&q="

MAX_RESULT_LENGTH=300

# Accumulate all parameters
QUERY="$*"
# Restrict length
QUERY=${QUERY:0:300}

if [[ -z $QUERY ]]; then
    QUERY="empty"
fi

fix_html_entities() {
    sed "s/\&\#39;/'/g" |
    sed 's/\&lt;/</g' |
    sed 's/\&gt;/>/g' |
    sed 's/\&quot;/"/g' |
    sed 's/\&amp;/\&/g'
}
encode_query() {
    # Escape single quotes for use in perl
    local ENCODED_QUERY=${1//\'/\\\'}
    ENCODED_QUERY=$(perl -MURI::Escape -e "print uri_escape('$ENCODED_QUERY');")
    echo "$URL$ENCODED_QUERY"
}
ask_google() {
    RESULT=$(wget "$(encode_query "$1")" \
        --quiet \
        -O - \
        | grep -m 10 -A 1 -e '<div  class="dct-em">' \
        | grep -v -e '^--$' \
        | awk 'NR % 2 == 0' \
        | sed 's#</b> <b># #g' \
        | sed 's#</\?b>#*#g' \
        | sed 's/<[^>]*>//g' \
        | sed 's/\\u0026/\&/g' \
        | fix_html_entities \
        | fix_html_entities)
    if [[ -n $RESULT ]]; then
        echo "${RESULT//$'\n'/   }"
        return
    fi
    RESULT=$(wget "$(encode_query "$1")" \
        --quiet \
        -O - \
        | grep -m 1 -A 2 -e '<font color="#CC0000">Did you mean:</font>' \
        | tail -n 1 \
        | sed 's/<[^>]*>//g' \
        | sed 's/\\u0026/\&/g' \
        | fix_html_entities \
        | fix_html_entities)
    [[ -n $RESULT ]] && echo "Did you mean: $RESULT"
}

RESULT=$(ask_google "$QUERY")

if [[ -z $RESULT ]]; then
    echo "No result. :-("
    exit 0
fi

if [[ ${#RESULT} -lt $(( $MAX_RESULT_LENGTH - 3 )) ]]; then
    echo "$RESULT"
    exit 0
fi

# Restrict length and print result
RESULT="${RESULT:0:$(( $MAX_RESULT_LENGTH - 3 ))}"
RESULT=$(echo "$RESULT" | sed 's/ [^ ]*$/ /')
echo "$RESULT... (more at $(encode_query "$QUERY") )"

exit 0
