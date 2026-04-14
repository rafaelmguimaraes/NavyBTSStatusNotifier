# NavyBTSStatusNotifier

NavyBTSStatusNotifier is a Python script that fetches the latest public ferry operation bulletin for the Bahia de Todos os Santos route and sends notifications to a specified Telegram chat.

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

NavyBTSStatusNotifier is a simple utility that periodically fetches the latest public operation bulletin published by Internacional Travessias and sends updates to a specified Telegram chat using the Telegram API.

## Features

- Fetches the latest operation bulletin from Internacional Travessias using its public WordPress API, with RSS fallback
- Notifies a Telegram chat only when the extracted operational summary changes
- Writes daily logs to `logs/YYYY-MM-DD.log`
- Fails with a non-zero exit code when fetch, parsing, or Telegram notification fails

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

- `ITS_POSTS_API_URL`: The public WordPress API endpoint used as the primary source
- `ITS_OPERACAO_FEED_URL`: The RSS feed used as a fallback source
- `TIMEOUT`: Timeout for requests (in seconds)
- `LOG_DIR`: Directory where daily log files are written
- `STATE_DIR`: Directory where the last sent summary state is cached between workflow runs

## Error Handling

The script handles errors and exceptions gracefully:

- `TokenNotAvailableException`: Raised if Telegram token is not available in the environment
- `FetchStatusException`: Raised if the bulletin source fails in both API and RSS fetch attempts
- `StatusNotFoundException`: Raised if the bulletin can no longer be parsed into a usable summary
- `TelegramNotificationException`: Raised if the Telegram API call fails or is rejected
- `StaleSourceException`: Raised if the latest bulletin is too old to trust
- The script exits with a non-zero code so GitHub Actions reflects the failure

## Automated Script Execution with GitHub Actions

NavyBTSStatusNotifier can be automatically executed at regular intervals using GitHub Actions. The workflow runs `main.py`, restores the last cached summary state, fetches the latest operation bulletin, and only sends Telegram when the summary changes.

### Workflow Details

The workflow is triggered by a scheduled event based on a cron expression. Recent bulletins have typically been published between 09:17 and 11:14 in Salvador time, so the workflow runs once per day after that window.

- **Event:** Scheduled event (Cron job)
- **Interval:** Daily at 15:00 UTC (12:00 in Salvador, UTC-3)

### Workflow Steps

1. **Checkout Repository Content:** The workflow starts by checking out the content of the repository to the GitHub runner.

2. **Setup Python Environment:** The required Python version (3.11) is set up using the `actions/setup-python` action.

3. **Install Python Packages:** The necessary Python packages are installed using `pip`.

4. **Restore Saved State:** The workflow restores the most recent cached `state/` directory so the script can compare the latest bulletin with the previously sent summary.

5. **Execute Python Script (`main.py`):** The `main.py` script is executed with the environment variables `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` provided as secrets.

6. **Save State Cache:** After a successful run, the latest `state/` directory is cached for the next execution.

7. **Upload Logs on Failure:** If the job fails, the generated files in `logs/` are uploaded as workflow artifacts for inspection.

### Secrets

To enable the automatic script execution and notification, you need to set up the following secrets in your repository:

- `TELEGRAM_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: The chat ID to receive notifications

These secrets are securely stored and can be accessed within the workflow for authentication purposes.

Please note that you can customize the workflow based on your requirements, such as adjusting the cron schedule or modifying the script execution process.

## Logging Strategy

- Runtime logs are written to `logs/YYYY-MM-DD.log`
- The `logs/` directory is ignored by git and is not committed back to the repository
- The `state/` directory is ignored by git and cached by GitHub Actions between successful runs
- In GitHub Actions, logs are uploaded only when the workflow fails

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
