import requests
import traceback

from threading import Thread
from utils import get_settings, get_proxy
from time import sleep
from datetime import datetime

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.37 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.37'}

RETRY_TIMEOUT = 3
MAX_WEBHOOK_RETRIES = 3
WEBHOOK_RETRY = 5

class EventMonitor(Thread):
    def __init__(self, event_id, event_name, webhook, section=None, delay=5, debug=False, use_proxies=False, proxies=None):
        super().__init__(daemon=True)
        self.webhook = webhook
        self.event_id = event_id
        self.notified = False
        self.event_name = event_name
        self.section = section
        self.date = None
        self.delay = delay
        self.debug = debug
        self.use_proxies = use_proxies
        self.proxies = proxies

    def run(self):
        current_tickets = self.get_event_tickets()
        # TODO: testing
        # print(current_tickets)
        # current_tickets = []

        # if self.debug:
        #     print(f"[{datetime.now().strftime('%H:%M:%S')}] | [{self.event_name}]", current_tickets)

        while True:
            if self.debug:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] | [{self.event_name}] looking for new tickets")

            new_tickets = self.get_event_tickets()

            while not self.validate_ticket_dict(new_tickets):
                if self.debug:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] | [{self.event_name}] failed to get new tickets")

                sleep(RETRY_TIMEOUT)
                continue

            found_new = False
            for ticket in new_tickets["picks"]:
                if ticket not in current_tickets["picks"]:
                    # check for section
                    if self.section and self.section not in ticket.get("section", ""):
                        continue

                    print(f"[{datetime.now().strftime('%H:%M:%S')}] | [{self.event_name}] found new")
                    self.send_webhook(ticket)
                    found_new = True

            if found_new:
                current_tickets = new_tickets

            sleep(self.delay)

    def get_event_tickets(self):
        try:
            resp = None
            if self.use_proxies:
                resp = requests.get(f"https://www.ticketmaster.co.uk/api/quickpicks/{self.event_id}/list?qty=1", headers=HEADERS, proxies=get_proxy(self.proxies))
            else:
                resp = requests.get(f"https://www.ticketmaster.co.uk/api/quickpicks/{self.event_id}/list?qty=1", headers=HEADERS)

            r = resp.json()

            for pick in r["picks"]:
                pick.pop("id", None)
                pick.pop("offerIds", None)

            return r
        except:
            # print(resp.text)
            return []

    def validate_ticket_dict(self, tickets):
        if not tickets and type(tickets) is not dict:
            return False

        if not "picks" in tickets.keys():
            return False

        return True

    def send_webhook(self, ticket):
        obj = {
            "embeds": [{
                "username": "Ticket Master Monitor",
                "url": f"https://www.ticketmaster.co.uk/event/{self.event_id}",
                "timestamp": datetime.utcnow().isoformat(),
                "color": 3779839,
                "fields": []
            }]
        }

        obj["embeds"][0]["title"] = f"TICKET RESTOCK FOR EVENT: {self.event_name}"

        if "originalPrice" in ticket.keys():
            obj["embeds"][0]["fields"].append({"name": "Price", "value": str(ticket["originalPrice"]), "inline": True})
        if "section" in ticket.keys():
            obj["embeds"][0]["fields"].append({"name": "Section", "value": str(ticket["section"]), "inline": True})
        if "row" in ticket.keys():
            obj["embeds"][0]["fields"].append({"name": "Row", "value": str(ticket["row"]), "inline": True})

        # obj["embeds"][0]["image"] = { 'url': self.nft_img_url }

        retries = 0
        resp = requests.post(self.webhook, json=obj)
        while not resp.status_code == 204:
            if retries == MAX_WEBHOOK_RETRIES:
                break
            print("too many requests... retrying...")
            resp = requests.post(self.webhook, json=obj)
            sleep(WEBHOOK_RETRY)
            retries += 1
        if resp.status_code == 204:
            return 0

def main():
    settings = get_settings()

    for event_id in settings["events"]:
        EventMonitor(event_id["id"], event_id["name"], settings["notification_webhook"], settings.get("section", None), settings["delay"], settings["debug"], settings["use_proxies"], settings["proxies"]).start()

    while True:
        sleep(10000)

if __name__ == "__main__":
    main()