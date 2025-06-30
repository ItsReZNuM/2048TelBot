# 🎮 2048 Telegram Bot 🚀

Welcome to the 2048 Telegram Bot! This bot allows you to play the classic 2048 game directly within Telegram, compete with others, and track your high scores on a leaderboard.

## ✨ Features

* **Play 2048**: Enjoy the classic 2048 game directly in your Telegram chat.
* **Multiple Difficulty Levels**: Choose from Easy (5x5), Medium (7x7), and Hard (9x9) board sizes.
* **Leaderboard**: See the top players and their scores.
* **Game Rules**: Get an explanation of how to play 2048.
* **Rate Limiting**: Prevents message flooding from users.
* **Admin Broadcast**: Admins can send messages to all users.
* **Persistent Data**: User data and leaderboard scores are saved to JSON files.

## 🛠️ Setup and Installation

### Prerequisites

* Python 3.10 >
* `pyTelegramBotAPI` library
* `pytz` library

### Installation Steps

1.  **Clone the repository (or download the `2048.py` file):**
    ```bash
    git clone [https://github.com/ItsReZNuM/2048TelBot](https://github.com/ItsReZNuM/2048TelBot)
    cd 2048TelBot
    ```

2.  **Install the required Python libraries:**
    ```bash
    pip install pyTelegramBotAPI pytz
    ```

3.  **Get your Telegram Bot Token:**
    * Talk to [@BotFather](https://t.me/botfather) on Telegram.
    * Use the `/newbot` command to create a new bot.
    * BotFather will give you a token. Copy it.

4.  **Configure the bot:**
    * Open the `2048.py` file.
    * Replace `"YOUR_BOT_TOKEN"` with your actual bot token:
        ```python
        TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
        ```
    * (Optional) Add your Telegram User ID to `ADMIN_USER_IDS` for admin functionalities like broadcasting:
        ```python
        ADMIN_USER_IDS = [YOUR_TELEGRAM_USER_ID]
        ```

5.  **Run the bot:**
    ```bash
    python 2048.py
    ```
    You should see "Bot is Starting.." in your console.

## 🕹️ How to Play

Once the bot is running:

1.  **Start the Bot**: Send the `/start` command to your bot on Telegram.
2.  **Choose Difficulty**: The bot will prompt you to choose a difficulty level (board size).
3.  **Make Moves**: Use the inline keyboard buttons (↑, ↓, ←, →) to move the tiles.
4.  **End Game**: You can choose to end the game at any time by pressing "دیگه نمیخوام بازی کنم ! " (I don't want to play anymore!).
5.  **Check Rules**: Use the `/rules` command to see the game rules.
6.  **Leaderboard**: Use the `/leaderboard` command to view the top scores.

## 🤖 Bot Commands

* `/start`: Start the 2048 game and get a welcome message.
* `/rules`: Display the rules of the 2048 game.
* `/leaderboard`: Show the top 5 players and their scores.
* `/alive`: Check if the bot is active.

### Admin Command

* `پیام همگانی 📢` (Broadcast Message): Admins can send this text to initiate a broadcast message to all users.

## 📁 File Structure

* `2048.py`: The main bot script containing all the logic.
* `users.json`: Stores information about the users who have interacted with the bot.
* `leaderboard.json`: Stores the high scores and player names for the leaderboard.

## 🤝 Contributing

Contributions are welcome! If you have any suggestions, bug reports, or want to contribute to the code, feel free to open an issue or submit a pull request.

## 🙏 Acknowledgements

* [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) for the Telegram Bot API wrapper.
* The classic 2048 game for the inspiration.

## 📞 Connect to contributer

- Telegram : (t.me/ItsReZNuM)
- Instagram : (rez.num)