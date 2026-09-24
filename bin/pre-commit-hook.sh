#!/bin/bash

while IFS= read -r file; do
    # Skip deleted files
    [[ -f "$file" ]] || continue

    if grep -q "^kind: Secret$" "$file" && ! grep -q "BEGIN AGE ENCRYPTED FILE" "$file"; then
        echo "ERROR: $file is an unencrypted Secret"
        exit 1
    fi
done < <(git diff --cached --name-only --diff-filter=ACM -- flux-components)

exit 0