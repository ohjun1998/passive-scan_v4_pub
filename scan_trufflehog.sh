#!/bin/bash
mkdir -p results
GROUP_SUFFIX=$1
split -d -n l/20 targets.txt targets_group
TARGET_FILE="targets_group${GROUP_SUFFIX}"

scan_truffle() {
    local domain=$(echo "$1" | xargs)
    [[ -z "$domain" || "$domain" =~ ^# ]] && return
    local download_dir="results/${domain}_js_files"

    if [ -d "$download_dir" ] && [ "$(ls -A "$download_dir" 2>/dev/null)" ]; then
        trufflehog filesystem "$download_dir" --only-verified --json 2>/dev/null > "results/${domain}_trufflehog_raw.json" || true
        if [ -s "results/${domain}_trufflehog_raw.json" ]; then
            cat "results/${domain}_trufflehog_raw.json" | jq -r '. | ((.SourceMetadata.Data.Filesystem.file // "unknown.js") | split("/") | last) + "\t[" + (.DetectorName // "Secret") + "] " + ((.Raw // "") | gsub("\n"; " "))' > "results/${domain}_trufflehog.txt" || true
            rm -f "results/${domain}_trufflehog_raw.json"
        else
            echo "" > "results/${domain}_trufflehog.txt"
        fi
    else
        echo "" > "results/${domain}_trufflehog.txt"
    fi
}
export -f scan_truffle
xargs -P 10 -n 1 -a "$TARGET_FILE" -I {} bash -c 'scan_truffle "{}"'
rm -f targets_group*
