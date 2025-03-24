from curl_cffi import requests #curl_cffi is a wrapper around requests a more browser like TLS fingerprint \\
from rich import print #Makes print look nicer
import redis
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time
import math
import aiohttp
import asyncio
import redis.asyncio as async_redis
from bot_functions import test, send_odds
from bot_functions import app

#Limits the amount of concurrent tasks
semaphore = asyncio.Semaphore(5)
start_time = time.time()

#Things to use
#https://curlconverter.com/

all_games = set()


#Asynchronously grabs all the NBA odds from FanDuel and adds it to the redis database
async def fan_duel_NBA(r, pipeline):
    async with semaphore:
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

        

        async with aiohttp.ClientSession() as session:
            async with session.get(
            'https://sbapi.nj.sportsbook.fanduel.com/api/content-managed-page?page=CUSTOM&customPageId=nba&pbHorizontal=false&_ak=FhMFpcPWXMeyZxOx&timezone=America%2FNew_York',
            headers=headers,
        ) as response:
                if response.status == 200:
                    data = await response.json()

                    #print(response.json())
                    team_counter = 0
                    american_odds = []
                    for item in data["attachments"]["markets"].values(): #.values() iterates through all of the market IDs, need values because markets is not a list
                        if (item["marketType"] == "MONEY_LINE" and item["sgmMarket"] == True): #sgmMarket check is to avoid the esports money lines
                            for runner in item["runners"]: #These are all the teams
                                team_counter += 1
                                utc_time_str = item["marketTime"]
                                et_time_str = UTC_to_ET(utc_time_str, False)
                                away_home = runner["result"]["type"]
                                if (away_home == "AWAY"):
                                    away = runner['runnerName'].split()[-1]
                                    away_odds = runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
                                else:
                                    home = runner['runnerName'].split()[-1]
                                    home_odds = runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
                                if (team_counter == 2):
                                    #print(f'NBA:{away}_{home}:{et_time_str}')
                                    pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'FanDuel:{away}': int(away_odds)})
                                    pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'FanDuel:{home}': int(home_odds)})
                                    all_games.add(f'NBA:{away}_{home}:{et_time_str}')
                                    team_counter = 0
#Asynchronously grabs all the NBA odds from MGM and adds it to the redis database
async def MGM_NBA(r, pipeline):
    async with semaphore:
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

        async with aiohttp.ClientSession() as session:
            async with session.get(
            'https://sports.on.betmgm.ca/en/sports/api/widget/widgetdata?layoutSize=Small&page=CompetitionLobby&sportId=7&regionId=9&competitionId=6004&compoundCompetitionId=1:6004&widgetId=/mobilesports-v1.0/layout/layout_us/modules/basketball/nba/nba-gamelines-complobby&shouldIncludePayload=true',
            headers=headers,
        ) as response:
                if response.status == 200:
                    data = await response.json()
                    for item in data["widgets"][0]["payload"]["items"][0]["activeChildren"][0]["payload"]["fixtures"]: #Widgets[0] is where the bets are at, items only has one item in it, active children only has one item in it, values not needed as this is a list so it will iterate through, each fixture is a game
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
                                et_time_str = UTC_to_ET(utc_time_str, False)
                                for option in bet["options"]:
                                    team_name = option["name"]["value"].split()[-1] #Grabbing just the last word of the name (New York Knicks would turn into Knicks)
                                    american_odds = option["price"]["americanOdds"]
                                    pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'MGM:{team_name}': int(american_odds)})
                                    all_games.add(f'NBA:{away}_{home}:{et_time_str}')
                                    #print(f"Runner Name: {team_name}, American Odds: {american_odds}")

