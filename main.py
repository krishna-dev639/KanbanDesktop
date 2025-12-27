"""
Kanban Board Desktop Application v2.0
© 2025 Murali Krishna. All Rights Reserved.

A modern standalone desktop application for task management.
"""

import webview
import json
import os
import sys
import threading
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import base64

# Optional imports with fallbacks
try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
    TRAY_AVAILABLE = True
except Exception as e:
    print(f"Tray icon disabled: {e}")
    TRAY_AVAILABLE = False

try:
    import keyboard
    HOTKEY_AVAILABLE = True
except ImportError:
    HOTKEY_AVAILABLE = False

# PyInstaller splash screen support
try:
    import pyi_splash
    # Check if splash is actually active (avoids crash if module exists but no splash loaded)
    if pyi_splash.is_alive():
        SPLASH_AVAILABLE = True
    else:
        SPLASH_AVAILABLE = False
except (ImportError, KeyError, Exception):
    SPLASH_AVAILABLE = False

try:
    from plyer import notification
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

APP_NAME = "Kanban Board"
APP_VERSION = "2.0.0"

if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent

DATA_DIR = APP_DIR / "data"
DATA_FILE = DATA_DIR / "kanban_data.json"
BACKUP_DIR = DATA_DIR / "backups"
SETTINGS_FILE = DATA_DIR / "settings.json"

DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)
ATTACHMENTS_DIR = DATA_DIR / "attachments"
ATTACHMENTS_DIR.mkdir(exist_ok=True)
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5MB


# ============================================================================
# API CLASS - Exposed to JavaScript
# ============================================================================

