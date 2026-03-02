# NLP2CMD Decision Tree and Schema Analysis

## Command Analyzed: `wejdź na jspaint.app i narysuj biedronkę`

## Available Flags for Decision Tree and Schema Analysis

### Key Flags:
- `--show-decision-tree` - Shows the complete decision tree for a query
- `--explain` - Explains how the result was produced
- `--verbose` - Enables verbose debug output
- `--md` - Generate Markdown log with inline thumbnails
- `--show-schema` - Show available schemas (intents, entities, templates)

## Decision Tree Analysis

### Step 1: Intent Detection
The system detects multiple intents with confidence scores:

1. **draw** (confidence: 0.95)
   - Domain: `canvas`
   - Method: `keyword`
   - Matched label: `narysuj` (pl)

2. **navigate** (confidence: 0.95) ← SELECTED
   - Domain: `browser`
   - Method: `keyword`
   - Matched label: `wejdz na` (pl)

3. Other intents with lower confidence (close_app, email_compose, minimize_all)

### Step 2: Pipeline Processing
- **Domain:** `browser` (selected over canvas)
- **Intent:** `navigate`
- **Detection Confidence:** 0.96
- **Source:** `adapter`

### Step 3: Entity Extraction
- Extracted entity: `url`: `jspaint.app`

### Step 4: Command Generation
- Generated DSL command: `{"dsl": "dom_dql.v1", "action": "goto", "url": "jspaint.app", "params": {}}`
- Final confidence: 0.96

## Execution Flow in Run Mode

1. **Detection Phase** - System identifies browser domain with navigate intent
2. **Browser Automation** - Automatically enables Playwright for browser automation
3. **Action Execution** - Performs goto action to navigate to jspaint.app
4. **Completion** - Reports successful execution

## Schema Information

The system uses multiple schemas:
- **Intent Schemas** - Defines available intents (navigate, draw, close_app, etc.)
- **Domain Schemas** - Browser, canvas, desktop, etc.
- **Entity Schemas** - URL, file paths, etc.
- **DSL Schemas** - dom_dql.v1 for browser automation

## Why Only Navigation?

The system prioritized the `navigate` intent over `draw` because:
1. Both had equal confidence (0.95)
2. The phrase "wejdź na" (enter/go to) is a strong navigation signal
3. The URL entity `jspaint.app` was extracted
4. Browser domain was selected over canvas domain

The drawing action ("narysuj biedronkę") was not executed because:
- The system processed only one intent at a time
- Navigation took precedence
- Multi-step actions require separate commands

## Recommendations

To execute both actions:
1. First: `nlp2cmd -r "wejdź na jspaint.app"`
2. Then: `nlp2cmd -r "narysuj biedronkę" -d canvas`

## Usage Examples

```bash
# Show decision tree for any query
nlp2cmd "your query" --show-decision-tree

# Run with explanation
nlp2cmd -r "your query" --explain

# Generate markdown log
nlp2cmd -r "your query" --md > output.md

# Show available schemas
nlp2cmd --show-schema

# Verbose output with all details
nlp2cmd "your query" --verbose
```
