Why:
This Hangman Game started of as a basic game but was developed further with additional features to test my skills.

How:
The hangman word is pulled using wonderwords library and the word length is set based on the difficulty chosen by the user.
The user is expected to create a profile to store all the cummalative game data and store each games results, the user can choose to set a password where the password is stored as a MD5 in a JSON.
Once the game is complete, the score is calculated based on:
  Word difficulty = points per letter in the word that was correct
  Negative points for using wrong letters
  bonus score for time taken to complete. 
    add points for within a set grace period, 
    sub points for over that grace period,
    sub points are capped if user goes over double the grace period
Finally, The game displays the currect game statistics and then a leaderboard to compare against other users.
    
  
