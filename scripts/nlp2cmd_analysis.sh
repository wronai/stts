#!/bin/bash

# Script to generate decision trees and logs for nlp2cmd examples

echo "# NLP2CMD Decision Tree and Schema Analysis"
echo ""
echo "## Command: wejdź na jspaint.app i narysuj biedronkę"
echo ""

# Run with decision tree flag
echo "### Decision Tree:"
echo '```'
nlp2cmd "wejdź na jspaint.app i narysuj biedronkę" --show-decision-tree
echo '```'
echo ""

# Run with explain flag
echo "### Execution Explanation:"
echo '```'
nlp2cmd -r "wejdź na jspaint.app i narysuj biedronkę" --explain
echo '```'
echo ""

# Run with verbose output
echo "### Verbose Output:"
echo '```'
nlp2cmd "wejdź na jspaint.app i narysuj biedronkę" --verbose 2>&1 | head -50
echo '```'
echo ""

# Save to markdown file
echo "### Saving to markdown file..."
nlp2cmd -r "wejdź na jspaint.app i narysuj biedronkę" --md > nlp2cmd_analysis.md 2>&1
echo "Saved to nlp2cmd_analysis.md"