class KanbanAPI:
    """API exposed to JavaScript for data management and native dialogs."""
    
    def __init__(self):
        self.window = None
        self._load_settings()
    
    def set_window(self, window):
        self.window = window
    
    # =========================
    # SETTINGS MANAGEMENT
    # =========================
    
    def _load_settings(self):
        """Load application settings."""
        default_settings = {
            'theme': 'light',
            'autoBackup': True,
            'backupInterval': 24,
            'backupRetention': 30,
            'maxBackups': 10,
            'lastBackup': None,
            'compactView': False,
            'showCompletedTasks': True,
            'defaultPriority': 'Medium',
            'windowState': {'width': 1400, 'height': 900}
        }
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.settings = {**default_settings, **loaded}
            else:
                self.settings = default_settings
                self._save_settings()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = default_settings
    
    def _save_settings(self):
        """Save application settings."""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_all_settings(self):
        """Get all settings."""
        return self.settings
    
    def get_setting(self, key):
        """Get a setting value."""
        return self.settings.get(key)
    
    def set_setting(self, key, value):
        """Set a setting value."""
        self.settings[key] = value
        self._save_settings()
        return {'success': True}
    
    def save_all_settings(self, new_settings):
        """Save multiple settings at once."""
        self.settings.update(new_settings)
        self._save_settings()
        return {'success': True}
    
    # =========================
    # DATA OPERATIONS
    # =========================
    
    def load_data(self):
        """Load all data (tasks + groups)."""
        try:
            if DATA_FILE.exists():
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        'tasks': data.get('tasks', []),
                        'groups': data.get('groups', ['General']),
                        'labels': data.get('labels', [
                            {'id': '1', 'name': 'Bug', 'color': '#ef4444'},
                            {'id': '2', 'name': 'Feature', 'color': '#3b82f6'},
                            {'id': '3', 'name': 'Urgent', 'color': '#f59e0b'},
                            {'id': '4', 'name': 'Review', 'color': '#8b5cf6'}
                        ])
                    }
            return {'tasks': [], 'groups': ['General'], 'labels': []}
        except Exception as e:
            print(f"Error loading data: {e}")
            return {'tasks': [], 'groups': ['General'], 'labels': []}
    
    def save_data(self, data):
        """Save all data."""
        try:
            data['lastModified'] = datetime.now().isoformat()
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            if self.settings.get('autoBackup', True):
                self._check_auto_backup()
            
            return {'success': True}
        except Exception as e:
            print(f"Error saving data: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================
    # NATIVE FILE DIALOGS
    # =========================
    
    def show_open_dialog(self, file_types=None):
        """Show native open file dialog."""
        if not self.window:
            return {'success': False, 'error': 'Window not available'}
        
        try:
            if file_types is None:
                file_types = ('JSON Files (*.json)', 'All Files (*.*)')
            elif isinstance(file_types, list):
                file_types = tuple(file_types)
            
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=file_types
            )
            
            if result and len(result) > 0:
                file_path = result[0]
                # For ZIP files, return path only (binary file)
                if file_path.lower().endswith('.zip'):
                    return {'success': True, 'path': file_path, 'content': None, 'isZip': True}
                # For text files, read and return content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {'success': True, 'path': file_path, 'content': content}
            return {'success': False, 'cancelled': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def show_save_dialog(self, default_name='kanban_export.json', file_types=None):
        """Show native save file dialog."""
        if not self.window:
            return {'success': False, 'error': 'Window not available'}
        
        try:
            if file_types is None:
                file_types = ('JSON Files (*.json)', 'All Files (*.*)')
            
            result = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=default_name,
                file_types=file_types
            )
            
            if result:
                if isinstance(result, (tuple, list)):
                    result = result[0]
                return {'success': True, 'path': result}
            return {'success': False, 'cancelled': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def save_to_file(self, path, content):
        """Save content to a specific file path."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_csv(self, default_name='kanban_export.csv'):
        """Show save dialog for CSV export."""
        if not self.window:
            return {'success': False, 'error': 'Window not available'}
        
        try:
            result = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=default_name,
                file_types=('CSV Files (*.csv)', 'All Files (*.*)')
            )
            
            if result:
                if isinstance(result, (tuple, list)):
                    result = result[0]
                return {'success': True, 'path': result}
            return {'success': False, 'cancelled': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_with_attachments(self, export_data):
        """Export JSON with attachments as a ZIP bundle."""
        import zipfile
        import tempfile
        
        if not self.window:
            return {'success': False, 'error': 'Window not available'}
        
        try:
            # Show save dialog for ZIP
            result = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename='kanban_export_bundle.zip',
                file_types=('ZIP Files (*.zip)', 'All Files (*.*)')
            )
            
            if not result:
                return {'success': False, 'cancelled': True}
            
            if isinstance(result, (tuple, list)):
                result = result[0]
                
            zip_path = result
            tasks = export_data.get('tasks', [])
            
            # Create ZIP file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Collect all attachments
                attachments_added = 0
                attachment_map = {}  # task_id -> list of attachment info
                
                for task in tasks:
                    task_id = task.get('id')
                    if not task_id:
                        continue
                    
                    task_attach_dir = ATTACHMENTS_DIR / task_id
                    if task_attach_dir.exists():
                        attachment_map[task_id] = []
                        for file_path in task_attach_dir.iterdir():
                            if file_path.is_file() and not file_path.name.endswith('.meta'):
                                # Add file to ZIP
                                archive_path = f"attachments/{task_id}/{file_path.name}"
                                zf.write(file_path, archive_path)
                                attachment_map[task_id].append({
                                    'name': file_path.name,
                                    'path': archive_path
                                })
                                attachments_added += 1
                
                # Add attachment info to export data
                export_data['attachments'] = attachment_map
                export_data['hasAttachments'] = True
                
                # Write JSON data to ZIP
                json_data = json.dumps(export_data, indent=2)
                zf.writestr('kanban_data.json', json_data)
            
            return {
                'success': True, 
                'path': zip_path,
                'attachmentsCount': attachments_added
            }
        except Exception as e:
            print(f"Export error: {e}")
            return {'success': False, 'error': str(e)}
    
    def import_with_attachments(self, zip_path):
        """Import JSON with attachments from a ZIP bundle."""
        import zipfile
        
        try:
            if not Path(zip_path).exists():
                return {'success': False, 'error': 'File not found'}
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Read JSON data
                if 'kanban_data.json' not in zf.namelist():
                    return {'success': False, 'error': 'Invalid bundle: no kanban_data.json found'}
                
                json_data = zf.read('kanban_data.json').decode('utf-8')
                import_data = json.loads(json_data)
                
                # Extract attachments
                attachments_extracted = 0
                for name in zf.namelist():
                    if name.startswith('attachments/') and not name.endswith('/'):
                        # Extract to attachments directory
                        parts = name.split('/')
                        if len(parts) >= 3:
                            task_id = parts[1]
                            file_name = parts[2]
                            dest_dir = ATTACHMENTS_DIR / task_id
                            dest_dir.mkdir(exist_ok=True)
                            dest_path = dest_dir / file_name
                            
                            with zf.open(name) as src, open(dest_path, 'wb') as dst:
                                dst.write(src.read())
                            attachments_extracted += 1
                
                return {
                    'success': True,
                    'data': import_data,
                    'attachmentsExtracted': attachments_extracted
                }
        except Exception as e:
            print(f"Import error: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================
    # BACKUP OPERATIONS
    # =========================
    
    def _check_auto_backup(self):
        """Check if auto backup is needed."""
        try:
            last_backup = self.settings.get('lastBackup')
            interval = self.settings.get('backupInterval', 24)
            
            should_backup = False
            if not last_backup:
                should_backup = True
            else:
                last_dt = datetime.fromisoformat(last_backup)
                if datetime.now() - last_dt > timedelta(hours=interval):
                    should_backup = True
            
            if should_backup:
                self.create_backup()
        except Exception as e:
            print(f"Auto backup check error: {e}")
    
    def create_backup(self):
        """Create a manual or auto backup."""
        try:
            if DATA_FILE.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = BACKUP_DIR / f"backup_{timestamp}.json"
                shutil.copy2(DATA_FILE, backup_file)
                
                self.settings['lastBackup'] = datetime.now().isoformat()
                self._save_settings()
                self._cleanup_old_backups()
                
                return {'success': True, 'file': backup_file.name}
            return {'success': False, 'error': 'No data file to backup'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _cleanup_old_backups(self):
        """Cleanup backups based on retention days AND max count."""
        try:
            # 1. Time-based Retention
            retention_days = int(self.settings.get('backupRetention', 30))
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            backups = sorted(BACKUP_DIR.glob("backup_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Filter by age
            for backup in backups[:]: # Copy list to iterate safely
                mtime = datetime.fromtimestamp(backup.stat().st_mtime)
                if mtime < cutoff_date:
                    backup.unlink()
                    backups.remove(backup) # Remove from list so count check is accurate

            # 2. Max Count Limit
            max_backups = int(self.settings.get('maxBackups', 10))
            if len(backups) > max_backups:
                # Delete oldest excess backups
                for excess_backup in backups[max_backups:]:
                    excess_backup.unlink()

        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def list_backups(self):
        """List available backups."""
        try:
            backups = []
            for f in sorted(BACKUP_DIR.glob("backup_*.json"), reverse=True):
                stat = f.stat()
                backups.append({
                    'name': f.name,
                    'path': str(f),
                    'date': stat.st_mtime,
                    'size': stat.st_size
                })
            return backups
        except Exception as e:
            return []
    
    def restore_backup(self, backup_name):
        """Restore from a backup file."""
        try:
            backup_file = BACKUP_DIR / backup_name
            if backup_file.exists():
                # Create a pre-restore backup first
                if DATA_FILE.exists():
                    pre_restore = BACKUP_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    shutil.copy2(DATA_FILE, pre_restore)
                
                shutil.copy2(backup_file, DATA_FILE)
                return {'success': True}
            return {'success': False, 'error': 'Backup file not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_backup(self, backup_name):
        """Delete a specific backup."""
        try:
            backup_file = BACKUP_DIR / backup_name
            if backup_file.exists():
                backup_file.unlink()
                return {'success': True}
            return {'success': False, 'error': 'Backup not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # =========================
    # EXTERNAL LINKS
    # =========================
    
    def open_url(self, url):
        """Open URL in default browser."""
        import webbrowser
        try:
            webbrowser.open(url)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # =========================
    # ATTACHMENT OPERATIONS
    # =========================
    
    def pick_attachment_file(self):
        """Show file picker for attachments."""
        if not self.window:
            return {'success': False, 'error': 'Window not available'}
        
        try:
            file_types = (
                'Images (*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.webp)',
                'Documents (*.pdf;*.doc;*.docx;*.txt;*.xls;*.xlsx)',
                'All Files (*.*)'
            )
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=file_types
            )
            
            if result and len(result) > 0:
                file_path = Path(result[0])
                file_size = file_path.stat().st_size
                
                if file_size > MAX_ATTACHMENT_SIZE:
                    return {'success': False, 'error': f'File too large. Maximum size is 5MB, file is {file_size / 1024 / 1024:.1f}MB'}
                
                return {
                    'success': True,
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_size,
                    'isImage': file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                }
            return {'success': False, 'cancelled': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def save_attachment(self, task_id, source_path, copy_file=True):
        """Save or link an attachment to a task."""
        try:
            source = Path(source_path)
            if not source.exists():
                return {'success': False, 'error': 'Source file not found'}
            
            # Create task attachment directory
            task_dir = ATTACHMENTS_DIR / str(task_id)
            task_dir.mkdir(exist_ok=True)
            
            if copy_file:
                # Copy file to attachments folder
                dest = task_dir / source.name
                # Avoid overwriting - add number suffix if exists
                counter = 1
                while dest.exists():
                    stem = source.stem
                    suffix = source.suffix
                    dest = task_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                shutil.copy2(source, dest)
                return {
                    'success': True,
                    'name': dest.name,
                    'path': str(dest),
                    'size': dest.stat().st_size,
                    'isImage': dest.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
                    'linked': False
                }
            else:
                # Just store the link (original path)
                link_file = task_dir / f"{source.name}.link"
                with open(link_file, 'w', encoding='utf-8') as f:
                    f.write(str(source))
                return {
                    'success': True,
                    'name': source.name,
                    'path': str(source),
                    'size': source.stat().st_size,
                    'isImage': source.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
                    'linked': True
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            return {'success': False, 'error': str(e)}

    def save_pasted_attachment(self, task_id, file_name, base64_data):
        """Save a base64 encoded file (from clipboard) as attachment."""
        try:
            import base64
            
            # Create task attachment directory
            task_dir = ATTACHMENTS_DIR / str(task_id)
            task_dir.mkdir(exist_ok=True)
            
            # Handle duplicates
            dest = task_dir / file_name
            counter = 1
            while dest.exists():
                stem = dest.stem
                if '_' in stem and stem.rsplit('_', 1)[1].isdigit():
                     stem = stem.rsplit('_', 1)[0]
                suffix = dest.suffix
                dest = task_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # Remove header if present (e.g., "data:image/png;base64,")
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            
            file_bytes = base64.b64decode(base64_data)
            
            with open(dest, 'wb') as f:
                f.write(file_bytes)
                
            return {
                'success': True,
                'name': dest.name,
                'path': str(dest),
                'size': dest.stat().st_size,
                'isImage': dest.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
                'linked': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
            return {'success': False, 'error': str(e)}

    def delete_task_attachments(self, task_id):
        """Delete all attachments for a specific task."""
        try:
            task_dir = ATTACHMENTS_DIR / str(task_id)
            if task_dir.exists():
                shutil.rmtree(task_dir)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_attachment(self, task_id, file_name):
        """Get attachment file as base64 for display."""
        try:
            task_dir = ATTACHMENTS_DIR / str(task_id)
            file_path = task_dir / file_name
            
            # Check if it's a link file
            link_file = task_dir / f"{file_name}.link"
            if link_file.exists():
                with open(link_file, 'r', encoding='utf-8') as f:
                    file_path = Path(f.read().strip())
            
            if not file_path.exists():
                return {'success': False, 'error': 'File not found'}
            
            with open(file_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')
            
            suffix = file_path.suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.bmp': 'image/bmp', '.webp': 'image/webp',
                '.pdf': 'application/pdf', '.txt': 'text/plain'
            }
            mime = mime_types.get(suffix, 'application/octet-stream')
            
            return {
                'success': True,
                'data': f'data:{mime};base64,{data}',
                'name': file_path.name,
                'size': file_path.stat().st_size
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_attachment(self, task_id, file_name):
        """Delete an attachment file."""
        try:
            task_dir = ATTACHMENTS_DIR / str(task_id)
            file_path = task_dir / file_name
            link_file = task_dir / f"{file_name}.link"
            
            deleted = False
            if file_path.exists():
                file_path.unlink()
                deleted = True
            if link_file.exists():
                link_file.unlink()
                deleted = True
            
            # Clean up empty task directory
            if task_dir.exists() and not any(task_dir.iterdir()):
                task_dir.rmdir()
            
            if deleted:
                return {'success': True}
            return {'success': False, 'error': 'File not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def import_data_unified(self, file_path):
        """Import data from either a ZIP bundle or a JSON file."""
        import zipfile
        import json
        
        try:
            if file_path.lower().endswith('.zip'):
                # Handle ZIP Bundle
                with zipfile.ZipFile(file_path, 'r') as zf:
                    # Look for export data JSON inside
                    json_files = [f for f in zf.namelist() if f.endswith('.json') and 'task' in f.lower() or 'export' in f.lower() or 'data' in f.lower()]
                    
                    # Fallback: try any json if specific name not found
                    if not json_files:
                        json_files = [f for f in zf.namelist() if f.endswith('.json')]
                    
                    if not json_files:
                        return {'success': False, 'error': 'No JSON data found in ZIP'}
                    
                    # Read the JSON data
                    with zf.open(json_files[0]) as f:
                        data = json.load(f)
                    
                    # Extract attachments
                    # We assume attachments are in 'attachments/' folder in zip
                    # and need to be extracted to DATA_DIR/attachments
                    for file in zf.namelist():
                        if file.startswith('attachments/'):
                            # Extract securely
                            zf.extract(file, DATA_DIR)
                            
                    return {'success': True, 'data': data, 'attachmentsCount': len([f for f in zf.namelist() if f.startswith('attachments/')])}
            
            else:
                # Handle plain JSON
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {'success': True, 'data': data, 'attachmentsCount': 0}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_attachments(self, task_id):
        """List all attachments for a task."""
        try:
            task_dir = ATTACHMENTS_DIR / str(task_id)
            if not task_dir.exists():
                return []
            
            attachments = []
            for f in task_dir.iterdir():
                if f.suffix == '.link':
                    # It's a linked file
                    with open(f, 'r', encoding='utf-8') as lf:
                        original_path = Path(lf.read().strip())
                    name = f.stem  # Remove .link suffix
                    exists = original_path.exists()
                    attachments.append({
                        'name': name,
                        'size': original_path.stat().st_size if exists else 0,
                        'isImage': original_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
                        'linked': True,
                        'exists': exists,
                        'originalPath': str(original_path)
                    })
                else:
                    # It's a copied file
                    attachments.append({
                        'name': f.name,
                        'size': f.stat().st_size,
                        'isImage': f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
                        'linked': False,
                        'exists': True
                    })
            
            return attachments
        except Exception as e:
            return []
    
    # =========================
    # NOTIFICATIONS
    # =========================
    
    def show_notification(self, title, message):
        """Show a desktop notification."""
        if NOTIFICATION_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name=APP_NAME,
                    timeout=5
                )
                return {'success': True}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        return {'success': False, 'error': 'Notifications not available'}
    
    def check_due_tasks(self, tasks):
        """Check for tasks due today or overdue."""
        today = datetime.now().strftime('%Y-%m-%d')
        due_today = []
        overdue = []
        
        for task in tasks:
            if task.get('status') == 'done':
                continue
            target = task.get('targetDate', '')
            if target:
                if target == today:
                    due_today.append(task.get('title', 'Untitled'))
                elif target < today:
                    overdue.append(task.get('title', 'Untitled'))
        
        return {'dueToday': due_today, 'overdue': overdue}
    
    # =========================
    # WINDOW CONTROLS
    # =========================
    
    def minimize_to_tray(self):
        """Minimize to system tray."""
        if self.window:
            self.window.hide()
            return {'success': True}
        return {'success': False}
    
    def close_app(self):
        """Close the application."""
        if self.window:
            self.window.destroy()
        return {'success': True}
    
    def minimize_window(self):
        """Minimize window."""
        if self.window:
            self.window.minimize()
        return {'success': True}
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.window:
            self.window.toggle_fullscreen()
        return {'success': True}
    
    def open_quick_add(self):
        """Show window and open quick add dialog."""
        if self.window:
            self.window.show()
            self.window.evaluate_js('openNewTaskModal();')
        return {'success': True}
    
    # =========================
    # UTILITY
    # =========================
    
    def get_app_info(self):
        """Get application information."""
        return {
            'name': APP_NAME,
            'version': APP_VERSION,
            'dataDir': str(DATA_DIR),
            'hasTray': TRAY_AVAILABLE,
            'hasHotkeys': HOTKEY_AVAILABLE,
            'hasNotifications': NOTIFICATION_AVAILABLE
        }


# ============================================================================
# SYSTEM TRAY
# ============================================================================

tray_icon = None
main_window = None
api = None

def create_tray_icon():
    """Create system tray icon."""
    global tray_icon
    
    if not TRAY_AVAILABLE:
        return
    
    def create_image():
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill=(99, 102, 241, 255))
        draw.text((18, 10), "K", fill=(255, 255, 255, 255))
        return img
    
    def on_show(icon, item):
        if main_window:
            main_window.show()
    
    def on_quick_add(icon, item):
        if main_window and api:
            main_window.show()
            api.open_quick_add()
    
    def on_quit(icon, item):
        icon.stop()
        if main_window:
            main_window.destroy()
    
    menu = pystray.Menu(
        pystray.MenuItem("Show Kanban Board", on_show, default=True),
        pystray.MenuItem("Quick Add Task", on_quick_add),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit)
    )
    
    tray_icon = pystray.Icon(APP_NAME, create_image(), APP_NAME, menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()


def setup_global_hotkeys():
    """Setup global keyboard shortcuts."""
    if not HOTKEY_AVAILABLE:
        return
    
    try:
        keyboard.add_hotkey('ctrl+shift+k', lambda: api.open_quick_add() if api else None)
    except Exception as e:
        print(f"Could not register global hotkeys: {e}")


def on_window_closed():
    """Handle window close event."""
    global tray_icon
    if tray_icon:
        tray_icon.stop()


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def get_html_path():
    """Get the path to the HTML file."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    
    return str(base_path / "kanban.html")


def main():
    global main_window, api
    
    print(f"Starting {APP_NAME} v{APP_VERSION}")
    print(f"Data directory: {DATA_DIR}")
    
    api = KanbanAPI()
    create_tray_icon()
    setup_global_hotkeys()
    
    window_state = api.settings.get('windowState', {'width': 1400, 'height': 900})
    html_path = get_html_path()
    
    
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
        
    icon_path = base_path / "logo.png"
    
    main_window = webview.create_window(
        title=APP_NAME,
        url=html_path,
        js_api=api,
        width=window_state.get('width', 1400),
        height=window_state.get('height', 900),
        min_size=(900, 600),
        resizable=True,
        frameless=False,
        easy_drag=False,
        text_select=True
    )
    
    api.set_window(main_window)
    
    def on_shown():
        """Close splash screen when window is shown (earlier than loaded)."""
        if SPLASH_AVAILABLE:
            try:
                pyi_splash.close()
            except Exception as e:
                print(f"Splash close error: {e}")
    
    def on_loaded():
        """Handle post-load tasks."""
        # Small delay for smooth transition
        threading.Timer(0.5, lambda: check_startup_notifications()).start()
    
    def check_startup_notifications():
        if NOTIFICATION_AVAILABLE and api:
            try:
                data = api.load_data()
                result = api.check_due_tasks(data.get('tasks', []))
                overdue = result.get('overdue', [])
                due_today = result.get('dueToday', [])
                
                if overdue:
                    api.show_notification("⚠️ Overdue Tasks", f"You have {len(overdue)} overdue task(s)!")
                elif due_today:
                    api.show_notification("📅 Tasks Due Today", f"You have {len(due_today)} task(s) due today.")
            except Exception as e:
                print(f"Startup notification error: {e}")
    
    main_window.events.shown += on_shown
    main_window.events.loaded += on_loaded
    webview.start(debug=False)
    on_window_closed()


if __name__ == "__main__":
    main()
