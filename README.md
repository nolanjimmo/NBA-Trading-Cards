# CS205 Final Project
### Trading Card Webserver Game

Charles Morgan, Nolan Jimmo, Dean Stuart, George Fafard

We have built a client-server system implementing a trading card platform based on the NBA and it's players.

Each user of the system can have up to 5 players on their "team" at any one time, and each of those spots can be made up by any player that the user chooses. No need for the players to be on the same team or even in the same conference.

By visiting the Flask-based website, you will be greeted with a sign-in/sign-up prompt. After signing in or signing up, the user can then "buy" players, see their current team, or trade with other users of the system. At this point in the software, we are assuming that users with communicate outside of this card system to decide who think the best players are, who they want to trade for, what lineup is best, etc. with the system mostly acting as a ledger and record that the users can manipulate and trust to hold a certain state after trades have been made or players bought/dropped.

We used Python and Flask (and html of course) as our main tools for builiding this app. Through the series of files in the repository you will be able to see the inner-working of our database connection and interation with our objiect-oriented Python logic, which is then visualized and displayed using Flask and all of it's wonderful features for creating webpages. 

Thank you for taking an interest in our project!
