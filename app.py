"""
Campus Compass — BUas Student Life Navigator
=============================================
Terminal chatbot that runs in VS Code.
No API keys needed. No installs needed. Just Python + your CSV.

How to run:
    1. Place BUas_Campus_Compass_Dataset_FINAL.csv in the same folder
    2. Open terminal in VS Code
    3. Run: python app.py
"""

import csv
import os
import random

# ============================================================
# CONFIGURATION
# ============================================================

CSV_PATH = "BUas_Campus-Compass_Dataset_FINAL.csv"

# ============================================================
# LOAD CSV KNOWLEDGE BASE
# ============================================================

def load_csv(filepath):
    """Load CSV file into a list of dictionaries."""
    entries = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)
        print(f"  ✅ Loaded {len(entries)} campus entries from CSV\n")
    except FileNotFoundError:
        print(f"  ⚠️  File not found: {filepath}")
        print(f"  Make sure the CSV is in the same folder as this script.\n")
    return entries

# ============================================================
# SEARCH & FILTER FUNCTIONS
# ============================================================

def search(entries, query="", category=None, programme=None, year=None, tags=None):
    """
    Search the knowledge base with optional filters.
    Returns matching entries sorted by relevance.
    """
    results = []
    query_words = query.lower().split() if query else []

    for entry in entries:
        # --- Apply filters ---
        if category:
            if entry.get("category", "").lower() != category.lower():
                continue

        if programme:
            target_prog = entry.get("target_programme", "").lower()
            if "all" not in target_prog and programme.lower() not in target_prog:
                continue

        if year:
            target_year = entry.get("target_year", "").lower()
            if "all" not in target_year and str(year) not in target_year:
                continue

        # --- Score by keyword match ---
        searchable = " ".join([
            entry.get("name", ""),
            entry.get("description", ""),
            entry.get("tags", ""),
            entry.get("category", ""),
        ]).lower()

        if query_words:
            score = sum(1 for w in query_words if w in searchable)
            if score == 0:
                continue
        else:
            score = 1  # No query = return all filtered results

        if tags:
            tag_list = tags.lower().split(";")
            entry_tags = entry.get("tags", "").lower()
            score += sum(2 for t in tag_list if t in entry_tags)

        results.append((score, entry))

    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results]


def get_by_category(entries, category):
    """Get all entries of a specific category."""
    return [e for e in entries if e.get("category", "").lower() == category.lower()]


def format_entry(entry, index=None):
    """Format a single entry for display."""
    prefix = f"  {index}." if index else "  •"
    name = entry.get("name", "Unknown")
    desc = entry.get("description", "")
    deadline = entry.get("deadline", "")
    date_start = entry.get("date_start", "")
    location = entry.get("location", "")
    category = entry.get("category", "").upper()

    lines = [f"{prefix} [{category}] {name}"]
    lines.append(f"     {desc}")
    if deadline:
        lines.append(f"     📅 Deadline: {deadline}")
    if date_start:
        lines.append(f"     🗓️  Date: {date_start}")
    if location:
        lines.append(f"     📍 Location: {location}")
    return "\n".join(lines)


# ============================================================
# STUDENT PROFILE
# ============================================================

class StudentProfile:
    """Stores info about the current student for personalisation."""

    def __init__(self):
        self.programme = None
        self.year = None
        self.interests = []
        self.name = None

    def is_complete(self):
        return self.programme is not None and self.year is not None

    def summary(self):
        interests_str = ", ".join(self.interests) if self.interests else "not specified yet"
        return (
            f"  Programme: {self.programme or 'Unknown'}\n"
            f"  Year: {self.year or 'Unknown'}\n"
            f"  Interests: {interests_str}"
        )


# ============================================================
# INTEREST MAPPING — connects words to CSV tags
# ============================================================

INTEREST_MAP = {
    "sports": "sports;fitness;rowing;tennis;outdoor;running",
    "social": "social;networking;parties;nightlife;casual",
    "creative": "creative;theatre;music;performance;design;immersive",
    "career": "career;internship;networking;companies;CV;professional",
    "international": "international;exchange;cultural",
    "academic": "academic;research;conference;sustainability",
    "gaming": "games;esports;tabletop;gaming",
    "music": "music;performance;creative;festivals",
    "food": "cooking;food;hospitality;restaurant",
    "tech": "data-science;AI;tech;analytics;programming",
    "events": "events;experience-design;festivals;entertainment",
    "nature": "outdoor;park;running;cycling;nature",
}

