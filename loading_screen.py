# screens/loading_screen.py

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock


class LoadingScreen(Screen):
    message = StringProperty("Loading...")
    progress = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._event, self.next_screen, self._spinner_event = None, None, None
    
    def start_loading(self, next_screen, message="Loading...", duration=1.0):  # ← Changed from 2.0 to 1.0
        """
        Start loading animation
        
        Args:
            next_screen: Screen to navigate to after loading
            message: Loading message to display
            duration: Total duration of loading animation (default: 1.0 seconds, was 2.0)
        """
        self.message = message
        if hasattr(self.ids, "loading_bar"):
            self.ids.loading_bar.value = 0
        self.next_screen = next_screen
        self.progress = 0
        
        # Calculate update interval for smooth animation
        # 50 steps total, so interval = duration / 50
        period = max(duration / 50.0, 0.02)  # Minimum 0.02 seconds between updates
        
        if self._event:
            self._event.cancel()
        self._event = Clock.schedule_interval(self.update_progress, period)
        self._start_spinner_animation()
    
    def _start_spinner_animation(self):
        """Start spinner animation (optional visual effect)"""
        try:
            def animate_spinner(dt):
                # You can add spinner rotation logic here if needed
                pass
            
            if self._spinner_event:
                self._spinner_event.cancel()
            # Update spinner every 0.05 seconds (was 0.05, keep same for smoothness)
            self._spinner_event = Clock.schedule_interval(animate_spinner, 0.05)
        except Exception:
            pass
    
    def update_progress(self, dt):
        """Update progress bar"""
        if self.progress >= 100:
            # Loading complete
            if self._event:
                self._event.cancel()
                self._event = None
            if self._spinner_event:
                self._spinner_event.cancel()
                self._spinner_event = None
            
            # Navigate to next screen
            if self.manager and self.next_screen:
                self.manager.current = self.next_screen
            return False
        else:
            # Increment progress
            self.progress += 2  # Increment by 2 each step (50 steps total)
            if hasattr(self.ids, "loading_bar"):
                self.ids.loading_bar.value = min(self.progress, 100)
            return True

