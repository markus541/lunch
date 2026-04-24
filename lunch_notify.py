import datetime
import json
import urllib.request
import urllib.parse
import random
import os
import sys

# --- BRUKERE ---
# Fyll inn Azure AD Object ID for hver bruker.
# Finn dem i Azure Portal → Azure Active Directory → Users → klikk bruker → "Object ID"
# Eller spør IT-admin. E-post er kun for referanse.
USERS = {
    "Torbjørn": {"email": "torbjorn@havnevik.no", "object_id": ""},
    "Gry":       {"email": "gry@havnevik.no",      "object_id": ""},
    "Thomas":    {"email": "thomas@havnevik.no",   "object_id": ""},
    "Torgeir":   {"email": "torgeir@havnevik.no",  "object_id": ""},
    "Espen":     {"email": "espen@havnevik.no",    "object_id": ""},
    "Mary Ellen":{"email": "mary-ellen@havnevik.no","object_id": ""},
    "Øyvind":    {"email": "oyvind@havnevik.no",   "object_id": ""},
    "Lise":      {"email": "lise@havnevik.no",     "object_id": ""},
    "Markus":    {"email": "markus@havnevik.no",   "object_id": ""},
    "Guri":      {"email": "guri@havnevik.no",     "object_id": ""},
}

# --- ROTASJONSLISTE ---
ROTATION = [
    {"uke": 17, "dato": "2025-04-21", "ansvarlige": ["Torbjørn", "Gry"]},
    {"uke": 18, "dato": "2025-04-28", "ansvarlige": ["Thomas", "Torgeir"]},
    {"uke": 19, "dato": "2025-05-05", "ansvarlige": ["Espen", "Mary Ellen"]},
    {"uke": 20, "dato": "2025-05-12", "ansvarlige": ["Øyvind", "Lise"]},
    {"uke": 21, "dato": "2025-05-19", "ansvarlige": ["Markus", "Guri"]},
    {"uke": 22, "dato": "2025-05-26", "ansvarlige": ["Torbjørn", "Gry"]},
    {"uke": 23, "dato": "2025-06-02", "ansvarlige": ["Thomas", "Torgeir"]},
    {"uke": 24, "dato": "2025-06-09", "ansvarlige": ["Espen", "Mary Ellen"]},
    {"uke": 25, "dato": "2025-06-16", "ansvarlige": ["Øyvind", "Lise"]},
    {"uke": 26, "dato": "2025-06-23", "ansvarlige": ["Markus", "Guri"]},
    {"uke": 27, "dato": "2025-06-30", "ansvarlige": ["Torbjørn", "Gry"]},
    {"uke": 28, "dato": "2025-07-07", "ansvarlige": ["Thomas", "Torgeir"]},
    {"uke": 29, "dato": "2025-07-14", "ansvarlige": ["Espen", "Mary Ellen"]},
]

# --- SITATER ---
QUOTES = [
    {"text": "Man lever ikke av brød alene – men det hjelper veldig.", "author": "Ukjent vismann"},
    {"text": "Lunsj er frokosten til de som faktisk fikk sove.", "author": "Ukjent"},
    {"text": "Tell me what you eat, and I will tell you what you are.", "author": "Jean Anthelme Brillat-Savarin"},
    {"text": "Life is uncertain. Eat dessert first.", "author": "Ernestine Ulmer"},
    {"text": "One cannot think well, love well, sleep well, if one has not dined well.", "author": "Virginia Woolf"},
    {"text": "I come from a family where gravy is considered a beverage.", "author": "Erma Bombeck"},
    {"text": "The only time to eat diet food is while you're waiting for the steak to cook.", "author": "Julia Child"},
    {"text": "Lunsj: Den eneste møtetypen alle faktisk møter opp til.", "author": "Kontorfilosofen"},
    {"text": "Verden er full av problemer – heldigvis er det også full av mat.", "author": "Optimistisk filosof"},
    {"text": "You are what you eat, so don't be fast, cheap, easy, or fake.", "author": "Ukjent"},
    {"text": "In the end, it's not the years in your life that count, it's the lunches.", "author": "Abraham Lincoln (omtrent)"},
    {"text": "Mat som er laget med kjærlighet smaker alltid best. Mat laget av kollegaer smaker også greit.", "author": "Ukjent"},
    {"text": "A balanced diet is a cookie in each hand.", "author": "Barbara Johnson"},
    {"text": "I'm on a seafood diet. I see food and I eat it.", "author": "Klassiker"},
    {"text": "The secret ingredient is always cheese.", "author": "Enhver god kokk"},
    {"text": "Cooking is like love – it should be entered into with abandon or not at all.", "author": "Harriet van Horne"},
    {"text": "Først spiser vi, så gjør vi alt det andre.", "author": "Ukjent, men klok"},
    {"text": "A good meal is a good mood.", "author": "Ukjent"},
]

