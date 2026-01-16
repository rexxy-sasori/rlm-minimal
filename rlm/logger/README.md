# Recursive Language Models (minimal version) 

[Link to the official RLM codebase](https://github.com/alexzhang13/rlm)

[Link to the paper](https://arxiv.org/abs/2512.24601v1)

[Link to the original blogpost 📝](https://alexzhang13.github.io/blog/2025/rlm/)

I received a lot of requests to put out a notebook or gist version of the codebase I've been using. Sadly it's a bit entangled with a bunch of random state, cost, and code execution tracking logic that I want to clean up while I run other experiments. In the meantime, I've re-written a simpler version of what I'm using so people can get started building on top and writing their own RLM implementations. Happy hacking!

![teaser](media/rlm.png)

I've provided a basic, minimal implementation of a recursive language model (RLM) with a REPL environment for OpenAI clients. Like the blogpost, we only implement recursive sub-calls with `depth=1` inside the RLM environment. Enabling further depths is as simple as replacing the `Sub_RLM` class with the `RLM_REPL` class, but you may need to finagle the `exec`-based REPL environments to work better here (because now your sub-RLMs have their own REPL environments!).

In this stripped implementation, we exclude a lot of the logging, cost tracking, prompting, and REPL execution details of the experiments run in the blogpost. It's relatively easy to modify and build on top of this code to reproduce those results, but it's currently harder to go from my full codebase to supporting any new functionality.

## Basic Example
We have all the basic dependencies in `requirements.txt`, although none are really necessary if you change your implementation (`openai` for LM API calls, `dotenv` for .env loading, and `rich` for logging).

In `main.py`, we have a basic needle-in-the-haystack (NIAH) example that embeds a random number inside ~1M lines of random words, and asks the model to go find it. It's a silly Hello World type example to emphasize that `RLM.completion()` calls are meant to replace `LM.completion()` calls.

## Code Structure
In the `rlm/` folder, the two main files are `rlm_repl.py` and `repl.py`. 
* `rlm_repl.py` offers a basic implementation of an RLM using a REPL environment in the `RLM_REPL` class. The `completion()` function gets called when we query an RLM.
* `repl.py` is a simple `exec`-based implementation of a REPL environment that adds an LM sub-call function. To make the system truly recursive beyond `depth=1`, you can replace the `Sub_RLM` class with `RLM_REPL` (they all inherit from the `RLM` base class).

The functionality for parsing and handling base LLM clients are all in `rlm/utils/`. We also add example prompts here.

> The `rlm/logger/` folder contains logging utilities used by the RLM REPL implementation.

## Features

1. **Colorful Logging**: Enhanced logging using the `rich` library
2. **Python Logging Integration**: Uses Python's standard logging package
3. **TimescaleDB Integration**: Database-backed latency and token tracking
4. **Token Cache Tracking**: Monitor LLM token cache usage and cost savings

## Installation

Install required dependencies:
```bash
pip install -r requirements.txt
```

## Documentation

- **[Quick Start Guide](doc/QUICKSTART_TIMESCALE.md)**: Get started with TimescaleDB logging
- **[Token Cache Tracking](doc/TOKEN_CACHE_TRACKING.md)**: Track token cache usage and cost savings
- **[Query API Reference](doc/QUERY_API.md)**: Query and retrieve records using query_id and run_id

## Usage Examples

- **[TimescaleDB Examples](examples/timescale_examples.py)**: Basic usage examples
- **[Token Cache Examples](examples/token_cache_example.py)**: Token cache tracking examples
- **[Query Records Examples](examples/query_records_example.py)**: Extract all records for (query_id, run_id)
- **[RLM REPL with TimescaleDB](../rlm_repl_tsdb.py)**: RLM_REPL integration with TimescaleDB (at rlm/ level)

## Project Structure

```
rlm/logger/
├── __init__.py              # Package initialization
├── README.md                # This file
├── requirements.txt         # Logger dependencies
├── root_logger.py           # Root logger with colorful output
├── repl_logger.py           # REPL environment logger
├── timescale_client.py      # TimescaleDB client for latency tracking
├── doc/                     # Documentation
│   ├── QUICKSTART_TIMESCALE.md
│   ├── TOKEN_CACHE_TRACKING.md
│   └── QUERY_API.md
├── examples/                # Usage examples
│   ├── timescale_examples.py
│   ├── token_cache_example.py
│   └── query_records_example.py
└── sql/                     # Database schemas
    └── timescale_schema.sql
```

## RLM Integration

The [rlm_repl_tsdb.py](../rlm_repl_tsdb.py) file (RLM_REPL with TimescaleDB) is located at the `rlm/` level alongside `rlm_repl.py`. It provides a drop-in replacement for `RLM_REPL` with built-in TimescaleDB latency tracking.

When you run your code, you'll see something like this:

![Example logging output using `rich`](media/rich.png)
