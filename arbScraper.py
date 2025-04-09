from curl_cffi import requests #curl_cffi is a wrapper around requests a more browser like TLS fingerprint \\
from rich import print #Makes print look nicer
import time
import asyncio
import redis.asyncio as async_redis
from bot_functions import test, send_odds
from bot_functions import app
from NBA.NBA_FanDuel import fan_duel_NBA
from NBA.NBA_MGM import MGM_NBA
from NBA.NBA_BetRivers import bet_rivers_NBA
from NBA.NBA_DraftKings import draft_kings_NBA
from NBA.NBA_BetSafe import bet_safe_NBA
from NBA.NBA_BetVictors import bet_victors_NBA
from NBA.NBA_888 import eightx3_NBA
from utils import calculate_best_odds

class ArbitrageScraper:
    def __init__(self, total_bet=100, semaphore_limit=10):
        self.total_bet = total_bet #Total amount to wager
        self.semaphore = asyncio.Semaphore(semaphore_limit) #Amount of allowed concurrent tasks
        self.all_games = set() #Tracks current games to use for querying redis
        self.pipeline = None #Pipeline for redis query optimizations
        self.r_async = None #Asynchronous connection to redis

    async def create_async_redis_connection(self):
        self.r_async = async_redis.from_url('redis://localhost')
    
    async def scrape_sites(self):
        #Is done here instead of a helper method because when it's asynchronous it chokes a little
        if not self.pipeline:
            self.pipeline = self.r_async.pipeline()
        
        # Scrape sites concurrently
        await asyncio.gather(
            MGM_NBA(self.all_games, self.semaphore, self.pipeline),
            fan_duel_NBA(self.all_games, self.semaphore, self.pipeline),
            bet_rivers_NBA(self.all_games, self.semaphore, self.pipeline),
            draft_kings_NBA(self.all_games, self.semaphore, self.pipeline),
            bet_safe_NBA(self.all_games, self.semaphore, self.pipeline),
            #bet_victors_NBA(self.all_games, self.semaphore, self.pipeline),
            #eightx3_NBA(self.all_games, self.semaphore, self.pipeline)
        )

        # Execute all commands in the pipeline
        try:
            await self.pipeline.execute()
        except Exception as e:
            print(f"Error executing Redis pipeline: {e}")

    async def run(self):
        # Set up Redis connection and clear DB before scraping
        await self.create_async_redis_connection()
        await self.r_async.flushall()

        # Scrape all the sites
        await self.scrape_sites()

        # Calculate the odds after scraping
        arbitrage_messages = await calculate_best_odds(self.all_games, self.r_async, self.total_bet)

        # Send the odds to the bot only if there are odds to send
        if (arbitrage_messages):
            await send_odds(app, arbitrage_messages)

        #Close the redis connection
        await self.r_async.aclose()
        print("--- %s seconds ---" % (time.time() - start_time))

async def main():
    #Initialize the main process
    arb_scraper = ArbitrageScraper(100, 100)

    #Start the process
    await arb_scraper.run()

if __name__ == "__main__":
    start_time = time.time()
    #run main asynchronously
    asyncio.run(main())