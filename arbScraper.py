from curl_cffi import requests #curl_cffi is a wrapper around requests a more browser like TLS fingerprint \\
from rich import print #Makes print look nicer
import redis
from datetime import datetime
from zoneinfo import ZoneInfo
import time
import math

start_time = time.time()

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

r.flushall()

#Things to use
#https://curlconverter.com/

all_games = set()

def fan_duel_NBA():
    headers = {
        'sec-ch-ua-platform': '"Windows"',
        'Referer': 'https://sportsbook.fanduel.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'x-px-context': '_px3=2d44d86567d9907c02316789ba42457d0480d20412d8ce44b8977e990f9995ee:IanvxagRKKugQLlyMvvQGJzYEH6+Vqx1YYRyCCXtX3JJzKqJoKfQK3/EWPgHPNrLGDTAboE26gNy0hppS/ii2w==:1000:kkCBBRavT6decwEZRciWF1LhCMYaot1e4HHAt1joEt++a5RGDHGId4pH32+w387QqpP/YVWNxV4+/eN6YB3CU5+dq4HBmBv4SlFaLZ4eLGehoRnsnGNvxQAuubiCq2Ei8/ngtCDYi0AwuKhADpJhnJgjSQAh/Ud02cKMi3IUDpADJNfR7fppF0q4VIXk50DXEikHwy74o4rFY1NxLnACDh0HFKdhjIelOrPuoBCmXX0=;_pxvid=3e505686-fd07-11ef-b2c8-3e20b48b6e71;pxcts=86dac6cc-fdd2-11ef-b678-18c3d5d892a6;',
        'sec-ch-ua-mobile': '?0',
    }

    params = {
        'page': 'CUSTOM',
        'customPageId': 'nba',
        'pbHorizontal': 'false',
        '_ak': 'FhMFpcPWXMeyZxOx',
        'timezone': 'America/New_York',
    }

    response = requests.get('https://sbapi.nj.sportsbook.fanduel.com/api/content-managed-page?page=CUSTOM&customPageId=nba&pbHorizontal=false&_ak=FhMFpcPWXMeyZxOx&timezone=America%2FNew_York', params=params, headers=headers)

    #print(response.json())
    team_counter = 0
    american_odds = []
    for item in response.json()["attachments"]["markets"].values(): #.values() iterates through all of the market IDs, need values because markets is not a list
        if (item["marketType"] == "MONEY_LINE" and item["sgmMarket"] == True): #sgmMarket check is to avoid the esports money lines
            for runner in item["runners"]: #These are all the teams
                team_counter += 1
                utc_time_str = item["marketTime"]
                et_time_str = UTC_to_ET(utc_time_str)
                away_home = runner["result"]["type"]
                if (away_home == "AWAY"):
                    away = runner['runnerName'].split()[-1]
                    away_odds = runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
                else:
                    home = runner['runnerName'].split()[-1]
                    home_odds = runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
                if (team_counter == 2):
                    #print(f'NBA:{away}_{home}:{et_time_str}')
                    r.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'FanDuel:{away}': int(away_odds)})
                    r.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'FanDuel:{home}': int(home_odds)})
                    all_games.add(f'NBA:{away}_{home}:{et_time_str}')
                    team_counter = 0
