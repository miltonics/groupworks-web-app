"""
fetch_hearts.py — scrape official heart text and patch groupworks.html
=======================================================================
Usage (Windows PowerShell):
    pip install requests beautifulsoup4 --break-system-packages
    python fetch_hearts.py

What it does:
1. Visits each of the 91 pattern pages on groupworksdeck.org
2. Extracts the "Heart:" paragraph (the official one-sentence description
   printed on the physical card)
3. Patches the d:'...' field for each card inside groupworks.html
4. Writes the result to groupworks.html (backs up original first)

Run this once after you have groupworks.html in the same folder.
The script is polite — it waits 1.5 seconds between requests.
"""

import re, time, pathlib, shutil, sys
import requests
from bs4 import BeautifulSoup

BASE = "https://groupworksdeck.org/patterns/"

# Same slug list as extract_cards.py / the app's DECK array
CARDS = [
    ("Commitment",                   "Commitment"),
    ("Invitation",                   "Invitation"),
    ("Priority Focus",               "Priority_Focus"),
    ("Purpose",                      "Purpose"),
    ("Setting Intention",            "Setting_Intention"),
    ("Aesthetics of Space",          "Aesthetics_of_Space"),
    ("Circle",                       "Circle"),
    ("Gaia",                         "Gaia"),
    ("Group Culture",                "Group_Culture"),
    ("History and Context",          "History_and_Context"),
    ("Nooks in Space and Time",      "Nooks_in_Space_and_Time"),
    ("Power of Place",               "Power_of_Place"),
    ("Whole System in the Room",     "Whole_System_in_the_Room"),
    ("Appreciation",                 "Appreciation"),
    ("Breaking Bread Together",      "Breaking_Bread_Together"),
    ("Celebrate",                    "Celebrate"),
    ("Good Faith Assumptions",       "Good_Faith_Assumptions"),
    ("Honour Each Person",           "Honour_Each_Person"),
    ("Hosting",                      "Hosting"),
    ("Power Shift",                  "Power_Shift"),
    ("Shared Airtime",               "Shared_Airtime"),
    ("Tend Relationships",           "Tend_Relationships"),
    ("Transparency",                 "Transparency"),
    ("Balance Process and Content",  "Balance_Process_and_Content"),
    ("Balance Structure and Flexibility","Balance_Structure_and_Flexibility"),
    ("Closing",                      "Closing"),
    ("Divergence and Convergence Rhythm","Divergence_and_Convergence_Rhythm"),
    ("Follow the Energy",            "Follow_the_Energy"),
    ("Iteration",                    "Iteration"),
    ("Opening and Welcome",          "Opening_and_Welcome"),
    ("Preparedness",                 "Preparedness"),
    ("Reflection-Action Cycle",      "Reflection_Action_Cycle"),
    ("Rest",                         "Rest"),
    ("Right Size Bite",              "Right_Size_Bite"),
    ("Ritual",                       "Ritual"),
    ("Seasoned Timing",              "Seasoned_Timing"),
    ("Subgroup and Whole Group",     "Subgroup_and_Whole_Group"),
    ("Trajectory",                   "Trajectory"),
    ("Challenge",                    "Challenge"),
    ("Expressive Arts",              "Expressive_Arts"),
    ("Generate Possibilities",       "Generate_Possibilities"),
    ("Improvise",                    "Improvise"),
    ("Mode Choice",                  "Mode_Choice"),
    ("Playfulness",                  "Playfulness"),
    ("Power of Constraints",         "Power_of_Constraints"),
    ("Common Ground",                "Common_Ground"),
    ("Embrace Dissonance and Difference","Embrace_Dissonance_and_Difference"),
    ("Fractal",                      "Fractal"),
    ("Go Meta",                      "Go_Meta"),
    ("Seeing the Forest, Seeing the Trees","Seeing_the_Forest_Seeing_the_Trees"),
    ("Time Shift",                   "Time_Shift"),
    ("Translation",                  "Translation"),
    ("Unity and Diversity",          "Unity_and_Diversity"),
    ("Value the Margins",            "Value_the_Margins"),
    ("Viewpoint Shift",              "Viewpoint_Shift"),
    ("Appropriate Boundaries",       "Appropriate_Boundaries"),
    ("Courageous Modelling",         "Courageous_Modelling"),
    ("Discharging",                  "Discharging"),
    ("Dwell with Emotions",          "Dwell_with_Emotions"),
    ("Guerrilla Facilitation",       "Guerrilla_Facilitation"),
    ("Holding Space",                "Holding_Space"),
    ("Listening",                    "Listening"),
    ("Mirroring",                    "Mirroring"),
    ("Not about You",                "Not_about_You"),
    ("Self-Awareness",               "Self_Awareness"),
    ("Shared Leadership and Roles",  "Shared_Leadership_and_Roles"),
    ("Simplify",                     "Simplify"),
    ("Taking Responsibility",        "Taking_Responsibility"),
    ("Witness with Compassion",      "Witness_with_Compassion"),
    ("Deliberate",                   "Deliberate"),
    ("Distilling",                   "Distilling"),
    ("Experts on Tap",               "Experts_on_Tap"),
    ("Feedback",                     "Feedback"),
    ("Go Deeper",                    "Go_Deeper"),
    ("Harvesting",                   "Harvesting"),
    ("Inform the Group Mind",        "Inform_the_Group_Mind"),
    ("Inquiry",                      "Inquiry"),
    ("Mapping and Measurement",      "Mapping_and_Measurement"),
    ("Moving toward Alignment",      "Moving_toward_Alignment"),
    ("Naming",                       "Naming"),
    ("Story",                        "Story"),
    ("Yes, and",                     "Yes_and"),
    ("All Grist for the Mill",       "All_Grist_for_the_Mill"),
    ("Dive In",                      "Dive_In"),
    ("Emergence",                    "Emergence"),
    ("Letting Go",                   "Letting_Go"),
    ("Magic",                        "Magic"),
    ("Presence",                     "Presence"),
    ("Silence",                      "Silence"),
    ("Spirit",                       "Spirit"),
    ("Trust the Wisdom of the Group","Trust_the_Wisdom_of_the_Group"),
]

