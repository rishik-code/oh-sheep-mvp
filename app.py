import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
from cities import iata_codes, destination_images

# 👇 NEW CACHE FUNCTION: Loads data once and keeps it in memory!
@st.cache_data
def load_expert_data():
    try:
        with open("trips_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@st.cache_resource
def init_ai_brain():
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("models/gemini-3-flash-preview")
    return None

gemini_model = init_ai_brain()

# --- 1. THE FOUNDATION ---
load_dotenv(override=True)

# The Smart Bridge: Broadened to catch ALL local Streamlit exceptions
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    api_key = os.getenv("GEMINI_API_KEY")

# Failsafe: Prevent crash if key is entirely missing
if not api_key:
    st.warning("⚠️ API Key is missing! Check your .env file locally or Secrets in the cloud.")
else:
    genai.configure(api_key=api_key)

STAY22_AID = os.getenv("STAY22_AID", "12345")


# --- CUSTOM CSS (Premium Travel Magazine UI) ---
def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Global Background - Airy and Light */
        .stApp { background-color: #F9FAFB !important; }
        
        /* Global Text to Premium Dark Slate */
        html, body, [data-testid="stWidgetLabel"], p, span, div, h1, h2, h3, h4 {
            color: #1F2937 !important;
            font-family: 'Inter', sans-serif;
        }

        /* OCEAN BLUE LINKS */
        a { color: #0284C7 !important; text-decoration: none !important; font-weight: 700 !important; }
        a:hover { text-decoration: underline !important; }

        /* INPUT BOXES & FORMS */
        /* INPUT BOXES & FORMS */
        div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
            background-color: #FFFFFF !important; 
            border-radius: 8px !important; 
            border: 1px solid #E5E7EB !important; 
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }
        [data-testid="stForm"] { background-color: #FFFFFF !important; border: 1px solid #E5E7EB !important; border-radius: 12px !important; }
        
        /* FIX FOR DROPDOWN MENUS (POPOVERS) */
        [data-baseweb="popover"], [data-baseweb="menu"] { 
            background-color: #FFFFFF !important; 
        }
        li[role="option"] { 
            background-color: #FFFFFF !important; 
            color: #1F2937 !important; 
        }
        li[role="option"]:hover { 
            background-color: #F9FAFB !important; 
        }

        /* NUMBER INPUT +/- BUTTON FIX */
        button[kind="stepUp"], button[kind="stepDown"] { background-color: #F3F4F6 !important; }
        button[kind="stepUp"] svg, button[kind="stepDown"] svg { fill: #1F2937 !important; }

        /* EXPANDER HEADER FIX */
        [data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #E5E7EB !important; border-radius: 12px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; }
        [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span, [data-testid="stExpander"] summary svg {
            color: #1F2937 !important; fill: #1F2937 !important; font-weight: bold !important; background-color: #FFFFFF !important;
        }
        [data-testid="stExpander"] summary:hover { background-color: #F9FAFB !important; }

        /* BUTTONS */
        div.stButton > button {
            background-color: #E8DCC4 !important; color: #1F2937 !important; font-weight: 700 !important; border: 1px solid #D6C5AD !important; border-radius: 8px !important; height: 3.5em; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; transition: all 0.2s ease-in-out;
        }
        div.stButton > button:hover { background-color: #D6C5AD !important; box-shadow: 0 6px 8px rgba(0,0,0,0.08) !important; }

        /* IMAGE GALLERY UNIFORMITY */
        [data-testid="stImage"] img { pointer-events: none; border-radius: 12px; width: 100% !important; aspect-ratio: 16 / 9; object-fit: cover; display: block; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        
        /* THE ITINERARY CARD */
        .div[data-testid="stMarkdownContainer"]:has(.itinerary-marker){ background-color: #FFFFFF; padding: 40px; border-radius: 12px; border: 1px solid #F3F4F6; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); margin-bottom: 25px; line-height: 1.8; }
        
        /* THE HERO TITLE */
        .block-container { padding-top: 1rem !important; }
        [data-testid="stHeader"] { display: none !important; }
        .hero-container { background: linear-gradient(180deg, #FFFFFF 0%, #F3F4F6 100%); padding: 40px 20px 30px 20px; margin-top: -15px; margin-bottom: 40px; border-bottom: 1px solid #E5E7EB; text-align: center; width: 100%; border-radius: 0px; box-shadow: none !important; }
        .hero-title { font-size: 4em !important; font-weight: 900 !important; margin: 0px !important; letter-spacing: -1.5px; color: #111827 !important; }
        .hero-subtitle { color: #6B7280 !important; font-size: 1.2em; margin: 10px 0px 0px 0px !important; }
        </style>
    """,
        unsafe_allow_html=True,
    )

# --- 2. INITIALIZE MEMORY ---
if "itinerary" not in st.session_state:
    st.session_state.itinerary = None
if "request_prepped" not in st.session_state:
    st.session_state.request_prepped = False
if "final_confirmed" not in st.session_state:
    st.session_state.final_confirmed = False

# --- 3. AFFILIATE LOGIC ---
def create_stay22_link(location, style):
    search_query = f"{location}+{style}+hotel"
    return f"https://www.stay22.com/allez/go?aid={STAY22_AID}&address={search_query.replace(' ', '+')}"

def create_flight_link(origin, destination):
    return "https://tp.media/click?shmarker=722430&promo_id=3413&source_type=link&type=click&campaign_id=111&trs=522560"

# --- 4. THE BRAIN ---
def get_rk_itinerary(user_request, expert_data):
    # 👇 Grab the instant, cached model from memory!
    model = init_ai_brain() 
    
    if not model:
        return "⚠️ The AI Brain is resting (API key missing). Please check your settings."

    matching_trip = next(
        (item for item in expert_data if item["city"].lower() in user_request["destination"].lower()), None
    )

    expert_injection = (
        f"EXCLUSIVE R&K SECRETS TO USE: Pro Tip: {matching_trip['pro_tip']} | Local Secret: {matching_trip['local_secret']}"
        if matching_trip else "Create unique, unconventional tips to avoid tourist traps."
    )

    f_url = create_flight_link(user_request["origin"], user_request["destination"])
    
    system_instructions = f"""
    You are the 'Oh Sheep!' Boutique AI Architect. 
    
    YOUR PERSONALITY & RULES:
    - Your tone must be warm, friendly, human, and highly readable. Speak like a well-traveled friend giving advice over coffee.
    - You are an expert itinerary creator, NOT a travel agent. NEVER say "we will book this for you". Always tell the user to use the provided links to book themselves.
    - MUST DO: **Bold** all specific locations, landmarks, cafes, and restaurant names so they are easy to scan.
    - Keep it breathable. Avoid dense "walls of text".
    
    STRUCTURE YOUR RESPONSE EXACTLY AS FOLLOWS:
    1. 🗺️ **The Route Summary:** Start with a short, welcoming introduction. explicitly outline the logistics:
       - If {user_request["destination"]} is a country: Format it similar to: "Fly into [City A], spend [X] days here, then head to [City B] for [Y] days, and fly out of [City C]."
       - If {user_request["destination"]} is a specific city: "The itinerary below is designed for you to spend your entire {user_request["days"]}-day trip deeply exploring {user_request["destination"]}."
       
    2. 🔗 **Quick Booking Dashboard:** Immediately after the summary, create a clean list of links.
       **✈️ Flights:** <a href="{f_url}" target="_blank">Check Flights to {user_request["destination"]}</a>
       **🏨 Hotels:** <a href="https://www.stay22.com/allez/go?aid={STAY22_AID}&address=[CITY_A]+{user_request["style"]}+hotel" target="_blank">Curated Stays in [CITY_A]</a>
    
    3. 📅 **The Daily Breakdown:** For each day, start with the exact text "### Day [Number]: [City Name]". 
       - 🏨 **The Local Stay:** If this is the FIRST day arriving in a new city, insert the hotel link.
       - 🌅 **Morning:** [2 activities max. Make cafe name a clickable Google Maps link]
       - ☀️ **Afternoon:** [2 activities max. Make restaurant name a clickable Google Maps link]
       - 🌙 **Evening:** [2 activities max. Make restaurant name a clickable Google Maps link]
       
    4. 🦙 **Ditch the Flock Tips:** Provide 3 to 5 unique tips formatted as bullets.
       
    5. FINAL LINE: 
       "Note: This is an AI-powered itinerary. In order to get a custom-made Ditch the Flock version vetted by our human experts, please fill out the <a href='#ditch-the-flock-form'>request form</a>."

    GROUNDING: {expert_injection}.
    """
    
    pref_instruction = ""
    if user_request.get("preferences"):
        pref_instruction = f"CRITICAL PERSONALIZATION: The user specifically requested these vibes: {', '.join(user_request['preferences'])}. You MUST heavily tailor the activities, restaurants, and tone to match these exact preferences."

    user_prompt = f"""
    Plan a {user_request["days"]}-day {user_request["style"]} trip to {user_request["destination"]} for a {user_request["group"]}. 
    
    {pref_instruction}
    
    CRITICAL LOGIC:
    - If {user_request["destination"]} is a specific city, focus deeply on that city.
    - If {user_request["destination"]} is a country, create a logical multi-city journey.
    """

    try:
        response = model.generate_content([system_instructions, user_prompt])
        return response.text
    except Exception as e:
        return "⚠️ The sheep are resting. Please try again!"

# --- 5. UI LAYOUT ---
st.set_page_config(page_title="Oh Sheep!", page_icon="🐑", layout="wide")
inject_custom_css()

st.markdown(
    """
    <div class="hero-container">
        <h1 class="hero-title">🐑 Oh Sheep!</h1>
        <p class="hero-subtitle">Boutique Itinerary Creators. Stop following the herd.</p>
    </div>
    """, unsafe_allow_html=True
)

with st.container():
    st.write("---")
    european_cities = sorted(list(iata_codes.keys()))
    pop_cities = ["Paris", "Rome", "London", "Amsterdam"]
    pop_countries = ["Italy", "France", "Spain", "Greece", "Portugal"]
    other_destinations = sorted([loc for loc in iata_codes.keys() if loc not in pop_cities and loc not in pop_countries])

    grouped_destinations = (
        ["--- POPULAR CITIES ---"] + pop_cities + 
        ["--- POPULAR COUNTRIES ---"] + pop_countries + 
        ["--- OTHER DESTINATIONS ---"] + other_destinations
    )

    destination = st.selectbox(
        "Destination: Where do you want to go grazing?",
        options=grouped_destinations,
        index=None,
        placeholder="City or Country... e.g., Italy",
    )

    col_days, col_style, col_group = st.columns(3)
    with col_days: days = st.number_input("Days", 1, 14, 5)
    with col_style: style = st.selectbox("Style", ["Budget", "Mid-range", "Luxury"])
    with col_group: group = st.selectbox("With?", ["Solo", "Couple", "Family", "Friends"])

    st.write("")
    preferences = st.multiselect(
        "Trip Vibe & Preferences (Optional)",
        [
            "🏛️ Time Traveler (History & Ruins)",
            "🗺️ The Off-Trail Explorer (Hidden gems only)",
            "🎬 Pop Culture Buff (Film & book locations)",
            "🍷 The Epicurean (Deep local culinary & wine)",
            "🌱 Plant-Based (Vegan & Vegetarian focus)",
        ],
        placeholder="Select what you love to tailor your itinerary...",
        max_selections=5,
    )

    _, btn_col, _ = st.columns([1.5, 1, 1.5])
    with btn_col:
        if st.button("Generate My Itinerary", use_container_width=True):
            if not destination or destination.startswith("---"):
                st.error("🐑 Please select a valid city or country from the list!")
            else:
                with st.spinner("🐑 The sheep are awake and are coming up with your itinerary..."):
                    # Now it loads instantly from memory!
                    my_trips = load_expert_data()

                    user_info = {
                        "origin": "Auto-detect",
                        "destination": destination,
                        "days": days,
                        "style": style,
                        "group": group,
                        "preferences": preferences,
                    }
                    st.session_state.itinerary = get_rk_itinerary(user_info, my_trips)
                    st.session_state.request_prepped = False
                    st.session_state.final_confirmed = False
                    st.rerun()

# --- 6. RESULTS DISPLAY (The Split Funnel) ---
if st.session_state.itinerary:
    st.write("---")
    res_left, res_right = st.columns([1.5, 1], gap="large")

    with res_left:
        st.write("### 🐑 Your Sheep-Approved Itinerary")
        st.markdown(f'<div class="itinerary-marker"></div>\n\n{st.session_state.itinerary}', 
            unsafe_allow_html=True)

    with res_right:
        st.markdown("<div id='ditch-the-flock-form'></div>", unsafe_allow_html=True)
        st.write("### 🦙 Ditch the Flock")
        st.info(f"Generic trips are for sheep. Let us build you a 1-on-1 personalized itinerary for {destination} filled with local secrets and hidden gems.")

        if not st.session_state.request_prepped:
            with st.expander("📩 Request a Full Ditch the Flock Itinerary", expanded=True):
                with st.form("bespoke_request"):
                    st.write("#### 👥 Guest Details")
                    gc1, gc2, gc3 = st.columns(3)
                    with gc1: adults = st.selectbox("Adults 18+", options=list(range(0, 11)), index=2)
                    with gc2: young_adults = st.selectbox("Young Adults 12-18", options=list(range(0, 11)), index=0)
                    with gc3: children = st.selectbox("Children <12", options=list(range(0, 11)), index=0)

                    st.write("#### 📅 Timing & Contact")
                    form_origin_options = ["🌍 Other (Type in the Form Below)"] + european_cities
                    form_origin_dropdown = st.selectbox("Departure City", options=form_origin_options, index=None)

                    form_origin_custom = ""
                    if form_origin_dropdown == "🌍 Other (Type in the Form Below)":
                        form_origin_custom = st.text_input("Enter your city manually:", placeholder="e.g., New York, Tokyo...")
                    
                    travel_month = st.selectbox("Tentative Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
                    mobile = st.text_input("Mobile Number", placeholder="+1 234 567 890")
                    user_email = st.text_input("Email Address")
                    user_notes = st.text_area("Notes")
                    
                    st.write("### 🧳 Tailor Your Experience (Optional)")
                    st.write("Check any that apply so our Alpaca concierges can perfect your trip:")

                    col1, col2 = st.columns(2)
                    with col1:
                        drive = st.checkbox("🚗 We will be driving/renting a car")
                        pets = st.checkbox("🐾 Traveling with pets")
                        seniors = st.checkbox("🧓 Traveling with seniors")
                        foodie = st.checkbox("🍷 Love trying Local cuisines")

                    with col2:
                        trains = st.checkbox("🚆 We prefer train travel")
                        budget = st.checkbox("💰 Strict budget traveler")
                        walking = st.checkbox("👟 Interested in walking tours")
                        slow_pace = st.checkbox("🐢 Slow travel (Relaxed pace)")

                    consent = st.checkbox("I agree to the Privacy policy and consent to be contacted.")

                    if st.form_submit_button("Prepare My Request"):
                        if not (consent and user_email and mobile):
                            st.error("Please fill in all details and check the consent box.")
                        else:
                            nl = "%0D%0A"
                            subject = f"Oh Sheep! Request: {destination} ({travel_month})"
                            
                            email_origin = form_origin_custom if form_origin_dropdown == "🌍 Other (Type in the Form Below)" else form_origin_dropdown
                            email_origin = email_origin if email_origin else "Not specified"

                            # 1. Grab the specific checkboxes
                            specific_prefs = []
                            if drive: specific_prefs.append("Will be driving/renting a car")
                            if pets: specific_prefs.append("Traveling with pets")
                            if seniors: specific_prefs.append("Traveling with seniors")
                            if foodie: specific_prefs.append("Foodie focus (Local cuisine)")
                            if trains: specific_prefs.append("Prefers train travel")
                            if budget: specific_prefs.append("Strict budget traveler")
                            if walking: specific_prefs.append("Interested in walking tours")
                            if slow_pace: specific_prefs.append("Slow travel (Relaxed pace)")

                            email_specific_prefs = f"{nl}- ".join(specific_prefs)
                            email_specific_prefs = f"- {email_specific_prefs}" if specific_prefs else "No specific logistical constraints."

                            # 2. Grab the vibes from the generic multiselect above
                            if preferences:
                                email_vibe = f"{nl}- ".join(preferences)
                                email_vibe = f"- {email_vibe}"
                            else:
                                email_vibe = "Open to anything (Offer me what Alpacas like!)"

                            email_notes = user_notes if user_notes else "No additional notes provided."

                            
                            # 3. Build the Ultimate Email Body (Captures absolutely everything)
                            email_body = (
                                f"🚨 OH SHEEP! PREMIUM TRIP REQUEST 🚨{nl}{nl}"
                                f"✈️ THE BASICS{nl}"
                                f"- From: {email_origin}{nl}"
                                f"- To: {destination}{nl}"
                                f"- When: {travel_month} (for {days} days){nl}"
                                f"- Style: {style}{nl}{nl}"  # <--- THIS IS THE MISSING LINE!
                                f"👥 THE FLOCK{nl}"
                                f"- Group Style: {group}{nl}"
                                f"- Adults: {adults}{nl}"
                                f"- Young Adults: {young_adults}{nl}"
                                f"- Children: {children}{nl}{nl}"
                                f"✨ THE VIBE (From Initial Search){nl}"
                                f"{email_vibe}{nl}{nl}"
                                f"🎒 SPECIFIC PREFERENCES{nl}"
                                f"{email_specific_prefs}{nl}{nl}"
                                f"📝 ADDITIONAL NOTES{nl}"
                                f"{email_notes}{nl}{nl}"
                                f"📞 CONTACT INFO{nl}"
                                f"- Email: {user_email}{nl}"
                                f"- Mobile: {mobile}"
                            )

                            st.session_state.mailto_url = f"mailto:rnktrips@gmail.com?subject={subject.replace(' ', '%20')}&body={email_body.replace(' ', '%20')}"
                            st.session_state.request_prepped = True
                            st.rerun()

        if st.session_state.request_prepped:
            st.markdown(
                f'''
                <a href="{st.session_state.mailto_url}" 
                style="background-color:#FFFFFF; color:#000000 !important; padding:18px; text-decoration:none; display:block; text-align:center; border-radius:8px; font-weight:900; font-size:1.2em; border: 2px solid #DDDDDD;">
                🚀 CLICK HERE TO OPEN EMAIL & SEND REQUEST
                </a>
                ''',
                unsafe_allow_html=True,
            )
            st.write("")
            st.success("✅ Once you click the button above and send the email, our experts will review your details and will get back to you within **1 business day**.")

            if st.button("⬅️ Start Over / Edit Details"):
                st.session_state.request_prepped = False
                st.rerun()

        st.write("---")
        st.write("### ✈️ Ready? Check Live Flights")
        clean_dest_input = destination.strip().title() if destination else ""
        dest_code = iata_codes.get(clean_dest_input, "")
        origin_code = ""

        tp_widget_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ margin: 0; padding: 0; background-color: #F9FAFB; }}
                .widget-clipper {{ overflow: hidden; border-radius: 12px; width: 100%; height: 400px; }}
                .widget-stretcher {{ margin: -8px -8px -60px -8px; }}
            </style>
        </head>
        <body>
            <div class="widget-clipper">
                <div class="widget-stretcher">
                    <script async src="https://tpwidg.com/content?currency=eur&trs=528110&shmarker=722430&show_hotels=false&powered_by=true&locale=en&searchUrl=www.aviasales.com%2Fsearch&origin={origin_code}&destination={dest_code}&primary_override=%2332a8dd&color_button=%2332a8dd&color_icons=%2332a8dd&dark=%23262626&light=%23FFFFFF&secondary=%23FFFFFF&special=%23C4C4C4&color_focused=%2332a8dd&border_radius=0&plain=false&promo_id=7879&campaign_id=100" charset="utf-8"></script>
                </div>
            </div>
        </body>
        </html>
        """
        components.html(tp_widget_html, height=350, scrolling=False)

# --- 7. FOOTER ---
st.write("---")
active_dest = destination if destination and not destination.startswith("---") else "Default"
images_to_show = destination_images.get(active_dest, destination_images["Default"])

st.write("### 📸 The Sheep Views")
w1, w2, w3 = st.columns(3)
with w1: st.image(images_to_show[0], use_container_width=True)
with w2: st.image(images_to_show[1], use_container_width=True)
with w3: st.image(images_to_show[2], use_container_width=True)