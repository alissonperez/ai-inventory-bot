# Inventory Bot

A smart Telegram bot that revolutionizes personal inventory management. With AI-powered image analysis, it automatically identifies items, fills in details, and enriches them with web-sourced information. Designed for seamless integration with Markdown-based note-taking apps like Obsidian, this bot makes keeping track of your belongings effortless and intelligent.

## Features

*   **Add Items:** Easily add new items to your inventory with a name, quantity, photo, description, size and status.
*   **AI-Powered Data Enrichment:** Automatically populate item details by analyzing its image. The AI fills in the name and description, and enriches the information with a web search, considering any data you've already provided.
*   **Quick Add:** Fill location, box and quantity in name creation (e.g. `Item name; q 2 c box-name l location`).
*   **Organize with Boxes:** Assign items to specific boxes to keep track of their location.
*   **Telegram Interface:** Interact with your inventory through a simple and intuitive Telegram bot interface.
*   **Markdown Integration:** Each inventory item is saved as a separate Markdown file with YAML front matter, making it easy to integrate with your existing notes.

## Getting Started

### Prerequisites

*   Python 3.13+
*   Poetry
*   A Telegram Bot Token

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/inventorybot.git
    cd inventorybot
    ```

2.  **Install dependencies using Poetry:**

    ```bash
    poetry install
    ```

### Configuration

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

### Running the Bot

To start the bot, run the following command:

```bash
poetry run python main.py
```

## Usage

1.  **Start a chat with your bot on Telegram and send the `/start` command.**
2.  **Send the name of the item you want to add.**
3.  **Follow the prompts to set the quantity, add a photo, and assign a box.**
4.  **Once you're done, click "Save" to save the item to your inventory.**

### Example: Using AI to Add an Item

1.  **Send a photo of your item with a caption.** Include any information you have, such as the item's name, brand, or model (e.g., "Sony WH-1000XM4"). This is especially useful if the text is not visible in the image.
2.  **The bot will analyze the image and use the provided information to search the web.** It will automatically fill in the item's name and description with the data it finds.
3.  **Review the information and save the item.**

## Project Structure

```
.
├── inventorybot/
│   ├── entities.py       # Data structures for Item, Box, and Status
│   ├── service.py        # Business logic for the bot
│   ├── vision.py         # Computer vision services for image analysis
│   └── infra/
│       └── markdown_output.py # Handles saving items to Markdown files
├── main.py             # Main application entry point
├── pyproject.toml      # Project dependencies
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

### Running Tests

To run the tests, use the following command:

```bash
poetry run pytest
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
