#============================================================
# FILE 3: screens/register_screen.py
# ============================================================

from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
import utils.database as db
import utils.utils as utils
from widgets.common import show_popup

class RegisterScreen(Screen):
    def on_enter(self):
        btn = getattr(self.ids, "register_btn", None)
        if btn:
            btn.disabled = False
            btn.text = "REGISTER"
            btn.background_color = (0.15, 0.65, 0.95, 1)  # Blue color
    
    def do_register(self, username, password, email):
        btn = getattr(self.ids, "register_btn", None)
        if btn:
            btn.disabled = True
        
        if not username or not password:
            show_popup("Error", "Username and Password required")
            if btn:
                Clock.schedule_once(lambda dt: setattr(btn, 'disabled', False), 0.4)
            return
        
        v, msg = utils.validate_username(username)
        if not v:
            show_popup("Error", msg)
            if btn:
                Clock.schedule_once(lambda dt: setattr(btn, 'disabled', False), 0.4)
            return
        
        v, msg = utils.validate_password(password)
        if not v:
            show_popup("Error", msg)
            if btn:
                Clock.schedule_once(lambda dt: setattr(btn, 'disabled', False), 0.4)
            return
        
        if email and not utils.validate_email(email):
            show_popup("Error", "Invalid email format")
            if btn:
                Clock.schedule_once(lambda dt: setattr(btn, 'disabled', False), 0.4)
            return
        
        if db.add_user(username, password, email):
            show_popup("Success", "User registered successfully!\nYou can now login.")
            if btn:
                btn.disabled = False
                btn.background_color = (0.15, 0.65, 0.95, 1)
            self.manager.current = "login"
        else:
            show_popup("Error", "Username already exists")
            if btn:
                Clock.schedule_once(lambda dt: setattr(btn, 'disabled', False), 0.4)