PROGRAMME_MAP = {
    "1": "Data Science & AI",
    "2": "Games",
    "3": "Creative Business",
    "4": "Built Environment",
    "5": "Hotel",
    "6": "Facility",
    "7": "Leisure & Events",
    "8": "Tourism",
    "9": "Logistics",
    "data": "Data Science & AI",
    "ai": "Data Science & AI",
    "games": "Games",
    "creative": "Creative Business",
    "media": "Creative Business",
    "built": "Built Environment",
    "hotel": "Hotel",
    "facility": "Facility",
    "leisure": "Leisure & Events",
    "events": "Leisure & Events",
    "tourism": "Tourism",
    "logistics": "Logistics",
}


# ============================================================
# CAMPUS COMPASS CHATBOT
# ============================================================

class CampusCompass:
    """The Campus Compass AI Persona chatbot."""

    def __init__(self, entries):
        self.entries = entries
        self.profile = StudentProfile()
        self.state = "greeting"  # greeting → get_programme → get_year → get_interests → chatting
        self.greeted = False

    # --- Main response handler ---
    def respond(self, user_input):
        """Process user input and return a response based on current state."""
        text = user_input.strip().lower()

        # Handle commands
        if text in ("quit", "exit", "bye", "q"):
            return self.say_goodbye()
        if text in ("reset", "new", "start over"):
            return self.reset()
        if text in ("profile", "me", "my profile"):
            return self.show_profile()
        if text in ("help", "?"):
            return self.show_help()

        # State machine
        if self.state == "greeting":
            self.state = "get_programme"
            return self.ask_programme()

        elif self.state == "get_programme":
            return self.handle_programme(text)

        elif self.state == "get_year":
            return self.handle_year(text)

        elif self.state == "get_interests":
            return self.handle_interests(text)

        elif self.state == "chatting":
            return self.handle_chat(text)

        return "Hmm, I got a bit confused. Type 'reset' to start over!"

    # --- State handlers ---

    def ask_programme(self):
        lines = [
            "To give you the best recommendations, I need to know a bit about you! 🎯",
            "",
            "What programme are you in?",
            "",
            "  1. Data Science & AI",
            "  2. Games",
            "  3. Creative Business",
            "  4. Built Environment",
            "  5. Hotel Management",
            "  6. Facility Management",
            "  7. Leisure & Events",
            "  8. Tourism",
            "  9. Logistics",
            "",
            "Type the number or name:"
        ]
        return "\n".join(lines)

    def handle_programme(self, text):
        # Try to match input to a programme
        matched = None
        for key, prog in PROGRAMME_MAP.items():
            if key in text:
                matched = prog
                break

        if not matched:
            return "I didn't catch that. Type a number (1-9) or the programme name:"

        self.profile.programme = matched
        self.state = "get_year"

        return (
            f"Nice! {matched} is a great programme! 🎉\n\n"
            "What year are you in?\n\n"
            "  1. First year\n"
            "  2. Second year\n"
            "  3. Third year\n"
            "  4. Fourth year\n"
            "  5. Master\n\n"
            "Type the number:"
        )

    def handle_year(self, text):
        year_map = {"1": "1", "2": "2", "3": "3", "4": "4", "5": "Master",
                     "first": "1", "second": "2", "third": "3", "fourth": "4", "master": "Master"}

        matched = None
        for key, yr in year_map.items():
            if key in text:
                matched = yr
                break

        if not matched:
            return "Just type a number (1-5) for your year:"

        self.profile.year = matched
        self.state = "get_interests"

        return (
            f"Year {matched} — got it! ✅\n\n"
            "Last question: what are you most interested in?\n"
            "Pick one or more (separate with commas):\n\n"
            "  • sports       • social      • creative\n"
            "  • career       • international • academic\n"
            "  • gaming       • music       • food\n"
            "  • tech         • events      • nature\n\n"
            "Or just type 'skip' to see everything:"
        )

    def handle_interests(self, text):
        if text != "skip":
            for interest in INTEREST_MAP:
                if interest in text:
                    self.profile.interests.append(interest)

        self.state = "chatting"

        response = f"Awesome, here's your profile:\n\n{self.profile.summary()}\n\n"
        response += "=" * 50 + "\n\n"
        response += self.get_personalised_overview()
        response += (
            "\n\nWhat would you like to explore?\n"
            "  • Type 'clubs' to see all clubs\n"
            "  • Type 'events' to see upcoming events\n"
            "  • Type 'deadlines' to see important dates\n"
            "  • Type 'internships' to explore opportunities\n"
            "  • Or just ask me anything!"
        )
        return response

    def handle_chat(self, text):
        """Handle free conversation once profile is set."""

        # Category browsing
        if any(w in text for w in ["club", "clubs", "association", "join"]):
            return self.recommend("club")
        if any(w in text for w in ["event", "events", "happening", "coming up"]):
            return self.recommend("event")
        if any(w in text for w in ["deadline", "deadlines", "due", "date", "when"]):
            return self.recommend("deadline")
        if any(w in text for w in ["internship", "internships", "job", "work", "career", "stage"]):
            return self.recommend("internship")

        # Interest-based queries
        if any(w in text for w in ["sport", "sports", "fitness", "gym", "active"]):
            return self.search_and_respond(text, tags="sports;fitness;outdoor")
        if any(w in text for w in ["social", "friends", "people", "meet", "party"]):
            return self.search_and_respond(text, tags="social;networking;parties")
        if any(w in text for w in ["creative", "art", "theatre", "music", "perform"]):
            return self.search_and_respond(text, tags="creative;theatre;music;performance")
        if any(w in text for w in ["international", "exchange", "abroad", "erasmus"]):
            return self.search_and_respond(text, tags="international;exchange;cultural")
        if any(w in text for w in ["minor", "minors"]):
            return self.minor_info()
        if any(w in text for w in ["new", "first", "just started", "arrived", "freshman"]):
            return self.new_student_tips()

        # General search
        results = search(self.entries, query=text, programme=self.profile.programme)
        if results:
            return self.format_results(results[:5], f"Here's what I found for '{text}':")

        return (
            "Hmm, I couldn't find a direct match for that. 🤔\n\n"
            "Try asking about:\n"
            "  • clubs, events, deadlines, or internships\n"
            "  • specific interests like 'sports' or 'creative'\n"
            "  • or type 'help' to see all commands"
        )

    # --- Recommendation functions ---

    def recommend(self, category):
        """Get personalised recommendations for a category."""
        year = self.profile.year if self.profile.year != "Master" else "Master"
        results = search(
            self.entries,
            category=category,
            programme=self.profile.programme,
            year=year,
            tags=";".join(self.profile.interests) if self.profile.interests else None
        )

        # If personalised search gives few results, broaden it
        if len(results) < 3:
            results = get_by_category(self.entries, category)

        cat_label = {
            "club": "clubs & associations",
            "event": "events",
            "deadline": "deadlines",
            "internship": "internship opportunities"
        }.get(category, category)

        title = f"Here are the {cat_label} I'd recommend for you:"
        if self.profile.programme:
            title = f"As a year {self.profile.year} {self.profile.programme} student, here are your top {cat_label}:"

        return self.format_results(results[:7], title)

    def search_and_respond(self, query, tags=None):
        """Search with tags and format response."""
        results = search(
            self.entries, query=query,
            programme=self.profile.programme,
            year=self.profile.year,
            tags=tags
        )
        if not results:
            results = search(self.entries, query=query, tags=tags)

        if results:
            return self.format_results(results[:5], "Great question! Here's what I found:")
        return "I couldn't find anything matching that. Try a different keyword!"

    def get_personalised_overview(self):
        """Generate a personalised welcome overview."""
        lines = ["🧭 YOUR PERSONALISED CAMPUS HIGHLIGHTS\n"]

        # Top club recommendation
        clubs = search(self.entries, category="club", programme=self.profile.programme,
                       tags=";".join(self.profile.interests) if self.profile.interests else None)
        if clubs:
            c = clubs[0]
            lines.append(f"🎭 Top club for you: {c['name']}")
            lines.append(f"   {c['description'][:80]}...\n")

        # Next upcoming event
        events = search(self.entries, category="event", programme=self.profile.programme,
                        year=self.profile.year)
        if events:
            e = events[0]
            lines.append(f"📅 Don't miss: {e['name']}")
            lines.append(f"   Date: {e.get('date_start', 'TBD')} | {e.get('location', 'BUas Campus')}\n")

        # Important deadline
        deadlines = search(self.entries, category="deadline", programme=self.profile.programme,
                           year=self.profile.year)
        if deadlines:
            d = deadlines[0]
            lines.append(f"⏰ Key deadline: {d['name']}")
            lines.append(f"   Due: {d.get('deadline', 'TBD')}\n")

        # Internship if year 3+
        if self.profile.year in ("3", "4", "Master"):
            internships = search(self.entries, category="internship",
                                 programme=self.profile.programme)
            if internships:
                i = internships[0]
                lines.append(f"💼 Internship tip: {i['name']}")
                lines.append(f"   {i['description'][:80]}...")

        return "\n".join(lines)

    def minor_info(self):
        """Provide minor-related info."""
        deadlines = search(self.entries, query="minor", category="deadline")
        response = (
            "📚 MINORS AT BUas\n\n"
            "BUas offers 23 minors in your 3rd year. Here's what you need to know:\n\n"
        )
        if deadlines:
            for d in deadlines[:3]:
                response += f"  ⏰ {d['name']}\n     Deadline: {d.get('deadline', 'TBD')}\n\n"

        response += (
            "  💡 Tip: Attend the Minor Information Evening to meet all coordinators!\n\n"
            "Want to know about a specific minor? Just ask!"
        )
        return response

    def new_student_tips(self):
        """Tips for new/first-year students."""
        tips = search(self.entries, query="introduction welcome international first",
                      year="1")
        response = (
            "Welcome to BUas! 🎉 Here are my top tips for new students:\n\n"
        )
        # Always recommend these
        essentials = search(self.entries, query="ESN welcome week BRESS", year="1")
        for e in essentials[:4]:
            response += f"  • {e['name']}: {e['description'][:70]}...\n"
            if e.get("date_start"):
                response += f"    📅 {e['date_start']}\n"
            response += "\n"

        response += (
            "  📌 Also remember:\n"
            "  • Get a bike — Breda is a cycling city!\n"
            "  • BUas has no campus housing — start searching early\n"
            "  • International students: arrange health insurance before arrival\n\n"
            "Want more details on any of these?"
        )
        return response

    # --- Utility functions ---

    def format_results(self, results, title):
        """Format a list of results for display."""
        if not results:
            return "I couldn't find anything matching that. Try a different search!"

        lines = [title, ""]
        for i, entry in enumerate(results, 1):
            lines.append(format_entry(entry, index=i))
            lines.append("")
        return "\n".join(lines)

    def show_profile(self):
        if not self.profile.is_complete():
            return "I don't know much about you yet. Let's fix that — what programme are you in?"
        return f"Here's what I know about you:\n\n{self.profile.summary()}"

    def show_help(self):
        return (
            "🧭 CAMPUS COMPASS — COMMANDS\n\n"
            "  clubs         → Browse clubs & associations\n"
            "  events        → See upcoming events\n"
            "  deadlines     → Check important dates\n"
            "  internships   → Explore opportunities\n"
            "  minors        → Learn about minors\n"
            "  profile       → See your current profile\n"
            "  reset         → Start a new conversation\n"
            "  help          → Show this menu\n"
            "  quit          → Exit\n\n"
            "Or just ask me anything in your own words!"
        )

    def say_goodbye(self):
        return (
            f"Bye! Good luck with your studies at BUas! 🎓\n"
            "Remember — there's always something cool happening on campus. "
            "Come back anytime!"
        )

    def reset(self):
        self.profile = StudentProfile()
        self.state = "greeting"
        return "Starting fresh! Let's go again 🔄"


