import datetime
import json
import os
import random
import sys
import urllib.parse
import urllib.request

# --- BRUKERE ---
# Leses fra miljøvariabel USERS_JSON (GitHub Secret) for å unngå å eksponere
# personopplysninger i et offentlig repo. Forventet format:
# {
#   "Navn": {"email": "navn@firma.no", "object_id": "<azure-ad-objekt-id>"},
#   ...
# }
def load_users():
    raw = os.environ.get("USERS_JSON")
    if not raw:
        print("Mangler USERS_JSON miljøvariabel")
        sys.exit(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"USERS_JSON er ikke gyldig JSON: {e}")
        sys.exit(1)


# --- ROTASJONSLISTE ---
# Leses fra miljøvariabel ROTATION_JSON (GitHub Secret). Forventet format:
# [["Navn1", "Navn2"], ["Navn3", "Navn4"], ...]
def load_rotation():
    raw = os.environ.get("ROTATION_JSON")
    if not raw:
        print("Mangler ROTATION_JSON miljøvariabel")
        sys.exit(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ROTATION_JSON er ikke gyldig JSON: {e}")
        sys.exit(1)


ROTATION_START_WEEK = 17
ROTATION_START_YEAR = 2026

# --- SITATER ---
QUOTES = [
    {"text": "Man lever ikke av brod alene - men det hjelper veldig.", "author": "Ukjent vismann"},
    {"text": "Lunsj er frokosten til de som faktisk fikk sove.", "author": "Ukjent"},
    {"text": "Tell me what you eat, and I will tell you what you are.", "author": "Jean Anthelme Brillat-Savarin"},
    {"text": "Life is uncertain. Eat dessert first.", "author": "Ernestine Ulmer"},
    {"text": "One cannot think well, love well, sleep well, if one has not dined well.", "author": "Virginia Woolf"},
    {"text": "I come from a family where gravy is considered a beverage.", "author": "Erma Bombeck"},
    {"text": "The only time to eat diet food is while you're waiting for the steak to cook.", "author": "Julia Child"},
    {"text": "Lunsj: Den eneste motetypen alle faktisk moter opp til.", "author": "Kontorfilosofen"},
    {"text": "Verden er full av problemer - heldigvis er det ogsa full av mat.", "author": "Optimistisk filosof"},
    {"text": "You are what you eat, so don't be fast, cheap, easy, or fake.", "author": "Ukjent"},
    {"text": "In the end, it's not the years in your life that count, it's the lunches.", "author": "Abraham Lincoln (omtrent)"},
    {"text": "Mat laget med kjaerlighet smaker alltid best. Mat laget av kollegaer smaker ogsa greit.", "author": "Ukjent"},
    {"text": "A balanced diet is a cookie in each hand.", "author": "Barbara Johnson"},
    {"text": "I'm on a seafood diet. I see food and I eat it.", "author": "Klassiker"},
    {"text": "The secret ingredient is always cheese.", "author": "Enhver god kokk"},
    {"text": "Cooking is like love - it should be entered into with abandon or not at all.", "author": "Harriet van Horne"},
    {"text": "Forst spiser vi, sa gjor vi alt det andre.", "author": "Ukjent, men klok"},
    {"text": "A good meal is a good mood.", "author": "Ukjent"},
]

GIPHY_SEARCH_TERMS = [
    "food fail", "cooking disaster", "pizza dance", "hungry cat food",
    "chef kiss", "food explosion", "spaghetti mess", "burger falling",
    "hot dog dance", "taco falling", "noodles slurp", "food baby",
]


def get_week_entry(rotation, offset_weeks=0):
    today = datetime.date.today() + datetime.timedelta(weeks=offset_weeks)
    start = datetime.date.fromisocalendar(ROTATION_START_YEAR, ROTATION_START_WEEK, 1)
    weeks_since_start = (today - start).days // 7
    index = weeks_since_start % len(rotation)
    week_num = today.isocalendar()[1]
    return {"uke": week_num, "ansvarlige": rotation[index]}


def make_mention(users, name):
    user = users.get(name, {})
    object_id = user.get("object_id", "")
    if object_id:
        mention_text = f"<at>{name}</at>"
        entity = {
            "type": "mention",
            "text": mention_text,
            "mentioned": {"id": object_id, "name": name}
        }
        return mention_text, entity
    return name, None


def get_giphy_gif(api_key):
    search_term = random.choice(GIPHY_SEARCH_TERMS)
    url = (
        f"https://api.giphy.com/v1/gifs/random"
        f"?api_key={api_key}"
        f"&tag={urllib.parse.quote(search_term)}"
        f"&rating=pg"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LunchBot/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data["data"]["images"]["fixed_height"]["url"]
    except Exception as e:
        print(f"Kunne ikke hente GIF: {e}")
        return None


def send_teams_message(webhook_url, users, entry, gif_url=None):
    names = entry["ansvarlige"]
    week_num = entry["uke"]
    quote = random.choice(QUOTES)

    mention_texts = []
    entities = []
    for name in names:
        text, entity = make_mention(users, name)
        mention_texts.append(text)
        if entity:
            entities.append(entity)

    names_str = " og ".join(mention_texts)
    plain_names = " og ".join(names)

    card_body = [
        {
            "type": "TextBlock",
            "text": f"Lunsjansvar - uke {week_num}",
            "weight": "Bolder",
            "size": "Large",
            "wrap": True
        },
        {
            "type": "TextBlock",
            "text": f"Denne uken er det {names_str} som har ansvaret for lunsjen. Lykke til!",
            "wrap": True,
            "spacing": "Medium"
        },
        {
            "type": "TextBlock",
            "text": f'"{quote["text"]}" - {quote["author"]}',
            "wrap": True,
            "spacing": "Medium"
        },
    ]

    if gif_url:
        card_body.append({
            "type": "Image",
            "url": gif_url,
            "size": "Stretch",
            "spacing": "Medium",
            "altText": "Ukens mat-GIF"
        })

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": card_body,
                    **({"msteams": {"entities": entities}} if entities else {})
                }
            }
        ]
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        print(f"Melding sendt! Status: {response.status}")
        print(f"Uke {week_num}: {plain_names}")


def main():
    webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        print("Mangler TEAMS_WEBHOOK_URL miljøvariabel")
        sys.exit(1)

    users = load_users()
    rotation = load_rotation()

    entry = get_week_entry(rotation, 0)

    gif_url = None
    giphy_api_key = os.environ.get("GIPHY_API_KEY")
    if giphy_api_key:
        gif_url = get_giphy_gif(giphy_api_key)

    send_teams_message(webhook_url, users, entry, gif_url)


if __name__ == "__main__":
    main()
