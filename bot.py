#!/usr/bin/env python3
"""
🤖 StexSMS Bot Unified Runner - Fixed Version
----------------------------------
Fixed: Number allocation API call issue
"""

import os
import re
import sys
import time
import json
import random
import logging
import threading
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Load env variables
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DXA_VoltxBot")

# Config Files
PANELS_FILE = "panels.json"
SERVICES_FILE = "services.json"
ADMIN_DB_FILE = "admin_db.json"
OWNER_ID = "1849126202"
TELEGRAM_TOKEN = "8994153110:AAFyc_ZzOK5FhG7Yl-2DQ50QqUjLU-VaG-8"

# Admin DB Logic
def load_admin_db():
    default_db = {"users": [], "today_date": datetime.now().strftime("%Y-%m-%d"), "today_numbers_count": 0, "admins": [OWNER_ID], "force_join_status": False, "force_join_channels": [], "otp_group_link": "", "forward_groups": [], "dxa_config": {"withdraw_group": "", "otp_reward": 0.0, "min_withdraw": 20.0, "methods": [], "max_concurrent": 3, "cooldown": 0}, "user_stats": {}, "active_numbers": {}, "banned_users": []}
    if os.path.exists(ADMIN_DB_FILE):
        try:
            with open(ADMIN_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in default_db:
                    if key not in data:
                        data[key] = default_db[key]
                return data
        except:
            pass
    return default_db

admin_db = load_admin_db()

def save_admin_db():
    try:
        with open(ADMIN_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(admin_db, f, indent=2)
    except Exception as e:
        logger.error(f"Save admin db error: {e}")

# Firebase Setup
firebase_cred_dict = {
  "type": "service_account",
  "project_id": "number-bot-59529",
  "private_key_id": "22d97ad9c63d9b959254078e04c1c321e405515e",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCecGYjFgZHiM9Q\nCwu8nUhc4HgAogAFbuOf5UMvc03rzq5CRcrOxj5fcnrBiIHxrFP0g7x5NIcbppEZ\ny+ogMhLuvVS8CzpDV+qh1nf4GREQo/SoJMT2cbAqfxh9HV34OQ/lKWhKYKzN/rEj\nJgt/JDGKwM7UuPL135fglA5eny6D08KPubBbfbhr9h5Riz91BamOv1H3KUKgydYM\ng10U2Q74zD6vSeAnf5/oPz4jms/DWK2lEsHlVj5Qx9rp0WCZ4zVOBypbzOn0FZrV\nWPiFRC4M7b9mgqPflWkKW+PKzScfxRgBxfs7X1QW+iFKGGoRezkvN5SNf8e2PU9O\nTpxX/zI9AgMBAAECggEABN8R1NxVfxeOwDhGuRrg4bIpHmPcuk4Jg54J7ciOycRG\nCVWaAbeIrWiYq6Cl1idlQWxXfCaITOpXJcLmRO0lNd/uXgW+Wdm3JhixAZjLtIZF\n/HF8+NLQBs53k0k23W3rtjEKuta0GXVOPvVpfxQ+zbRV56Z0GekxAz+qHXCpfnYU\n74pWDRItZ6ue9Q0S2dsUf6tjWY8ZGjsFAAdgKqG8zuu1n+19IX8ppzFsn/PiENNL\nvWzDUOlZ7zxgiV3R7jDjEBVsWd1IgIz2IbtHy0/1UhYj9GD6xbUuWwtaeN3oiT1D\nA5BxgDMv3R5kcWRtUjImI8FWuGUKHFmIW64ROo2cBQKBgQDMguzfhHitkT+XNJwv\n1VLhZiw1wAs//YSHQkFctSq1eBkUJl+Nv5otRGmL+d2JV+ij6E01fjL5N/5Osx/B\nlwiNyxkot512tMdItXDfXxAeJ43LN/IPA3xyjxbpeM1dWviE08oFrm8foYXvhcV1\noLyHjDXMg6zaiA/mKOdCsKWr/wKBgQDGVAn6NJ/aNvIpA0Qx734jqgzRpTXPpm5x\nFi8sdUqPy5eHEj0mMf2x3UAOu4ZjbGh4blHXZu0KU5IOmLqakCdby4n3D1Ui+X+H\nRPO4Q5UsOMlFTI5nCRP/+z4tvxWWzdhbrp/4An8f9yLwnnsC2DqFsMtYRVAA80XX\nRNt7n57RwwKBgDXrgwZ/h83DUO/N2CwoY1y4MonNY2nwroN27YLC5UrJKluMrn7R\n+JVcxzM3org2bEji05B6AHiC0dLwGTxSVNgFp1F779E/YpeB9wt9peM9bH4a9wAM\nXEBcB59w0Tx+4q0qpcYPso61aHm5XFFiGrLmPbz5LpbDbuWw/SAxMM0DAoGAaHMM\nCiS65z62zFi3CqF5yiidta+PpnudgJtRXtWq3g44EF/PqpT7ajf+q4OhZC1M29gl\n7A592klnC57t78bpo5OPZnlBujiyLDhpLusQ3ghOH9wQxzzltpPIDGmtYg2o26gd\nAY23C8upMBYW7MmaEJyqiyN93fJBHv1ZpkLLbucCgYBMq3uTH4jA2fa1tCOog2QE\nEA+onUznxrtgk5Aun/TjhYjO0ZY7Mf064mDeX8qEiaj24ebBqH1knvdkHH1YY5P6\n+nJSbhH6wvA16k28o0YB+WDNRj1YasWUEuihJ3sG9luz4/ZYvmb24YFn8rYxJkI5\nZJj1vQkssYhaYfDRiq9C/w==\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@number-bot-59529.iam.gserviceaccount.com",
  "client_id": "105165468312212380453",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40number-bot-59529.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
db_firestore = None

def initialize_firebase():
    global db_firestore
    try:
        cred = credentials.Certificate(firebase_cred_dict)
        if firebase_admin._apps:
            firebase_admin.delete_app(firebase_admin.get_app())
        firebase_admin.initialize_app(cred)
        db_firestore = firestore.client()
        logger.info("Firebase initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"Firebase init failed: {e}")
        db_firestore = None
        return False

initialize_firebase()

# Global variables
user_conversations = {}
user_prompts = {}
sessions = {}
local_traffic_stats = {}
local_raw_logs_cache = {}

# Country data
PREMIUM_EMOJIS = {
    "dxa": "<tg-emoji emoji-id='5366486221021264181'>😒</tg-emoji>",
    "time": "<tg-emoji emoji-id='5336983442125001376'>🕓</tg-emoji>",
    "otp": "<tg-emoji emoji-id='5337255927735163754'>🔐</tg-emoji>",
    "fire": "<tg-emoji emoji-id='6217523115866459467'>🔥</tg-emoji>",
    "king": "<tg-emoji emoji-id='6217489026711031722'>👑</tg-emoji>",
    "dashboard": "<tg-emoji emoji-id='5352877703043258544'>📊</tg-emoji>",
    "user": "<tg-emoji emoji-id='5352861489541714456'>👤</tg-emoji>",
    "rocket": "<tg-emoji emoji-id='5352597830089347330'>🚀</tg-emoji>",
    "gem": "<tg-emoji emoji-id='5352838545826420397'>💎</tg-emoji>",
    "done": "<tg-emoji emoji-id='5352694861990501856'>✅</tg-emoji>",
    "error": "<tg-emoji emoji-id='6276272470269891500'>❌</tg-emoji>",
    "search": "<tg-emoji emoji-id='5463352748751753567'>🔍</tg-emoji>",
    "number": "<tg-emoji emoji-id='5337132498965010628'>🍏</tg-emoji>",
    "phone": "<tg-emoji emoji-id='5355208818017999139'>📱</tg-emoji>",
    "warn": "<tg-emoji emoji-id='6276132901012640832'>⚠️</tg-emoji>",
    "wait": "<tg-emoji emoji-id='5337172996211648018'>⏳</tg-emoji>",
    "note": "<tg-emoji emoji-id='5395444784611480792'>📝</tg-emoji>",
    "world": "<tg-emoji emoji-id='5336972142066047577'>🌐</tg-emoji>",
    "gear": "<tg-emoji emoji-id='5420155432272438703'>⚙️</tg-emoji>",
    "back": "<tg-emoji emoji-id='5267490665117275176'>⬅️</tg-emoji>"
}

RAW_APP_EMOJIS = {
    "facebook": "5389064576333527180", "whatsapp": "5233354831984353090",
    "telegram": "6276327209628078918", "imo": "5337155807752524558",
    "instagram": "5389064576333527180", "apple": "5334637951894722661",
    "google": "5321244246705989720", "microsoft": "5334880948259427772",
    "tiktok": "5339213256001102461", "amazon": "4995019580536524226",
    "twitter": "5215726959056662534", "snapchat": "5359441366554255082",
    "netflix": "6255738712664050133", "linkedin": "6224222994265279792",
    "discord": "5116246243646898866", "viber": "5463060437572528782",
    "wechat": "5782757599560602950", "line": "5399818044866327279",
    "paypal": "5776103539872896061", "uber": "5298715455316303708",
    "bkash": "5348469219761626211", "rocket": "5352597830089347330",
    "binance": "5348212415077064131", "bybit": "5348372939479751825",
    "gmail": "5348494358205207761", "messenger": "5348486915026884464",
    "chrome": "5346311574221000149", "chatgpt": "5296516998996445955",
    "github": "5417836094098007862", "canva": "5111661409008092227"
}

RAW_FLAG_EMOJIS = {
    "CI": {"phone_code": "225", "flag": "🇨🇮", "name": "Côte d'Ivoire", "id": "6230805705956269859"},
    "CM": {"phone_code": "237", "flag": "🇨🇲", "name": "Cameroon", "id": "5911172109484167745"},
    "TG": {"phone_code": "228", "flag": "🇹🇬", "name": "Togo", "id": "5913423260757790970"},
    "MG": {"phone_code": "261", "flag": "🇲🇬", "name": "Madagascar", "id": "5913766918271012920"},
    "BJ": {"phone_code": "229", "flag": "🇧🇯", "name": "Benin", "id": "5913735869952430547"},
    "GN": {"phone_code": "224", "flag": "🇬🇳", "name": "Guinea", "id": "5913471858312744319"},
    "SN": {"phone_code": "221", "flag": "🇸🇳", "name": "Senegal", "id": "5913467813892853162"},
    "ML": {"phone_code": "223", "flag": "🇲🇱", "name": "Mali", "id": "5913493954892305604"},
    "BF": {"phone_code": "226", "flag": "🇧🇫", "name": "Burkina Faso", "id": "5913446658288190966"},
    "NE": {"phone_code": "227", "flag": "🇳🇪", "name": "Niger", "id": "5913503058745560521"},
    "TD": {"phone_code": "235", "flag": "🇹🇩", "name": "Chad", "id": "5913440017882943430"},
    "CF": {"phone_code": "236", "flag": "🇨🇫", "name": "Central African Republic", "id": "5913443245240619222"},
    "GA": {"phone_code": "241", "flag": "🇬🇦", "name": "Gabon", "id": "5913472362742834017"},
    "CG": {"phone_code": "242", "flag": "🇨🇬", "name": "Congo", "id": "5913759902067322781"},
    "CD": {"phone_code": "243", "flag": "🇨🇩", "name": "DR Congo", "id": "5911292131752614903"},
    "TJ": {"phone_code": "992", "flag": "🇹🇯", "name": "Tajikistan", "id": "5911287639809463107"},
}

def get_pemoji(key, fallback=""):
    return PREMIUM_EMOJIS.get(key.lower(), fallback)

def get_app_raw_id(app_name):
    name_lower = app_name.lower()
    for key, val in RAW_APP_EMOJIS.items():
        if key in name_lower:
            return val
    return "5336879280578138635"

def get_country_info(short_code):
    if short_code in RAW_FLAG_EMOJIS:
        return RAW_FLAG_EMOJIS[short_code]
    return {"name": short_code, "flag": "🏳️", "id": "5336972142066047577"}

def escape_html(text):
    if not text:
        return ""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def mask_number(num):
    if not num:
        return ""
    num_str = str(num).replace("+", "").strip()
    if len(num_str) <= 6:
        return num_str
    first_3 = num_str[:3]
    last_3 = num_str[-3:]
    return f"{first_3}❖DXA❖{last_3}"

def extract_otp(text):
    if not text:
        return "No OTP Found"
    match = re.search(r'\b\d{4,8}\b', text)
    if match:
        return match.group(0)
    match = re.search(r'\b\d{3}-\d{3}\b', text)
    if match:
        return match.group(0).replace("-", "")
    match = re.search(r'\b\d{3}\s\d{3}\b', text)
    if match:
        return match.group(0).replace(" ", "")
    return "No OTP Found"

def normalize_base_url(input_url):
    url = input_url.strip()
    if not re.match(r'^https?://', url, re.IGNORECASE):
        url = 'https://' + url
    if '/#/' in url:
        url = url.split('/#/')[0]
    elif '/#' in url:
        url = url.split('/#')[0]
    while url.endswith('/'):
        url = url[:-1]
    return url

def get_clean_base_url(panel, base_url):
    if panel.get("resolvedBaseUrl"):
        return panel["resolvedBaseUrl"].rstrip('/')
    return base_url.split('#')[0].rstrip('/')

def get_country_code(num):
    clean = str(num).replace('+', '').strip()
    sorted_flags = sorted(RAW_FLAG_EMOJIS.items(), key=lambda x: len(x[1].get("phone_code", "")), reverse=True)
    for short_code, info in sorted_flags:
        if clean.startswith(info["phone_code"]):
            return short_code
    return 'Unknown'

def get_range_from_number(num):
    clean = str(num).replace('+', '').strip()
    first_x = re.search(r'[Xx*\-]', clean)
    if first_x:
        clean = clean[:first_x.start()]
    if len(clean) > 7:
        return clean[:7]
    return clean

def get_service_display_name(name):
    lower = str(name).strip().lower()
    if 'facebook' in lower or lower == 'fb': return 'Facebook'
    if 'whatsapp' in lower or lower == 'wa': return 'WhatsApp'
    if 'telegram' in lower or lower == 'tg': return 'Telegram'
    if 'instagram' in lower or lower == 'ig': return 'Instagram'
    if 'tiktok' in lower or lower == 'tt': return 'TikTok'
    if 'google' in lower: return 'Google'
    if 'microsoft' in lower: return 'Microsoft'
    return str(name).strip().capitalize()

# Load Services
def load_services():
    if os.path.exists(SERVICES_FILE):
        try:
            with open(SERVICES_FILE, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict):
                    return content
        except Exception as e:
            logger.error(f"Error loading services: {e}")
    return {}

def save_services(services_dict):
    try:
        with open(SERVICES_FILE, "w", encoding="utf-8") as f:
            json.dump(services_dict, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving services: {e}")

# Load Panels
def load_panels():
    default_panels = [
        {
            "id": "voltx_api",
            "name": "Voltx API",
            "url": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api",
            "username": "API",
            "password": "MKJGS2MSZYB",
            "getNumberUrl": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/getnum",
            "getMessageUrl": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/success-otp",
            "trafficUrl": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/console",
            "sessionCookie": "MKJGS2MSZYB",
            "status": "Running (API)",
            "is_active": True,
            "is_traffic_active": True,
            "lastSeenGetnumIds": []
        }
    ]
    if os.path.exists(PANELS_FILE):
        try:
            with open(PANELS_FILE, "r", encoding="utf-8") as f:
                panels = json.load(f)
                for p in panels:
                    p.setdefault("is_active", True)
                    p.setdefault("is_traffic_active", True)
                    p.setdefault("sessionCookie", p.get("password", ""))
                    p.setdefault("lastSeenGetnumIds", [])
                return panels
        except Exception as e:
            logger.error(f"Error loading panels: {e}")
    return default_panels

panels = load_panels()

def save_panels_to_file(panels_list):
    try:
        with open(PANELS_FILE, "w", encoding="utf-8") as f:
            json.dump(panels_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving panels: {e}")

def get_session(panel_id):
    if panel_id not in sessions:
        s = requests.Session()
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        sessions[panel_id] = s
    return sessions[panel_id]

# ============================================================
# 🔥 FIXED: BUY NUMBER FUNCTION - COMPLETE REWRITE
# ============================================================
def buy_number(range_val, target_panel_id=None):
    """Get number from API - Fixed version with proper error handling"""
    logger.info(f"🔍 buy_number called with range: {range_val}, panel: {target_panel_id}")
    
    # Panel selection
    panel = None
    if target_panel_id:
        panel = next((p for p in panels if p.get("id") == target_panel_id), None)
    else:
        # Try to find panel from services
        services_data = load_services()
        for p_id, s_list in services_data.items():
            for s in s_list:
                for c in s.get("countries", []):
                    clean_target = re.sub(r'[Xx*]', '', range_val)
                    if any(clean_target in r for r in c.get("ranges", [])):
                        panel = next((p for p in panels if p.get("id") == p_id), None)
                        if panel:
                            break
                if panel:
                    break
            if panel:
                break
        
        # Fallback to first panel
        if not panel:
            panel = panels[0] if panels else None
    
    if not panel:
        logger.error("❌ No panel found")
        return {"success": False, "message": "No panel configuration found"}
    
    logger.info(f"✅ Using panel: {panel.get('name')} ({panel.get('id')})")
    
    # Get API URL
    base_url = normalize_base_url(panel.get("url", ""))
    get_num_url = panel.get("getNumberUrl") or f"{base_url}/getnum"
    api_key = panel.get("sessionCookie") or panel.get("password", "MKJGS2MSZYB")
    
    # Clean range - remove X, x, *
    rid = re.sub(r'[Xx*]', '', range_val).strip()
    if not rid:
        rid = range_val.strip()
    
    logger.info(f"📤 API Request: URL={get_num_url}, RID={rid}, API_KEY={api_key[:10]}...")
    
    try:
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "mauthapi": api_key
        }
        
        payload = {"rid": rid}
        
        # Make request
        response = requests.post(
            get_num_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"📥 Response Status: {response.status_code}")
        logger.info(f"📥 Response Body: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"📥 Parsed Response: {json.dumps(data, indent=2)[:500]}")
                
                # Check different response formats
                # Format 1: {"meta": {"code": 200}, "data": {...}}
                if data.get("meta", {}).get("code") == 200:
                    num_data = data.get("data", {})
                    number = num_data.get("full_number") or num_data.get("no_plus_number") or num_data.get("number") or ""
                    
                    if number:
                        logger.info(f"✅ Number allocated: {number}")
                        return {
                            "success": True,
                            "number": number,
                            "operator": num_data.get("operator", "Unknown"),
                            "country": num_data.get("country", "Unknown"),
                            "message": data.get("message", "Success")
                        }
                
                # Format 2: {"code": 200, "data": {...}}
                if data.get("code") == 200:
                    num_data = data.get("data", {})
                    number = num_data.get("full_number") or num_data.get("no_plus_number") or num_data.get("number") or ""
                    
                    if number:
                        logger.info(f"✅ Number allocated: {number}")
                        return {
                            "success": True,
                            "number": number,
                            "operator": num_data.get("operator", "Unknown"),
                            "country": num_data.get("country", "Unknown"),
                            "message": data.get("message", "Success")
                        }
                
                # Format 3: Direct data
                if data.get("data"):
                    num_data = data.get("data", {})
                    if isinstance(num_data, dict):
                        number = num_data.get("full_number") or num_data.get("no_plus_number") or num_data.get("number") or ""
                        if number:
                            logger.info(f"✅ Number allocated: {number}")
                            return {
                                "success": True,
                                "number": number,
                                "operator": num_data.get("operator", "Unknown"),
                                "country": num_data.get("country", "Unknown"),
                                "message": data.get("message", "Success")
                            }
                
                # Check if number is in response directly
                if isinstance(data, dict):
                    number = data.get("number") or data.get("full_number") or data.get("no_plus_number") or ""
                    if number:
                        logger.info(f"✅ Number allocated: {number}")
                        return {
                            "success": True,
                            "number": number,
                            "operator": data.get("operator", "Unknown"),
                            "country": data.get("country", "Unknown"),
                            "message": data.get("message", "Success")
                        }
                
                # Error message from API
                error_msg = data.get("message") or data.get("meta", {}).get("message") or "Unknown API error"
                logger.error(f"❌ API returned error: {error_msg}")
                return {"success": False, "message": error_msg}
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parse error: {e}")
                return {"success": False, "message": f"Invalid JSON response: {response.text[:100]}"}
        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            return {"success": False, "message": f"HTTP Error: {response.status_code}"}
            
    except requests.exceptions.Timeout:
        logger.error("❌ Request timeout")
        return {"success": False, "message": "Request timed out"}
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection error")
        return {"success": False, "message": "Cannot connect to API"}
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return {"success": False, "message": str(e)}

# ============================================================
# TELEGRAM FUNCTIONS
# ============================================================

def call_telegram(method, payload):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    try:
        response = requests.post(url, json=payload, timeout=40)
        return response.json()
    except Exception as e:
        logger.error(f"Telegram API error: {e}")
        return None

def send_bot_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return call_telegram("sendMessage", payload)

def edit_bot_message(chat_id, message_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return call_telegram("editMessageText", payload)

def answer_callback(callback_query_id, text=None, show_alert=False):
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
        if show_alert:
            payload["show_alert"] = True
    call_telegram("answerCallbackQuery", payload)

def get_otp_group_btn():
    link = admin_db.get("otp_group_link", "").strip()
    if link and link.startswith("http"):
        return {"text": " Otp Group", "url": link, "style": "primary", "icon_custom_emoji_id": "5420145051336485498"}
    return {"text": " Otp Group", "callback_data": "usr_otp_grp", "style": "primary", "icon_custom_emoji_id": "5420145051336485498"}

def check_user_limits(chat_id, update_cooldown=True):
    cfg = admin_db.get("dxa_config", {})
    max_c = int(cfg.get("max_concurrent", 3))
    if max_c < 1:
        max_c = 1
    
    if str(chat_id) in admin_db.get("admins", [OWNER_ID]):
        return True, "", max_c
        
    cd = int(cfg.get("cooldown", 0))
    stats = admin_db.setdefault("user_stats", {}).setdefault(str(chat_id), {})
    stats.setdefault("otp_count", 0)
    stats.setdefault("balance", 0.0)
    stats.setdefault("last_req", 0)

    now = int(time.time())
    last_req = stats.get("last_req", 0)
    
    if cd > 0 and (now - last_req) < cd:
        rem = cd - (now - last_req)
        return False, f"⏳ Cooldown Active!\nPlease wait {rem} seconds.", max_c

    if update_cooldown:
        stats["last_req"] = now
        save_admin_db()
        
    return True, "", max_c

# ============================================================
# FIXED: TRIGGER BUY NUMBER
# ============================================================
def trigger_buy_number(chat_id, range_val, target_panel_id=None, message_id=None, callback_id=None):
    """Trigger number purchase with proper error handling"""
    logger.info(f"🎯 Trigger buy: chat={chat_id}, range={range_val}, panel={target_panel_id}")
    
    try:
        passed, err_msg, batch_size = check_user_limits(chat_id)
        if not passed:
            if callback_id:
                answer_callback(callback_id, err_msg, show_alert=True)
            else:
                kb = {"inline_keyboard": [[{"text": " Back", "callback_data": "usr_menu_home", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]]}
                if message_id:
                    edit_bot_message(chat_id, message_id, f"⚠️ {err_msg}", kb)
                else:
                    send_bot_message(chat_id, f"⚠️ {err_msg}", kb)
            return

        if callback_id:
            answer_callback(callback_id, f"Requesting {range_val}...")

        # Show waiting message
        wait_text = f"{get_pemoji('wait', '⏳')} <i>Allocating {batch_size} number(s) for range <b>{escape_html(range_val)}</b>... Please wait.</i>"
        
        try:
            if message_id:
                edit_bot_message(chat_id, message_id, wait_text)
            else:
                res = send_bot_message(chat_id, wait_text)
                if res and res.get("result"):
                    message_id = res["result"]["message_id"]
        except Exception as e:
            logger.error(f"Wait message error: {e}")
            res = send_bot_message(chat_id, wait_text)
            if res and res.get("result"):
                message_id = res["result"]["message_id"]

        # Get numbers
        numbers_fetched = []
        last_err = "Unknown error"
        
        for attempt in range(batch_size):
            logger.info(f"🔄 Attempt {attempt+1}/{batch_size}")
            result = buy_number(range_val, target_panel_id)
            
            if result.get("success"):
                number = result.get("number", "")
                if number:
                    numbers_fetched.append(result)
                    clean_num = str(number).replace("+", "").strip()
                    if "active_numbers" not in admin_db:
                        admin_db["active_numbers"] = {}
                    admin_db["active_numbers"][clean_num] = str(chat_id)
                    logger.info(f"✅ Number {clean_num} allocated for user {chat_id}")
                else:
                    logger.warning(f"⚠️ Success but no number: {result}")
            else:
                last_err = result.get("message", "Unknown error")
                logger.error(f"❌ Attempt {attempt+1} failed: {last_err}")
                break

        # Show results
        if numbers_fetched:
            save_admin_db()
            
            # Get country info from first number
            first_num = numbers_fetched[0].get("number", "")
            if first_num:
                c_code = get_country_code(first_num)
                c_info = get_country_info(c_code)
                flag_em_id = c_info.get("id", "5336972142066047577")
            else:
                flag_em_id = "5336972142066047577"
            
            # Build keyboard
            keyboard = {"inline_keyboard": []}
            
            for res in numbers_fetched:
                num = res.get("number", "")
                if num:
                    keyboard["inline_keyboard"].append([{
                        "text": f" +{num.replace('+', '')}",
                        "copy_text": {"text": num},
                        "style": "primary",
                        "icon_custom_emoji_id": flag_em_id
                    }])
            
            # If no numbers in keyboard (should not happen)
            if not keyboard["inline_keyboard"]:
                error_text = f"❌ <b>No valid numbers returned!</b>\n\nRange: <code>{escape_html(range_val)}</code>"
                kb = {"inline_keyboard": [
                    [{"text": "🔁 Retry", "callback_data": f"buy_{range_val}", "style": "danger"}],
                    [{"text": " Back", "callback_data": "usr_search_home", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]
                ]}
                try:
                    if message_id:
                        edit_bot_message(chat_id, message_id, error_text, kb)
                    else:
                        send_bot_message(chat_id, error_text, kb)
                except:
                    send_bot_message(chat_id, error_text, kb)
                return
            
            # Add control buttons
            keyboard["inline_keyboard"].extend([
                [
                    {"text": " Change Number", "callback_data": f"buy_{range_val}", "style": "danger", "icon_custom_emoji_id": "5420155432272438703"},
                    get_otp_group_btn()
                ],
                [{"text": " Back", "callback_data": "usr_search_home", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]
            ])
            
            # Send final message
            blank_text = "ㅤ"
            try:
                if message_id:
                    edit_bot_message(chat_id, message_id, blank_text, keyboard)
                else:
                    send_bot_message(chat_id, blank_text, keyboard)
            except Exception as e:
                logger.error(f"Final message error: {e}")
                send_bot_message(chat_id, blank_text, keyboard)
                
        else:
            # All attempts failed
            error_text = f"❌ <b>Get Number Failed!</b>\n\n" \
                         f"<b>Range:</b> <code>{escape_html(range_val)}</code>\n" \
                         f"<b>Error:</b> <code>{escape_html(last_err)}</code>\n\n" \
                         f"<i>Check API configuration or try again.</i>"
            
            kb = {
                "inline_keyboard": [
                    [{"text": "🔁 Retry", "callback_data": f"buy_{range_val}", "style": "danger"}],
                    [{"text": " Back", "callback_data": "usr_search_home", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]
                ]
            }
            
            try:
                if message_id:
                    edit_bot_message(chat_id, message_id, error_text, kb)
                else:
                    send_bot_message(chat_id, error_text, kb)
            except Exception as e:
                logger.error(f"Error message error: {e}")
                send_bot_message(chat_id, error_text, kb)
                
    except Exception as e:
        logger.error(f"❌ Critical error in trigger_buy_number: {e}")
        try:
            error_text = f"❌ <b>System Error!</b>\n\n<code>{escape_html(str(e))}</code>"
            if message_id:
                edit_bot_message(chat_id, message_id, error_text)
            else:
                send_bot_message(chat_id, error_text)
        except:
            send_bot_message(chat_id, f"❌ System Error: {e}")

# ============================================================
# FIXED: ALLOCATE AND SHOW NUMBER
# ============================================================
def allocate_and_show_number_py(chat_id, message_id, service_id, country_code, callback_id=None):
    """Allocate number from service - Fixed version"""
    logger.info(f"🎯 Allocate: chat={chat_id}, service={service_id}, country={country_code}")
    
    try:
        passed, err_msg, batch_size = check_user_limits(chat_id)
        if not passed:
            if callback_id:
                answer_callback(callback_id, err_msg, show_alert=True)
            else:
                kb = {"inline_keyboard": [[{"text": " Back", "callback_data": f"usr_srv_sel:{service_id}", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]]}
                try:
                    if message_id:
                        edit_bot_message(chat_id, message_id, f"⚠️ {err_msg}", kb)
                    else:
                        send_bot_message(chat_id, f"⚠️ {err_msg}", kb)
                except:
                    send_bot_message(chat_id, f"⚠️ {err_msg}", kb)
            return

        if callback_id:
            answer_callback(callback_id, "Allocating number...")

        # Find available panels
        services_dict = load_services()
        available_panels = []
        service_name = "Unknown"
        
        for p_id, s_list in services_dict.items():
            panel = next((p for p in panels if p.get("id") == p_id and p.get("is_active", True)), None)
            if not panel:
                continue
            for s in s_list:
                if s["id"] == service_id:
                    service_name = s["name"]
                    for c in s.get("countries", []):
                        if c["code"] == country_code and len(c.get("ranges", [])) > 0:
                            available_panels.append({"panel_id": p_id, "ranges": c["ranges"]})
        
        if not available_panels:
            error_text = f"{get_pemoji('error', '❌')} No ranges configured for this selection."
            kb = {"inline_keyboard": [[{"text": " Back", "callback_data": f"usr_srv_sel:{service_id}", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]]}
            try:
                if message_id:
                    edit_bot_message(chat_id, message_id, error_text, kb)
                else:
                    send_bot_message(chat_id, error_text, kb)
            except:
                send_bot_message(chat_id, error_text, kb)
            return

        # Select random panel and range
        chosen_setup = random.choice(available_panels)
        panel_id = chosen_setup["panel_id"]
        range_val = random.choice(chosen_setup["ranges"]).strip().upper()
        
        # Add XXX if no wildcard
        if not any(c in range_val for c in ("X", "x", "*")) and range_val.isdigit():
            range_val += "XXX"
        
        logger.info(f"📌 Selected: panel={panel_id}, range={range_val}")
        
        # Show waiting message
        wait_emoji = get_pemoji("wait", "⏳")
        wait_text = f"{wait_emoji} <i>Allocating {batch_size} number(s) for <b>{escape_html(service_name)}</b>... Please wait.</i>"
        
        try:
            if message_id:
                edit_bot_message(chat_id, message_id, wait_text)
            else:
                res = send_bot_message(chat_id, wait_text)
                if res and res.get("result"):
                    message_id = res["result"]["message_id"]
        except Exception as e:
            logger.error(f"Wait message error: {e}")
            res = send_bot_message(chat_id, wait_text)
            if res and res.get("result"):
                message_id = res["result"]["message_id"]

        # Get numbers
        numbers_fetched = []
        last_err = "Unknown error"
        
        for attempt in range(batch_size):
            logger.info(f"🔄 Attempt {attempt+1}/{batch_size} for {service_name}")
            result = buy_number(range_val, panel_id)
            
            if result.get("success"):
                number = result.get("number", "")
                if number:
                    numbers_fetched.append(result)
                    clean_num = str(number).replace("+", "").strip()
                    if "active_numbers" not in admin_db:
                        admin_db["active_numbers"] = {}
                    admin_db["active_numbers"][clean_num] = str(chat_id)
                    logger.info(f"✅ Number {clean_num} allocated")
                else:
                    logger.warning(f"⚠️ Success but no number: {result}")
            else:
                last_err = result.get("message", "Unknown error")
                logger.error(f"❌ Attempt {attempt+1} failed: {last_err}")
                break

        # Show results
        if numbers_fetched:
            save_admin_db()
            
            svc_em_id = get_app_raw_id(service_name)
            
            # Build keyboard
            keyboard = {"inline_keyboard": [
                [{"text": f" {service_name}", "callback_data": "none", "style": "success", "icon_custom_emoji_id": svc_em_id}]
            ]}
            
            for res in numbers_fetched:
                num = res.get("number", "")
                if num:
                    c_code = get_country_code(num)
                    c_info = get_country_info(c_code)
                    flag_em_id = c_info.get("id", "5336972142066047577")
                    
                    keyboard["inline_keyboard"].append([{
                        "text": f" +{num.replace('+', '')}",
                        "copy_text": {"text": num},
                        "style": "primary",
                        "icon_custom_emoji_id": flag_em_id
                    }])
            
            # Add control buttons
            keyboard["inline_keyboard"].extend([
                [
                    {"text": " Change Number", "callback_data": f"usr_change_num:{service_id}:{country_code}", "style": "danger", "icon_custom_emoji_id": "5420155432272438703"},
                    get_otp_group_btn()
                ],
                [{"text": " Back", "callback_data": f"usr_srv_sel:{service_id}", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]
            ])
            
            # Send final message
            blank_text = "ㅤ"
            try:
                if message_id:
                    edit_bot_message(chat_id, message_id, blank_text, keyboard)
                else:
                    send_bot_message(chat_id, blank_text, keyboard)
            except Exception as e:
                logger.error(f"Final message error: {e}")
                send_bot_message(chat_id, blank_text, keyboard)
                
        else:
            # All attempts failed
            error_text = f"{get_pemoji('error', '❌')} <b>Get Number Failed!</b>\n\n" \
                         f"<b>Service:</b> {escape_html(service_name)}\n" \
                         f"<b>Country:</b> {escape_html(country_code)}\n" \
                         f"<b>Range tried:</b> <code>{escape_html(range_val)}</code>\n" \
                         f"<b>Error:</b> <code>{escape_html(last_err)}</code>"
            
            kb = {
                "inline_keyboard": [
                    [{"text": " Retry", "callback_data": f"usr_change_num:{service_id}:{country_code}", "style": "success", "icon_custom_emoji_id": "5465368548702446780"}],
                    [{"text": " Back", "callback_data": f"usr_srv_sel:{service_id}", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]
                ]
            }
            
            try:
                if message_id:
                    edit_bot_message(chat_id, message_id, error_text, kb)
                else:
                    send_bot_message(chat_id, error_text, kb)
            except Exception as e:
                logger.error(f"Error message error: {e}")
                send_bot_message(chat_id, error_text, kb)
                
    except Exception as e:
        logger.error(f"❌ Critical error in allocate: {e}")
        try:
            error_text = f"❌ <b>System Error!</b>\n\n<code>{escape_html(str(e))}</code>"
            if message_id:
                edit_bot_message(chat_id, message_id, error_text)
            else:
                send_bot_message(chat_id, error_text)
        except:
            send_bot_message(chat_id, f"❌ System Error: {e}")

# ============================================================
# SIMPLIFIED HANDLER FUNCTIONS (Minimal)
# ============================================================

def render_services_list(chat_id, message_id=None):
    """Show services list"""
    services_dict = load_services()
    merged_services = {}
    
    for p_id, s_list in services_dict.items():
        panel = next((p for p in panels if p.get("id") == p_id and p.get("is_active", True)), None)
        if not panel:
            continue
        for s in s_list:
            if s["id"] not in merged_services:
                merged_services[s["id"]] = {"id": s["id"], "name": s["name"]}
    
    text = f"{get_pemoji('phone', '📱')} <b>Select a service:</b>"
    
    keyboard = {"inline_keyboard": []}
    if not merged_services:
        keyboard["inline_keyboard"].append([{"text": " No Services Available", "callback_data": "none", "style": "danger"}])
    else:
        for s_id, s_data in merged_services.items():
            em_id = get_app_raw_id(s_data['name'])
            keyboard["inline_keyboard"].append([{"text": f" {s_data['name']}", "callback_data": f"usr_srv_sel:{s_id}", "style": "primary", "icon_custom_emoji_id": em_id}])
    
    if message_id:
        edit_bot_message(chat_id, message_id, text, keyboard)
    else:
        send_bot_message(chat_id, text, keyboard)

def render_countries_list(chat_id, message_id, service_id):
    """Show countries for service"""
    services_dict = load_services()
    merged_countries = {}
    service_name = "Unknown"
    
    for p_id, s_list in services_dict.items():
        panel = next((p for p in panels if p.get("id") == p_id and p.get("is_active", True)), None)
        if not panel:
            continue
        for s in s_list:
            if s["id"] == service_id:
                service_name = s["name"]
                for c in s.get("countries", []):
                    if len(c.get("ranges", [])) > 0:
                        merged_countries[c["code"]] = c
    
    if not merged_countries:
        edit_bot_message(chat_id, message_id, f"{get_pemoji('error', '❌')} No countries configured.", {
            "inline_keyboard": [[{"text": " Back", "callback_data": "usr_menu_home", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]]
        })
        return
    
    text = f"{get_pemoji('phone', '📱')} <b>Select a country for {service_name.upper()}:</b>"
    keyboard = {"inline_keyboard": []}
    
    for code, c in merged_countries.items():
        c_info = get_country_info(code)
        name = c.get("name") or c_info["name"]
        em_id = c_info.get("id", "5336972142066047577")
        keyboard["inline_keyboard"].append([{
            "text": f" {name} ({code})",
            "callback_data": f"usr_ctr_sel:{service_id}:{code}",
            "style": "primary",
            "icon_custom_emoji_id": em_id
        }])
    
    keyboard["inline_keyboard"].append([{"text": " Back", "callback_data": "usr_menu_home", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}])
    edit_bot_message(chat_id, message_id, text, keyboard)

def get_bot_menu_keyboard(chat_id):
    keyboard = [
        [
            {"text": "GET NUMBER", "style": "primary", "icon_custom_emoji_id": "5337132498965010628"},
            {"text": "SEARCH RANGE", "style": "success", "icon_custom_emoji_id": "5463352748751753567"}
        ],
        [
            {"text": "TRAFFIC", "style": "primary", "icon_custom_emoji_id": "5352877703043258544"},
            {"text": "BALANCE", "style": "success", "icon_custom_emoji_id": "5352838545826420397"}
        ]
    ]
    if str(chat_id) in admin_db.get("admins", [OWNER_ID]):
        keyboard.append([{"text": "ADMIN PANEL", "style": "danger", "icon_custom_emoji_id": "5420155432272438703"}])
    return {"keyboard": keyboard, "resize_keyboard": True}

def search_number_otp(chat_id, query):
    """Search for number"""
    clean_num = str(query).replace("+", "").strip()
    send_bot_message(chat_id, f"{get_pemoji('search', '🔍')} Searching for <code>{escape_html(clean_num)}</code>...")
    
    # Simple search - just try to buy number with XXX
    if clean_num.isdigit() and 3 <= len(clean_num) <= 11:
        trigger_buy_number(chat_id, clean_num + "XXX")
    else:
        send_bot_message(chat_id, f"❌ Invalid number format. Please enter 3-11 digits.")

def render_user_balance(chat_id, message_id=None):
    """Show user balance"""
    stats = admin_db.get("user_stats", {}).get(str(chat_id), {"otp_count": 0, "balance": 0.0})
    text = f"━━━━━━━━━━━━\n《 {get_pemoji('dxa', '😒')} <b>Profile</b> 》\n━━━━━━━━━━━━\n"
    text += f"{get_pemoji('done', '👋')} <b>Total Otp:</b> {stats.get('otp_count', 0)}\n"
    text += f"{get_pemoji('user', '👤')} <b>User Id:</b> <code>{chat_id}</code>\n"
    text += f"{get_pemoji('gem', '📅')} <b>BALANCE:</b> {stats.get('balance', 0.0)} ৳\n━━━━━━━━━━━━"
    
    if message_id:
        edit_bot_message(chat_id, message_id, text)
    else:
        send_bot_message(chat_id, text)

def render_traffic_home(chat_id, message_id=None):
    """Show traffic stats"""
    text = "╔═══════════════╗\n║ <b>📈 NETWORK TRAFFIC</b>\n╚═══════════════╝\n\n"
    text += "<i>Traffic monitoring active. Check back later for stats.</i>"
    
    keyboard = {"inline_keyboard": [
        [{"text": " Refresh", "callback_data": "tr_refresh", "style": "success"}],
        [{"text": " Close", "callback_data": "tr_close", "style": "danger"}]
    ]}
    
    if message_id:
        edit_bot_message(chat_id, message_id, text, keyboard)
    else:
        send_bot_message(chat_id, text, keyboard)

# ============================================================
# MAIN HANDLER
# ============================================================

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    chat_type = msg["chat"].get("type", "private")
    
    if chat_type in ["group", "supergroup"]:
        return
    
    if str(chat_id) in admin_db.get("banned_users", []):
        return
    
    text = msg.get("text", "").strip() or msg.get("caption", "").strip()
    
    # Track user
    if chat_id not in admin_db.get("users", []):
        admin_db.setdefault("users", []).append(chat_id)
        save_admin_db()
    
    lower = text.lower()
    logger.info(f"📩 Message from {chat_id}: {text[:50]}...")
    
    # Check force join
    # (simplified - skip for now)
    
    # Commands
    if lower in ["/start", "/help", "/menu"]:
        text_start = (
            "╔═══════════╗\n"
            f"       {get_pemoji('dashboard', '📊')} <b>NUMBER BOT</b>\n"
            "╚═══════════╝\n"
            f"{get_pemoji('rocket', '🚀')} Welcome to Number & OTP Service\n"
            "━━━━━━━━━━━━\n"
            f"{get_pemoji('done', '✅')} Choose an option below\n"
            "to continue using the bot.\n"
            "━━━━━━━━━━━━\n"
            f"{get_pemoji('gem', '💎')} Premium OTP Service"
        )
        send_bot_message(chat_id, text_start, get_bot_menu_keyboard(chat_id))
        return
    
    if "get number" in lower:
        render_services_list(chat_id)
        return
    
    if "search range" in lower or "search number" in lower or lower == "/search":
        user_conversations[chat_id] = "waiting_for_search"
        text_help = (
            "╔═══════════╗\n"
            f"     {get_pemoji('search', '🔍')} <b>SEARCH RANGE</b>\n"
            "╚═══════════╝\n"
            f"{get_pemoji('done', '📌')} Enter 3 to 11 digits\n"
            "to search for a number.\n"
            "━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id='5395444784611480792'>📝</tg-emoji> Example:\n"
            "➥ 880\n"
            "➥ 9227373\n"
            "━━━━━━━━━━━━━\n"
            f"{get_pemoji('search', '🔍')} Fast Number Lookup System"
        )
        send_bot_message(chat_id, text_help, {"inline_keyboard": [[{"text": " Back", "callback_data": "usr_menu_home", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]]})
        return
    
    if lower.startswith("/search "):
        query = text[8:].strip()
        if query:
            clean = re.sub(r'[Xx*]', '', query.replace("+", "").strip())
            if clean.isdigit() and 3 <= len(clean) <= 11:
                trigger_buy_number(chat_id, clean + "XXX")
            else:
                search_number_otp(chat_id, clean)
        else:
            send_bot_message(chat_id, "❌ Please specify a number to search.")
        return
    
    if "traffic" in lower or lower == "/traffic":
        render_traffic_home(chat_id)
        return
    
    if "balance" in lower or lower == "/balance":
        render_user_balance(chat_id)
        return
    
    if lower.startswith(("/getnum ", "/buy ", "/get ")):
        parts = text.split()
        if len(parts) > 1:
            q = parts[-1].replace("+", "").strip()
            trigger_buy_number(chat_id, q)
        else:
            send_bot_message(chat_id, "❌ Please specify a range. Usage: <code>/getnum 237620610XXX</code>")
        return
    
    # Handle search input
    if user_conversations.get(chat_id) == "waiting_for_search":
        user_conversations.pop(chat_id, None)
        clean_text = re.sub(r'[Xx*]', '', text.replace("+", "").strip())
        
        if clean_text.isdigit() and 3 <= len(clean_text) <= 11:
            trigger_buy_number(chat_id, clean_text + "XXX")
        else:
            search_number_otp(chat_id, clean_text)
        return
    
    # Admin panel
    if "admin panel" in lower or lower == "/admin":
        if str(chat_id) in admin_db.get("admins", [OWNER_ID]):
            send_bot_message(chat_id, "👑 <b>Admin Panel</b>\n\nUse the buttons below:", {
                "inline_keyboard": [
                    [{"text": "📊 Dashboard", "callback_data": "adm_main_menu", "style": "primary"}]
                ]
            })
        else:
            send_bot_message(chat_id, "❌ You are not authorized.")
        return

# ============================================================
# CALLBACK HANDLER
# ============================================================

def handle_callback_query(callback_query):
    callback_id = callback_query.get("id")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    message_id = callback_query.get("message", {}).get("message_id")
    data = callback_query.get("data", "")
    
    if not chat_id or not message_id:
        answer_callback(callback_id)
        return
    
    logger.info(f"🔄 Callback: {data} from {chat_id}")
    
    if data == "usr_menu_home":
        answer_callback(callback_id)
        render_services_list(chat_id, message_id)
    
    elif data.startswith("usr_srv_sel:"):
        service_id = data.split(":")[1]
        answer_callback(callback_id, "Loading countries...")
        render_countries_list(chat_id, message_id, service_id)
    
    elif data.startswith("usr_ctr_sel:"):
        parts = data.split(":")
        service_id = parts[1]
        country_code = parts[2]
        answer_callback(callback_id, "Allocating...")
        allocate_and_show_number_py(chat_id, message_id, service_id, country_code, callback_id)
    
    elif data.startswith("usr_change_num:"):
        parts = data.split(":")
        service_id = parts[1]
        country_code = parts[2]
        answer_callback(callback_id, "Retrying...")
        allocate_and_show_number_py(chat_id, message_id, service_id, country_code, callback_id)
    
    elif data.startswith("buy_"):
        range_val = data.split("_", 1)[1]
        answer_callback(callback_id, "Getting number...")
        trigger_buy_number(chat_id, range_val, message_id=message_id, callback_id=callback_id)
    
    elif data == "usr_search_home":
        answer_callback(callback_id, "Opening search...")
        user_conversations[chat_id] = "waiting_for_search"
        text_help = (
            "╔═══════════╗\n"
            f"     {get_pemoji('search', '🔍')} <b>SEARCH RANGE</b>\n"
            "╚═══════════╝\n"
            f"{get_pemoji('done', '📌')} Enter 3 to 11 digits\n"
            "to search for a number.\n"
            "━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id='5395444784611480792'>📝</tg-emoji> Example:\n"
            "➥ 880\n"
            "➥ 9227373\n"
            "━━━━━━━━━━━━━\n"
            f"{get_pemoji('search', '🔍')} Fast Number Lookup System"
        )
        edit_bot_message(chat_id, message_id, text_help, {"inline_keyboard": [[{"text": " Back", "callback_data": "usr_menu_home", "style": "danger", "icon_custom_emoji_id": "5267490665117275176"}]]})
    
    elif data == "usr_otp_grp":
        answer_callback(callback_id, "OTP Group link not set!", show_alert=True)
    
    elif data == "tr_refresh":
        answer_callback(callback_id, "Refreshing...")
        render_traffic_home(chat_id, message_id)
    
    elif data == "tr_close":
        answer_callback(callback_id, "Closed")
        call_telegram("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    
    elif data == "adm_main_menu":
        answer_callback(callback_id)
        send_bot_message(chat_id, "👑 <b>Admin Panel</b>\n\nUse the buttons below:", {
            "inline_keyboard": [
                [{"text": "📊 Dashboard", "callback_data": "adm_main_menu", "style": "primary"}]
            ]
        })
    
    else:
        answer_callback(callback_id, "Unknown command", show_alert=True)

# ============================================================
# BACKGROUND MONITOR (SIMPLIFIED)
# ============================================================

def monitor_loop():
    logger.info("Monitor loop started")
    while True:
        try:
            # Simple ping to keep sessions alive
            for panel in panels:
                if panel.get("sessionCookie"):
                    pass
            time.sleep(60)
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            time.sleep(60)

# ============================================================
# MAIN
# ============================================================

def main():
    logger.info("🚀 Starting DXA Voltx Bot...")
    logger.info(f"📋 Panels loaded: {len(panels)}")
    logger.info(f"📋 Services loaded: {len(load_services())}")
    
    # Start monitor
    threading.Thread(target=monitor_loop, daemon=True).start()
    
    # Clear old updates
    call_telegram("getUpdates", {"offset": -1, "timeout": 0})
    logger.info("✅ Bot is running!")
    
    offset = None
    while True:
        try:
            payload = {"timeout": 30}
            if offset:
                payload["offset"] = offset
            
            updates = call_telegram("getUpdates", payload)
            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        threading.Thread(target=handle_message, args=(update["message"],)).start()
                    elif "callback_query" in update:
                        threading.Thread(target=handle_callback_query, args=(update["callback_query"],)).start()
            
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