# ============================================================
# MAIN — Run in terminal
# ============================================================

def main():
    os.system("cls" if os.name == "nt" else "clear")

    print("=" * 55)
    print("  🧭 CAMPUS COMPASS — BUas Student Life Navigator")
    print("=" * 55)
    print()

    # Load knowledge base
    entries = load_csv(CSV_PATH)
    if not entries:
        print("Cannot run without the CSV knowledge base.")
        print(f"Place '{CSV_PATH}' in the same folder and try again.")
        return

    # Create chatbot
    bot = CampusCompass(entries)

    # Welcome message
    print("-" * 55)
    print("  Hey there! Welcome to BUas! 🎉")
    print("  I'm Campus Compass — your personal guide to")
    print("  everything happening on campus.")
    print()
    print("  Type 'help' for commands or 'quit' to exit.")
    print("-" * 55)
    print()

    # Initial prompt
    response = bot.respond("start")
    print(f"🧭 Campus Compass:\n{response}\n")

    # Conversation loop
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            print(bot.say_goodbye())
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q", "bye"):
            print(f"\n🧭 Campus Compass:\n{bot.say_goodbye()}\n")
            break

        response = bot.respond(user_input)
        print(f"\n🧭 Campus Compass:\n{response}\n")


if __name__ == "__main__":
    main()