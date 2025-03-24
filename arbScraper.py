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
async def draft_kings_NBA(pipeline):
    cookies = {
    '_csrf': '1879cb3b-764e-429c-a01e-cb971df5d4d0',
    'hgg': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2aWQiOiI1NzgzNDU2NjE3NSIsImRrZS0xMjYiOiIzNzQiLCJka2UtMjA0IjoiNzEwIiwiZGtlLTI4OCI6IjExMjgiLCJka2UtMzE4IjoiMTI2MCIsImRrZS0zNDUiOiIxMzUzIiwiZGtlLTM0NiI6IjEzNTYiLCJka2UtNDI5IjoiMTcwNSIsImRrZS03MDAiOiIyOTkyIiwiZGtlLTczOSI6IjMxNDAiLCJka2UtNzU3IjoiMzIxMiIsImRrZS04MDYiOiIzNDI1IiwiZGtlLTgwNyI6IjM0MzciLCJka2UtODI0IjoiMzUxMSIsImRrZS04MjUiOiIzNTE0IiwiZGtlLTgzNiI6IjM1NzAiLCJka2gtODk1IjoiOGVTdlpEbzAiLCJka2UtODk1IjoiMCIsImRrZS05MDMiOiIzODQ4IiwiZGtlLTkxNyI6IjM5MTMiLCJka2UtOTQ3IjoiNDA0MiIsImRrZS05NzYiOiI0MTcxIiwiZGtoLTE2NDEiOiJSMGtfbG1rRyIsImRrZS0xNjQxIjoiMCIsImRrZS0xNjUzIjoiNzEzMSIsImRrZS0xNjg2IjoiNzI3MSIsImRrZS0xNjg5IjoiNzI4NyIsImRrZS0xNzU0IjoiNzYwNSIsImRrZS0xNzYwIjoiNzY0OSIsImRrZS0xNzc0IjoiNzcxMCIsImRrZS0xNzgwIjoiNzczMCIsImRrZS0xNzk0IjoiNzgwMSIsImRraC0xODA1IjoiT0drYmxrSHgiLCJka2UtMTgwNSI6IjAiLCJka2UtMTgyOCI6Ijc5NTYiLCJka2UtMTg2MSI6IjgxNTciLCJka2UtMTg2OCI6IjgxODgiLCJka2UtMTg4MyI6IjgyNDIiLCJka2UtMTg5OCI6IjgzMTQiLCJka2UtMTkxMCI6IjgzNjMiLCJka2gtMTk0OSI6IlhKQ3NKb2JkIiwiZGtlLTE5NDkiOiIwIiwiZGtoLTE5NTAiOiJEWGNqRmJWSiIsImRrZS0xOTUwIjoiMCIsImRrZS0xOTUyIjoiODUxNCIsImRrZS0xOTY3IjoiODU3NiIsImRrZS0xOTk2IjoiODc0OSIsImRrZS0yMDYyIjoiOTA0OCIsImRrZS0yMDg3IjoiOTE2MiIsImRrZS0yMDk3IjoiOTIwNSIsImRrZS0yMTAwIjoiOTIyMyIsImRrZS0yMTAzIjoiOTI0MSIsImRraC0yMTI3IjoiTURFUUhOYTQiLCJka2UtMjEyNyI6IjAiLCJka2UtMjEzNSI6IjkzOTMiLCJka2UtMjEzOCI6Ijk0MjAiLCJka2UtMjE0MSI6Ijk0MzUiLCJka2UtMjE0MyI6Ijk0NDIiLCJka2gtMjE1MCI6Ik5rYmFTRjhmIiwiZGtlLTIxNTAiOiIwIiwiZGtlLTIxNTMiOiI5NDc1IiwiZGtlLTIxNjAiOiI5NTA5IiwiZGtlLTIxNjEiOiI5NTE1IiwiZGtlLTIxNjUiOiI5NTM1IiwiZGtlLTIxNjkiOiI5NTUzIiwiZGtlLTIxNzQiOiI5NTcyIiwiZGtlLTIxODciOiI5NjI0IiwiZGtlLTIxODkiOiI5NjQxIiwiZGtlLTIxOTIiOiI5NjUyIiwiZGtlLTIxOTUiOiI5NjY1IiwiZGtlLTIyMDAiOiI5NjgzIiwiZGtlLTIyMDciOiI5NzA5IiwiZGtlLTIyMTEiOiI5NzI3IiwiZGtlLTIyMTYiOiI5NzQ0IiwiZGtlLTIyMTciOiI5NzUxIiwiZGtlLTIyMjAiOiI5NzY5IiwiZGtlLTIyMjIiOiI5Nzc1IiwiZGtlLTIyMjMiOiI5NzgwIiwiZGtoLTIyMjQiOiJyMEVDTGh3cyIsImRrZS0yMjI0IjoiMCIsImRraC0yMjI2IjoiS2VkTXJtRk8iLCJka2UtMjIyNiI6IjAiLCJka2UtMjIzNiI6Ijk4MjYiLCJka2UtMjIzNyI6Ijk4MzQiLCJka2UtMjIzOCI6Ijk4MzciLCJka2UtMjI0MCI6Ijk4NTciLCJka2UtMjI0MSI6Ijk4NjQiLCJka2UtMjI0MyI6Ijk4NzMiLCJka2UtMjI0NCI6Ijk4NzgiLCJka2UtMjI0NiI6Ijk4ODciLCJka2UtMjI1NSI6Ijk5MjciLCJka2gtMjI1OCI6IlF3UFpPS1U2IiwiZGtlLTIyNTgiOiIwIiwiZGtoLTIyNTkiOiJvMWhKc3VnUyIsImRrZS0yMjU5IjoiMCIsImRrZS0yMjY0IjoiOTk3MCIsImRrZS0yMjY5IjoiOTk4OSIsImRrZS0yMjcwIjoiOTk5MiIsImRrZS0yMjc0IjoiMTAwMTAiLCJka2UtMjI3NyI6IjEwMDE5IiwiZGtlLTIyNzkiOiIxMDAzMyIsImRrZS0yMjgwIjoiMTAwMzUiLCJka2UtMjI4MSI6IjEwMDQzIiwiZGtlLTIyODgiOiIxMDA5MiIsImRrZS0yMjg5IjoiMTAwOTciLCJka2UtMjI5MSI6IjEwMTAyIiwiZGtoLTIyOTIiOiJNbHdDUVFVTSIsImRrZS0yMjkyIjoiMCIsImRraC0yMjkzIjoiT2xsbmowQlMiLCJka2UtMjI5MyI6IjAiLCJka2gtMjI5NCI6IjFEUEtEaW94IiwiZGtlLTIyOTQiOiIwIiwiZGtlLTIyOTUiOiIxMDEzMSIsImRrZS0yMjk3IjoiMTAxNDciLCJka2UtMjI5OCI6IjEwMTU0IiwiZGtlLTIzMDAiOiIxMDE3NSIsImRraC0yMzAyIjoiOWhKOHZLeTYiLCJka2UtMjMwMiI6IjAiLCJka2UtMjMwMyI6IjEwMjAwIiwiZGtlLTIzMDQiOiIxMDIwMyIsImRrZS0yMzA1IjoiMTAyMDkiLCJka2UtMjMwOSI6IjEwMjQzIiwiZGtoLTIzMTAiOiJ4WUkxeUxKaCIsImRrZS0yMzEwIjoiMCIsImRraC0yMzExIjoieEN6bUtVOEoiLCJka2UtMjMxMSI6IjAiLCJka2gtMjMxMiI6IlJKQTQ4RHYzIiwiZGtlLTIzMTIiOiIwIiwiZGtoLTIzMTQiOiJKX2pFX3VoLSIsImRrZS0yMzE0IjoiMCIsImRrZS0yMzE1IjoiMTAyNjgiLCJuYmYiOjE3NDI4NDA0NjksImV4cCI6MTc0Mjg0MDc2OSwiaWF0IjoxNzQyODQwNDY5LCJpc3MiOiJkayJ9.qn8M3BKUxkXYA6zuxbwu2g8l5idhYmFP-WN-qGfXyeQ',
    'STIDN': 'eyJDIjoxMjIzNTQ4NTIzLCJTIjo4ODAyMTA4MTAwOSwiU1MiOjkxOTYzMjMxNTA2LCJWIjo1NzgzNDU2NjE3NSwiTCI6MSwiRSI6IjIwMjUtMDMtMjRUMTg6NTE6MDkuMDgyNDA0NFoiLCJTRSI6IkNBLURLIiwiVUEiOiJ5ZGlRUWp2ZGoyY3BKcWJrYS9OaHczcjhpaDNvc0IxNzZSQ1JYbWtkaGNrPSIsIkRLIjoiY2YzNWRiMTMtOWFiZi00ZDg5LTk4Y2MtMGMyMjNhN2Y1NGI2IiwiREkiOiI2NzNhZDRhZC0zOWU5LTQ1MzctOWUxZC1jNzY3OTNiYTQxNjMiLCJERCI6NTczMzgxOTYzMDN9',
    'STH': '4137e044d34fdb3b9767ac52daa554ce55941326aedc0a9cb5c42a13f354a360',
    'ak_bmsc': 'E20A9035D0FE2965AC0304816120981C~000000000000000000000000000000~YAAQNMIcuKZajLCVAQAAxxdjyRvfcpezIrr2FOXz+Ij6JluR9P61DzGuvjrPKH03zTQ9+7mYQXtko4t8nQZVx8HZ4Xh2tdTi7JsK6A8JOFzyfMYb1O94d5VUziOgxWtaPqZjCvHK5h57w0NOpbWpSLhbIVrqR/YBq+kr5Ox9BoZJKqW8jJbHF43Tp2AlBd2G9cKwjHe7KzWjduR/Dk4DmVbUGPjK4HfU7jWfl/x34gIN+itNREnihjzWAZEh+EH/R95Jo7YX4pPTrndrkWMj3tcw56CdbVqZSXlrjXvtNhDeVyInWhiS43LWzZm6OoGzjkp/RhRrTLQ8NhE6whZjNzHz+gICKTyTgaw2DSiTJwzc3JQ4Gbkp9/jP6bhQrXuOVh4/zvCa5gzGkpQUdF/ma/vc0uY=',
    '_gcl_au': '1.1.608944585.1742840470',
    '_gid': 'GA1.2.371290566.1742840472',
    '_gat_UA-28146424-9': '1',
    '_gat_UA-28146424-14': '1',
    '_dpm_ses.16f4': '*',
    'ab.storage.deviceId.b543cb99-2762-451f-9b3e-91b2b1538a42': '%7B%22g%22%3A%2265d3b7de-ecee-1bb4-1424-f53a7c2ff909%22%2C%22c%22%3A1742840471733%2C%22l%22%3A1742840471733%7D',
    '_ga': 'GA1.2.1347696125.1742840472',
    '_scid': 'BKjCgo3j4SJVUtOVaAZ9GD69jg9ThFaN',
    '__ssid': '0f1ab059b1b0400237c066030150700',
    '_ga_M8T3LWXCC5': 'GS1.2.1742840473.1.1.1742840473.60.0.0',
    '_hjSessionUser_2150570': 'eyJpZCI6IjUxMTI4MmU2LWFjMDMtNTEyZC05ZTlkLTdjMjk2N2M2MDYwNCIsImNyZWF0ZWQiOjE3NDI4NDA0NzQwNzgsImV4aXN0aW5nIjpmYWxzZX0=',
    '_hjSession_2150570': 'eyJpZCI6ImIyNDExMjAyLTNjZmYtNDgxOS05NmY0LWFlNDYzMTBmZmY1YiIsImMiOjE3NDI4NDA0NzQwODMsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=',
    '_uetsid': 'c5321f4008dc11f0b227a1e967ff766c',
    '_uetvid': 'c53235d008dc11f083aaf7076d2376ab',
    '_abck': '214D91E4FD2D309290EDF1928DEB7D20~0~YAAQ7xghF0eAeaqVAQAABC5jyQ0K7A3KE+IDLiXFXsAw+lduXjUjdtKQBoVhTFzRuAJLPy25ESMOGHvIkJ2xM3z0FDHLgyzJcN814KQi9fm3u6ssa5szTEUee40Ws9dQLtD/LssitbQ6JRPl2aoLmNBQyY7eXu7/kGR8soYI4KMgk2Xho9Atidg3T+J1BXAIFjHe3d6O7OyNfZjPBDN8airyWRbV9pmAj8oZE7dfio9c2DuFZphzzXfPpS4+q9FzpyS7Fc1/4GsydOXdYtvFT07Undt5VSDmvUtxyczz+pZpcZCG9K63DKpTfXtQw29U+0WdKtQmmyvSfcXKz2noqYSUGnipAtzffSORzsg1rKdCNOHeTaRszD5JDAoKTTd58HFANoXScVdpBRnhJMhzRoYMsZ/vWHhdD51NUQeQF2wgXxWp/zeyDvTPrtGXk4gASOhUQD6dadmsy1WW4aGQcThGeIrFUEuzp2fV47/hgNRFZHjnxnm939y9rxDWusgQWZyo7ghxaigvWqjJBd9p/2qbFBj/D2ba2IGDPQFykzI=~-1~||0||~-1',
    '_sctr': '1%7C1742788800000',
    'bm_sz': '0634BCE2ECF48FFAFCF681ECFE3608F8~YAAQ7xghF4iEeaqVAQAAL0xjyRv6JdqyEh0YiNdVu5jVOnA8tphYgPAteXeuu3jyxWiU0bNbR8U0Bihjg3af0jpbGyHH7ZzfNv+dQRJuGbVcYI39Uwxn4F12hmoTc3K7mSFcozt98aKLU4JwePqZwlRUH2Rux8lCd/sHBZb4lPtvwN7qDm83MA95bz+YJXTMqYAckbXKFLcvcDB6xYRw5bjTTPSHQ/c/bNppAZ8Wi4a6GAHGxXypIajbO163MNx4R5X3Am1aaWPwUEYBSSQhzR/dZYkh3RS+AP26Awun9eQLfh1IqpT9QxohvExkF9ZVeCKVD75ckGitcczugS/8A8kZJ/BeDiyBW82bGSCYI1C3QZvDhj6p6mmWSyvLekRKj2T/Y1gaNcPUHOq764bkqck3P97xkRTxmy6qPlw=~3618104~4470073',
    '_ga_QG8WHJSQMJ': 'GS1.1.1742840471.1.1.1742840483.47.0.0',
    '_rdt_uuid': '1742840471657.8c46091b-8982-4af0-b379-f7bcb5ddca10',
    '_dpm_id.16f4': '795303ca-e973-4314-8445-fb366243e6c7.1742840472.1.1742840484.1742840472.98ebfdff-a129-4c36-b17e-accebc6119c1',
    '_scid_r': 'HSjCgo3j4SJVUtOVaAZ9GD69jg9ThFaNI_6KVw',
    'ab.storage.sessionId.b543cb99-2762-451f-9b3e-91b2b1538a42': '%7B%22g%22%3A%222e7c1c16-9c3b-1965-d9f5-a8d75360a42d%22%2C%22e%22%3A1742842284592%2C%22c%22%3A1742840471728%2C%22l%22%3A1742840484592%7D',
    'STE': '"2025-03-24T18:51:24.8641552Z"',
    'bm_sv': '6DE1B01E7686294B02092171AE2174B2~YAAQ5hghF5AJNcOVAQAAFVRjyRtcZZjsjS+u7y5lFbW585ITscESFfUOjR6u2CDGQZncyP1cFDcxR+5MwOVUgQPsaiS16lpIXh3dluhFkj4ue1lMLVy9L2IPc/OmaOdHnfJuIm/cgDbQOmPzYNZE1boh5jXOc+GiI+nZHzFlIVaXQJBHWF7YJJqkYiLU/PFdWtQWI2uoznYrZJDVo2UG36Ycme8SAXgCiKKkXFMHhmatxaCMk+heAqanlqpoc7H9s7GvAR0=~1',
    }

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://sportsbook.draftkings.com',
        'priority': 'u=1, i',
        'referer': 'https://sportsbook.draftkings.com/',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        # 'cookie': '_csrf=1879cb3b-764e-429c-a01e-cb971df5d4d0; hgg=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2aWQiOiI1NzgzNDU2NjE3NSIsImRrZS0xMjYiOiIzNzQiLCJka2UtMjA0IjoiNzEwIiwiZGtlLTI4OCI6IjExMjgiLCJka2UtMzE4IjoiMTI2MCIsImRrZS0zNDUiOiIxMzUzIiwiZGtlLTM0NiI6IjEzNTYiLCJka2UtNDI5IjoiMTcwNSIsImRrZS03MDAiOiIyOTkyIiwiZGtlLTczOSI6IjMxNDAiLCJka2UtNzU3IjoiMzIxMiIsImRrZS04MDYiOiIzNDI1IiwiZGtlLTgwNyI6IjM0MzciLCJka2UtODI0IjoiMzUxMSIsImRrZS04MjUiOiIzNTE0IiwiZGtlLTgzNiI6IjM1NzAiLCJka2gtODk1IjoiOGVTdlpEbzAiLCJka2UtODk1IjoiMCIsImRrZS05MDMiOiIzODQ4IiwiZGtlLTkxNyI6IjM5MTMiLCJka2UtOTQ3IjoiNDA0MiIsImRrZS05NzYiOiI0MTcxIiwiZGtoLTE2NDEiOiJSMGtfbG1rRyIsImRrZS0xNjQxIjoiMCIsImRrZS0xNjUzIjoiNzEzMSIsImRrZS0xNjg2IjoiNzI3MSIsImRrZS0xNjg5IjoiNzI4NyIsImRrZS0xNzU0IjoiNzYwNSIsImRrZS0xNzYwIjoiNzY0OSIsImRrZS0xNzc0IjoiNzcxMCIsImRrZS0xNzgwIjoiNzczMCIsImRrZS0xNzk0IjoiNzgwMSIsImRraC0xODA1IjoiT0drYmxrSHgiLCJka2UtMTgwNSI6IjAiLCJka2UtMTgyOCI6Ijc5NTYiLCJka2UtMTg2MSI6IjgxNTciLCJka2UtMTg2OCI6IjgxODgiLCJka2UtMTg4MyI6IjgyNDIiLCJka2UtMTg5OCI6IjgzMTQiLCJka2UtMTkxMCI6IjgzNjMiLCJka2gtMTk0OSI6IlhKQ3NKb2JkIiwiZGtlLTE5NDkiOiIwIiwiZGtoLTE5NTAiOiJEWGNqRmJWSiIsImRrZS0xOTUwIjoiMCIsImRrZS0xOTUyIjoiODUxNCIsImRrZS0xOTY3IjoiODU3NiIsImRrZS0xOTk2IjoiODc0OSIsImRrZS0yMDYyIjoiOTA0OCIsImRrZS0yMDg3IjoiOTE2MiIsImRrZS0yMDk3IjoiOTIwNSIsImRrZS0yMTAwIjoiOTIyMyIsImRrZS0yMTAzIjoiOTI0MSIsImRraC0yMTI3IjoiTURFUUhOYTQiLCJka2UtMjEyNyI6IjAiLCJka2UtMjEzNSI6IjkzOTMiLCJka2UtMjEzOCI6Ijk0MjAiLCJka2UtMjE0MSI6Ijk0MzUiLCJka2UtMjE0MyI6Ijk0NDIiLCJka2gtMjE1MCI6Ik5rYmFTRjhmIiwiZGtlLTIxNTAiOiIwIiwiZGtlLTIxNTMiOiI5NDc1IiwiZGtlLTIxNjAiOiI5NTA5IiwiZGtlLTIxNjEiOiI5NTE1IiwiZGtlLTIxNjUiOiI5NTM1IiwiZGtlLTIxNjkiOiI5NTUzIiwiZGtlLTIxNzQiOiI5NTcyIiwiZGtlLTIxODciOiI5NjI0IiwiZGtlLTIxODkiOiI5NjQxIiwiZGtlLTIxOTIiOiI5NjUyIiwiZGtlLTIxOTUiOiI5NjY1IiwiZGtlLTIyMDAiOiI5NjgzIiwiZGtlLTIyMDciOiI5NzA5IiwiZGtlLTIyMTEiOiI5NzI3IiwiZGtlLTIyMTYiOiI5NzQ0IiwiZGtlLTIyMTciOiI5NzUxIiwiZGtlLTIyMjAiOiI5NzY5IiwiZGtlLTIyMjIiOiI5Nzc1IiwiZGtlLTIyMjMiOiI5NzgwIiwiZGtoLTIyMjQiOiJyMEVDTGh3cyIsImRrZS0yMjI0IjoiMCIsImRraC0yMjI2IjoiS2VkTXJtRk8iLCJka2UtMjIyNiI6IjAiLCJka2UtMjIzNiI6Ijk4MjYiLCJka2UtMjIzNyI6Ijk4MzQiLCJka2UtMjIzOCI6Ijk4MzciLCJka2UtMjI0MCI6Ijk4NTciLCJka2UtMjI0MSI6Ijk4NjQiLCJka2UtMjI0MyI6Ijk4NzMiLCJka2UtMjI0NCI6Ijk4NzgiLCJka2UtMjI0NiI6Ijk4ODciLCJka2UtMjI1NSI6Ijk5MjciLCJka2gtMjI1OCI6IlF3UFpPS1U2IiwiZGtlLTIyNTgiOiIwIiwiZGtoLTIyNTkiOiJvMWhKc3VnUyIsImRrZS0yMjU5IjoiMCIsImRrZS0yMjY0IjoiOTk3MCIsImRrZS0yMjY5IjoiOTk4OSIsImRrZS0yMjcwIjoiOTk5MiIsImRrZS0yMjc0IjoiMTAwMTAiLCJka2UtMjI3NyI6IjEwMDE5IiwiZGtlLTIyNzkiOiIxMDAzMyIsImRrZS0yMjgwIjoiMTAwMzUiLCJka2UtMjI4MSI6IjEwMDQzIiwiZGtlLTIyODgiOiIxMDA5MiIsImRrZS0yMjg5IjoiMTAwOTciLCJka2UtMjI5MSI6IjEwMTAyIiwiZGtoLTIyOTIiOiJNbHdDUVFVTSIsImRrZS0yMjkyIjoiMCIsImRraC0yMjkzIjoiT2xsbmowQlMiLCJka2UtMjI5MyI6IjAiLCJka2gtMjI5NCI6IjFEUEtEaW94IiwiZGtlLTIyOTQiOiIwIiwiZGtlLTIyOTUiOiIxMDEzMSIsImRrZS0yMjk3IjoiMTAxNDciLCJka2UtMjI5OCI6IjEwMTU0IiwiZGtlLTIzMDAiOiIxMDE3NSIsImRraC0yMzAyIjoiOWhKOHZLeTYiLCJka2UtMjMwMiI6IjAiLCJka2UtMjMwMyI6IjEwMjAwIiwiZGtlLTIzMDQiOiIxMDIwMyIsImRrZS0yMzA1IjoiMTAyMDkiLCJka2UtMjMwOSI6IjEwMjQzIiwiZGtoLTIzMTAiOiJ4WUkxeUxKaCIsImRrZS0yMzEwIjoiMCIsImRraC0yMzExIjoieEN6bUtVOEoiLCJka2UtMjMxMSI6IjAiLCJka2gtMjMxMiI6IlJKQTQ4RHYzIiwiZGtlLTIzMTIiOiIwIiwiZGtoLTIzMTQiOiJKX2pFX3VoLSIsImRrZS0yMzE0IjoiMCIsImRrZS0yMzE1IjoiMTAyNjgiLCJuYmYiOjE3NDI4NDA0NjksImV4cCI6MTc0Mjg0MDc2OSwiaWF0IjoxNzQyODQwNDY5LCJpc3MiOiJkayJ9.qn8M3BKUxkXYA6zuxbwu2g8l5idhYmFP-WN-qGfXyeQ; STIDN=eyJDIjoxMjIzNTQ4NTIzLCJTIjo4ODAyMTA4MTAwOSwiU1MiOjkxOTYzMjMxNTA2LCJWIjo1NzgzNDU2NjE3NSwiTCI6MSwiRSI6IjIwMjUtMDMtMjRUMTg6NTE6MDkuMDgyNDA0NFoiLCJTRSI6IkNBLURLIiwiVUEiOiJ5ZGlRUWp2ZGoyY3BKcWJrYS9OaHczcjhpaDNvc0IxNzZSQ1JYbWtkaGNrPSIsIkRLIjoiY2YzNWRiMTMtOWFiZi00ZDg5LTk4Y2MtMGMyMjNhN2Y1NGI2IiwiREkiOiI2NzNhZDRhZC0zOWU5LTQ1MzctOWUxZC1jNzY3OTNiYTQxNjMiLCJERCI6NTczMzgxOTYzMDN9; STH=4137e044d34fdb3b9767ac52daa554ce55941326aedc0a9cb5c42a13f354a360; ak_bmsc=E20A9035D0FE2965AC0304816120981C~000000000000000000000000000000~YAAQNMIcuKZajLCVAQAAxxdjyRvfcpezIrr2FOXz+Ij6JluR9P61DzGuvjrPKH03zTQ9+7mYQXtko4t8nQZVx8HZ4Xh2tdTi7JsK6A8JOFzyfMYb1O94d5VUziOgxWtaPqZjCvHK5h57w0NOpbWpSLhbIVrqR/YBq+kr5Ox9BoZJKqW8jJbHF43Tp2AlBd2G9cKwjHe7KzWjduR/Dk4DmVbUGPjK4HfU7jWfl/x34gIN+itNREnihjzWAZEh+EH/R95Jo7YX4pPTrndrkWMj3tcw56CdbVqZSXlrjXvtNhDeVyInWhiS43LWzZm6OoGzjkp/RhRrTLQ8NhE6whZjNzHz+gICKTyTgaw2DSiTJwzc3JQ4Gbkp9/jP6bhQrXuOVh4/zvCa5gzGkpQUdF/ma/vc0uY=; _gcl_au=1.1.608944585.1742840470; _gid=GA1.2.371290566.1742840472; _gat_UA-28146424-9=1; _gat_UA-28146424-14=1; _dpm_ses.16f4=*; ab.storage.deviceId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%2265d3b7de-ecee-1bb4-1424-f53a7c2ff909%22%2C%22c%22%3A1742840471733%2C%22l%22%3A1742840471733%7D; _ga=GA1.2.1347696125.1742840472; _scid=BKjCgo3j4SJVUtOVaAZ9GD69jg9ThFaN; __ssid=0f1ab059b1b0400237c066030150700; _ga_M8T3LWXCC5=GS1.2.1742840473.1.1.1742840473.60.0.0; _hjSessionUser_2150570=eyJpZCI6IjUxMTI4MmU2LWFjMDMtNTEyZC05ZTlkLTdjMjk2N2M2MDYwNCIsImNyZWF0ZWQiOjE3NDI4NDA0NzQwNzgsImV4aXN0aW5nIjpmYWxzZX0=; _hjSession_2150570=eyJpZCI6ImIyNDExMjAyLTNjZmYtNDgxOS05NmY0LWFlNDYzMTBmZmY1YiIsImMiOjE3NDI4NDA0NzQwODMsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=; _uetsid=c5321f4008dc11f0b227a1e967ff766c; _uetvid=c53235d008dc11f083aaf7076d2376ab; _abck=214D91E4FD2D309290EDF1928DEB7D20~0~YAAQ7xghF0eAeaqVAQAABC5jyQ0K7A3KE+IDLiXFXsAw+lduXjUjdtKQBoVhTFzRuAJLPy25ESMOGHvIkJ2xM3z0FDHLgyzJcN814KQi9fm3u6ssa5szTEUee40Ws9dQLtD/LssitbQ6JRPl2aoLmNBQyY7eXu7/kGR8soYI4KMgk2Xho9Atidg3T+J1BXAIFjHe3d6O7OyNfZjPBDN8airyWRbV9pmAj8oZE7dfio9c2DuFZphzzXfPpS4+q9FzpyS7Fc1/4GsydOXdYtvFT07Undt5VSDmvUtxyczz+pZpcZCG9K63DKpTfXtQw29U+0WdKtQmmyvSfcXKz2noqYSUGnipAtzffSORzsg1rKdCNOHeTaRszD5JDAoKTTd58HFANoXScVdpBRnhJMhzRoYMsZ/vWHhdD51NUQeQF2wgXxWp/zeyDvTPrtGXk4gASOhUQD6dadmsy1WW4aGQcThGeIrFUEuzp2fV47/hgNRFZHjnxnm939y9rxDWusgQWZyo7ghxaigvWqjJBd9p/2qbFBj/D2ba2IGDPQFykzI=~-1~||0||~-1; _sctr=1%7C1742788800000; bm_sz=0634BCE2ECF48FFAFCF681ECFE3608F8~YAAQ7xghF4iEeaqVAQAAL0xjyRv6JdqyEh0YiNdVu5jVOnA8tphYgPAteXeuu3jyxWiU0bNbR8U0Bihjg3af0jpbGyHH7ZzfNv+dQRJuGbVcYI39Uwxn4F12hmoTc3K7mSFcozt98aKLU4JwePqZwlRUH2Rux8lCd/sHBZb4lPtvwN7qDm83MA95bz+YJXTMqYAckbXKFLcvcDB6xYRw5bjTTPSHQ/c/bNppAZ8Wi4a6GAHGxXypIajbO163MNx4R5X3Am1aaWPwUEYBSSQhzR/dZYkh3RS+AP26Awun9eQLfh1IqpT9QxohvExkF9ZVeCKVD75ckGitcczugS/8A8kZJ/BeDiyBW82bGSCYI1C3QZvDhj6p6mmWSyvLekRKj2T/Y1gaNcPUHOq764bkqck3P97xkRTxmy6qPlw=~3618104~4470073; _ga_QG8WHJSQMJ=GS1.1.1742840471.1.1.1742840483.47.0.0; _rdt_uuid=1742840471657.8c46091b-8982-4af0-b379-f7bcb5ddca10; _dpm_id.16f4=795303ca-e973-4314-8445-fb366243e6c7.1742840472.1.1742840484.1742840472.98ebfdff-a129-4c36-b17e-accebc6119c1; _scid_r=HSjCgo3j4SJVUtOVaAZ9GD69jg9ThFaNI_6KVw; ab.storage.sessionId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%222e7c1c16-9c3b-1965-d9f5-a8d75360a42d%22%2C%22e%22%3A1742842284592%2C%22c%22%3A1742840471728%2C%22l%22%3A1742840484592%7D; STE="2025-03-24T18:51:24.8641552Z"; bm_sv=6DE1B01E7686294B02092171AE2174B2~YAAQ5hghF5AJNcOVAQAAFVRjyRtcZZjsjS+u7y5lFbW585ITscESFfUOjR6u2CDGQZncyP1cFDcxR+5MwOVUgQPsaiS16lpIXh3dluhFkj4ue1lMLVy9L2IPc/OmaOdHnfJuIm/cgDbQOmPzYNZE1boh5jXOc+GiI+nZHzFlIVaXQJBHWF7YJJqkYiLU/PFdWtQWI2uoznYrZJDVo2UG36Ycme8SAXgCiKKkXFMHhmatxaCMk+heAqanlqpoc7H9s7GvAR0=~1',
    }

    async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://sportsbook-nash.draftkings.com/api/sportscontent/dkcaon/v1/leagues/42648',
                    cookies=cookies,
                    headers=headers,
                ) as response:
                    # Read the response content
                    data = await response.json()

                    #First grab all the odds for each team
                    team_odds = {}
                    for team in data["selections"]:
                        current_team = team["label"].split()[-1]
                        odds = team["displayOdds"]["american"]
                        team_odds[current_team] = odds
                    #Now match the odds with each team in each game
                    for event in data["events"]:
                        teams = event["name"]
                        home = teams.split()[-1]
                        away_full = teams.split(" @ ")
                        away = away_full[0].split()[-1]
                        utc_time_str = event["startEventDate"]
                        utc_time_str = utc_time_str[:-2]  + "Z" #There are 7 0s, datetime only sees 6 for microseconds. Need to add back the Z as that is accounted for
                        et_time_str = UTC_to_ET(utc_time_str, False)
                        away_odds = team_odds.get(away)
                        home_odds = team_odds.get(home)
                        #The negative sign isn't just a hyphen, so int breaks, so must replace with a hyphen. .Replace returns original if replacing char not found
                        away_odds = away_odds.replace("−", "-")
                        home_odds = home_odds.replace("−", "-")
                        pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'DraftKings:{away}': int(away_odds)})
                        pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'DraftKings:{home}': int(home_odds)})
                        all_games.add(f'NBA:{away}_{home}:{et_time_str}')
                        







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
        bet_rivers_NBA(pipeline),
        draft_kings_NBA(pipeline)
    )

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