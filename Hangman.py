import string # for ascii_lowercase
import subprocess # for pip install
import os # for clear terminal
import sys # for exit
import json # for json file handling
import hashlib # for password hashing
from datetime import datetime # for time calculations
import getpass # for password input
import configparser # for config file handling
import pandas as pd # for dataframes
try:
    from wonderwords import RandomWord # pip install wonderwords
except ImportError:
    print("wonderwords not installed, installing now...")
    subprocess.run(["pip", "install", "wonderwords"])
    print("...wonderwords installed")

#=======================================
# Configuration
#=======================================
program_location = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(program_location, "config.ini")
config = configparser.ConfigParser()

if not os.path.exists(config_file):
    config["Word Settings"] = {
        "easy word length": "8",         
        "normal word length": "10",
        "hard word length": "15"
    }
    config["Score Multipliers"] = {
        "add points per correct letter": "100",
        "sub points per wrong letter": "50",
        "allowed seconds per letter": "5",
        "add/sub points per second to finish": "5",
        "add points for winning": "500"
    }
    config["Password Settings"] = {
        "min password length": "8",
        "incorrect password attempts": "3"
    }
    config["Game Settings"] = {
        "clear_screen": "True",
        "show_word": "True",
        "debug": "False"
    }
    with open(config_file, "w") as file:
        config.write(file)
    print("Config file created, please update the settings in the config file and run the program again")
else:
    config.read(config_file)
    print("Config file found, loading settings...")

# config["Word Settings"]
length_of_easy_word = int(config["Word Settings"]["easy word length"])
length_of_normal_word = int(config["Word Settings"]["normal word length"])
length_of_hard_word = int(config["Word Settings"]["hard word length"])
# config["Score Multipliers"]
correct_letters_multiplier = int(config["Score Multipliers"]["add points per correct letter"])
wrong_letter_multiplier = int(config["Score Multipliers"]["sub points per wrong letter"])
grace_period_multiplier = int(config["Score Multipliers"]["allowed seconds per letter"])
time_points_multiplier = int(config["Score Multipliers"]["add/sub points per second to finish"])
win_multiplier = int(config["Score Multipliers"]["add points for winning"])
# config["Password Settings"]
min_password_length = int(config["Password Settings"]["min password length"])
incorrect_password_attempts = int(config["Password Settings"]["incorrect password attempts"])
# config["Game Settings"]
clear_screen = config["Game Settings"].getboolean("clear_screen")
show_word = config["Game Settings"].getboolean("show_word")
debug = config["Game Settings"].getboolean("debug")

# Global Variables
#=======================================
# file name for the game stats json file
file_name = "hangman_stats.json"
# file name for the player credentials and stats json file
player_file_name = "player_stats.json"
# difficulty map
difficulty_word_length = {
    ("1", "Easy"): length_of_easy_word, 
    ("2", "Normal"): length_of_normal_word, 
    ("3", "Hard"): length_of_hard_word}

#=======================================
# Functions
#=======================================
def clear_terminal():
    if clear_screen == True:
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:
            os.system('clear') # Linux / MacOS

