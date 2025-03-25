import aiohttp
#Will only work if run arbScraper
from utils import UTC_to_ET

#Asynchronously grabs all the NBA odds from MGM and adds it to the redis database
async def MGM_NBA(all_games, semaphore, pipeline):
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