async def bet_rivers_NBA(pipeline):
    async with semaphore:
        cookies = {
        'uiThemeName': 'light',
        'language': 'ENG',
        'QuantumMetricUserID': '8bfce83569f515cd36420258fb314b5f',
        'mainViewType': 'SPORTSBOOK',
        '__cf_bm': 'DlSuZbgHpBvUMx.5bU6w0NiO7g6q5KETKC9jYeso.Z4-1742821979-1.0.1.1-pks_QIDBLVdcfBZSwtLlQwNrfbLblC4Chh2HFLfGAIXynTojkgLY0488RFxGQpZJGOmJbyvy4Le1cpci7YF5EHH_ixT27Z0r4XSDesqhjJM',
        'QuantumMetricSessionID': 'a332b438e4e3d4b016bc397ac22cdd68',
        '_dd_s': 'rum=2&id=98cc2679-1f93-494f-b0e1-e6bcd49c6df5&created=1742821979823&expire=1742823158085',
        }

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=1, i',
            'referer': 'https://on.betrivers.ca/?page=sportsbook&group=1000093652&type=matches',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            # 'cookie': 'uiThemeName=light; language=ENG; QuantumMetricUserID=8bfce83569f515cd36420258fb314b5f; mainViewType=SPORTSBOOK; __cf_bm=DlSuZbgHpBvUMx.5bU6w0NiO7g6q5KETKC9jYeso.Z4-1742821979-1.0.1.1-pks_QIDBLVdcfBZSwtLlQwNrfbLblC4Chh2HFLfGAIXynTojkgLY0488RFxGQpZJGOmJbyvy4Le1cpci7YF5EHH_ixT27Z0r4XSDesqhjJM; QuantumMetricSessionID=a332b438e4e3d4b016bc397ac22cdd68; _dd_s=rum=2&id=98cc2679-1f93-494f-b0e1-e6bcd49c6df5&created=1742821979823&expire=1742823158085',
        }

        params = {
            't': '20252241310',
            'cageCode': '249',
            'type': [
                'live',
                'prematch',
            ],
            'groupId': '1000093652',
            'pageNr': '1',
            'pageSize': '10',
            'offset': '0',
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://on.betrivers.ca/api/service/sportsbook/offering/listview/events',
                params=params,
                cookies=cookies,
                headers=headers,
            ) as response:
                # Read the response content
                data = await response.json()
                
                for game in data["items"]:
                    #This grabs the odds. Can be optimized if necessary by choosing specific indices rather than searching, but higher risk
                    teams = game["name"]
                    home = teams.split()[-1]
                    away_full = teams.split(" @ ")
                    away = away_full[0].split()[-1]
                    #Grab the game time and add 10 minutes, as other sites have time as 10 minutes after game starts
                    utc_time_str = game["start"]
                    et_time_str = UTC_to_ET(utc_time_str, True)
                    for offers in game["betOffers"]:
                        if offers["betDescription"].split()[0] == "Moneyline":
                            for bets in offers["outcomes"]:
                                team = bets["label"].split()[-1]
                                american_odds = bets["oddsAmerican"]
                                pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'BetRivers:{team}': int(american_odds)})
                                all_games.add(f'NBA:{away}_{home}:{et_time_str}')

#Converts utc time to ET time by converting UTC to string, then adding the info that the time is UTC, converting datetime object to ET time, then converting back to time
def UTC_to_ET(utc_time_str, add):
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
    if (add):
        utc_time = utc_time + timedelta(minutes=10)

    utc_time = utc_time.replace(tzinfo=ZoneInfo("UTC"))
    et_time = utc_time.astimezone(ZoneInfo("America/New_York"))
    et_time_str = et_time.strftime("%Y-%m-%dT%H:%M:%S")
    return et_time_str

async def calculate_best_odds(r):
    total_bet = 100 #Total amount of money willing to wager
    for game in all_games:
        best_pos_odds = await r.zrevrange(game, 0, 0, withscores=True) #Gets the highest positive odds, (returns a list of tuples, but in this case just one tuple in the list)
        if not best_pos_odds:  # Check if the list is empty
            continue #Maybe change to something else for now? Don't know what happens when there are no NBA games
        
        best_pos_member = best_pos_odds[0]
        best_pos_score = best_pos_member[1]  # Extract score
        pos_probability = (100/(best_pos_score + 100)) #Convert the money line odds to probability

        best_neg_odds = await r.zrangebyscore(game, -math.inf, 0, withscores=True) #Gets the best negative odds (closest to 0)
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
            print("arb found")
    await r.aclose()

async def create_async_redis_connection():
    r_async = await async_redis.from_url('redis://localhost')
    return r_async


async def main():
    #Set up the synchronous and asynchronous Redis connections
    r_async = await create_async_redis_connection()

    #Clear Redis database before scraping
    await r_async.flushall()

    #Create a pipeline for all redis operations
    pipeline = r_async.pipeline()

    #Scrape all the sites simultaneously
    await asyncio.gather(
        MGM_NBA(r_async, pipeline),
        fan_duel_NBA(r_async, pipeline),
        bet_rivers_NBA(pipeline)
    )
    print(all_games)

    # Execute all commands in the pipeline at once
    try:
        await pipeline.execute()
    except Exception as e:
        print(f"Error executing Redis pipeline: {e}")

    #Calculate the odds
    await calculate_best_odds(r_async)
    print("--- %s seconds ---" % (time.time() - start_time))
    #print(all_games)

    await send_odds(app, str(all_games))

if __name__ == "__main__":
    asyncio.run(main())