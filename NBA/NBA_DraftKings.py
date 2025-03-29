import aiohttp
#Will only work if run arbScraper
from utils import UTC_to_ET

async def draft_kings_NBA(all_games, semaphore, pipeline):
    async with semaphore:
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
                            et_time_str = UTC_to_ET(utc_time_str, 0)
                            away_odds = team_odds.get(away)
                            home_odds = team_odds.get(home)
                            #The negative sign isn't just a hyphen, so int breaks, so must replace with a hyphen. .Replace returns original if replacing char not found
                            away_odds = away_odds.replace("−", "-")
                            home_odds = home_odds.replace("−", "-")
                            pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'DraftKings:{away}': int(away_odds)})
                            pipeline.zadd(f'NBA:{away}_{home}:{et_time_str}', {f'DraftKings:{home}': int(home_odds)})
                            all_games.add(f'NBA:{away}_{home}:{et_time_str}')