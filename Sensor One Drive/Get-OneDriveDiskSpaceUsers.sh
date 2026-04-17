#!/bin/sh

output_file="$(mktemp -t onedrive_usage)"
trap 'rm -f "$output_file"' EXIT

for user_home in /Users/*; do
  [ -d "$user_home" ] || continue

  user_name="$(basename "$user_home")"
  [ "$user_name" = "Shared" ] && continue

  for folder in "$user_home"/OneDrive*; do
    [ -d "$folder" ] || continue

    locally_available=0
    online_only=0
    always_available=0

    file_list="$(mktemp -t onedrive_files)"
    find "$folder" -type f 2>/dev/null > "$file_list"

    while IFS= read -r file; do
      [ -f "$file" ] || continue

      logical_size="$(stat -f %z "$file" 2>/dev/null)"
      blocks="$(stat -f %b "$file" 2>/dev/null)"

      case "$logical_size" in ''|*[!0-9]*) logical_size=0 ;; esac
      case "$blocks" in ''|*[!0-9]*) blocks=0 ;; esac

      physical_size=$((blocks * 512))

      # Best-effort macOS mapping:
      # logical size > 0 and no allocated blocks => online-only placeholder
      # otherwise => locally available
      if [ "$logical_size" -gt 0 ] && [ "$physical_size" -eq 0 ]; then
        online_only=$((online_only + logical_size))
      else
        locally_available=$((locally_available + physical_size))
      fi
    done < "$file_list"

    rm -f "$file_list"

    loc_gb=$(awk "BEGIN { printf \"%.2f\", $locally_available/1073741824 }")
    online_gb=$(awk "BEGIN { printf \"%.2f\", $online_only/1073741824 }")
    always_gb=$(awk "BEGIN { printf \"%.2f\", $always_available/1073741824 }")

    printf "%s|%s|%s|%s|%s\n" \
      "$user_name" \
      "$folder" \
      "$loc_gb" \
      "$online_gb" \
      "$always_gb" >> "$output_file"
  done
done

if [ -s "$output_file" ]; then
  cat "$output_file"
else
  echo "No OneDrive folders found"
fi