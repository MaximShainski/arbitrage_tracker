import aiohttp
#Will only work if run arbScraper
from utils import UTC_to_ET

#Asynchronously grabs all the NBA odds from FanDuel and adds it to the redis database
async def fan_duel_NBA(all_games, semaphore, pipeline):
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
        async with aiohttp.ClientSession() as session:
            async with session.get(
            'https://sbapi.nj.sportsbook.fanduel.com/api/content-managed-page?page=CUSTOM&customPageId=nba&pbHorizontal=false&_ak=FhMFpcPWXMeyZxOx&timezone=America%2FNew_York',
            headers=headers,
        ) as response:
                if response.status == 200:
                    data = await response.json()

                    team_counter = 0
                    for item in data["attachments"]["markets"].values(): #.values() iterates through all of the market IDs, need values because markets is not a list
                        if (item["marketType"] == "MONEY_LINE" and item["sgmMarket"] == True): #sgmMarket check is to avoid the esports money lines
                            for runner in item["runners"]: #These are all the teams
                                team_counter += 1
                                utc_time_str = item["marketTime"]
                                et_time_str = UTC_to_ET(utc_time_str, 0)
                                away_home = runner["result"]["type"]
                                if (away_home == "AWAY"):
                                    away = runner['runnerName'].split()[-1]
                                    away_odds = runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
                                else:
                                    home = runner['runnerName'].split()[-1]
                                    home_odds = runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
                                if (team_counter == 2):
                                    pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'FanDuel:{away}': int(away_odds)})
                                    pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'FanDuel:{home}': int(home_odds)})
                                    all_games.add(f'NBA:{away}_{home}:{et_time_str}')
                                    team_counter = 0
    