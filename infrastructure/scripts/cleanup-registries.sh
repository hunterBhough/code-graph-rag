#!/opt/homebrew/bin/bash
# Clean up duplicate entries in registry files
# Keeps only the most recent entry for each project path

set -e

cleanup_registry() {
    local file="$1"
    local temp_file="${file}.tmp"

    echo "Cleaning up $file..."

    # Extract header and projects section separately
    awk '/^projects:/ {found=1} !found {print}' "$file" > "$temp_file"
    echo "projects:" >> "$temp_file"

    # Get all project entries, deduplicate by path (keeping most recent), and append
    awk '/^	- name:/ {
        entry = ""
        name = ""
        path = ""
    }
    /^	- name:/ || /^	  / {
        entry = entry $0 "\n"
        if ($0 ~ /name:/) {
            sub(/.*name: /, "", $0)
            name = $0
        }
        if ($0 ~ /path:/) {
            sub(/.*path: /, "", $0)
            path = $0
        }
    }
    /^$/ || (/^[^ \t]/ && !/^	/) {
        if (entry != "" && path != "") {
            # Use path as unique key
            projects[path] = entry
        } else if (entry != "" && name != "") {
            # Fallback to name if no path
            if (!(name in seen_names)) {
                projects[name] = entry
                seen_names[name] = 1
            }
        }
        entry = ""
    }
    END {
        for (key in projects) {
            printf "%s", projects[key]
        }
    }' "$file" | sort -u >> "$temp_file"

    mv "$temp_file" "$file"
    echo "✅ Cleaned up $file"
}

# Clean up both registries
cleanup_registry "/Users/hunter/code/ai_agency/shared/mcp-servers/weavr/infrastructure/registry/projects.toon"
# cleanup_registry "/Users/hunter/code/ai_agency/shared/mcp-servers/seekr/infrastructure/registry/projects.toon"  # Seekr no longer uses .toon files

echo ""
echo "✅ Registry cleanup complete!"