def MGM_NBA():
    headers = {
    'sec-ch-ua-platform': '"Windows"',
    'x-bwin-sports-api': 'prod',
    'Referer': 'https://sports.on.betmgm.ca/en/sports/basketball-7/betting/usa-9/nba-6004',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'x-bwin-browser-url': 'https://sports.on.betmgm.ca/en/sports/basketball-7/betting/usa-9/nba-6004',
    'sec-ch-ua-mobile': '?0',
    'X-From-Product': 'sports',
    'X-Device-Type': 'desktop',
    'Sports-Api-Version': 'SportsAPIv2',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    }

    response = requests.get(
        'https://sports.on.betmgm.ca/en/sports/api/widget/widgetdata?layoutSize=Small&page=CompetitionLobby&sportId=7&regionId=9&competitionId=6004&compoundCompetitionId=1:6004&widgetId=/mobilesports-v1.0/layout/layout_us/modules/basketball/nba/nba-gamelines-complobby&shouldIncludePayload=true',
        headers=headers,
    )
    for item in response.json()["widgets"][0]["payload"]["items"][0]["activeChildren"][0]["payload"]["fixtures"]: #Widgets[0] is where the bets are at, items only has one item in it, active children only has one item in it, values not needed as this is a list so it will iterate through, each fixture is a game
        #Tries to get the away and home team using the name, value json format
        if (item.get("name", {}).get("value")):
            home = item["name"]["value"].split()[-1]
            away_full = item["name"]["value"].split(" at ")
            away = away_full[0].split()[-1]
        #If not found, use the original way that grabs it from the participants (added previous way as sometimes participants didn't have this information)
        else:
            for team in item["participants"]:
                if team.get("properties", {}).get("type") == "AwayTeam": #.get is used to safely check if properties exists, returns a dictionary so can use .get again
                    away = team["name"]["value"].split()[-1] #Getting the last part of the team name
                elif team.get("properties", {}).get("type") == "HomeTeam":
                    home = team["name"]["value"].split()[-1] #Getting the last part of the team name
        for bet in item["optionMarkets"]:
            if (bet["name"]["value"] == "Money Line"):
                utc_time_str = item["startDate"]
                et_time_str = UTC_to_ET(utc_time_str)
                for option in bet["options"]:
                    team_name = option["name"]["value"].split()[-1] #Grabbing just the last word of the name (New York Knicks would turn into Knicks)
                    american_odds = option["price"]["americanOdds"]
                    r.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'MGM:{team_name}': int(american_odds)})
                    all_games.add(f'NBA:{away}_{home}:{et_time_str}')
                    #print(f"Runner Name: {team_name}, American Odds: {american_odds}")
#Converts utc time to ET time by converting UTC to string, then adding the info that the time is UTC, converting datetime object to ET time, then converting back to time
def UTC_to_ET(utc_time_str):
    # List of possible formats
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

    utc_time = utc_time.replace(tzinfo=ZoneInfo("UTC"))
    et_time = utc_time.astimezone(ZoneInfo("America/New_York"))
    et_time_str = et_time.strftime("%Y-%m-%dT%H:%M:%S")
    return et_time_str

def calculate_best_odds():
    total_bet = 100 #Total amount of money willing to wager
    for game in all_games:
        best_pos_odds = r.zrevrange(game, 0, 0, withscores=True) #Gets the highest positive odds, (returns a list of tuples, but in this case just one tuple in the list)
        if not best_pos_odds:  # Check if the list is empty
            continue #Maybe change to something else for now? Don't know what happens when there are no NBA games
        
        best_pos_member = best_pos_odds[0]
        best_pos_score = best_pos_member[1]  # Extract score
        pos_probability = (100/(best_pos_score + 100)) #Convert the money line odds to probability

        best_neg_odds = r.zrangebyscore(game, -math.inf, 0, withscores=True) #Gets the best negative odds (closest to 0)
        if not best_neg_odds:  # Check if the list is empty
            continue
        
        best_neg_member = best_neg_odds[-1]  # Get the highest negative odds
        best_neg_score = best_neg_member[1]  # Extract score
        neg_probability = abs(best_neg_score) / (abs(best_neg_score) + 100)  # Convert odds to probability
        #print(best_pos_odds)
        print(best_neg_odds)
        print(best_neg_score)
        if(pos_probability + neg_probability < 1): #Checks for arbitrage
            total_probability = pos_probability + neg_probability
            pos_bet = (total_bet /pos_probability)/ total_probability #How much to bet on the positive odds
            neg_bet = (total_bet /neg_probability)/ total_probability #How much to bet on the negative odds
            print("hello")
fan_duel_NBA()
MGM_NBA()
calculate_best_odds()
print("--- %s seconds ---" % (time.time() - start_time))