# RLM Minimal

Minimal implementation of RLM (Reinforcement Learning with Models) for code execution and LLM interaction tracking.

## Features

- **Code Execution**: Execute Python code in a sandboxed environment
- **LLM Integration**: Interact with various LLM models
- **Logging**: Comprehensive logging with TimescaleDB integration
- **Token Cache Tracking**: Monitor LLM token cache usage and cost savings

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the RLM REPL:
```bash
python rlm/rlm_repl.py
```

## Documentation

- **[TimescaleDB Quick Start](rlm/logger/doc/QUICKSTART_TIMESCALE.md)**: Get started with TimescaleDB logging
- **[Token Cache Tracking](rlm/logger/doc/TOKEN_CACHE_TRACKING.md)**: Track token cache usage and cost savings
- **[Logger Documentation](rlm/logger/README.md)**: Detailed logger implementation guide

## Project Structure

```
rlm-minimal/
├── rlm/
│   ├── logger/          # Logging utilities
│   ├── utils/           # Utility functions
│   └── rlm_repl.py      # Main REPL implementation
├── README.md
└── requirements.txt
```

## License

MIT