EMOJIS = ["🍕", "🥗", "🍱", "🌮", "🥪", "🍜", "🥘"]

GIPHY_SEARCH_TERMS = [
    "food fail", "cooking disaster", "pizza dance", "hungry cat food",
    "chef kiss", "food explosion", "spaghetti mess", "burger falling",
    "hot dog dance", "taco falling", "noodles slurp", "food baby",
]

def make_mention(name: str) -> tuple[str, dict | None]:
    """
    Returnerer (display_tekst, mention_entity) for en bruker.
    Hvis object_id er satt, brukes Teams @mention-format.
    Hvis ikke, faller vi tilbake til vanlig fet tekst.
    """
    user = USERS.get(name, {})
    object_id = user.get("object_id", "")
    email = user.get("email", "")

    if object_id:
        mention_text = f"<at>{name}</at>"
        entity = {
            "type": "mention",
            "text": f"<at>{name}</at>",
            "mentioned": {
                "id": object_id,
                "name": name,
            }
        }
        return mention_text, entity
    else:
        # Fallback: bare navn i fet tekst
        return f"**{name}**", None

def get_giphy_gif(api_key: str) -> str | None:
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
        print(f"⚠️  Kunne ikke hente GIF: {e}")
        return None

def get_current_week_entry():
    today = datetime.date.today()
    current_week = today.isocalendar()[1]
    current_year = today.isocalendar()[0]
    for entry in ROTATION:
        week_date = datetime.date.fromisoformat(entry["dato"])
        if week_date.isocalendar()[1] == current_week and week_date.isocalendar()[0] == current_year:
            return entry
    return None

def get_next_week_entry():
    today = datetime.date.today()
    next_week_num = (today + datetime.timedelta(weeks=1)).isocalendar()[1]
    next_year = (today + datetime.timedelta(weeks=1)).isocalendar()[0]
    for entry in ROTATION:
        week_date = datetime.date.fromisoformat(entry["dato"])
        if week_date.isocalendar()[1] == next_week_num and week_date.isocalendar()[0] == next_year:
            return entry
    return None

def send_teams_message(webhook_url: str, entry: dict, next_entry: dict = None, gif_url: str = None):
    names = entry["ansvarlige"]
    week_num = entry["uke"]
    emoji = EMOJIS[week_num % len(EMOJIS)]
    quote = random.choice(QUOTES)

    # Bygg mentions
    mention_texts = []
    entities = []
    for name in names:
        text, entity = make_mention(name)
        mention_texts.append(text)
        if entity:
            entities.append(entity)

    names_str = " og ".join(mention_texts)

    # Fallback-visning for FactSet (uten HTML-tags)
    plain_names = " og ".join(names)

    facts = [
        {"name": "Uke", "value": str(week_num)},
        {"name": "Ansvarlige", "value": plain_names},
    ]
    if next_entry:
        next_names = " og ".join(next_entry["ansvarlige"])
        facts.append({"name": "Neste uke", "value": f"Uke {next_entry['uke']}: {next_names}"})

    card_body = [
        {
            "type": "TextBlock",
            "text": f"{emoji} Lunsjansvar – uke {week_num}",
            "weight": "Bolder",
            "size": "Large",
            "wrap": True
        },
        {
            "type": "TextBlock",
            "text": f"Denne uken er det {names_str} som har ansvaret for lunsjen. Lykke til! 🙌",
            "wrap": True,
            "spacing": "Medium"
        },
        {
            "type": "FactSet",
            "facts": facts,
            "spacing": "Medium"
        },
        {
            "type": "TextBlock",
            "text": f"💬 *\"{quote['text']}\"*\n— {quote['author']}",
            "wrap": True,
            "isSubtle": True,
            "spacing": "Medium",
            "size": "Small"
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
        print(f"✅ Melding sendt! Status: {response.status}")
        print(f"   Uke {week_num}: {plain_names}")
        print(f"   Sitat: \"{quote['text']}\"")
        if gif_url:
            print(f"   GIF: {gif_url}")

def main():
    webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        print("❌ Mangler TEAMS_WEBHOOK_URL miljøvariabel")
        sys.exit(1)

    entry = get_current_week_entry()
    if not entry:
        print("⚠️  Ingen rotasjonsoppføring funnet for denne uken.")
        sys.exit(0)

    next_entry = get_next_week_entry()

    gif_url = None
    giphy_api_key = os.environ.get("GIPHY_API_KEY")
    if giphy_api_key:
        gif_url = get_giphy_gif(giphy_api_key)
    else:
        print("ℹ️  Ingen GIPHY_API_KEY – sender uten GIF.")

    send_teams_message(webhook_url, entry, next_entry, gif_url)

if __name__ == "__main__":
    main()
