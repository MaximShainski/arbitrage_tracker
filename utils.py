from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import math
from rich import print #Makes print look nicer

#Converts utc time to ET time by converting UTC to string, then adding the info that the time is UTC, converting datetime object to ET time, then converting back to time
def UTC_to_ET(utc_time_str, time_change):
    # List of possible formats, can replace with a hashmap later for efficiency
    time_formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]
    utc_time = ""
    for format_str in time_formats:
        try:
            # Try parsing with the current format
            utc_time = datetime.strptime(utc_time_str, format_str)
            # If successful, return the parsed time
            break
        except ValueError:
            # If the current format fails, continue with the next format
            continue
    utc_time = utc_time + timedelta(minutes=time_change)

    utc_time = utc_time.replace(tzinfo=ZoneInfo("UTC"))
    et_time = utc_time.astimezone(ZoneInfo("America/New_York"))
    #Reduced it to just hours, as sites are incosistent in their timings, including different formats in the same site
    et_time_str = et_time.strftime("%Y-%m-%dT%H")
    return et_time_str

def decimal_to_american(odds):
    if (int(odds) < 2):
        american_odds = round(-100/(odds - 1))
    else:
        american_odds = round((odds-1)*100)
    return american_odds

async def calculate_best_odds(all_games, r_async, total_bet):
        arbitrage_messages = []
        for game in all_games:
            best_pos_odds = await r_async.zrevrange(game, 0, 0, withscores=True) #Gets the highest positive odds, (returns a list of tuples, but in this case just one tuple in the list)
            if not best_pos_odds:  # Check if the list is empty
                continue #Maybe change to something else for now? Don't know what happens when there are no NBA games
            #print(game)
            
            best_pos_member = best_pos_odds[0]
            best_pos_score = best_pos_member[1]  # Extract score
            pos_probability = (100/(best_pos_score + 100)) #Convert the money line odds to probability

            best_neg_odds = await r_async.zrangebyscore(game, -math.inf, 0, withscores=True) #Gets the best negative odds (closest to 0)
            if not best_neg_odds:  # Check if the list is empty
                continue
            
            best_neg_member = best_neg_odds[-1]  # Get the highest negative odds
            best_neg_score = best_neg_member[1]  # Extract score
            neg_probability = abs(best_neg_score) / (abs(best_neg_score) + 100)  # Convert odds to probability

            #print(best_pos_odds)
            #print(best_neg_odds)
            #print(best_neg_score)

            #This checks if the current game is already live, avoiding sending it as an arbitrage as they are too risky
            game_date = game.split(':')[-1]
            if datetime.strptime(game_date, "%Y-%m-%dT%H") < datetime.now():
                continue
            

            #Need to check if greater than 0 as sometimes both odds are negative leading to a probability far below 0 but no arb
            if(0 < pos_probability + neg_probability < 1): #Checks for arbitrage
                #print(await r_async.zrevrange(game, 0, 0))
                #print(await r_async.zrangebyscore(game, -math.inf, 0))
                #Checks if the arb found is for the same team on different sites, happens often in live games where the same time has both positive and negative odds
                pos_team = best_pos_member[0].decode('utf-8').split(":")[-1]
                neg_team = best_neg_member[0].decode('utf-8').split(":")[-1]
                if (pos_team == neg_team):
                    continue
                total_probability = pos_probability + neg_probability
                #print(pos_probability)
                #print(neg_probability)
                pos_bet = (total_bet * pos_probability)/ total_probability #How much to bet on the positive odds
                neg_bet = (total_bet * neg_probability)/ total_probability #How much to bet on the negative odds

                pos_bet_site = (best_pos_odds[0][0].decode("utf-8").split(":")[0])
                neg_bet_site = (best_neg_odds[-1][0].decode("utf-8").split(":")[0])
                arbitrage_messages.append((f'{pos_team} vs {neg_team} - {pos_bet_site}: {round(pos_bet, 2)} on {pos_team} - {neg_bet_site}: {round(neg_bet, 2)} on {neg_team}'))
                
                print("arb found!!!!!!")
        return arbitrage_messages
        
        

