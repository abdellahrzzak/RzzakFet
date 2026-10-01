# -*- coding: utf-8 -*-
"""
RzzakFet Hardware-Bound License & Anti-Abuse Authentication Engine
Enforces:
1. Strict Machine-Hardware Binding (MachineGuid / Hardware Fingerprint).
2. Exactly One 15-Day Trial per Computer:
   - The trial is bound to the physical machine hardware.
   - If 15 days expire, changing or re-registering with another Google account is strictly blocked.
3. Central Super-Admin control for alizdihardevlop@gmail.com:
   - Can activate, extend (1 year / 2 years), or block any computer remotely.
4. Seamless in-app activation:
   - No external mock web pages or browser redirects.
   - All activation happens directly inside the application.
5. In-App Auto-Update checker via Firebase Cloud metadata.
"""

import os
import sys
import json
import time
import uuid
import hmac
import hashlib
import winreg
import threading
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_data_dir():
    if getattr(sys, 'frozen', False):
        app_data = os.path.join(os.path.expanduser("~"), "AppData", "Local", "RzzakFet")
        os.makedirs(app_data, exist_ok=True)
        return os.path.join(app_data, "data")
    return os.path.join(get_base_dir(), "data")

def to_firestore_value(v):
    if isinstance(v, bool):
        return {"booleanValue": v}
    elif isinstance(v, int):
        return {"integerValue": str(v)}
    elif isinstance(v, float):
        return {"doubleValue": v}
    elif isinstance(v, str):
        return {"stringValue": v}
    elif isinstance(v, dict):
        return {"mapValue": {"fields": {k: to_firestore_value(val) for k, val in v.items()}}}
    elif isinstance(v, list):
        return {"arrayValue": {"values": [to_firestore_value(item) for item in v]}}
    elif v is None:
        return {"nullValue": None}
    return {"stringValue": str(v)}

def from_firestore_value(val_dict):
    if not isinstance(val_dict, dict):
        return val_dict
    if "stringValue" in val_dict:
        return val_dict["stringValue"]
    if "booleanValue" in val_dict:
        return val_dict["booleanValue"]
    if "integerValue" in val_dict:
        try:
            return int(val_dict["integerValue"])
        except Exception:
            return val_dict["integerValue"]
    if "doubleValue" in val_dict:
        return val_dict["doubleValue"]
    if "timestampValue" in val_dict:
        return val_dict["timestampValue"]
    if "mapValue" in val_dict:
        fields = val_dict["mapValue"].get("fields", {})
        return {k: from_firestore_value(v) for k, v in fields.items()}
    if "arrayValue" in val_dict:
        values = val_dict["arrayValue"].get("values", [])
        return [from_firestore_value(v) for v in values]
    if "nullValue" in val_dict:
        return None
    return str(val_dict)


