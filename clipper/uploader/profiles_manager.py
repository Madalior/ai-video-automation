"""
Profile & Session Manager for Multi-Account Uploader
====================================================
Manages account configurations, persistent session directories,
and proxy routing for up to 30+ social media accounts.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_PROFILES_DIR = Path(__file__).resolve().parent.parent.parent / "uploader_profiles"


class ProfileManager:
    """
    Manages multi-account profiles and their persistent browser storage on disk.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_PROFILES_DIR
        self.sessions_dir = self.base_dir / "sessions"
        self.registry_file = self.base_dir / "accounts.json"
        
        # Ensure directories exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.registry_file.exists():
            self._save_registry({
                "version": "1.0",
                "updated_at": datetime.utcnow().isoformat(),
                "accounts": {}
            })

    def _load_registry(self) -> Dict[str, Any]:
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[PROFILE_MGR] Warning: Could not read registry ({e}), creating fresh one.")
            return {"version": "1.0", "updated_at": datetime.utcnow().isoformat(), "accounts": {}}

    def _save_registry(self, data: Dict[str, Any]) -> None:
        data["updated_at"] = datetime.utcnow().isoformat()
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def list_accounts(self, fleet: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all registered accounts with status, optionally filtered by fleet."""
        reg = self._load_registry()
        accounts = []
        for acc_id, meta in reg.get("accounts", {}).items():
            acc_fleet = meta.get("fleet", "normal").lower()
            if fleet and acc_fleet != fleet.lower():
                continue

            session_path = self.get_session_dir(acc_id)
            has_session = session_path.exists() and any(session_path.iterdir())
            item = {
                "id": acc_id,
                "name": meta.get("name", acc_id),
                "fleet": acc_fleet,
                "pod": meta.get("pod", ""),
                "assigned_campaign": meta.get("assigned_campaign", ""),
                "niche": meta.get("niche", ""),
                "platforms": meta.get("platforms", ["youtube", "tiktok", "instagram"]),
                "proxy": meta.get("proxy", ""),
                "has_session": has_session,
                "created_at": meta.get("created_at", ""),
                "last_upload": meta.get("last_upload", None),
                "notes": meta.get("notes", "")
            }
            accounts.append(item)
        return accounts

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        reg = self._load_registry()
        return reg.get("accounts", {}).get(account_id)

    def add_account(
        self,
        account_id: str,
        name: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        proxy: Optional[str] = None,
        fleet: str = "normal",
        pod: str = "",
        assigned_campaign: str = "",
        niche: str = "",
        notes: str = ""
    ) -> Dict[str, Any]:
        """Registers a new account and creates its session directory."""
        reg = self._load_registry()
        acc_id = account_id.strip().lower()
        if not acc_id:
            raise ValueError("Account ID cannot be empty.")

        entry = {
            "id": acc_id,
            "name": name or acc_id,
            "fleet": fleet.lower(),
            "pod": pod,
            "assigned_campaign": assigned_campaign,
            "niche": niche,
            "platforms": platforms or ["youtube", "tiktok", "instagram"],
            "proxy": proxy or "",
            "created_at": datetime.utcnow().isoformat(),
            "notes": notes
        }

        reg.setdefault("accounts", {})[acc_id] = entry
        self._save_registry(reg)

        # Create session directory
        session_dir = self.get_session_dir(acc_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        print(f"[PROFILE_MGR] ✅ Registered account '{acc_id}' ({entry['name']}) [Fleet: {fleet}] -> {session_dir}")
        return entry

    def update_account_fleet(
        self,
        account_id: str,
        fleet: str,
        pod: Optional[str] = None,
        assigned_campaign: Optional[str] = None,
        niche: Optional[str] = None
    ) -> bool:
        """Updates fleet allocation and campaign assignment for an account."""
        reg = self._load_registry()
        if account_id in reg.get("accounts", {}):
            reg["accounts"][account_id]["fleet"] = fleet.lower()
            if pod is not None:
                reg["accounts"][account_id]["pod"] = pod
            if assigned_campaign is not None:
                reg["accounts"][account_id]["assigned_campaign"] = assigned_campaign
            if niche is not None:
                reg["accounts"][account_id]["niche"] = niche
            self._save_registry(reg)
            print(f"[PROFILE_MGR] 🔄 Updated '{account_id}' -> Fleet: {fleet}, Pod: {pod or 'N/A'}, Campaign: {assigned_campaign or 'auto'}")
            return True
        return False

    def delete_account(self, account_id: str) -> bool:
        reg = self._load_registry()
        if account_id in reg.get("accounts", {}):
            del reg["accounts"][account_id]
            self._save_registry(reg)
            print(f"[PROFILE_MGR] 🗑️ Deleted account '{account_id}' from registry.")
            return True
        return False

    def update_last_upload(self, account_id: str) -> None:
        reg = self._load_registry()
        if account_id in reg.get("accounts", {}):
            reg["accounts"][account_id]["last_upload"] = datetime.utcnow().isoformat()
            self._save_registry(reg)

    def get_session_dir(self, account_id: str) -> Path:
        """Returns the isolated Chrome User Data Directory for this account."""
        return self.sessions_dir / account_id
