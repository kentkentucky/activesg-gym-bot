from telegram.ext import Application, MessageHandler, filters
from bs4 import BeautifulSoup
from curl_cffi import requests as cf_requests
from dotenv import load_dotenv
from datetime import time

import requests as regular_requests
import os
import pytz

load_dotenv()

SGT = pytz.timezone("Asia/Singapore")
GYM_NAME = "Sengkang ActiveSG Gym"
CHAT_ID = int(os.getenv("CHAT_ID"))
TOKEN = os.getenv("BOT_TOKEN")

def getFacilitiesClosure():
    res = regular_requests.get("https://www.activesgcircle.gov.sg/facilities/sport-centres/facilities-closure")
    soup = BeautifulSoup(res.content, "html.parser")
    announcements = soup.find("table", class_="announcements_list")
    rows = announcements.find("tbody").find_all("tr")

    for row in rows:
        facility = row.find("span", class_="facility-name").get_text(strip=True)
        if GYM_NAME.lower() in facility.lower():
            period = row.find("span", class_="period-label").get_text(strip=True)
            area = row.find("span", class_="facility-sub").get_text(strip=True)
            closure_type = row.find("td", class_="closure-col").get_text(strip=True)
            return f"🏋️ {facility}\n📅 {period}\n📍 {area}\n🔧 {closure_type}"

    return None

async def checkAndNotify(context):
    closure = getFacilitiesClosure()
    if not closure:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"✅ No closures found for {GYM_NAME} today.")
    else:
        await context.bot.send_message(chat_id=CHAT_ID, text=closure)

def getGymCapacity():
    url = "https://activesg.gov.sg/api/trpc/pass.getFacilityCapacities?input=%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D"
    res = cf_requests.get(url, impersonate="chrome")
    data = res.json()
    gym_facilities = data["result"]["data"]["json"]["gymFacilities"]

    for gym in gym_facilities:
        if GYM_NAME in gym["name"]:
            status = "🔴 Closed" if gym["isClosed"] else "🟢 Open"
            return f"🏋️ {gym['name']}\n📊 Capacity: {gym['capacityPercentage']}%\n{status}"
        
    return None

async def handleCapacity(update, context):
    text = update.message.text.lower()
    
    if text == "c":
        capacity = getGymCapacity()
        if capacity:
            await update.message.reply_text(capacity)
        else:
            await update.message.reply_text("Could not find gym capacity.")


def main():
    """
    Handles the initial launch of the program (entry point).
    """
    application = Application.builder().token(TOKEN).build()
    # add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handleCapacity))
    # schedule job 
    application.job_queue.run_daily(checkAndNotify, time=time(8, 0, tzinfo=SGT))
    application.run_polling()

if __name__ == '__main__':
    main()