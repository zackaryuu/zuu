#!/usr/bin/env python3
"""
SyncDict i18n Demo - Real-World Internationalization Use Case

This demo shows how SyncDict can be used to manage translation files
for a web application. It demonstrates:

1. Maintaining structural consistency across language files
2. Preserving unique translation values while syncing structure  
3. Adding new translation keys to all languages at once
4. Reorganizing translation structure across all files
5. Handling missing translations and fallbacks

This is the primary use case for SyncDict - managing i18n JSON files
where you need the same key structure but different values (translations).
"""

import json
import os
import shutil
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from zuu.syncdict import SyncDict


class I18nSyncDemo:
    def __init__(self):
        self.demo_dir = os.path.dirname(os.path.abspath(__file__))
        self.playground_dir = os.path.join(self.demo_dir, "playground")
        self.base_translations_dir = os.path.join(self.demo_dir, "base_translations")
        self.sync_dict = None
        self.language_files = {}
        self.languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'ja': 'Japanese',
            'zh': 'Chinese'
        }
        
    def copy_base_translations_to_playground(self):
        """Copy the complex nested base translations to playground"""
        self.demo_dir = os.path.dirname(os.path.abspath(__file__))
        base_translations_dir = os.path.join(self.demo_dir, "base_translations")  # Fixed path
        self.playground_dir = os.path.join(self.demo_dir, "playground")
        
        # Create playground directory
        os.makedirs(self.playground_dir, exist_ok=True)
        
        print("Setting up complex nested translation demo")
        print(f"Base translations: {base_translations_dir}")
        print(f"Playground: {self.playground_dir}")
        
        # Copy all base translation files to playground
        for lang_code in self.languages.keys():
            src_file = os.path.join(base_translations_dir, f"{lang_code}.json")
            if os.path.exists(src_file):
                dest_file = os.path.join(self.playground_dir, f"{lang_code}.json")
                shutil.copy2(src_file, dest_file)
                self.language_files[lang_code] = dest_file
                lang_name = self.languages[lang_code]
                print(f"✓ Copied {lang_name} translations: {lang_code}.json")
            else:
                print(f"✗ Missing base translation file: {src_file}")
                
        print(f"Playground ready with {len(self.language_files)} language files")
        
    def create_base_translations(self):
        """Create base English translations with realistic web app content"""
        return {
            "navigation": {
                "home": "Home",
                "about": "About Us",
                "services": "Services",
                "contact": "Contact",
                "login": "Login",
                "logout": "Logout",
                "dashboard": "Dashboard",
                "profile": "Profile"
            },
            "auth": {
                "login": {
                    "title": "Sign In",
                    "email": "Email Address",
                    "password": "Password",
                    "remember": "Remember me",
                    "forgot_password": "Forgot your password?",
                    "submit": "Sign In",
                    "no_account": "Don't have an account?",
                    "create_account": "Create one here"
                },
                "register": {
                    "title": "Create Account",
                    "first_name": "First Name",
                    "last_name": "Last Name", 
                    "email": "Email Address",
                    "password": "Password",
                    "confirm_password": "Confirm Password",
                    "terms": "I agree to the Terms of Service",
                    "submit": "Create Account",
                    "have_account": "Already have an account?",
                    "sign_in": "Sign in here"
                },
                "messages": {
                    "login_success": "Welcome back!",
                    "login_failed": "Invalid email or password",
                    "register_success": "Account created successfully",
                    "password_reset_sent": "Password reset link sent to your email"
                }
            },
            "dashboard": {
                "welcome": "Welcome back, {name}!",
                "stats": {
                    "total_users": "Total Users",
                    "active_sessions": "Active Sessions", 
                    "revenue": "Revenue",
                    "growth": "Growth"
                },
                "actions": {
                    "create_new": "Create New",
                    "view_reports": "View Reports",
                    "manage_users": "Manage Users",
                    "settings": "Settings"
                }
            },
            "forms": {
                "validation": {
                    "required": "This field is required",
                    "email_invalid": "Please enter a valid email address",
                    "password_too_short": "Password must be at least 8 characters",
                    "passwords_dont_match": "Passwords do not match",
                    "terms_required": "You must accept the terms of service"
                },
                "buttons": {
                    "save": "Save",
                    "cancel": "Cancel",
                    "delete": "Delete",
                    "edit": "Edit",
                    "submit": "Submit",
                    "reset": "Reset"
                }
            },
            "notifications": {
                "success": {
                    "saved": "Changes saved successfully",
                    "deleted": "Item deleted successfully",
                    "updated": "Profile updated successfully"
                },
                "errors": {
                    "network": "Network error occurred",
                    "server": "Server error, please try again",
                    "not_found": "The requested item was not found",
                    "unauthorized": "You don't have permission for this action"
                }
            }
        }
        
    def create_translated_content(self, base_content, language_code):
        """Create translated content for each language (simulated translations)"""
        translations = {
            'es': {  # Spanish
                "navigation/home": "Inicio",
                "navigation/about": "Acerca de",
                "navigation/services": "Servicios", 
                "navigation/contact": "Contacto",
                "navigation/login": "Iniciar Sesión",
                "navigation/logout": "Cerrar Sesión",
                "navigation/dashboard": "Panel de Control",
                "navigation/profile": "Perfil",
                
                "auth/login/title": "Iniciar Sesión",
                "auth/login/email": "Correo Electrónico",
                "auth/login/password": "Contraseña",
                "auth/login/remember": "Recordarme",
                "auth/login/forgot_password": "¿Olvidaste tu contraseña?",
                "auth/login/submit": "Iniciar Sesión",
                "auth/login/no_account": "¿No tienes una cuenta?",
                "auth/login/create_account": "Créala aquí",
                
                "auth/register/title": "Crear Cuenta",
                "auth/register/first_name": "Nombre",
                "auth/register/last_name": "Apellido",
                "auth/register/email": "Correo Electrónico",
                "auth/register/password": "Contraseña", 
                "auth/register/confirm_password": "Confirmar Contraseña",
                "auth/register/terms": "Acepto los Términos de Servicio",
                "auth/register/submit": "Crear Cuenta",
                "auth/register/have_account": "¿Ya tienes una cuenta?",
                "auth/register/sign_in": "Inicia sesión aquí",
                
                "dashboard/welcome": "¡Bienvenido de vuelta, {name}!",
                "forms/buttons/save": "Guardar",
                "forms/buttons/cancel": "Cancelar",
                "forms/buttons/delete": "Eliminar"
            },
            'fr': {  # French
                "navigation/home": "Accueil",
                "navigation/about": "À Propos",
                "navigation/services": "Services",
                "navigation/contact": "Contact",
                "navigation/login": "Connexion",
                "navigation/logout": "Déconnexion",
                "navigation/dashboard": "Tableau de Bord",
                "navigation/profile": "Profil",
                
                "auth/login/title": "Se Connecter",
                "auth/login/email": "Adresse E-mail",
                "auth/login/password": "Mot de Passe",
                "auth/login/remember": "Se souvenir de moi",
                "auth/login/submit": "Se Connecter",
                
                "dashboard/welcome": "Bon retour, {name}!",
                "forms/buttons/save": "Enregistrer",
                "forms/buttons/cancel": "Annuler",
                "forms/buttons/delete": "Supprimer"
            },
            'de': {  # German
                "navigation/home": "Startseite",
                "navigation/about": "Über Uns",
                "navigation/services": "Dienstleistungen",
                "navigation/contact": "Kontakt",
                "navigation/login": "Anmelden",
                "navigation/logout": "Abmelden",
                "navigation/dashboard": "Dashboard",
                "navigation/profile": "Profil",
                
                "auth/login/title": "Anmelden",
                "auth/login/email": "E-Mail-Adresse", 
                "auth/login/password": "Passwort",
                "auth/login/submit": "Anmelden",
                
                "dashboard/welcome": "Willkommen zurück, {name}!",
                "forms/buttons/save": "Speichern",
                "forms/buttons/cancel": "Abbrechen",
                "forms/buttons/delete": "Löschen"
            },
            'ja': {  # Japanese
                "navigation/home": "ホーム",
                "navigation/about": "会社について",
                "navigation/services": "サービス",
                "navigation/contact": "お問い合わせ",
                "navigation/login": "ログイン",
                "navigation/logout": "ログアウト",
                "navigation/dashboard": "ダッシュボード",
                "navigation/profile": "プロフィール",
                
                "auth/login/title": "ログイン",
                "auth/login/email": "メールアドレス",
                "auth/login/password": "パスワード",
                "auth/login/submit": "ログイン",
                
                "dashboard/welcome": "おかえりなさい、{name}さん！",
                "forms/buttons/save": "保存",
                "forms/buttons/cancel": "キャンセル",
                "forms/buttons/delete": "削除"
            },
            'zh': {  # Chinese
                "navigation/home": "首页",
                "navigation/about": "关于我们",
                "navigation/services": "服务",
                "navigation/contact": "联系我们",
                "navigation/login": "登录",
                "navigation/logout": "登出",
                "navigation/dashboard": "仪表板",
                "navigation/profile": "个人资料",
                
                "auth/login/title": "登录",
                "auth/login/email": "电子邮件地址",
                "auth/login/password": "密码",
                "auth/login/submit": "登录",
                
                "dashboard/welcome": "欢迎回来，{name}！",
                "forms/buttons/save": "保存",
                "forms/buttons/cancel": "取消",
                "forms/buttons/delete": "删除"
            }
        }
        
        # Create translated version by copying base and replacing translated keys
        translated = json.loads(json.dumps(base_content))  # Deep copy
        
        if language_code in translations:
            lang_translations = translations[language_code]
            
            def apply_translations(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}/{key}" if path else key
                        if isinstance(value, (dict, list)):
                            apply_translations(value, current_path)
                        elif current_path in lang_translations:
                            obj[key] = lang_translations[current_path]
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        apply_translations(item, f"{path}[{i}]")
                        
            apply_translations(translated)
            
        return translated
        
    def setup_i18n_files(self):
        """Create realistic i18n folder structure with translation files using playground"""
        # Copy base translations to playground 
        self.copy_base_translations_to_playground()
        
        # Use playground files
        for lang_code in self.languages.keys():
            file_path = os.path.join(self.playground_dir, f"{lang_code}.json")
            self.language_files[lang_code] = file_path
            
        print(f"Created {len(self.language_files)} language files")
        
    def initialize_syncdict(self):
        """Initialize SyncDict with English as base language"""
        base_file = self.language_files['en']
        self.sync_dict = SyncDict(base_file)
        
        # Add all other language files to watch
        watched_count = 0
        desynced_count = 0
        
        for lang_code, file_path in self.language_files.items():
            if lang_code != 'en':  # Skip base file
                try:
                    self.sync_dict.add_watch(file_path)
                    if file_path in self.sync_dict.watched_files:
                        watched_count += 1
                        print(f"✓ Watching {lang_code}.json")
                    else:
                        desynced_count += 1
                        print(f"✗ Failed to watch {lang_code}.json (desynced)")
                except Exception as e:
                    print(f"✗ Error adding {lang_code}.json: {e}")
                    desynced_count += 1
        
        print("\nSyncDict Status:")
        print("  - Base file: en.json")
        print(f"  - Successfully watching: {watched_count} files")
        print(f"  - Desynced files: {desynced_count} files")
        
        return watched_count, desynced_count
        
    def demonstrate_adding_new_features(self):
        """Demonstrate adding new feature translations that work with existing structure"""
        print("\n" + "="*60)
        print("ADDING NEW FEATURE: Advanced Search with Filters")
        print("="*60)
        
        print("\nAdding search functionality to existing structure...")
        
        # Add search features that extend the existing structure
        search_features = {
            "features/search/enabled": True,
            "features/search/advanced/title": "Advanced Search",
            "features/search/advanced/placeholder": "Search everything...",
            "features/search/filters/categories": ["all", "messages", "files", "users"],
            "features/search/results/per_page": 25,
            "features/search/results/sort_options": ["relevance", "date", "name"],
            "ui/search/toolbar/expand": "Show Filters",
            "ui/search/toolbar/collapse": "Hide Filters",
            "ui/search/toolbar/clear": "Clear All"
        }
        
        # Add all new features
        for key, value in search_features.items():
            print(f"  + Adding: {key}")
            self.sync_dict[key] = value
            
        # Monitor changes and apply to all watched files
        print("\n📊 Detecting changes...")
        changes_detected = self.sync_dict.monitor()
        print(f"   Changes detected: {len(changes_detected.get('added', []))} added, {len(changes_detected.get('removed', []))} removed")
        
        if changes_detected.get('added') or changes_detected.get('removed'):
            print("🔄 Applying changes to all watched files...")
            self.sync_dict.applyChanges()
            print("✓ All language files updated with new search features")
        
        print(f"\nNew search structure added across all {len(self.sync_dict.watched_files)} language files!")
        
        # Show how new features appear in different languages
        self._show_translation_sample("es", "features/search/advanced/title")
        self._show_translation_sample("ja", "ui/search/toolbar/expand")
        
    def _flatten_dict(self, d, parent_key='', sep='/'):
        """Flatten nested dictionary for SyncDict keys"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Handle arrays by creating indexed keys
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}/{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}/{i}", item))
            else:
                items.append((new_key, v))
        return dict(items)
        
    def demonstrate_structural_moves(self):
        """Demonstrate moving existing keys to new structure (the core SyncDict functionality)"""
        print("\n" + "="*60)
        print("STRUCTURAL MOVE: Reorganizing Existing Form Structure")
        print("="*60)
        
        print("\nBefore: forms/login/title and forms/login/fields/email/label exist")
        print("After: Moving login form to auth/signin structure")
        
        # Show current structure in base file
        current_login_title = self.sync_dict['forms/login/title']
        current_email_label = self.sync_dict['forms/login/fields/email/label']
        current_password_label = self.sync_dict['forms/login/fields/password/label']
        
        print(f"\nCurrent forms/login/title: '{current_login_title}'")
        print(f"Current forms/login/fields/email/label: '{current_email_label}'")
        print(f"Current forms/login/fields/password/label: '{current_password_label}'")
        
        # MOVE existing structure - this is the core SyncDict functionality!
        # Delete from old locations  
        del self.sync_dict['forms/login/title']
        del self.sync_dict['forms/login/fields/email/label']
        del self.sync_dict['forms/login/fields/password/label']
        
        # Add to new locations with same content (SyncDict should preserve translations!)
        self.sync_dict['auth/signin/title'] = current_login_title
        self.sync_dict['auth/signin/fields/email/label'] = current_email_label
        self.sync_dict['auth/signin/fields/password/label'] = current_password_label
        
        # Also add some new structure alongside the moves
        self.sync_dict['auth/signin/remember_me'] = "Remember me"
        self.sync_dict['auth/register/title'] = "Create Account"
        
        # Monitor and apply - this should detect the MOVES
        print("\n📊 Detecting structural changes...")
        changes = self.sync_dict.monitor()
        print(f"   Moves detected: {len(changes.get('moved', {}))}")
        print(f"   True additions: {len(changes.get('added', []))}")
        print(f"   True removals: {len(changes.get('removed', []))}")
        
        if changes.get('moved'):
            print("\n🔄 Applying structural moves to all watched files...")
            for old_key, new_key in changes['moved'].items():
                print(f"   Moving: {old_key} → {new_key}")
                
        print("🔄 Applying all changes to all watched files...")
        self.sync_dict.applyChanges()
        print("✅ All language files updated with new structure")
        
        # Show how moves preserved translations
        self._show_translation_sample("es", "auth/signin/title")
        self._show_translation_sample("ja", "auth/signin/fields/email/label") 
        
        print(f"\n✅ Structural reorganization completed across all {len(self.sync_dict.watched_files)} language files!")
        
    def demonstrate_adding_new_pages(self):
        """Demonstrate adding translations for new pages"""
        print("\n" + "="*60)
        print("ADDING NEW PAGES: Help Center & FAQ")
        print("="*60)
        
        print("\nAdding help center translations...")
        
        help_translations = {
            "help/center/title": "Help Center",
            "help/center/search": "How can we help you?",
            "help/categories/getting_started": "Getting Started",
            "help/categories/account": "Account Management", 
            "help/categories/billing": "Billing & Payments",
            "help/categories/technical": "Technical Support",
            "help/articles/popular": "Popular Articles",
            "help/contact/title": "Still need help?",
            "help/contact/description": "Our support team is here to help",
            "help/contact/button": "Contact Support"
        }
        
        faq_translations = {
            "faq/title": "Frequently Asked Questions",
            "faq/general/title": "General Questions",
            "faq/general/what_is": "What is this service?",
            "faq/general/how_to_start": "How do I get started?",
            "faq/general/pricing": "What does it cost?",
            "faq/account/title": "Account Questions",
            "faq/account/forgot_password": "I forgot my password",
            "faq/account/change_email": "How do I change my email?",
            "faq/account/delete_account": "How do I delete my account?",
            "faq/search_placeholder": "Search FAQ..."
        }
        
        # Add all new translations
        all_new_translations = {**help_translations, **faq_translations}
        
        for key, value in all_new_translations.items():
            self.sync_dict[key] = value
        
        # Monitor changes and apply to all watched files
        self.sync_dict.monitor()
        self.sync_dict.applyChanges()
            
        print(f"✓ Added {len(help_translations)} help center translations")
        print(f"✓ Added {len(faq_translations)} FAQ translations")
        
        # Show samples
        self._show_translation_sample("ja", "help/center/title")
        self._show_translation_sample("zh", "faq/title")
        
    def _show_translation_sample(self, lang_code, key):
        """Show how a translation appears in a specific language file"""
        if lang_code in self.language_files:
            file_path = self.language_files[lang_code]
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Navigate to the key
            keys = key.split('/')
            current = data
            try:
                for k in keys:
                    current = current[k]
                lang_name = self.languages[lang_code]
                print(f"  {lang_name} ({lang_code}): '{key}' = '{current}'")
            except KeyError:
                print(f"  {lang_code}: Key '{key}' not found")
                
    def show_change_summary(self):
        """Show summary of all changes made"""
        print("\n" + "="*60)
        print("CHANGE SUMMARY")
        print("="*60)
        
        changes = self.sync_dict.changes["all"]
        
        # Group changes by type
        additions = [c for c in changes if c["previous"] is None]
        deletions = [c for c in changes if c["new"] is None]
        updates = [c for c in changes if c["previous"] is not None and c["new"] is not None]
        
        print(f"\nTotal changes applied: {len(changes)}")
        print(f"  - New keys added: {len(additions)}")
        print(f"  - Keys moved/deleted: {len(deletions)}")
        print(f"  - Keys updated: {len(updates)}")
        
        # Show file sync status
        print("\nFile synchronization:")
        print("  - Base file: en.json") 
        print(f"  - Synchronized files: {len(self.sync_dict.watched_files)}")
        print(f"  - Total language files: {len(self.language_files)}")
        
        # Show final structure
        print("\nFinal translation structure sections:")
        current_keys = set()
        for change in changes:
            if change["new"] is not None:
                top_level = change["key"].split("/")[0]
                current_keys.add(top_level)
                
        print(f"  Sections: {', '.join(sorted(current_keys))}")
        
        # Show file sizes
        print("\nTranslation file sizes:")
        total_size = 0
        for lang_code, file_path in self.language_files.items():
            size = os.path.getsize(file_path)
            total_size += size
            lang_name = self.languages[lang_code]
            print(f"  - {lang_name} ({lang_code}.json): {size:,} bytes")
            
        print(f"\nTotal translation data: {total_size:,} bytes")
        
    def save_final_state(self):
        """Save the final state and create a summary"""
        print("\n" + "="*60)
        print("SAVING FINAL STATE")
        print("="*60)
        
        # Save base file
        self.sync_dict.save()
        print("✓ Saved base translation file (en.json)")
        
        # Create summary file
        summary_file = os.path.join(self.playground_dir, "sync_summary.json")
        
        summary_data = {
            "demo_info": {
                "created": datetime.now().isoformat(),
                "languages": list(self.languages.keys()),
                "total_files": len(self.language_files)
            },
            "sync_stats": {
                "total_changes": len(self.sync_dict.changes["all"]),
                "watched_files": len(self.sync_dict.watched_files),
                "base_file": "en.json"
            },
            "final_structure": {}
        }
        
        # Get final structure from base file
        with open(self.language_files['en'], 'r', encoding='utf-8') as f:
            base_data = json.load(f)
            
        def get_structure(obj, path=""):
            structure = {}
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}/{key}" if path else key
                    if isinstance(value, dict):
                        structure[key] = get_structure(value, current_path)
                    else:
                        structure[key] = type(value).__name__
            return structure
            
        summary_data["final_structure"] = get_structure(base_data)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
        print("✓ Created summary file: sync_summary.json")
        print(f"\nDemo files available at: {self.playground_dir}")
        print("You can examine the generated translation files to see the structure sync in action!")
        
    def cleanup(self):
        """Clean up demo files (optional)"""
        if hasattr(self, 'playground_dir') and os.path.exists(self.playground_dir):
            response = input(f"\nDelete playground files in {self.playground_dir}? (y/N): ")
            if response.lower() == 'y':
                shutil.rmtree(self.playground_dir)
                print("Playground files cleaned up.")
            else:
                print(f"Playground files preserved in: {self.playground_dir}")
        else:
            print("No playground files to clean up.")
                
    def run_demo(self):
        """Run the complete i18n synchronization demo"""
        try:
            print("SyncDict i18n Demo - Real-World Translation Management")
            print("="*70)
            
            # Setup
            self.setup_i18n_files()
            watched, desynced = self.initialize_syncdict()
            
            if desynced > 0:
                print(f"\n⚠️  Warning: {desynced} files could not be synchronized.")
                print("This might indicate an issue with the SyncDict implementation.")
                
            # Only proceed if we have some working files
            if watched > 0:
                # Demonstrate various i18n operations
                self.demonstrate_adding_new_features()
                self.demonstrate_structural_moves()  # Core SyncDict functionality
                self.demonstrate_adding_new_pages()
                self.show_change_summary()
                self.save_final_state()
            else:
                print("\n❌ No files could be synchronized. Demo cannot proceed.")
                
        except Exception as e:
            print(f"\nError during demo: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Ask about cleanup
            if hasattr(self, 'demo_dir') and self.demo_dir:
                self.cleanup()


def main():
    """Run the i18n synchronization demo"""
    demo = I18nSyncDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()
