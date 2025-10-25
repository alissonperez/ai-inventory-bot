# Project Overview

This project is a Python-based Telegram bot for managing a personal inventory. It allows users to add items with details like name, quantity, photo, and location (box). The bot is designed to work with a Markdown-based notes app like Obsidian, as it saves each inventory item as a separate Markdown file with YAML front matter.

## Main Technologies

*   **Python:** The core programming language.
*   **python-telegram-bot:** The library used to interact with the Telegram Bot API.
*   **Poetry:** The dependency management and packaging tool.
*   **YAML:** Used for storing structured data in the Markdown front matter.
*   **Markdown:** The format for saving inventory items.

## Architecture

The bot's architecture is simple and modular:

*   **`main.py`:** The main entry point of the application. It contains the Telegram bot handlers for processing messages and callbacks.
*   **`inventorybot/entities.py`:** Defines the data structures for `Item`, `Box`, and `Status`.
*   **`inventorybot/infra/markdown_output.py`:** Handles the persistence of inventory items to Markdown files.

# Building and Running

## Prerequisites

*   Python 3.13+
*   Poetry

## Installation

1.  Install dependencies using Poetry:

    ```bash
    poetry install
    ```

## Running the Bot

1.  **Create a `.env` file:**

    In the root of the project, create a file named `.env`. You can copy the example file:

    ```bash
    cp .env.example .env
    ```

2.  **Set your environment variables:**

    Open the `.env` file and add your Telegram bot token and the desired output directory:

    ```
    TELEGRAM_TOKEN="your_token_here"
    OUTPUT_DIR="/path/to/your/inventory"
    ```
3.  Run the bot:

    ```bash
    poetry run python main.py
    ```

## Running Tests

To run the tests, use the following command:

```bash
poetry run pytest
```

# Development Conventions

*   The project uses `black` for code formatting and `ruff` for linting (inferred from common Python practices, but not explicitly configured).
*   The bot interacts with users through a conversational interface, using inline keyboards for actions.
*   Data is persisted in a human-readable format (Markdown with YAML front matter), which is a key design choice.
