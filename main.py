from telegram.ext import Application
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os

load_dotenv()

CHECK_INTERVAL = 60 * 60 * 24
GYM_NAME = "Sengkang ActiveSG Gym"
CHAT_ID = int(os.getenv("CHAT_ID"))
TOKEN = os.getenv("BOT_TOKEN")

def getFacilitiesClosure():
    res = requests.get("https://www.activesgcircle.gov.sg/facilities/sport-centres/facilities-closure")
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


def main():
    """
    Handles the initial launch of the program (entry point).
    """
    application = Application.builder().token(TOKEN).build()
    # schedule job 
    application.job_queue.run_repeating(checkAndNotify, interval=CHECK_INTERVAL, first=10)
    application.run_polling()

if __name__ == '__main__':
    main()