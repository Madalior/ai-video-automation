"""
Google Drive Campaign Vault Downloader
======================================
Automatically discovers and downloads official raw campaign footage from
Google Drive links (folders, subfolders, or direct file IDs) provided in Whop briefs.
Uses Playwright for client-side folder enumeration + gdown for fast chunked downloads.
"""

import os
import re
import sys
import asyncio
from pathlib import Path
from typing import Optional, List, Dict
import gdown

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

class GoogleDriveVaultDownloader:
    """
    Downloads official campaign footage from Google Drive folders or files.
    """
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_file_id(self, url: str) -> Optional[str]:
        """Extract Google Drive file ID from URL."""
        match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)
        match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)
        return None

    def extract_folder_id(self, url: str) -> Optional[str]:
        """Extract Google Drive folder ID from URL."""
        match = re.search(r"/folders/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)
        return None

    async def list_folder_contents(self, folder_id: str) -> List[Dict[str, str]]:
        """
        Uses Playwright headless to inspect a Google Drive folder and return items.
        """
        from playwright.async_api import async_playwright
        url = f"https://drive.google.com/drive/folders/{folder_id}"
        items = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=25000)
                await page.wait_for_timeout(3000)

                elements = await page.query_selector_all('[role="row"], [data-target="item"], [data-id]')
                seen = set()
                for el in elements:
                    text = await el.inner_text()
                    data_id = await el.get_attribute('data-id')
                    label = await el.get_attribute('aria-label')
                    if data_id and data_id not in seen and data_id not in ['_gd', 'ucc-11']:
                        seen.add(data_id)
                        fname = text.split('\n')[0].strip() if text else (label or "").strip()
                        is_folder = "folder" in (label or "").lower() or (not "." in fname and len(fname) > 0)
                        items.append({
                            "id": data_id,
                            "name": fname,
                            "is_folder": is_folder
                        })
                await browser.close()
        except Exception as e:
            print(f"[DRIVE_DOWNLOADER] ⚠️ Playwright folder inspection error: {e}")

        return items

    async def find_best_video_in_folder(self, root_folder_id: str) -> Optional[Dict[str, str]]:
        """
        Recursively searches for video files in Google Drive folder tree.
        Prioritizes 'Main Footage', 'Shorts', 'Raw', and strictly skips 'Example - Don't use'.
        """
        print(f"[DRIVE_DOWNLOADER] 🔍 Scanning Google Drive folder: {root_folder_id}")
        items = await self.list_folder_contents(root_folder_id)
        
        video_extensions = ('.mp4', '.mov', '.mkv', '.avi', '.m4v')
        
        # 1. Look for direct video files first
        for it in items:
            name_lower = it['name'].lower()
            if any(name_lower.endswith(ext) for ext in video_extensions) and "example" not in name_lower:
                print(f"[DRIVE_DOWNLOADER] 🎯 Found direct video file: '{it['name']}' (ID: {it['id']})")
                return it

        # 2. Filter out 'don't use' or 'example' folders
        valid_folders = []
        for it in items:
            if it.get('is_folder'):
                name_l = it['name'].lower()
                if "don't use" in name_l or "dont use" in name_l or "example" in name_l:
                    print(f"[DRIVE_DOWNLOADER] ⏭️ Skipping excluded folder: '{it['name']}'")
                    continue
                valid_folders.append(it)

        # Sort folders by priority: 'main' / 'footage' / 'short' first
        def folder_priority(f):
            nl = f['name'].lower()
            if "main" in nl or "footage" in nl:
                return 0
            if "short" in nl:
                return 1
            return 2

        valid_folders.sort(key=folder_priority)

        # 3. Search valid subfolders
        for it in valid_folders:
            print(f"[DRIVE_DOWNLOADER] 📁 Checking subfolder: '{it['name']}' (ID: {it['id']})")
            sub_items = await self.list_folder_contents(it['id'])
            
            # Check for direct videos in subfolder
            for s in sub_items:
                s_name_lower = s['name'].lower()
                if any(s_name_lower.endswith(ext) for ext in video_extensions) and "example" not in s_name_lower:
                    print(f"[DRIVE_DOWNLOADER] 🎯 Found authentic campaign video: '{s['name']}' (ID: {s['id']})")
                    return s
            
            # Check nested folders
            for s in sub_items:
                if s.get('is_folder'):
                    sn_l = s['name'].lower()
                    if "don't use" in sn_l or "dont use" in sn_l:
                        continue
                    print(f"[DRIVE_DOWNLOADER] 📁 Checking nested folder: '{s['name']}' (ID: {s['id']})")
                    nested_items = await self.list_folder_contents(s['id'])
                    for n in nested_items:
                        n_name_lower = n['name'].lower()
                        if any(n_name_lower.endswith(ext) for ext in video_extensions) and "example" not in n_name_lower:
                            print(f"[DRIVE_DOWNLOADER] 🎯 Found authentic campaign video in nested folder: '{n['name']}' (ID: {n['id']})")
                            return n

        return None

    async def download_from_url(self, url: str, target_filename: str) -> Optional[str]:
        """
        Downloads the campaign footage given a Google Drive link or file ID.
        """
        target_path = self.output_dir / target_filename
        
        # Direct file ID check
        file_id = self.extract_file_id(url)
        if not file_id:
            folder_id = self.extract_folder_id(url)
            if folder_id:
                best_video = await self.find_best_video_in_folder(folder_id)
                if best_video:
                    file_id = best_video['id']
                    print(f"[DRIVE_DOWNLOADER] 📥 Downloading '{best_video['name']}' via file ID: {file_id}")
                else:
                    print(f"[DRIVE_DOWNLOADER] ❌ No video files detected in folder {folder_id}")
                    return None

        if not file_id:
            print(f"[DRIVE_DOWNLOADER] ❌ Could not extract valid Google Drive file or folder ID from: {url}")
            return None

        print(f"[DRIVE_DOWNLOADER] ⚡ Starting gdown chunked transfer for ID: {file_id}...")
        try:
            # Download via gdown
            downloaded = gdown.download(id=file_id, output=str(target_path), quiet=False)
            if downloaded and os.path.exists(downloaded) and os.path.getsize(downloaded) > 1024:
                size_mb = os.path.getsize(downloaded) / (1024 * 1024)
                print(f"[DRIVE_DOWNLOADER] ✅ Successfully downloaded: {os.path.basename(downloaded)} ({size_mb:.2f} MB)")
                return str(downloaded)
            else:
                print(f"[DRIVE_DOWNLOADER] ❌ Download failed or file empty.")
                return None
        except Exception as e:
            print(f"[DRIVE_DOWNLOADER] ❌ Download error: {e}")
            return None
