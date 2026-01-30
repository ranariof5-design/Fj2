# main.py

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.properties import StringProperty
from kivy.metrics import dp, sp
from kivy.core.window import Window
import os

from screens import(
    LoginScreen,
    RegisterScreen,
    HomeScreen,
    AddExpenseScreen,
    ActivityLogScreen,
    ChartsScreen,
    LoadingScreen
    )

from widgets import NavButton
from utils.gesture_handler import SwipeDetector
from utils.auth_manager import AuthManager  
import utils.database as db
import utils.utils as utils

# Constants
SIDEBAR_COLLAPSED = dp(0)
SIDEBAR_EXPANDED = dp(200)
ANIMATION_SIDEBAR = 0.4


# ← ADD THIS CLASS BEFORE FJExpensesApp
class ScreenManagement(ScreenManager):
    """Main screen manager"""
    admin_name = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transition = SlideTransition(duration=0.3)


class MainAppScreen(Screen):
    """Main application screen with sidebar and inner navigation"""
    screen_order = ["home", "add_expense", "activity_log", "charts"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.swipe_detector = None
    
    def on_enter(self):
        """Initialize screen when entering"""
        self._init_inner_manager(0)
        self._setup_swipe_detector()
        if hasattr(self.ids, 'main_sidebar'):
            App.get_running_app()._init_user_area(self.ids.main_sidebar.ids.get("user_area"))
    
    def _init_inner_manager(self, dt):
        """Initialize inner screen manager"""
        if hasattr(self.ids, 'inner_content_manager'):
            self.ids.inner_content_manager.transition = SlideTransition(duration=0.3)
            if self.ids.inner_content_manager.current not in self.screen_order:
                self.ids.inner_content_manager.current = "home"
    
    def _setup_swipe_detector(self):
        """Setup swipe gesture detection"""
        if self.swipe_detector:
            return
        self.swipe_detector = SwipeDetector()
        self.swipe_detector.size = self.size
        self.swipe_detector.pos = self.pos
        self.swipe_detector.swipe_threshold = dp(80)
        self.swipe_detector.bind(
            on_swipe_left=self._on_swipe_left,
            on_swipe_right=self._on_swipe_right,
            on_swipe_up=self._on_swipe_up,
            on_swipe_down=self._on_swipe_down
        )
        self.bind(
            size=lambda *a: setattr(self.swipe_detector, 'size', self.size),
            pos=lambda *a: setattr(self.swipe_detector, 'pos', self.pos)
        )
        self.add_widget(self.swipe_detector)
    
    def _is_sidebar_expanded(self):
        """Check if sidebar is expanded"""
        return hasattr(self.ids, 'main_sidebar') and self.ids.main_sidebar.width > SIDEBAR_COLLAPSED + dp(10)
    
    def _on_swipe_left(self, instance):
        """Handle swipe left - close sidebar"""
        if self._is_sidebar_expanded():
            App.get_running_app().toggle_sidebar()
    
    def _on_swipe_right(self, instance):
        """Handle swipe right - open sidebar"""
        if not self._is_sidebar_expanded():
            App.get_running_app().toggle_sidebar()
    
    def _on_swipe_up(self, instance):
        """Handle swipe up - next screen"""
        if not self._is_sidebar_expanded():
            return
        current = self.ids.inner_content_manager.current
        if current in self.screen_order:
            idx = self.screen_order.index(current)
            if idx < len(self.screen_order) - 1:
                next_screen = self.screen_order[idx + 1]
                self.switch_to_screen(next_screen)
                App.get_running_app()._set_active_nav(next_screen)
    
    def _on_swipe_down(self, instance):
        """Handle swipe down - previous screen"""
        if not self._is_sidebar_expanded():
            return
        current = self.ids.inner_content_manager.current
        if current in self.screen_order:
            idx = self.screen_order.index(current)
            if idx > 0:
                prev_screen = self.screen_order[idx - 1]
                self.switch_to_screen(prev_screen)
                App.get_running_app()._set_active_nav(prev_screen)
    
    def switch_to_screen(self, screen_name):
        """Switch to screen with proper transition direction"""
        if not hasattr(self.ids, 'inner_content_manager'):
            return
        cm = self.ids.inner_content_manager
        current = cm.current
        if current in self.screen_order and screen_name in self.screen_order:
            ci = self.screen_order.index(current)
            ti = self.screen_order.index(screen_name)
            cm.transition.direction = 'up' if ti > ci else 'down'
        cm.current = screen_name


class FJExpensesApp(App):
    """Main application class"""
    logged_user = StringProperty("Guest")
    theme_mode = StringProperty('dark')
    
    def build(self):
        """Build the app"""
        root = Builder.load_file("main.kv")
        self.root = root
        
        # Set initial screen to loading
        self.root.current = "loading"
        
        # Collapse sidebar initially
        try:
            for sb in self._collect_sidebars():
                sb.width = SIDEBAR_COLLAPSED
        except Exception:
            pass
        
        # Bind window touch events
        Clock.schedule_once(lambda dt: Window.bind(on_touch_up=self._on_window_touch_up), 0)
        Clock.schedule_once(lambda dt: self._set_active_nav("home"), 0.1)
        
        # Check auto-login after a short delay
        Clock.schedule_once(self._check_auto_login, 0.2)
        
        return self.root
    
    def _check_auto_login(self, dt):
        """Check for existing session and decide where to go"""
        if AuthManager.is_session_valid():
            logged_user = AuthManager.get_logged_in_user()
            if logged_user:
                print(f"✓ Auto-login: Found valid session for {logged_user}")
                self.logged_user = logged_user
                
                # Go to main app
                self.root.get_screen("loading").start_loading(
                    next_screen="main_app",
                    message=f"Welcome back, {logged_user}!",
                    duration=1.0
                )
                
                # Preload screens
                Clock.schedule_once(lambda dt: self._preload_all_screens(logged_user), 0.3)
                return
        
        # No valid session, go to login
        print("No valid session found, showing login screen")
        self.root.get_screen("loading").start_loading(
            next_screen="login",
            message="Welcome to FJ Expenses Tracker",
            duration=0.8
        )
    
    def _preload_all_screens(self, username):
        """Preload all screens after auto-login"""
        try:
            main_app = self.root.get_screen("main_app")
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
                from datetime import datetime
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
                un = self.logged_user
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
 
    
    def on_pause(self):
        """Update session activity when app is paused"""
        AuthManager.update_session_activity()
        return True
    
    def on_resume(self):
        """Check session validity when app resumes"""
        if not AuthManager.is_session_valid():
            # Session expired while app was paused
            self.logout_user()
    
    def on_start(self):
        """Check for required icon files"""
        required = [
            "icons/home.png",
            "icons/add_expense.png",
            "icons/activity_log.png",
            "icons/chart.png",
            "icons/toggle.png"
        ]
        missing = [p for p in required if not os.path.exists(p)]
        if missing:
            msg = "The following icon files are missing:\n\n" + "\n".join(missing)
            print(msg)
            Clock.schedule_once(
                lambda dt: Popup(
                    title="Missing Icons",
                    content=Label(text=msg),
                    size_hint=(0.85, 0.6)
                ).open(),
                0.2
            )
    
    def on_stop(self):
        """Cleanup on app stop"""
        try:
            Window.unbind(on_touch_up=self._on_window_touch_up)
        except Exception:
            pass
    
    def _on_window_touch_up(self, window, touch):
        """Handle window touch to close sidebar when clicking outside"""
        if getattr(touch, "is_mouse_scrolling", False):
            return False
        
        # Detect swipe vs click
        if hasattr(touch, 'opos'):
            dx = abs(touch.x - touch.opos[0])
            dy = abs(touch.y - touch.opos[1])
            total_distance = (dx ** 2 + dy ** 2) ** 0.5
            
            if total_distance > dp(50):
                return False
        
        try:
            for sb in self._collect_sidebars():
                try:
                    current_width = getattr(sb, "width", SIDEBAR_COLLAPSED)
                    threshold = SIDEBAR_COLLAPSED + dp(10)
                    
                    if current_width > threshold:
                        sb_local_x, sb_local_y = sb.to_widget(*touch.pos)
                        if not sb.collide_point(sb_local_x, sb_local_y):
                            self.toggle_sidebar()
                            return False
                except Exception:
                    pass
                
                ua = sb.ids.get("user_area") if sb and hasattr(sb, "ids") else None
                if not ua or not getattr(ua, "menu_open", False):
                    continue
                
                local_x, local_y = ua.to_widget(*touch.pos)
                if ua.collide_point(local_x, local_y):
                    return False
                
                sb_local_x, sb_local_y = sb.to_widget(*touch.pos)
                if sb.collide_point(sb_local_x, sb_local_y):
                    ub = ua.ids.get("user_btn")
                    if ub:
                        self.toggle_user_menu(ub)
                        return False
                
                ub = ua.ids.get("user_btn")
                if ub:
                    self.toggle_user_menu(ub)
                    return False
        except Exception as e:
            print("Error in global touch handler:", e)
        
        return False
    
    def _init_user_area(self, ua):
        """Initialize user area with collapsed menu"""
        base_y = dp(8)
        try:
            ub = ua.ids.get("user_btn")
            ch = ua.ids.get("change_pass_btn")
            lo = ua.ids.get("logout_btn")
            
            try:
                if ub:
                    Animation.cancel_all(ub)
                if ch:
                    Animation.cancel_all(ch)
                if lo:
                    Animation.cancel_all(lo)
            except Exception:
                pass
            
            if ch:
                ch.y = base_y
                ch.opacity = 0
                ch.disabled = True
            if lo:
                lo.y = base_y
                lo.opacity = 0
                lo.disabled = True
            if ub:
                ub.y = base_y
                ub.opacity = 1
            
            ua.menu_open = False
            ua.initialized = True
        except Exception:
            pass
    
    def _collect_sidebars(self):
        """Collect all sidebar widgets"""
        sidebars = []
        try:
            if self.root:
                main_app = self.root.get_screen("main_app")
                if main_app and hasattr(main_app.ids, 'main_sidebar'):
                    sidebars.append(main_app.ids.main_sidebar)
        except Exception:
            pass
        return sidebars
    
    def toggle_sidebar(self):
        """Toggle sidebar open/closed"""
        sidebars = self._collect_sidebars()
        if not sidebars:
            return
        
        for sb in sidebars:
            try:
                current = sb.width
            except Exception:
                current = SIDEBAR_COLLAPSED
            
            is_phone = Window.width <= dp(420)
            expanded_target = max(Window.width * 0.6, SIDEBAR_EXPANDED) if is_phone else SIDEBAR_EXPANDED
            target = SIDEBAR_COLLAPSED if current > SIDEBAR_COLLAPSED + dp(10) else expanded_target
            
            try:
                Animation(width=target, d=ANIMATION_SIDEBAR, t="out_quad").start(sb)
            except Exception:
                sb.width = target
    
    def navigate_to(self, screen_name):
        """Navigate to a screen"""
        try:
            main_app = self.root.get_screen("main_app")
            if main_app and hasattr(main_app, 'switch_to_screen'):
                main_app.switch_to_screen(screen_name)
            self._set_active_nav(screen_name)
        except Exception as e:
            print(f"Navigation error: {e}")
    
    def _set_active_nav(self, screen_name):
        """Set active navigation button"""
        mapping = {
            "home": "Home",
            "add_expense": "Add Expense",
            "activity_log": "Activity Log",
            "charts": "Charts"
        }
        target_text = mapping.get(screen_name, "")
        
        for sb in self._collect_sidebars():
            for child in sb.walk():
                try:
                    if isinstance(child, NavButton):
                        child.active = (child.full_text == target_text)
                except Exception:
                    pass
    
    def refresh_all_screens(self):
        """Refresh all screens after data change"""
        try:
            main_app = self.root.get_screen("main_app")
            if not main_app:
                return
            
            # Refresh home screen
            home_screen = main_app.ids.inner_content_manager.get_screen("home")
            if home_screen and hasattr(home_screen, 'refresh_statistics'):
                home_screen.refresh_statistics()
            
            # Mark activity log to refresh
            activity_screen = main_app.ids.inner_content_manager.get_screen("activity_log")
            if activity_screen:
                activity_screen._items_loaded = False
            
            # Mark charts to refresh
            charts_screen = main_app.ids.inner_content_manager.get_screen("charts")
            if charts_screen:
                charts_screen._charts_generated = False
        except Exception as e:
            print(f"Error refreshing screens: {e}")
    
    def toggle_user_menu(self, user_btn):
        """Toggle user menu open/closed"""
        fl = user_btn.parent
        if not fl:
            return
        
        change = fl.ids.get("change_pass_btn")
        logout = fl.ids.get("logout_btn")
        
        if not getattr(fl, "initialized", False):
            self._init_user_area(fl)
        
        base_y = dp(8)
        btn_height = dp(36)
        spacing = dp(8)
        user_lift = dp(100)
        logout_target_y = base_y
        change_target_y = logout_target_y + btn_height + spacing
        
        try:
            Animation.cancel_all(user_btn)
            if change:
                Animation.cancel_all(change)
            if logout:
                Animation.cancel_all(logout)
        except Exception:
            pass
        
        if not change or not logout:
            return
        
        if not hasattr(fl, "menu_open"):
            fl.menu_open = False
        
        if not fl.menu_open:
            fl.menu_open = True
            change.disabled = False
            logout.disabled = False
            
            def start(dt):
                user_target_y = user_btn.y + user_lift
                change.opacity = 1
                change.y = logout_target_y
                logout.opacity = 1
                logout.y = logout_target_y
                Animation(y=user_target_y, d=0.22, t="out_quad").start(user_btn)
                Animation(y=change_target_y, d=0.22, t="out_quad").start(change)
            
            Clock.schedule_once(start, 0)
        else:
            def collapse_final(a=None, w=None):
                try:
                    Animation.cancel_all(user_btn)
                except Exception:
                    pass
                anim_down = Animation(y=base_y, d=0.12, t="out_quad")
                
                def on_down_done(a2, w2):
                    change.disabled = True
                    logout.disabled = True
                    fl.menu_open = False
                
                anim_down.bind(on_complete=on_down_done)
                anim_down.start(user_btn)
            
            anim_change_down = Animation(y=base_y, opacity=0, d=0.12, t="out_quad")
            anim_logout_down = Animation(y=base_y, opacity=0, d=0.12, t="out_quad")
            if change.opacity > 0.1:
                anim_change_down.start(change)
            if logout.opacity > 0.1:
                anim_logout_down.start(logout)
            Clock.schedule_once(lambda dt: collapse_final(), 0.13)
    
    def open_change_pass_popup(self):
        """Open change password popup"""
        if not self.logged_user or self.logged_user == "Guest":
            Popup(
                title="Error",
                content=Label(text="No user logged in"),
                size_hint=(0.6, 0.4)
            ).open()
            return
        
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(14))
        content.add_widget(Label(
            text="Change Password",
            size_hint_y=None,
            height=dp(34),
            font_size=sp(16),
            bold=True
        ))
        content.add_widget(Label(
            text="Enter a new password (min 6 characters).",
            size_hint_y=None,
            height=dp(20),
            font_size=sp(12),
            color=(0.8, 0.8, 0.8, 1)
        ))
        
        inputs_box = BoxLayout(orientation="vertical", spacing=dp(8), padding=(dp(8), dp(6)))
        from kivy.uix.textinput import TextInput
        new_pw = TextInput(
            hint_text="New password",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(38),
            font_size=sp(14),
            background_color=(0.12, 0.12, 0.12, 1),
            foreground_color=(1, 1, 1, 1)
        )
        confirm_pw = TextInput(
            hint_text="Confirm password",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(38),
            font_size=sp(14),
            background_color=(0.12, 0.12, 0.12, 1),
            foreground_color=(1, 1, 1, 1)
        )
        inputs_box.add_widget(new_pw)
        inputs_box.add_widget(confirm_pw)
        content.add_widget(inputs_box)
        
        btn_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        cancel = Button(
            text="Cancel",
            size_hint_x=0.45,
            background_color=(0.18, 0.18, 0.18, 1),
            font_size=sp(13)
        )
        submit = Button(
            text="Change",
            size_hint_x=0.55,
            background_color=(0.15, 0.65, 0.95, 1),
            font_size=sp(13)
        )
        btn_row.add_widget(cancel)
        btn_row.add_widget(submit)
        content.add_widget(btn_row)
        
        popup = Popup(
            title="",
            content=content,
            size_hint=(0.82, 0.36),
            auto_dismiss=False
        )
        
        def do_submit(inst):
            np, cp = new_pw.text.strip(), confirm_pw.text.strip()
            if not np or not cp:
                Popup(
                    title="Error",
                    content=Label(text="Please fill both fields"),
                    size_hint=(0.6, 0.35)
                ).open()
                return
            if np != cp:
                Popup(
                    title="Error",
                    content=Label(text="Passwords do not match"),
                    size_hint=(0.6, 0.35)
                ).open()
                return
            
            valid, msg = utils.validate_password(np)
            if not valid:
                Popup(title="Error", content=Label(text=msg), size_hint=(0.6, 0.35)).open()
                return
            
            try:
                with db.sqlite3.connect(db.DB_NAME) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET password=? WHERE username=?",
                        (np, self.logged_user)
                    )
                    conn.commit()
                Popup(
                    title="Success",
                    content=Label(text="Password changed"),
                    size_hint=(0.6, 0.35)
                ).open()
                popup.dismiss()
            except Exception as e:
                Popup(
                    title="Error",
                    content=Label(text=f"Failed: {e}"),
                    size_hint=(0.7, 0.45)
                ).open()
        
        cancel.bind(on_release=lambda x: popup.dismiss())
        submit.bind(on_release=do_submit)
        popup.open()
    
    def confirm_logout(self):
        """Confirm logout"""
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(Label(text="Are you sure you want to logout?"))
        
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        yes_btn = Button(text="Yes")
        no_btn = Button(text="No")
        btn_row.add_widget(no_btn)
        btn_row.add_widget(yes_btn)
        content.add_widget(btn_row)
        
        popup = Popup(
            title="Confirm Logout",
            content=content,
            size_hint=(0.6, 0.38)
        )
        
        def do_yes(instance):
            popup.dismiss()
            try:
                for sb in self._collect_sidebars():
                    ua = sb.ids.get("user_area")
                    if ua:
                        for btn in ["change_pass_btn", "logout_btn", "user_btn"]:
                            w = ua.ids.get(btn)
                            if w:
                                Animation.cancel_all(w)
                        ua.ids.change_pass_btn.opacity = 0
                        ua.ids.change_pass_btn.disabled = True
                        ua.ids.logout_btn.opacity = 0
                        ua.ids.logout_btn.disabled = True
                        ua.menu_open = False
            except Exception:
                pass
            self.logout_user()
        
        yes_btn.bind(on_release=do_yes)
        no_btn.bind(on_release=lambda x: popup.dismiss())
        popup.open()
    
    def logout_user(self):
        """Logout user and clear session"""
        AuthManager.clear_session()  # ← CRITICAL LINE
        print("✓ User session cleared")
        
        self.logged_user = "Guest"
        if self.root:
            if hasattr(self.root, 'admin_name'):
                self.root.admin_name = ""
            self.root.current = "loading"
            loading_screen = self.root.get_screen("loading")
            if loading_screen:
                loading_screen.start_loading(
                    next_screen="login",
                    message="Logging out..."
                )
    def toggle_theme_mode(self):
        """Toggle between dark and light theme"""
        self.theme_mode = 'light' if self.theme_mode == 'dark' else 'dark'
        Builder.unload_file('main.kv')
        self.root.clear_widgets()
        self.root.add_widget(Builder.load_file('main.kv'))


if __name__ == "__main__":
    FJExpensesApp().run()