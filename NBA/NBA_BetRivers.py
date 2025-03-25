import aiohttp
#Will only work if run arbScraper
from utils import UTC_to_ET

async def bet_rivers_NBA(all_games, semaphore, pipeline):
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