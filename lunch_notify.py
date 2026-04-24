import datetime
import json
import urllib.request
import urllib.parse
import random
import os
import sys

# --- BRUKERE ---
USERS = {
    "Torbjørn": {"email": "torbjorn@havnevik.no", "object_id": "383611c2-6cf0-4af0-8c29-99b74423d116"},
    "Gry": {"email": "gry@havnevik.no", "object_id": "ec151031-16b4-48ae-8baf-4ddde3cc6720"},
    "Thomas": {"email": "thomas@havnevik.no", "object_id": "cb7998bb-c9f0-41ac-938a-b5201992c865"},
    "Torgeir": {"email": "torgeir@havnevik.no", "object_id": "eb3123d5-a540-4712-8d97-757a0c9853f1"},
    "Espen": {"email": "espen@havnevik.no", "object_id": "68b34adf-7592-4920-9a72-a158ea8e8183"},
    "Mary Ellen": {"email": "mary-ellen@havnevik.no", "object_id": "2d41b594-4335-4be0-9cf8-c8b2c55d03b9"},
    "Øyvind": {"email": "oyvind@havnevik.no", "object_id": "6c9efa23-7b6d-456e-b990-a62224124962"},
    "Lise": {"email": "lise@havnevik.no", "object_id": "cca04942-c824-4001-9143-d160a0fb1d55"},
    "Markus": {"email": "markus@havnevik.no", "object_id": "cf201853-fb34-4307-8e00-ae93af661ffe"},
    "Guri": {"email": "guri@havnevik.no", "object_id": "3e841680-8e19-4db4-89d3-31b39a76b786"},
}

# --- ROTASJONSLISTE ---
ROTATION = [
    ["Torbjørn", "Gry"],
    ["Thomas", "Torgeir"],
    ["Espen", "Mary Ellen"],
    ["Øyvind", "Lise"],
    ["Markus", "Guri"],
]

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

EMOJIS = ["pizza", "salat", "matboks", "taco", "sandwich", "nudler", "gryte"]
EMOJI_CHARS = ["<3", ":)", "=)", ":]", ":D", "^_^", "o/"]

GIPHY_SEARCH_TERMS = [
    "food fail", "cooking disaster", "pizza dance", "hungry cat food",
    "chef kiss", "food explosion", "spaghetti mess", "burger falling",
    "hot dog dance", "taco falling", "noodles slurp", "food baby",
]

def get_week_entry(offset_weeks=0):
    today = datetime.date.today() + datetime.timedelta(weeks=offset_weeks)
    start = datetime.date.fromisocalendar(ROTATION_START_YEAR, ROTATION_START_WEEK, 1)
    weeks_since_start = (today - start).days // 7
    index = weeks_since_start % len(ROTATION)
    week_num = today.isocalendar()[1]
    return {"uke": week_num, "ansvarlige": ROTATION[index]}

def make_mention(name: str):
    user = USERS.get(name, {})
    object_id = user.get("object_id", "")
    if object_id:
        mention_text = f"<at>{name}</at>"
        entity = {
            "type": "mention",
            "text": mention_text,
            "mentioned": {"id": object_id, "name": name}
        }
        return mention_text, entity
    else:
        return name, None

def get_giphy_gif(api_key: str):
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

def send_teams_message(webhook_url: str, entry: dict, next_entry: dict = None, gif_url: str = None):
    names = entry["ansvarlige"]
    week_num = entry["uke"]
    quote = random.choice(QUOTES)

    mention_texts = []
    entities = []
    for name in names:
        text, entity = make_mention(name)
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
            "text": f"\"{quote['text']}\" - {quote['author']}",
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
        print("Mangler TEAMS_WEBHOOK_URL miljovariabel")
        sys.exit(1)

    entry = get_week_entry(0)
    next_entry = get_week_entry(1)

    gif_url = None
    giphy_api_key = os.environ.get("GIPHY_API_KEY")
    if giphy_api_key:
        gif_url = get_giphy_gif(giphy_api_key)

    send_teams_message(webhook_url, entry, next_entry, gif_url)

if __name__ == "__main__":
    main()