def check_data_directory_and_append_filename(file_name):
    """
    Make that the 'data' directory exists in the same location as the script.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    abs_file_path = os.path.join(data_dir, file_name)
    return abs_file_path

def load_statistics_from_json(file_name):
    """
    Load data from a json file in the data directory.

    Args:
    file_name (str): The name of the JSON file.

    Returns:
    list: The list of json entries as dicsts.
    """
    # get absolute path to data directory and file name
    file_path = check_data_directory_and_append_filename(file_name)
    # Load current data from the file if it exists
    if os.path.exists(file_path):
        with open(file_path, mode='r') as file:
            try:
                json_file = json.load(file)
            except json.JSONDecodeError:
                json_file = []
                return json_file  # If file is corrupted or empty, reset to an empty list
    else:
        json_file = []
    return json_file

def save_statistics_to_json(file_name, statistics):
    """
    Save game stats to a json file in the data directory.
    If the file already exists and contains data, append the new entry to the data.

    Args:
    file_name (str): The name of the JSON file.
    statistics (dict): The new game statistics entry to save.
    """
    # get absolute path to data directory and file name
    file_path = check_data_directory_and_append_filename(file_name)

    json_file = load_statistics_from_json(file_path)
    
    if json_file != []:
        # add stats to the list
        json_file.append(statistics)
    else:
        json_file = [statistics]
    
    # Save the list back to the file
    with open(file_path, mode='w') as file:
        json.dump(json_file, file, indent=4)

def check_player_exists(player_name):
    """
    Check if a player exists in the player stats file.

    Args: player_name (str): The player's name.

    Returns: bool: True if the player exists.
    """
    player_stats = load_statistics_from_json(player_file_name)
    for stats in player_stats:
        if stats["player_name"] == player_name:
            return True
    return False

def hash_password_md5(password):
    """
    Hash a password using MD5.

    Args: password (str): The password to hash.

    Returns: str: The hashed password.
    """
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    return hashed_password

def new_player_stats(player_name, player_password):
    """
    Create a new player stats dictionary.
    
    Args: player_name (str): The player's name, player_password (str): The player's password.
    
    Returns: dict: The new player stats dictionary.
    """
    if player_password == "":
        password = ""
    else:
        password = hash_password_md5(player_password)
    player_stats = {
        "player_name":player_name,
        "player_password": password,
        "easy_games":0,
        "easy_wins":0,
        "easy_highest_score":0,
        "easy_average_score":0,
        "easy_average_time":0,
        "normal_games":0,
        "normal_wins":0,
        "normal_highest_score":0,
        "normal_average_score":0,
        "normal_average_time":0,
        "hard_games":0,
        "hard_wins":0,
        "hard_highest_score":0,
        "hard_average_score":0,
        "hard_average_time":0,
        "total_games":0,
        "total_wins":0,
        "total_score":0,
        "average_score":0,
        "average_time":0
    } 
    return player_stats

def update_player_stats(player_name, game_stats):
    """
    Update the player stats with the new game statistics.

    Args:
    player_name (str): The player's name.
    game_stats (dict): The new game statistics entry to update the player stats with.
    """
    # 
    player_stats = load_statistics_from_json(player_file_name)
    print(f"Updating Player Stats for {player_name}...")
    # loop through the player stats and update the stats for the player
    for stats in player_stats:
        # check if player exists in the player stats file
        if stats["player_name"] == player_name:
            stats["total_games"] += 1
            stats["total_score"] += game_stats["total_score"]
            stats["average_time"] = round((float(stats["average_time"]) * (stats["total_games"] - 1) + float(game_stats["time_taken"])) / stats["total_games"], 2)
            stats["average_score"] = stats["total_score"] / stats["total_games"]
            if game_stats["win_bool"] == True:
                stats["total_wins"] += 1
                if game_stats["word_difficulty"] == "Easy":
                    stats["easy_games"] += 1
                    stats["easy_wins"] += 1
                    stats["easy_highest_score"] = game_stats["total_score"] if stats["easy_highest_score"] < game_stats["total_score"] else stats["easy_highest_score"]
                    stats["easy_average_score"] = (stats["easy_average_score"] * (stats["easy_games"] - 1) + game_stats["total_score"]) / stats["easy_games"]
                    stats["easy_average_time"] = (stats["easy_average_time"] * (stats["easy_games"] - 1) + game_stats["time_taken"]) / stats["easy_games"]
                elif game_stats["word_difficulty"] == "Normal":
                    stats["normal_games"] += 1
                    stats["normal_wins"] += 1
                    stats["normal_highest_score"] = game_stats["total_score"] if stats["normal_highest_score"] < game_stats["total_score"] else stats["normal_highest_score"]
                    stats["normal_average_score"] = (stats["normal_average_score"] * (stats["normal_games"] - 1) + game_stats["total_score"]) / stats["normal_games"]
                    stats["normal_average_time"] = (stats["normal_average_time"] * (stats["normal_games"] - 1) + game_stats["time_taken"]) / stats["normal_games"]
                elif game_stats["word_difficulty"] == "Hard":
                    stats["hard_games"] += 1
                    stats["hard_wins"] += 1
                    stats["hard_highest_score"] = game_stats["total_score"] if stats["hard_highest_score"] < game_stats["total_score"] else stats["hard_highest_score"]
                    stats["hard_average_score"] = (stats["hard_average_score"] * (stats["hard_games"] - 1) + game_stats["total_score"]) / stats["hard_games"]
                    stats["hard_average_time"] = (stats["hard_average_time"] * (stats["hard_games"] - 1) + game_stats["time_taken"]) / stats["hard_games"]
            else:
                if game_stats["word_difficulty"] == "Easy":
                    stats["easy_games"] += 1
                elif game_stats["word_difficulty"] == "Normal":
                    stats["normal_games"] += 1
                elif game_stats["word_difficulty"] == "Hard":
                    stats["hard_games"] += 1

    # Save the updated player stats back to the file
    try:
        player_file_path = check_data_directory_and_append_filename(player_file_name)
        with open(player_file_path, mode='w') as file:
            json.dump(player_stats, file, indent=4)
        print("Player Stats Updated!")
    except Exception as e:
        print(f"Error saving player stats: {e}")

def check_word_not_used_for_player(word, player_name):
    """
    Check if the player has already played the word.

    Args: word (str): The word to check, player_name (str): The player's name.

    Returns: bool: True if the player has not played the word.
    """
    # Load the game stats from the json file
    game_stats = load_statistics_from_json(file_name)
    # Check if the player has already played the word
    for stats in game_stats:
        if stats["player_name"] == player_name and stats["hangman_word"] == word:
            return False
    return True

def get_word(word_count, player_name):
    """
    Gets a random word from the wonderwords library.

    Args: word_count (int): The length of the word to get.

    Returns: word (str): The random word.
    """
    print("Getting Word...")
    word = RandomWord().word(word_min_length=(word_count), word_max_length=(word_count))
    # Check if the word has already been used by the player
    if check_word_not_used_for_player(word, player_name) == False:
        # Get a new word if the player has already played the word
        print("Word already used by player, getting new word...")
        get_word(word_count, player_name)
    # Return the word if it has not been used by the player or has repeat letters
    else:
        print("New Word Generated!")
        return word

def display_hangman_correct():
    """
    Displays the hangman word with the correct letters filled in.

    Args: None as it uses global variables.

    Returns: hidden_hangman (list): The hangman word with the correct letters filled in.
    """
    for i, letter in enumerate(hangman_list): # loops over the hangman list
        if letter in right_letters: # hangman letters in right letter list
            hidden_hangman[i] = letter
    return hidden_hangman

def calc_elapsed_time(start_time, end_time):
    """
    Calculates the time taken to complete the game.

    Args: end_time (datetime) - The end time of the game, start_time (datetime) - The start time of the game.

    Returns: ellapsed_time_seconds (float(round 2 places)): The time taken to complete the game in seconds.
    """
    elapsed_time = end_time - start_time
    elapsed_time_seconds = elapsed_time.total_seconds()
    return round(elapsed_time_seconds, 2)

def calc_score(name, loss, wrong_letters, hidden_hangman, hangman_word, elapsed_time):
    """
    calculates the score of the game based on: 
    # + points for correct letters guessed (per letter in hidden_hangman)
    # - points for wrong letters (per leeter in wrong_letters)
    # - points for time taken after grace period

    Args: 
        wrong_letters (list): list of wrong letters
        hidden_hangman (list): the hangman word with correct letters filled in
        hangman_word (str): the word to guess
        elapsed_time (float): the time taken to complete the game

    returns: list: dictionary of the score data, string: formatted score summary
    """


    grace_period = len(hangman_word) * grace_period_multiplier # grace period in seconds

    # if player is faster than grace period
    if round(elapsed_time) < grace_period: # round to an integer
        time_score = (grace_period - round(elapsed_time)) * time_points_multiplier
        time_string = f"\t+{time_score} pts for faster than grace period.\n"

    # if player is slower than grace period
    elif round(elapsed_time) > grace_period:
        time_score = -(round(elapsed_time) - grace_period) * time_points_multiplier
        time_string = f"\t{time_score} pts for slower than grace period.\n"

    # if player is average
    else:
        time_score = 0
        time_string = f"\t{time_score} pts for being an average guesser.\n"
    print(f"time_score: {time_score}\n Calculated by:\t(round time:{round(elapsed_time)} - {grace_period}) * 5")

    # BASIC CALCULATIONS
    correct_letters_score = (len(hidden_hangman) - hidden_hangman.count("_")) * correct_letters_multiplier # number of correct guessed letters calculated
    wrong_letters_score = len(wrong_letters) * wrong_letter_multiplier # number of wrong letters calculated

    # TOTAL SCORE TRACKING
    total_score = 0 # start with 0 points
    total_score += correct_letters_score # add correct letter score
    total_score -= wrong_letters_score # subtract wrong letter score
    total_score += time_score # add time score


    if loss == True:
        win = False
        finished = "Lost"
    else:
        total_score += win_multiplier
        win = True
        finished = "Won"

    score_summarised = (
                        f"YOU {finished}!\nHangman word was: {hangman_word.upper()}\n"
                        f"Score Summarised:\n"
                        f"{"#"*20}\n"
                        f"\t  0 pts baseline\n"
                        "Additional Scores:\n"
                        f"\t+ {correct_letters_score} pts (+{correct_letters_multiplier} pts per correct letter in '{hangman_word}')\n"
                        f"\t{('+ ' + str(win_multiplier) + ' pts for winning') if win else '0 pts for losing'}\n"
                        "Penalties:\n"
                        f"\t- {wrong_letters_score} pts (-{wrong_letter_multiplier} per wrong letters, \'{",".join(wrong_letters)}\')\n"
                        "Time Penalties/Bonuses:\n"
                        f"{time_string}"
                        "Total Score:\n"
                        f"\t= {total_score} pts\n"
                        f"{"#"*20}\n"
                        )
    return ({
        "player_name":name,
        "win_bool":win,
        "total_score":total_score, 
        "game_time":game_open_time,
        "hangman_word":hangman_word,
        "guessed_word":"".join(hidden_hangman),
        "word_difficulty": (lambda word_length: [key[1] for key, value in difficulty_word_length.items() if value == word_length][0])(word_length),
        "score_wrong_letters":wrong_letters_score,
        "total_wrong_letters":len(wrong_letters),
        "time_taken":elapsed_time,
        "score_time_taken":time_score
            }, score_summarised)

def select_difficulty():
    """
    Selects the difficulty of the game.

    Args: None

    Returns: diff_dict[difficulty] (int): The length of the word to guess.
    """
    # Display Difficulty
    clear_terminal()
    print("Select Difficulty:")
    print("-"*20)
    # Display Difficulty Options in a loop
    for key, value in difficulty_word_length.items():
        print(f"{key[0]} = {key[1]} ({value} Letters)")
    difficulty = input("Type Number:\n: ")
    # Check if the difficulty is in options and return the word length from the dictionary
    for key, value in difficulty_word_length.items():
        if difficulty == key[0]:
            print("You selected: ", key[1])
            return value
        
    print("You selected: ", difficulty)
    print("Invalid Selection, try again")
    select_difficulty()
    
def get_wrong_max():
    """
    Gets the maximum number of wrong guesses allowed.
    Easy Words: 1 more than the word length
    Normal Words: 1 less than the word length
    Hard Words: 4 less than the word length
    
    Args: None
    
    Returns: int: The maximum number of wrong guesses allowed.
    """
    if word_length == length_of_easy_word:
        return length_of_easy_word + 1
    elif word_length == length_of_normal_word:
        return length_of_normal_word - 1
    elif word_length == length_of_hard_word:
        return length_of_normal_word - 4

def get_player_name():
    """
    Gets the player's name.

    Args: None

    Returns: name (str): The player's name.
    """
    # Check if players name has been updated
    #=======================================
    player_name = input("\nEnter your name (longer than 3 characters): ")
    if len(player_name) < 3:
        print("Invalid Name, must be 3 or more characters")
        get_player_name()
    else:
        return player_name

def create_password():
    """
    Creates a password for the player.

    Args: None

    Returns: password (str): The player's password.
    """
    # Check if players password has been updated
    #=======================================
    special_chars = ["#", "=", "-"]
    password = getpass.getpass("\nEnter your password\n"
                     "Requirements:\n"
                    f"\t# {min_password_length} or more characters\n"
                    "\t# min 1 upper case\n"
                    "\t# min 1 lower case\n"
                    f"\t# 1 special character ({",".join(special_chars)})): ")
    if len(password) >= min_password_length:
        if any(char.isupper() for char in password):
            if any(char.islower() for char in password):
                if any(char in special_chars for char in password):
                    return password
                else:
                    print(f"Invalid Password, must have at least 1 special character ({",".join(special_chars)})")
                    create_password()
            else:
                print("Invalid Password, must have at least 1 lower case letter")
                create_password()
        else:
            print("Invalid Password, must have at least 1 upper case letter")
            create_password()
    else:
        print(f"Invalid Password, must be {min_password_length} or more characters")
        create_password()

def player_login(player_name):
    """
    Logs the player in.

    Args: player_name (str): The player's name.

    Returns: bool: True if the player is logged in.
    """
    player_stats = load_statistics_from_json(player_file_name)

    incorrect_password_count = 0
    while incorrect_password_count < incorrect_password_attempts:
        for stats in player_stats:
            if stats["player_name"] == player_name:
                # if no password set
                if stats["player_password"] == "":
                    return True
                # if password set
                if stats["player_password"] == hash_password_md5(getpass.getpass("Password: ")):
                    return True
                # if password incorrect
                else:
                    incorrect_password_count += 1
                    print(f"Incorrect Password, {incorrect_password_attempts - incorrect_password_count} attempts left")
    
    print("Too many incorrect password attempts, exiting")
    sys.exit()

def check_ready():
    """
    Checks if the player is ready to play the game.

    Args: None

    Returns: None
    """
    ready_check = input("Are you ready to play? \n(hit 'Enter/Return' to start or type 'exit'): ")
    if ready_check != "exit":
        clear_terminal()
    else:
        sys.exit()

def get_all_time_leaderboard():
    """
    Gets the all-time leaderboard.

    Args: None

    Returns: leaderboard (list): The all-time leaderboard.
    """
    player_stats = load_statistics_from_json(player_file_name)
    leaderboard = []
    for stats in player_stats:
        leaderboard.append({
            "player_name":stats["player_name"],
            "win_ratio":round((stats["total_wins"] / stats["total_games"]) * 100, 2),
            "total_score":stats["total_score"],
            "total_wins":stats["total_wins"],
            "total_games":stats["total_games"],
            "average_score":stats["average_score"],
            "average_time":stats["average_time"]
        })
    leaderboard = sorted(leaderboard, key=lambda x: x["total_score"], reverse=True)
    print("All Time Leaderboard:")
    print("-"*20)
    df = pd.DataFrame(leaderboard)

    print(df)

# Game Runtime Variables
#=======================================
# Welcome Message
print(f"{"="*20}\nWelcome to Hangman\n{"="*20}")
play_name = get_player_name()
# Check if player exists 
if check_player_exists(play_name) == False:
    print("Hi new player, lets build your profile")
    want_password = input("Do you want to set a password? (yes) or Enter to skip: ")

    if want_password.lower() == "yes":
        new_password = create_password()
        new_player = new_player_stats(play_name, new_password) # create new player stats with password
        save_statistics_to_json(player_file_name, new_player) # save new player stats to json

    else:
        new_player = new_player_stats(play_name, "") # create new player stats without password
        save_statistics_to_json(player_file_name, new_player)  # save new player stats to json

else:
    print("Welcome back, lets play!")
    player_login(play_name)

play_again = True
while play_again == True:
    # These start here to store time data when program first runs
    date_time_now = datetime.now()
    game_open_time = date_time_now.strftime("%d/%m/%y-%H:%M:%S")
    #=======================================
    # Global intergers
    #=======================================
    word_length = select_difficulty() # get word length
    check_ready() # pause before game starts
    hangman_word = get_word(word_length, play_name) # get random word
    wrong_max = get_wrong_max() # get max wrong guesses
    # Empty lists to store current game values
    right_letters = []
    wrong_letters = []
    # Lists of runtime Game Data
    hangman_list = [i for i in hangman_word]
    alphabet_list = list(string.ascii_lowercase) # list of all alphabet letters
    hidden_hangman = ["_" for _ in hangman_list] # list of "_" to represent hidden letters
    # Runtime Game booleans
    lost = False
    # Main Game Loop
    start_time = datetime.now() # start timer before main loop (JIC something hangs :/)
    #=======================================
    while True:
        # Check Win / Lose Conditions
        #=======================================     
        if "_" not in hidden_hangman: # WIN CONDITION
            clear_terminal()
            elapsed_time = calc_elapsed_time(start_time, datetime.now())
            break

        if len(wrong_letters) == wrong_max: # LOSE CONDITION
            clear_terminal()
            elapsed_time = calc_elapsed_time(start_time, datetime.now())
            lost = True
            break

        # Game Display Per Turn
        #=======================================
        # Game Display
        clear_terminal()
        print(f"Wrong letters so far: {", ".join(wrong_letters)}\nYou have {str(wrong_max - len(wrong_letters))} tries left.")
        print(f"Letters remaining: {alphabet_list}")
        print(f"Current Hangman: {display_hangman_correct()}")
        print(f"Current Game Time: {calc_elapsed_time(start_time, datetime.now())} seconds")
        print("="*20)
        # Debugging
        if show_word == True:
            print("Here is the word to guess: (for testing purposes)", hangman_word)
        # get user input, expected 1 letter or "exit"
        answer = input("\nType Hangman Letter:\n: ") 
        # answer processing
        #=======================================
        if len(answer) == 1:
            if answer in wrong_letters or answer in right_letters:
                clear_terminal()
                print("already tried, try again")
            elif answer in hangman_list:
                clear_terminal()
                right_letters.append(answer)
                alphabet_list.remove(answer)
                display_hangman_correct() 
            else:
                clear_terminal()
                wrong_letters.append(answer)
                alphabet_list.remove(answer)
        else:
            print("Invalid Input, try again")

    # End Game (print score and save to json)
    #=======================================
    # Save Score
    print("Saving Game Score...")
    game_stats = calc_score(play_name, lost, wrong_letters, hidden_hangman, hangman_word, elapsed_time)[0]
    save_statistics_to_json(file_name, game_stats)

    # Update Player Stats
    print("Updating Player Stats...")
    update_player_stats(play_name, game_stats)

    # Display score
    print(calc_score(play_name, lost, wrong_letters, hidden_hangman, hangman_word, elapsed_time)[1])

    # Display Leaderboard
    get_all_time_leaderboard()

    # Play Again
    #=======================================
    print("\n======================================")
    play_again = input("Play Again? (yes) or Enter to exit: ")
    if play_again.lower() == "yes":
        play_again = True
    else:
        play_again = False
        print("Goodbye!")
        sys.exit()



"""
Issues:
1. Time Score Calculation

Future Features:
3. Display player achievements
4. allow player to change password
5. allow player to delete account
6. allow player to reset stats
"""