# The Automated Philosopher

"embark on the ships! There is a new world to discover – and more than one!" (Friedrich Nietzsche, The Gay Science)

Can an LLM discover new philosophical insights?

## Overview

At its core, The Automated Philosopher is a state-machine-driven system that continuously synthesizes new philosophical propositions. Starting from a seed set of propositions, the system cycles through three states:

1. **Attention** - Selects two propositions to work with
2. **Synthesis** - Generate a new proposition that relates the two partners
4. **Judgement** - Evaluate the proposition's worth and decide whether to accept it

Each new proposition leads to other new propositions, creating a virtuous circle.

## Prerequisites

- Python 3.7+
- Anthropic API key

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser to `http://localhost:5000`

3. Click "Start" to begin the automated philosophy generation

4. Watch as the system:
   - Highlights propositions being considered
   - Shows draft propositions as they're created
   - Judges propositions
   - Adds accepted propositions to the collection

## Configuration

By default, this uses the Claude Opus 4 model (`claude-opus-4-1-20250805`) with a maximum of 1024 tokens per response. You can modify these settings in `app.py`:

```python
"model": "claude-opus-4-1-20250805",
"max_tokens": 1024
```

## Acknowledgments

Default propositions sourced from Ludwig Wittgenstein's *Tractatus Logico-Philosophicus* (1921).

This project is supported by a Cosmos grant. See https://blog.cosmos-institute.org/p/introducing-the-first-cohort-of-ai.
