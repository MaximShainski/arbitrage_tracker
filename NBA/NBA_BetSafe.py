import aiohttp
#Will only work if run arbScraper
from utils import UTC_to_ET, decimal_to_american
import json

async def bet_safe_NBA(all_games, semaphore, pipeline):
    async with semaphore:
        cookies = {
            'OBG-MARKET': 'ca',
            'OBG-LOBBY': 'sportsbook',
            'OBG-SB-THEME': 'dark',
            'sloc': '%7B%22flags%22%3A%7B%22strm%22%3A1%2C%22customerFavourites%22%3A1%2C%22bb%22%3A1%7D%2C%22segmentGuid%22%3A%2214e2cb7f-c477-4b32-921d-96a6c1196950%22%7D',
            'OPTIMIZELY_USER_ID': 'feefd4a8-9140-4a31-a080-51e5536a4ed8',
            'Acquisition_Status_Current': 'Prospect',
            'Start_Acquisition': 'Prospect',
            'Client_Status_Current': 'Prospect',
            'Start_Client_Status': 'Prospect',
            'Customer_Level': 'PC',
            'Initdone': '1',
            'TrafficType': 'Other Traffic',
            'AffCookie': 'Missing AffCode',
            'LoadAll': '0',
            'GAClientID_Cookie': 'undefined',
            'cwr_u': 'da8a3b04-204b-4911-ac02-737b6f94afcb',
            'token': 'https%3A%2F%2Fwww.google.com%2F',
            'affcode': 'hgjeap65',
            'PartnerId': 'hgjeap65',
            '_ga': 'GA1.1.1015646289.1743182730',
            'crw-_ga': '2025-03-28-365',
            'OptanonConsent': 'isIABGlobal=false&datestamp=Fri+Mar+28+2025+13%3A25%3A33+GMT-0400+(Eastern+Daylight+Time)&version=6.39.0&hosts=&landingPath=https%3A%2F%2Fwww.betsafe.com%2Fca%2Fsportsbook%2Fbasketball%2Fnba%3Ftab%3DliveAndUpcoming&groups=C0001%3A1%2CC0003%3A0%2CC0002%3A1%2CC0004%3A0',
            'Orientation': '0',
            '__zzatgib-w-bab-betsafe': 'MDA0dC0cTApcfEJcdGswPi17CT4VHThHKHIzd2UrbW1TZXsSIEAQCQosFhV8JipMOQ8VQz4nLDFxax8ZSVojShA/dRdZRkE2XBpLdWUvDDk6a2wkUlFDS2N8GgprLxoYe24kVwkSX0RDc3slLTFmJ3xLKTUdETJeV1U0O2dBVFg=f8b4Uw==',
            '__zzatgib-w-bab-betsafe': 'MDA0dC0cTApcfEJcdGswPi17CT4VHThHKHIzd2UrbW1TZXsSIEAQCQosFhV8JipMOQ8VQz4nLDFxax8ZSVojShA/dRdZRkE2XBpLdWUvDDk6a2wkUlFDS2N8GgprLxoYe24kVwkSX0RDc3slLTFmJ3xLKTUdETJeV1U0O2dBVFg=f8b4Uw==',
            'cfidsgib-w-bab-betsafe': '8QcDmJ9qWHgZhbT1tv40G0UbyQXpmRRFsFQUibIgSQygzzx9z9Fdjh/MX472z2Yu7DKOv5aOP6wtb8MHeV+QCvugUckBDJ5GL2Xu5mElQHDZCm0slyduaGGsu9v9JqYv+RQD9b4K4lFsG5bHcFxUOIZLiTzF+jUoYBEQ',
            'cfidsgib-w-bab-betsafe': '8QcDmJ9qWHgZhbT1tv40G0UbyQXpmRRFsFQUibIgSQygzzx9z9Fdjh/MX472z2Yu7DKOv5aOP6wtb8MHeV+QCvugUckBDJ5GL2Xu5mElQHDZCm0slyduaGGsu9v9JqYv+RQD9b4K4lFsG5bHcFxUOIZLiTzF+jUoYBEQ',
            'cwr_s': 'eyJzZXNzaW9uSWQiOiI5YzUzYmE2OS05ZmU4LTQ0ZTYtOTY5Ni1mMDBiMjVjMTRkODUiLCJyZWNvcmQiOmZhbHNlLCJldmVudENvdW50Ijo1OTQsInBhZ2UiOnsicGFnZUlkIjoiL2NhL3Nwb3J0c2Jvb2svYmFza2V0YmFsbC9uYmEiLCJwYXJlbnRQYWdlSWQiOiIvY2Evc3BvcnRzYm9vayIsImludGVyYWN0aW9uIjoxLCJyZWZlcnJlciI6Imh0dHBzOi8vd3d3LmJldHNhZmUuY29tL2NhL3Nwb3J0c2Jvb2siLCJyZWZlcnJlckRvbWFpbiI6Ind3dy5iZXRzYWZlLmNvbSIsInN0YXJ0IjoxNzQzMTgyNzMxMzk0fX0=',
            '_ga_NWZTHSHR5H': 'GS1.1.1743182729.1.1.1743182748.0.0.0',
            'aws-waf-token': '49a3c7d0-c066-4fd5-81fb-7bf87410c4d6:CAoAclN6Tw0NAAAA:YWvlo4pkKxINhdm8S3k8+Wj/55dQKzQJDxK154CVipL2NXdGujVGwx7cWW9n4mOWHFbK2+b32HYr6kBIZrJhie4wQGlxNZJu7CUap8EeGSvV3fZcB21jpKy3RQhdS720mseJ79d4ZCmFRj3yPo2USEmxDgrjyeyLZWLkJaMf7I7mo++R+dyKG0nt/I3nJkLvXWLuYJKR9j7CGaMv8MSC2Z9uoBKIarZVjNDE14sZdAyKWpqs445ErQ==',
        }


        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'brandid': '11a81f20-a960-49e4-8748-51f750c1b27c',
            'cloudfront-viewer-country': 'CA',
            'content-type': 'application/json',
            'correlationid': '9645bfeb-b683-424f-be58-9ba340b2fbf5',
            'marketcode': 'ca',
            'priority': 'u=1, i',
            'referer': 'https://www.betsafe.com/ca/sportsbook/basketball/nba?tab=liveAndUpcoming',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'x-obg-channel': 'Web',
            'x-obg-country-code': 'CA',
            'x-obg-device': 'Desktop',
            'x-obg-experiments': 'ssrClientConfiguration',
            'x-sb-identifier': 'EVENT_TABLE_REQUEST',
            'x-sb-segment-guid': '14e2cb7f-c477-4b32-921d-96a6c1196950',
            # 'cookie': 'OBG-MARKET=ca; OBG-LOBBY=sportsbook; OBG-SB-THEME=dark; sloc=%7B%22flags%22%3A%7B%22strm%22%3A1%2C%22customerFavourites%22%3A1%2C%22bb%22%3A1%7D%2C%22segmentGuid%22%3A%2214e2cb7f-c477-4b32-921d-96a6c1196950%22%7D; OPTIMIZELY_USER_ID=feefd4a8-9140-4a31-a080-51e5536a4ed8; Acquisition_Status_Current=Prospect; Start_Acquisition=Prospect; Client_Status_Current=Prospect; Start_Client_Status=Prospect; Customer_Level=PC; Initdone=1; TrafficType=Other Traffic; AffCookie=Missing AffCode; LoadAll=0; GAClientID_Cookie=undefined; cwr_u=da8a3b04-204b-4911-ac02-737b6f94afcb; token=https%3A%2F%2Fwww.google.com%2F; affcode=hgjeap65; PartnerId=hgjeap65; _ga=GA1.1.1015646289.1743182730; crw-_ga=2025-03-28-365; OptanonConsent=isIABGlobal=false&datestamp=Fri+Mar+28+2025+13%3A25%3A33+GMT-0400+(Eastern+Daylight+Time)&version=6.39.0&hosts=&landingPath=https%3A%2F%2Fwww.betsafe.com%2Fca%2Fsportsbook%2Fbasketball%2Fnba%3Ftab%3DliveAndUpcoming&groups=C0001%3A1%2CC0003%3A0%2CC0002%3A1%2CC0004%3A0; Orientation=0; __zzatgib-w-bab-betsafe=MDA0dC0cTApcfEJcdGswPi17CT4VHThHKHIzd2UrbW1TZXsSIEAQCQosFhV8JipMOQ8VQz4nLDFxax8ZSVojShA/dRdZRkE2XBpLdWUvDDk6a2wkUlFDS2N8GgprLxoYe24kVwkSX0RDc3slLTFmJ3xLKTUdETJeV1U0O2dBVFg=f8b4Uw==; __zzatgib-w-bab-betsafe=MDA0dC0cTApcfEJcdGswPi17CT4VHThHKHIzd2UrbW1TZXsSIEAQCQosFhV8JipMOQ8VQz4nLDFxax8ZSVojShA/dRdZRkE2XBpLdWUvDDk6a2wkUlFDS2N8GgprLxoYe24kVwkSX0RDc3slLTFmJ3xLKTUdETJeV1U0O2dBVFg=f8b4Uw==; cfidsgib-w-bab-betsafe=8QcDmJ9qWHgZhbT1tv40G0UbyQXpmRRFsFQUibIgSQygzzx9z9Fdjh/MX472z2Yu7DKOv5aOP6wtb8MHeV+QCvugUckBDJ5GL2Xu5mElQHDZCm0slyduaGGsu9v9JqYv+RQD9b4K4lFsG5bHcFxUOIZLiTzF+jUoYBEQ; cfidsgib-w-bab-betsafe=8QcDmJ9qWHgZhbT1tv40G0UbyQXpmRRFsFQUibIgSQygzzx9z9Fdjh/MX472z2Yu7DKOv5aOP6wtb8MHeV+QCvugUckBDJ5GL2Xu5mElQHDZCm0slyduaGGsu9v9JqYv+RQD9b4K4lFsG5bHcFxUOIZLiTzF+jUoYBEQ; cwr_s=eyJzZXNzaW9uSWQiOiI5YzUzYmE2OS05ZmU4LTQ0ZTYtOTY5Ni1mMDBiMjVjMTRkODUiLCJyZWNvcmQiOmZhbHNlLCJldmVudENvdW50Ijo1OTQsInBhZ2UiOnsicGFnZUlkIjoiL2NhL3Nwb3J0c2Jvb2svYmFza2V0YmFsbC9uYmEiLCJwYXJlbnRQYWdlSWQiOiIvY2Evc3BvcnRzYm9vayIsImludGVyYWN0aW9uIjoxLCJyZWZlcnJlciI6Imh0dHBzOi8vd3d3LmJldHNhZmUuY29tL2NhL3Nwb3J0c2Jvb2siLCJyZWZlcnJlckRvbWFpbiI6Ind3dy5iZXRzYWZlLmNvbSIsInN0YXJ0IjoxNzQzMTgyNzMxMzk0fX0=; _ga_NWZTHSHR5H=GS1.1.1743182729.1.1.1743182748.0.0.0; aws-waf-token=49a3c7d0-c066-4fd5-81fb-7bf87410c4d6:CAoAclN6Tw0NAAAA:YWvlo4pkKxINhdm8S3k8+Wj/55dQKzQJDxK154CVipL2NXdGujVGwx7cWW9n4mOWHFbK2+b32HYr6kBIZrJhie4wQGlxNZJu7CUap8EeGSvV3fZcB21jpKy3RQhdS720mseJ79d4ZCmFRj3yPo2USEmxDgrjyeyLZWLkJaMf7I7mo++R+dyKG0nt/I3nJkLvXWLuYJKR9j7CGaMv8MSC2Z9uoBKIarZVjNDE14sZdAyKWpqs445ErQ==',
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://www.betsafe.com/api/sb/v1/widgets/events-table/v2?categoryIds=4&competitionIds=87&eventPhase=Prematch&eventSortBy=StartDate&maxMarketCount=1&pageNumber=1',
                cookies=cookies,
                headers=headers,
            ) as response:
                # Read the response content
                data = await response.json()
                with open("response.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                #Grab all the odds for each team (incredibly similar to draft_kings extraction algorithm)
                team_odds = {}
                for team in data["data"]["selections"]:
                    #Get the team and the odds
                    current_team = team["participant"].split()[-1]
                    odds = team["odds"]
                    #Convert to american odds
                    american_odds = decimal_to_american(odds)
                    #Insert odds for current team
                    team_odds[current_team] = american_odds
                #Now match the odds with each team in each game
                for event in data["data"]["events"]:
                    teams = event["label"]
                    away = teams.split()[-1]
                    home_full = teams.split(" - ")
                    home = home_full[0].split()[-1]
                    utc_time_str = event["startDate"]
                    utc_time_str = utc_time_str[:-2]  + "Z" #There are 7 0s, datetime only sees 6 for microseconds. Need to add back the Z as that is accounted for
                    print(utc_time_str)
                    et_time_str = UTC_to_ET(utc_time_str, 5)
                    #print(team_odds) If the problem comes again where away_odds is nonetype, uncomment this
                    #print(away)
                    print(team_odds)
                    print(away)
                    away_odds = team_odds.get(away)
                    home_odds = team_odds.get(home)
                    try:
                        pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'BetSafe:{away}': int(away_odds)})
                        pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'BetSafe:{home}': int(home_odds)})
                    except:
                        print(f'{away_odds} and/or {home_odds} are not correct')
                        continue
                    print(f'NBA:{away}_{home}:{et_time_str}')
                    all_games.add(f'NBA:{away}_{home}:{et_time_str}')