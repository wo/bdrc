#!/bin/bash

show_usage() {
    cat <<EOF
Usage: ./make.sh [--html | --upload | --help]
  (no flags)  Build PDF only.
  --html      Build PDF, then regenerate html/ via create_html.py.
  --upload    Build PDF, regenerate html/, then rsync html/ to umsu.de.
EOF
}

BUILD_HTML=0
UPLOAD=0
for arg in "$@"; do
    case "$arg" in
        --html) BUILD_HTML=1 ;;
        --upload) BUILD_HTML=1; UPLOAD=1 ;;
        --help|-h) show_usage; exit 0 ;;
        *) echo "Unknown option: $arg"; show_usage; exit 1 ;;
    esac
done

echo "Compiling bdrc.tex..."

xelatex -interaction=batchmode -halt-on-error bdrc.tex > /dev/null 2>&1
EXIT_CODE=$?

if [ -f "bdrc.log" ]; then
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Compilation successful!"
    else
        echo "✗ Compilation failed. Error context:"
        echo "========================================"
        tail -25 bdrc.log
        exit 1
    fi
else
    echo "✗ No log file created - something went wrong with xelatex"
    exit 1
fi

if [ $BUILD_HTML -eq 1 ]; then
    echo ""
    echo "Regenerating HTML..."
    uv run create_html.py
    if [ $? -ne 0 ]; then
        echo "✗ HTML generation failed."
        exit 1
    fi
    echo "✓ HTML generated."
fi

if [ $UPLOAD -eq 1 ]; then
    echo ""
    echo "Uploading to umsu.de..."
    rsync -avz ./html/ wo@umsu.de:/var/www/umsu.de/public_html/bdrc/
    if [ $? -ne 0 ]; then
        echo "✗ Upload failed."
        exit 1
    fi
    echo "✓ Upload complete."
fi

if [ $BUILD_HTML -eq 0 ] && [ $UPLOAD -eq 0 ]; then
    echo ""
    echo "Note: ./make.sh --html also rebuilds HTML; --upload also uploads to umsu.de."
fi
