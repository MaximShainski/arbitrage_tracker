from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import math
from rich import print #Makes print look nicer

#Converts utc time to ET time by converting UTC to string, then adding the info that the time is UTC, converting datetime object to ET time, then converting back to time
def UTC_to_ET(utc_time_str, add):
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
    if (add):
        utc_time = utc_time + timedelta(minutes=10)

    utc_time = utc_time.replace(tzinfo=ZoneInfo("UTC"))
    et_time = utc_time.astimezone(ZoneInfo("America/New_York"))
    #Reduced it to just hours, as sites are incosistent in their timings, including different formats in the same site
    et_time_str = et_time.strftime("%Y-%m-%dT%H")
    return et_time_str

async def calculate_best_odds(all_games, r_async, total_bet):
        for game in all_games:
            best_pos_odds = await r_async.zrevrange(game, 0, 0, withscores=True) #Gets the highest positive odds, (returns a list of tuples, but in this case just one tuple in the list)
            if not best_pos_odds:  # Check if the list is empty
                continue #Maybe change to something else for now? Don't know what happens when there are no NBA games
            
            best_pos_member = best_pos_odds[0]
            best_pos_score = best_pos_member[1]  # Extract score
            pos_probability = (100/(best_pos_score + 100)) #Convert the money line odds to probability

            best_neg_odds = await r_async.zrangebyscore(game, -math.inf, 0, withscores=True) #Gets the best negative odds (closest to 0)
            if not best_neg_odds:  # Check if the list is empty
                continue
            
            best_neg_member = best_neg_odds[-1]  # Get the highest negative odds
            best_neg_score = best_neg_member[1]  # Extract score
            neg_probability = abs(best_neg_score) / (abs(best_neg_score) + 100)  # Convert odds to probability

            print(best_pos_odds)
            print(best_neg_odds)
            print(best_neg_score)
            
            if(pos_probability + neg_probability < 1): #Checks for arbitrage
                total_probability = pos_probability + neg_probability
                pos_bet = (total_bet /pos_probability)/ total_probability #How much to bet on the positive odds
                neg_bet = (total_bet /neg_probability)/ total_probability #How much to bet on the negative odds
                
                print("arb found!!!!!!")