class AuthEngine:
    def __init__(self):
        self.base_dir = get_base_dir()
        self.data_dir = get_data_dir()
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.config_file = os.path.join(self.base_dir, "config", "auth_config.json")
        self.session_file = os.path.join(self.data_dir, "user_session.json")
        self.users_db_file = os.path.join(self.data_dir, "registered_users.json")
        self.update_cache_file = os.path.join(self.data_dir, "version_cache.json")
        
        # Hidden Hardware Anchor (survives app reinstallation & session clearing)
        self.hw_anchor_file = os.path.join(
            os.path.expanduser("~"), "AppData", "Local", "Microsoft", "Windows", "RzzakFet_License.dat"
        )
        os.makedirs(os.path.dirname(self.hw_anchor_file), exist_ok=True)

        self.config = self._load_config()
        self.machine_id = self._get_machine_id()
        
        # Ensure default super admin account
        self._ensure_super_admin()

        # Non-blocking cloud state caching
        self._cached_cloud_machine = None
        self._last_cloud_sync_time = 0
        self._sync_in_progress = False

    def _trigger_background_cloud_sync(self):
        if getattr(self, '_sync_in_progress', False):
            return
        self._sync_in_progress = True
        self._last_cloud_sync_time = time.time()
        
        def _bg_task():
            try:
                cm = self._cloud_get_machine(self.machine_id)
                if cm:
                    self._cached_cloud_machine = cm
                    self._write_hw_ledger(cm)
            except Exception:
                pass
            finally:
                self._sync_in_progress = False

        t = threading.Thread(target=_bg_task, daemon=True)
        t.start()

    def _load_config(self):
        default_config = {
            "app_info": {
                "name": "RzzakFet",
                "version": "1.0.0",
                "version_label": "v1.0 الرسمية",
                "release_date": "2026-09-22"
            },
            "firebase": {
                "project_id": "rzzakfet-app",
                "api_key": "AIzaSyDRAO-ae9rMBFf722p-Jei1UnbtCQ4i0qQ",
                "firestore_base_url": "https://firestore.googleapis.com/v1/projects/rzzakfet-app/databases/(default)/documents"
            },
            "licensing": {
                "default_trial_days": 15,
                "super_admin_email": "alizdihardevlop@gmail.com",
                "admin_emails": ["alizdihardevlop@gmail.com"],
                "contact_whatsapp": "+212 600000000",
                "contact_email": "alizdihardevlop@gmail.com"
            }
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_config.update(data)
            except Exception as e:
                print(f"[AuthEngine] Error loading config: {e}")
        return default_config

    def _get_machine_id(self):
        """Generates permanent unique Hardware Serial: RZZAK-XXXX-XXXX-XXXX."""
        guid = ""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                val, _ = winreg.QueryValueEx(key, "MachineGuid")
                if val:
                    guid = str(val).strip().upper()
        except Exception:
            pass

        if not guid:
            guid = f"{uuid.getnode()}:{os.environ.get('COMPUTERNAME', 'PC')}"

        h = hashlib.sha256(f"RZZAK_HW_{guid}".encode('utf-8')).hexdigest().upper()
        return f"RZZAK-{h[:4]}-{h[4:8]}-{h[8:12]}"

    def _get_secret_key(self):
        return f"SEC_RZZAK_HW_{self.machine_id}"

    def _generate_signature(self, payload):
        secret = self._get_secret_key()
        msg = f"{payload.get('machine_id')}:{payload.get('bound_email')}:{payload.get('status')}:{payload.get('trial_expires_at')}:{payload.get('expires_at')}"
        return hmac.new(secret.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()

    def _read_hw_ledger(self):
        """Reads persistent hardware anchor from disk."""
        target_files = [self.hw_anchor_file, os.path.join(self.data_dir, "hw_anchor.dat")]
        for p in target_files:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Verify signature
                        if data.get("machine_id") == self.machine_id:
                            expected_sig = self._generate_signature(data)
                            if data.get("signature") == expected_sig:
                                return data
                except Exception:
                    pass
        return None

    def _write_hw_ledger(self, data):
        """Persists hardware anchor to hidden system location and app data."""
        data["machine_id"] = self.machine_id
        data["signature"] = self._generate_signature(data)
        data["last_synced"] = datetime.now().isoformat()

        target_files = [self.hw_anchor_file, os.path.join(self.data_dir, "hw_anchor.dat")]
        for p in target_files:
            try:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[AuthEngine] Error writing ledger to {p}: {e}")

    def _load_users_db(self):
        if os.path.exists(self.users_db_file):
            try:
                with open(self.users_db_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_users_db(self, db):
        try:
            with open(self.users_db_file, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[AuthEngine] Error saving users DB: {e}")

    def _ensure_super_admin(self):
        admin_email = self.config.get("licensing", {}).get("super_admin_email", "alizdihardevlop@gmail.com")
        db = self._load_users_db()
        if admin_email not in db:
            db[admin_email] = {
                "email": admin_email,
                "name": "المدير العام والتطوير",
                "role": "admin",
                "status": "active",
                "subscription_type": "lifetime",
                "machine_id": self.machine_id,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=36500)).isoformat(),
                "notes": "الحساب الإداري المالك الأوحد للبرنامج"
            }
            self._save_users_db(db)

    # ================= FIREBASE CLOUD FIRESTORE =================

    def _firestore_url(self, path):
        base = self.config.get("firebase", {}).get("firestore_base_url", "").rstrip("/")
        api_key = self.config.get("firebase", {}).get("api_key", "").strip()
        url = f"{base}/{path}"
        if api_key:
            url += f"?key={api_key}"
        return url

    def _cloud_get_machine(self, machine_id):
        doc_id = urllib.parse.quote(machine_id.strip(), safe="")
        url = self._firestore_url(f"machines/{doc_id}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RzzakFet-Desktop/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                fields = data.get("fields", {})
                return {k: from_firestore_value(v) for k, v in fields.items()}
        except Exception:
            return None

    def _cloud_save_machine(self, machine_record):
        m_id = machine_record.get("machine_id", "").strip()
        if not m_id:
            return False
        doc_id = urllib.parse.quote(m_id, safe="")
        url = self._firestore_url(f"machines/{doc_id}")
        
        fields = {k: to_firestore_value(v) for k, v in machine_record.items()}
        payload = json.dumps({"fields": fields}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "User-Agent": "RzzakFet-Desktop/1.0"
            }, method="PATCH")
            with urllib.request.urlopen(req, timeout=4) as resp:
                return True
        except Exception:
            return False

    def _cloud_list_machines(self):
        url = self._firestore_url("machines")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RzzakFet-Desktop/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                docs = data.get("documents", [])
                machines = []
                for d in docs:
                    fields = d.get("fields", {})
                    machines.append({k: from_firestore_value(v) for k, v in fields.items()})
                return machines
        except Exception:
            return None

    # ================= HARDWARE-BOUND ACTIVATION (ANTI-ABUSE) =================

    def activate_machine(self, email, name=""):
        """
        Activates the application on this machine.
        Enforces:
        - Exactly 15 days of trial per machine.
        - Super-admin (alizdihardevlop@gmail.com) always has full lifetime access.
        - Once 15 days expire on this PC, re-registering with another account is blocked!
        """
        email = email.lower().strip()
        if not email or "@" not in email:
            return {"success": False, "error": "يرجى إدخال بريد إلكتروني صحيح (Google / Gmail)."}

        super_admin_email = self.config.get("licensing", {}).get("super_admin_email", "alizdihardevlop@gmail.com").lower()
        now = datetime.now()

        # 1. SUPER ADMIN BYPASS: Always granted full active lifetime access on any machine
        if email == super_admin_email:
            session_data = {
                "machine_id": self.machine_id,
                "bound_email": email,
                "email": email,
                "name": name or "المدير العام والتطوير",
                "role": "admin",
                "status": "active",
                "subscription_type": "lifetime",
                "expires_at": (now + timedelta(days=36500)).isoformat(),
                "trial_consumed": True,
                "is_admin": True,
                "saved_at": now.isoformat()
            }
            self._save_session(session_data)
            self._write_hw_ledger(session_data)
            self._cloud_save_machine(session_data)
            
            # Record in DB
            db = self._load_users_db()
            db[email] = session_data
            db[self.machine_id] = session_data
            self._save_users_db(db)
            
            return {
                "success": True,
                "is_admin": True,
                "status": "active",
                "message": "مرحباً بك يا مدير النظام العام. تم تفعيل كامل الصلاحيات."
            }

        # Check if the entered email already has an active paid subscription in DB or Cloud
        db = self._load_users_db()
        email_record = db.get(email)
        if email_record and email_record.get("status") == "active":
            user_exp = email_record.get("expires_at")
            if user_exp:
                try:
                    exp_dt = datetime.fromisoformat(user_exp)
                    if exp_dt > now:
                        remaining = max(0, (exp_dt - now).days)
                        email_record["machine_id"] = self.machine_id
                        email_record["bound_email"] = email
                        self._save_active_session(email, name or email_record.get("name", ""), "active", user_exp, email_record.get("subscription_type", "active"))
                        self._write_hw_ledger(email_record)
                        self._cloud_save_machine(email_record)
                        return {
                            "success": True,
                            "status": "active",
                            "remaining_days": remaining,
                            "message": f"تم تفعيل اشتراكك المرخص على هذا الحاسوب بنجاح. متبقي: {remaining} يوماً."
                        }
                except Exception:
                    pass

        # 2. NORMAL USERS: Check hardware history to prevent multiple-account trial abuse
        ledger = self._read_hw_ledger()
        cloud_machine = self._cloud_get_machine(self.machine_id)
        active_rec = cloud_machine if cloud_machine else ledger

        if active_rec:
            # Machine was previously activated on this PC!
            rec_status = active_rec.get("status", "trial")
            first_date_str = active_rec.get("first_activation_date")
            trial_exp_str = active_rec.get("trial_expires_at")
            expires_at_str = active_rec.get("expires_at", trial_exp_str)
            bound_email = active_rec.get("bound_email", email)

            # Check if this machine was BLOCKED by the admin
            if rec_status == "blocked":
                return {
                    "success": False,
                    "error": "⛔ هذا الحاسوب محظور من قِبل إدارة البرنامج. يرجى التواصل مع الإدارة: alizdihardevlop@gmail.com"
                }

            # Check if ACTIVE subscription
            if rec_status == "active" and expires_at_str:
                try:
                    exp_dt = datetime.fromisoformat(expires_at_str)
                    if exp_dt > now:
                        # Machine has active valid subscription!
                        remaining = max(0, (exp_dt - now).days)
                        active_rec["bound_email"] = email
                        self._save_active_session(email, name, "active", expires_at_str, active_rec.get("subscription_type", "1_year"))
                        return {
                            "success": True,
                            "status": "active",
                            "remaining_days": remaining,
                            "message": f"اشتراك هذا الحاسوب نشيط ومرخص. متبقي: {remaining} يوماً."
                        }
                    else:
                        return {
                            "success": False,
                            "error": "⌛ انتهت مدة الاشتراك السنوي لهذا الحاسوب. لتجديد الاشتراك (سنة أو سنتين) يرجى التواصل مع الإدارة: alizdihardevlop@gmail.com"
                        }
                except Exception:
                    pass

            # Machine is in TRIAL mode: Check if 15 days have expired!
            if trial_exp_str:
                try:
                    trial_exp_dt = datetime.fromisoformat(trial_exp_str)
                    if now > trial_exp_dt:
                        # TRIAL HAS FULLY EXPIRED ON THIS MACHINE!
                        return {
                            "success": False,
                            "error": f"⛔ لقد استنفذ هذا الحاسوب فترته التجريبية المحددة (15 يوماً) مسبقاً (تم تشغيله أول مرة بتاريخ: {first_date_str[:10] if first_date_str else '-'}).\nلا يمكن بدء فترة تجريبية جديدة بحساب آخر على نفس الجهاز.\nلتفعيل واستخدام البرنامج، يرجى الاشتراك بالتواصل مع إدارة البرنامج: alizdihardevlop@gmail.com"
                        }
                    else:
                        # Still within the original 15 days: permit usage, bound to original expiry!
                        remaining = max(0, (trial_exp_dt - now).days)
                        self._save_active_session(bound_email, name, "trial", trial_exp_str, "trial")
                        return {
                            "success": True,
                            "status": "trial",
                            "remaining_days": remaining,
                            "message": f"تم استئناف الفترة التجريبية الأصلية لهذا الحاسوب. متبقي: {remaining} يوماً."
                        }
                except Exception:
                    pass

        # 3. BRAND NEW COMPUTER: Grant exactly 15 days of trial, locked to this machine ID
        default_days = self.config.get("licensing", {}).get("default_trial_days", 15)
        first_act_date = now.isoformat()
        trial_exp_date = (now + timedelta(days=default_days)).isoformat()

        new_machine_record = {
            "machine_id": self.machine_id,
            "bound_email": email,
            "user_name": name or email.split("@")[0],
            "first_activation_date": first_act_date,
            "trial_expires_at": trial_exp_date,
            "expires_at": trial_exp_date,
            "trial_consumed": True,
            "status": "trial",
            "subscription_type": "trial",
            "role": "user",
            "created_at": first_act_date,
            "last_login": first_act_date,
            "notes": f"فترة تجريبية أولى 15 يوماً مقترنة بعتاد الحاسوب {self.machine_id}"
        }

        # Write to Hardware Anchor & Firebase Cloud
        self._write_hw_ledger(new_machine_record)
        self._cloud_save_machine(new_machine_record)

        # Update local DB
        db = self._load_users_db()
        db[email] = new_machine_record
        self._save_users_db(db)

        # Save session
        self._save_active_session(email, name, "trial", trial_exp_date, "trial")

        return {
            "success": True,
            "status": "trial",
            "remaining_days": default_days,
            "message": f"تم تفعيل الفترة التجريبية (15 يوماً) لهذا الحاسوب بنجاح."
        }

    def _save_active_session(self, email, name, status, expires_at, sub_type):
        session_data = {
            "email": email,
            "name": name or email.split("@")[0],
            "photo": "https://lh3.googleusercontent.com/a/default-user=s96-c",
            "role": "user",
            "status": status,
            "subscription_type": sub_type,
            "machine_id": self.machine_id,
            "expires_at": expires_at,
            "saved_at": datetime.now().isoformat()
        }
        self._save_session(session_data)

    def _save_session(self, session_payload):
        session_payload["machine_id"] = self.machine_id
        session_payload["signature"] = self._generate_signature(session_payload)
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session_payload, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[AuthEngine] Error saving session: {e}")
            return False

    def load_session(self):
        if not os.path.exists(self.session_file):
            return None
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                session = json.load(f)
            
            # Verify machine ID
            if session.get("machine_id") != self.machine_id:
                return None
            
            return session
        except Exception:
            return None

    def clear_session(self):
        if os.path.exists(self.session_file):
            try:
                os.remove(self.session_file)
                return True
            except Exception:
                pass
        return False

    # ================= CORE LICENSING & STATUS EVALUATION =================

    def get_auth_status(self, force_cloud=False):
        session = self.load_session()
        super_admin_email = self.config.get("licensing", {}).get("super_admin_email", "alizdihardevlop@gmail.com").lower()
        now = datetime.now()

        cfg_info = {
            "machine_id": self.machine_id,
            "contact_email": super_admin_email,
            "version": self.config.get("app_info", {}).get("version", "1.0.0"),
            "version_label": self.config.get("app_info", {}).get("version_label", "v1.0 الرسمية")
        }

        # Check hardware anchor - local ledger returns instantly (0ms)
        ledger = self._read_hw_ledger()
        if force_cloud:
            cloud_machine = self._cloud_get_machine(self.machine_id)
            if cloud_machine:
                self._cached_cloud_machine = cloud_machine
                self._write_hw_ledger(cloud_machine)
            hw_rec = cloud_machine if cloud_machine else (self._cached_cloud_machine or ledger)
        else:
            hw_rec = self._cached_cloud_machine if self._cached_cloud_machine else ledger
            # Trigger background sync every 10 minutes without blocking the main thread
            if time.time() - getattr(self, '_last_cloud_sync_time', 0) > 600:
                self._trigger_background_cloud_sync()

        # If no session and no ledger, unauthenticated
        if not session and not hw_rec:
            return {
                "is_authenticated": False,
                "machine_id": self.machine_id,
                "email": None,
                "name": None,
                "status": None,
                "is_admin": False,
                "is_blocked": False,
                "is_expired": False,
                "is_valid": False,
                "expires_at": None,
                "remaining_days": None,
                "trial_consumed": False,
                "config": cfg_info
            }

        # Prioritize session or ledger
        email = (session.get("email") if session else (hw_rec.get("bound_email") if hw_rec else "")).lower().strip()
        is_admin = (email == super_admin_email)

        # Super Admin is always active
        if is_admin:
            return {
                "is_authenticated": True,
                "machine_id": self.machine_id,
                "email": email,
                "name": session.get("name", "المدير العام والتطوير") if session else "المدير العام والتطوير",
                "picture": "https://lh3.googleusercontent.com/a/default-user=s96-c",
                "status": "active",
                "is_admin": True,
                "is_blocked": False,
                "is_expired": False,
                "is_valid": True,
                "expires_at": "2099-01-01T00:00:00",
                "remaining_days": 26000,
                "trial_consumed": True,
                "config": cfg_info
            }

        # Check effective status of this machine
        status = hw_rec.get("status", "trial") if hw_rec else session.get("status", "trial")
        expires_at_str = hw_rec.get("expires_at") if hw_rec else session.get("expires_at")
        
        is_blocked = (status == "blocked")
        is_expired = False
        remaining_days = 0

        if expires_at_str:
            try:
                exp_dt = datetime.fromisoformat(expires_at_str)
                remaining_delta = exp_dt - now
                remaining_days = max(0, remaining_delta.days)
                if now > exp_dt:
                    is_expired = True
            except Exception:
                pass

        if is_blocked:
            is_valid = False
            effective_status = "blocked"
            error_message = "تم حظر هذا الحاسوب من قِبل إدارة البرنامج. يرجى التواصل مع المدير: alizdihardevlop@gmail.com"
        elif is_expired:
            is_valid = False
            effective_status = "expired"
            error_message = f"انتهت الفترة المحددة لهذا الحاسوب ({status}). يرجى تجديد الاشتراك بالتواصل مع الإدارة: alizdihardevlop@gmail.com"
        else:
            is_valid = True
            effective_status = status
            error_message = None

        name = session.get("name") if session else (hw_rec.get("user_name") if hw_rec else email.split("@")[0])

        return {
            "is_authenticated": True,
            "machine_id": self.machine_id,
            "email": email,
            "name": name or email.split("@")[0],
            "picture": "https://lh3.googleusercontent.com/a/default-user=s96-c",
            "status": effective_status,
            "is_admin": False,
            "is_blocked": is_blocked,
            "is_expired": is_expired,
            "is_valid": is_valid,
            "expires_at": expires_at_str,
            "remaining_days": remaining_days,
            "trial_consumed": bool(hw_rec.get("trial_consumed") if hw_rec else False),
            "error_message": error_message,
            "config": cfg_info
        }

    # ================= ADMIN LICENSING ACTIONS =================

    def list_all_users(self):
        """Lists all registered machines and accounts."""
        super_admin_email = self.config.get("licensing", {}).get("super_admin_email", "alizdihardevlop@gmail.com").lower()
        now = datetime.now()

        # Try cloud first
        cloud_machines = self._cloud_list_machines()
        db = self._load_users_db()

        if cloud_machines is not None:
            for m in cloud_machines:
                m_id = m.get("machine_id")
                if m_id:
                    db[m_id] = m
            self._save_users_db(db)

        items = []
        for key, rec in db.items():
            email = rec.get("bound_email") or rec.get("email") or key
            is_admin = (email.lower() == super_admin_email)
            expires_at_str = rec.get("expires_at")
            remaining_days = 0
            is_expired = False

            if expires_at_str:
                try:
                    exp = datetime.fromisoformat(expires_at_str)
                    diff = exp - now
                    remaining_days = max(0, diff.days)
                    if exp < now:
                        is_expired = True
                except Exception:
                    pass

            items.append({
                "machine_id": rec.get("machine_id", key),
                "email": email,
                "name": rec.get("user_name") or rec.get("name", email.split("@")[0]),
                "status": rec.get("status", "trial"),
                "subscription_type": rec.get("subscription_type", "trial"),
                "role": "admin" if is_admin else "user",
                "is_admin": is_admin,
                "created_at": rec.get("first_activation_date") or rec.get("created_at"),
                "expires_at": expires_at_str,
                "remaining_days": remaining_days,
                "is_expired": is_expired,
                "trial_consumed": rec.get("trial_consumed", True)
            })

        items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return items

    def update_user_subscription(self, target_identifier, status=None, extend_years=None, new_expires_at=None, sub_type=None):
        """Updates subscription for a given machine ID or email."""
        target_identifier = target_identifier.strip()
        db = self._load_users_db()
        
        # Find record by machine_id or email
        matched_key = None
        for k, v in db.items():
            if k == target_identifier or v.get("bound_email") == target_identifier.lower() or v.get("email") == target_identifier.lower() or v.get("machine_id") == target_identifier:
                matched_key = k
                break

        if not matched_key:
            # Create entry if not found
            matched_key = target_identifier
            db[matched_key] = {
                "machine_id": target_identifier if target_identifier.startswith("RZZAK-") else self.machine_id,
                "bound_email": target_identifier if "@" in target_identifier else "unknown@user.com",
                "status": "active",
                "created_at": datetime.now().isoformat()
            }

        rec = db[matched_key]

        if status is not None and status in ["active", "trial", "blocked"]:
            rec["status"] = status

        if sub_type is not None:
            rec["subscription_type"] = sub_type

        # Handle expiry extension (+1 or +2 years)
        if extend_years is not None and extend_years > 0:
            current_exp_str = rec.get("expires_at")
            base_date = datetime.now()
            if current_exp_str:
                try:
                    parsed_exp = datetime.fromisoformat(current_exp_str)
                    if parsed_exp > base_date:
                        base_date = parsed_exp
                except Exception:
                    pass
            new_exp = base_date + timedelta(days=365 * extend_years)
            rec["expires_at"] = new_exp.isoformat()
            rec["status"] = "active"
            rec["subscription_type"] = f"{extend_years}_year" if extend_years == 1 else f"{extend_years}_years"

        elif new_expires_at:
            rec["expires_at"] = new_expires_at

        # Save to Cloud & Local
        self._cloud_save_machine(rec)
        self._save_users_db(db)

        # If modifying current machine, update ledger and active session
        if rec.get("machine_id") == self.machine_id:
            self._write_hw_ledger(rec)
            active_s = self.load_session()
            if active_s:
                active_s["status"] = rec.get("status")
                active_s["expires_at"] = rec.get("expires_at")
                self._save_session(active_s)

        now = datetime.now()
        remaining_days = 0
        is_expired = False
        if rec.get("expires_at"):
            try:
                exp_dt = datetime.fromisoformat(rec["expires_at"])
                remaining_days = max(0, (exp_dt - now).days)
                if now > exp_dt:
                    is_expired = True
            except Exception:
                pass

        return {
            "success": True,
            "machine_id": rec.get("machine_id"),
            "status": rec.get("status"),
            "expires_at": rec.get("expires_at"),
            "remaining_days": remaining_days,
            "is_expired": is_expired
        }

    def delete_user(self, target_identifier):
        target_identifier = target_identifier.strip()
        db = self._load_users_db()
        matched_key = None
        for k, v in db.items():
            if k == target_identifier or v.get("bound_email") == target_identifier.lower() or v.get("machine_id") == target_identifier:
                matched_key = k
                break

        if matched_key and matched_key in db:
            del db[matched_key]
            self._save_users_db(db)
            return {"success": True}
        return {"success": False, "error": "السجل غير موجود"}

    # ================= IN-APP AUTO-UPDATE & OTA LIVE PATCH ENGINE =================

    def get_current_app_version(self):
        iv_file = os.path.join(get_data_dir(), "installed_version.json")
        if os.path.exists(iv_file):
            try:
                with open(iv_file, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    if d.get("version"):
                        return d["version"]
            except Exception:
                pass
        return self.config.get("app_info", {}).get("version", "2.0.0")

    def check_for_updates(self, force_cloud=False):
        current_version = self.get_current_app_version()
        meta = {
            "current_version": current_version,
            "latest_version": current_version,
            "patch_type": "live_patch",
            "patch_url": "",
            "download_url": "",
            "release_notes": "النسخة الحالية الرسمية: لوحة القيادة الذكية وإدارة القاعات المتخصصة والامتحانات.",
            "force_update": False,
            "update_available": False
        }

        # Check local cache first (instant 0ms response)
        if os.path.exists(self.update_cache_file):
            try:
                with open(self.update_cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    cached["current_version"] = current_version
                    cached["update_available"] = self._is_newer_version(cached.get("latest_version", current_version), current_version)
                    meta = cached
            except Exception:
                pass

        if force_cloud:
            return self._fetch_updates_from_cloud(meta, current_version)
        else:
            # Query cloud asynchronously in the background so startup is lightning fast
            t = threading.Thread(target=self._fetch_updates_from_cloud, args=(meta, current_version), daemon=True)
            t.start()
            return meta

    def _fetch_updates_from_cloud(self, meta, current_version):
        cloud_info = {}
        # 1. Primary: Firestore Cloud Metadata (Fastest for live patches & versions)
        url = self._firestore_url("app_meta/version_info")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RzzakFet-Desktop/2.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                fields = data.get("fields", {})
                cloud_info = {k: from_firestore_value(v) for k, v in fields.items()}
        except Exception:
            pass

        # 2. Secondary: GitHub Releases API
        gh_info = {}
        gh_url = "https://api.github.com/repos/abdellahrzzak/RzzakFet/releases/latest"
        try:
            req = urllib.request.Request(gh_url, headers={
                "User-Agent": "RzzakFet-Desktop/2.0",
                "Accept": "application/vnd.github.v3+json"
            })
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                tag_name = data.get("tag_name", "").lstrip("v").strip()
                if tag_name:
                    gh_info["latest_version"] = tag_name
                    gh_info["release_notes"] = data.get("body", "") or "تحديث جديد لبرنامج RzzakFet."
                    assets = data.get("assets", [])
                    download_url = ""
                    for a in assets:
                        name = a.get("name", "").lower()
                        if name.endswith(".exe"):
                            download_url = a.get("browser_download_url", "")
                            break
                    if not download_url:
                        download_url = data.get("html_url", "")
                    gh_info["download_url"] = download_url
                    gh_info["patch_type"] = "full_exe"
        except Exception:
            pass

        # Pick whichever source reports the newest version
        chosen = {}
        cloud_ver = str(cloud_info.get("latest_version", "0.0.0"))
        gh_ver = str(gh_info.get("latest_version", "0.0.0"))

        if self._is_newer_version(cloud_ver, gh_ver):
            chosen = cloud_info
        elif gh_info and gh_info.get("latest_version"):
            chosen = gh_info
        elif cloud_info and cloud_info.get("latest_version"):
            chosen = cloud_info

        if chosen and chosen.get("latest_version"):
            latest_ver = chosen.get("latest_version")
            meta["latest_version"] = latest_ver
            meta["download_url"] = chosen.get("download_url", "")
            meta["patch_type"] = chosen.get("patch_type", "live_patch" if "raw.githubusercontent" in chosen.get("patch_url", "") else "full_exe")
            meta["patch_url"] = chosen.get("patch_url", f"https://raw.githubusercontent.com/abdellahrzzak/RzzakFet/main/ui/index.html")
            meta["release_notes"] = chosen.get("release_notes", meta.get("release_notes", ""))
            meta["force_update"] = chosen.get("force_update", False)
            meta["update_available"] = self._is_newer_version(latest_ver, current_version)
            
            with open(self.update_cache_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            return meta

        return meta

    def publish_live_patch(self, new_version, release_notes, patch_type="live_patch", download_url=""):
        patch_url = f"https://raw.githubusercontent.com/abdellahrzzak/RzzakFet/main/ui/index.html?t={int(time.time())}"
        update_data = {
            "latest_version": new_version,
            "patch_type": patch_type,
            "patch_url": patch_url,
            "download_url": download_url or "https://github.com/abdellahrzzak/RzzakFet/releases",
            "release_notes": release_notes,
            "force_update": False,
            "updated_at": datetime.now().isoformat()
        }
        
        url = self._firestore_url("app_meta/version_info")
        fields = {k: to_firestore_value(v) for k, v in update_data.items()}
        payload = json.dumps({"fields": fields}).encode("utf-8")
        
        try:
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "User-Agent": "RzzakFet-Desktop/2.0"
            }, method="PATCH")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        except Exception as e:
            print("Notice updating Firestore meta:", e)

        update_data["current_version"] = self.get_current_app_version()
        update_data["update_available"] = False
        with open(self.update_cache_file, "w", encoding="utf-8") as f:
            json.dump(update_data, f, ensure_ascii=False, indent=2)

        return {"success": True, "data": update_data}

    def publish_update(self, new_version, download_url, release_notes, force_update=False):
        return self.publish_live_patch(new_version, release_notes, patch_type="full_exe", download_url=download_url)

    def _is_newer_version(self, latest, current):
        try:
            def parse_ver(v):
                clean = str(v).lower().lstrip("v").strip()
                return [int(x) for x in clean.split(".") if x.isdigit()]
            return parse_ver(latest) > parse_ver(current)
        except Exception:
            return False

