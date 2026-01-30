# screens/login_screen.py

from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.app import App
from datetime import datetime
import utils.database as db
import utils.utils as utils
from utils.auth_manager import AuthManager
from widgets.common import show_popup


class LoginScreen(Screen):
    def on_enter(self):
        """Initialize login screen when entering"""
        # Just clear the input fields, no auto-login check
        if hasattr(self.ids, 'username'):
            self.ids.username.text = ""
        if hasattr(self.ids, 'password'):
            self.ids.password.text = ""
        if hasattr(self.ids, 'remember_me'):
            self.ids.remember_me.active = True
    
    def do_login(self, username, password, remember_me=True):
        """Login with credentials"""
        if not username or not password:
            return show_popup("Error", "Username and Password required")
        
        if db.authenticate_user(username, password):
            # Save session if remember_me is checked
            if remember_me:
                AuthManager.save_session(username, remember_me=True)
                print(f"✓ Session saved for {username}")
            else:
                AuthManager.clear_session()
                print(f"✓ Session not saved (Remember Me unchecked)")
            
            self.manager.admin_name = username
            app = App.get_running_app()
            app.logged_user = username
            
            self.manager.current = "loading"
            self.manager.get_screen("loading").start_loading(
                next_screen="main_app",
                message="Loading your data...",
                duration=1.5
            )
            Clock.schedule_once(lambda dt: self._preload_all_screens(username), 0.3)
        else:
            show_popup("Login Failed", "Invalid username or password")
    
    def _preload_all_screens(self, username):
        """Preload all screens"""
        try:
            main_app = self.manager.get_screen("main_app")
            if not main_app or not hasattr(main_app.ids, 'inner_content_manager'):
                return
            
            cm = main_app.ids.inner_content_manager
            
            # Preload home
            hs = cm.get_screen("home")
            if hs:
                if hasattr(hs, 'refresh_statistics'):
                    hs.refresh_statistics()
                if hasattr(hs, 'refresh_income_cards'):
                    hs.refresh_income_cards()
            
            # Schedule other screens
            Clock.schedule_once(lambda dt: self._preload_activity_log(cm), 0.5)
            Clock.schedule_once(lambda dt: self._preload_charts(cm), 1.0)
            Clock.schedule_once(lambda dt: self._preload_add_expense(cm), 1.5)
        except Exception as e:
            print(f"Error preloading: {e}")
    
    def _preload_activity_log(self, cm):
        try:
            acs = cm.get_screen("activity_log")
            if acs and hasattr(acs, 'refresh_items'):
                acs.refresh_items()
                acs._items_loaded = True
        except Exception as e:
            print(f"Error: {e}")
    
    def _preload_charts(self, cm):
        try:
            cs = cm.get_screen("charts")
            if cs:
                cy, mo = datetime.now().year, datetime.now().month
                if hasattr(cs.ids, 'year_spinner'):
                    yrs = utils.get_year_range(cy)
                    cs.ids.year_spinner.values = yrs if yrs else [str(cy)]
                    cs.ids.year_spinner.text = str(cy) if str(cy) in (yrs or []) else (yrs[0] if yrs else str(cy))
                if hasattr(cs.ids, 'month_spinner'):
                    mos = utils.get_month_list()
                    cs.ids.month_spinner.values = mos if mos else ["January"]
                    cs.ids.month_spinner.text = mos[min(max(0, mo - 1), len(mos) - 1)] if mos else "January"
                cs._charts_generated = False
        except Exception as e:
            print(f"Error: {e}")
    
    def _preload_add_expense(self, cm):
        try:
            aes = cm.get_screen("add_expense")
            if aes and hasattr(aes, 'ids'):
                un = App.get_running_app().logged_user
                if hasattr(aes.ids, 'category_spinner'):
                    cats = db.get_categories(un)
                    aes.ids.category_spinner.values = cats
                    if cats:
                        aes.ids.category_spinner.text = cats[0]
                if hasattr(aes, 'refresh_income_spinner'):
                    aes.refresh_income_spinner()
                if hasattr(aes.ids, 'date_input'):
                    aes.ids.date_input.text = utils.get_current_date()
        except Exception as e:
            print(f"Error: {e}")