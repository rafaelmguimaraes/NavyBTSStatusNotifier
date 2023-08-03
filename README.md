# NavyBTSStatusNotifier

NavyBTSStatusNotifier is a Python script that fetches the status updates from the Capitania dos Portos da Bahia (Navy) website regarding the Bahia de Todos os Santos (BTS) area and sends notifications to a specified Telegram chat.

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

## Description

NavyBTSStatusNotifier is a simple utility that periodically fetches the status updates related to the Bahia de Todos os Santos (BTS) area from the Capitania dos Portos da Bahia (Navy) website and sends these updates to a specified Telegram chat using the Telegram API.

## Features

- Fetches Bahia de Todos os Santos (BTS) area status updates from the Capitania dos Portos da Bahia (Navy) website
- Notifies a Telegram chat with the status updates
- Configurable logging and error handling

## Requirements

- Python 3.x
- `requests` library (`pip install requests`)
- `parsel` library (`pip install parsel`)
- Valid Telegram bot token and chat ID

## Installation

1. Clone the repository:

git clone https://github.com/your-username/NavyBTSStatusNotifier.git
cd NavyBTSStatusNotifier


2. Install the required dependencies:

pip install -r requirements.txt

## Usage

1. Set up the required environment variables:

   - `TELEGRAM_TOKEN`: Your Telegram bot token
   - `TELEGRAM_CHAT_ID`: The chat ID to receive notifications

2. Run the script:
 
 python main.py


## Configuration

You can configure the script by modifying the constants in the `main.py` file:

- `BASE_URL`: The URL of the Capitania dos Portos da Bahia (Navy) website
- `TIMEOUT`: Timeout for requests (in seconds)
- `LOG_FILE`: Path to the log file

## Error Handling

The script handles errors and exceptions gracefully:

- `TokenNotAvailableException`: Raised if Telegram token is not available in the environment
- `TimeoutException`: Raised if a timeout occurs during network requests
- Other exceptions: General exception handling for unforeseen errors

## Automated Script Execution with GitHub Actions

NavyBTSStatusNotifier can be automatically executed at regular intervals using GitHub Actions. The following GitHub Actions workflow has been set up to run the `main.py` script and fetch the BTS status from the Capitania dos Portos da Bahia (Navy) website.

### Workflow Details

The workflow is triggered by a scheduled event based on a cron expression. It runs the script hourly to ensure timely updates.

- **Event:** Scheduled event (Cron job)
- **Interval:** Every hour (at minute 0 past every hour)

### Workflow Steps

1. **Checkout Repository Content:** The workflow starts by checking out the content of the repository to the GitHub runner.

2. **Setup Python Environment:** The required Python version (3.9) is set up using the `actions/setup-python` action.

3. **Install Python Packages:** The necessary Python packages are installed using `pip`.

4. **Execute Python Script (`main.py`):** The `main.py` script is executed with the environment variables `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` provided as secrets.

5. **Commit Changes:** If there are any changes made during the script execution (such as updating logs), the workflow commits these changes back to the repository.

6. **Push Changes:** Finally, the changes are pushed to the `main` branch of the repository using the `ad-m/github-push-action` action.

### Secrets

To enable the automatic script execution and notification, you need to set up the following secrets in your repository:

- `TELEGRAM_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: The chat ID to receive notifications

These secrets are securely stored and can be accessed within the workflow for authentication purposes.

Please note that you can customize the workflow based on your requirements, such as adjusting the cron schedule or modifying the script execution process.

For more information on GitHub Actions and how to set up and customize workflows, refer to the [GitHub Actions documentation](https://docs.github.com/en/actions).

## Contributing

Contributions are welcome! If you find a bug or have an enhancement in mind, feel free to open an issue or submit a pull request.

1. Fork the repository.
2. Create a new branch: `git checkout -b my-feature-branch`
3. Make your changes and commit them: `git commit -m "Add some feature"`
4. Push to the branch: `git push origin my-feature-branch`
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