HEADERS = {"User-Agent": "GroupWorksCardApp/1.0 (companion viewer; contact via groupworks.org)"}

def fetch_page(slug: str):
    """Fetch a pattern page and return (heart, related, soup) or (None, [], None)."""
    url = BASE + slug
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"    fetch error: {e}")
        return None, [], None

    soup = BeautifulSoup(r.text, "html.parser")
    body_text = soup.get_text("\n")

    heart = None
    m = re.search(r"Heart:\s*\n(.+?)(?:\n|Description:)", body_text, re.DOTALL)
    if m:
        candidate = re.sub(r"\s+", " ", m.group(1)).strip()
        if len(candidate) > 20:
            heart = candidate

    if heart is None:
        for tag in soup.find_all(["p","div","span"]):
            if tag.get_text().strip().startswith("Heart:"):
                text = re.sub(r"\s+", " ", tag.get_text().replace("Heart:","")).strip()
                if len(text) > 20:
                    heart = text
                    break

    related = fetch_related(soup)
    return heart, related, soup

def fetch_related(soup: 'BeautifulSoup') -> list[str]:
    """Return list of related pattern names from a pattern page."""
    body_text = soup.get_text("\n")
    # The related list typically follows the word "related:" and is
    # separated by ~ (tilde) characters, e.g.
    # "related: Common Ground ~ History and Context ~ Invitation ..."
    m = re.search(r"related:\s*(.+?)(?:\n\d+\s*$|\Z)", body_text, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    chunk = m.group(1)
    # Normalise whitespace/newlines, then split on ~ separators
    chunk = re.sub(r"\s+", " ", chunk).strip()
    # Drop a trailing page number if present
    chunk = re.sub(r"\s*\d{1,3}\s*$", "", chunk)
    parts = [p.strip(" .") for p in chunk.split("~")]
    return [p for p in parts if p]

def js_escape(s: str) -> str:
    """Escape a string for safe inclusion inside JS single-quoted string."""
    return (s.replace("\\", "\\\\")
             .replace("'",  "\\'")
             .replace("\n", " ")
             .replace("\r", ""))

def patch_html(html: str, name: str, heart: str) -> str:
    """Replace the d:'...' value for the named card in the HTML."""
    escaped = js_escape(heart)
    # Pattern: {n:'<name>',c:<n>,s:'<slug>',d:'<old>',rel:[...]}
    pattern = re.compile(
        r"(\{n:'" + re.escape(name) + r"',c:\d+,s:'[^']+',d:')([^']*?)('\s*,\s*rel:)"
    )
    if pattern.search(html):
        return pattern.sub(r"\g<1>" + escaped + r"\g<3>", html)
    return html   # no match — leave unchanged

def patch_rel(html: str, name: str, rel: list[str]) -> str:
    """Replace the rel:[...] value for the named card in the HTML."""
    rel_js = "[" + ",".join("'" + js_escape(r) + "'" for r in rel) + "]"
    pattern = re.compile(
        r"(\{n:'" + re.escape(name) + r"',c:\d+,s:'[^']+',d:'(?:[^'\\]|\\.)*',rel:)\[[^\]]*\](\})"
    )
    if pattern.search(html):
        return pattern.sub(lambda m: m.group(1) + rel_js + m.group(2), html)
    return html

def main():
    html_file = pathlib.Path("groupworks.html")
    if not html_file.exists():
        print("groupworks.html not found in the current directory.")
        print("Run this script from the same folder as the app file.")
        sys.exit(1)

    # Backup
    backup = pathlib.Path("groupworks.html.bak")
    shutil.copy(html_file, backup)
    print(f"Backup saved to {backup}\n")

    html = html_file.read_text(encoding="utf-8")
    results = {}
    failed  = []

    for i, (name, slug) in enumerate(CARDS, 1):
        print(f"[{i:02d}/91] {name} ...", end=" ", flush=True)
        heart, related, soup = fetch_page(slug)
        if heart:
            print(f"OK  ({len(heart)} chars, {len(related)} related)")
            html = patch_html(html, name, heart)
            results[name] = heart
        else:
            print(f"FAILED heart — keeping placeholder ({len(related)} related found)")
            failed.append(name)
        if related:
            html = patch_rel(html, name, related)
        time.sleep(1.5)   # be polite to the server

    html_file.write_text(html, encoding="utf-8")
    print(f"\nUpdated groupworks.html written.")

    if failed:
        print(f"\nFailed to fetch {len(failed)} card(s):")
        for n in failed:
            print(f"  {n}")
        print("Visit each pattern page manually and paste the Heart text")
        print("into the d:'...' field in groupworks.html using Notepad++.")
    else:
        print("\nAll 91 hearts fetched and patched successfully.")

if __name__ == "__main__":
    main()
