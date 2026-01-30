#============================================================
# FILE 2: widgets/long_press_row.py
# ============================================================

from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window


class LongPressRow(BoxLayout):
    """Widget that detects long press gestures"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_long_press')
        self._touch_start_time = 0
        self._long_press_triggered = False
        self._scheduled_event = None
        self._touch_start_pos = (0, 0)
        self._is_touching = False
        self._touch_uid = None
        self._highlight_instruction = None
        self._highlight_color = None
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_start_time = Clock.get_time()
            self._touch_start_pos = touch.pos
            self._long_press_triggered = False
            self._is_touching = True
            self._touch_uid = touch.uid
            
            self._show_press_feedback()
            
            if self._scheduled_event:
                self._scheduled_event.cancel()
            
            self._scheduled_event = Clock.schedule_once(self._trigger_long_press, 0.5)
            return True
        
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if self._is_touching and touch.uid == self._touch_uid:
            dx = touch.x - self._touch_start_pos[0]
            dy = touch.y - self._touch_start_pos[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            
            if distance > dp(20):
                self._cancel_long_press()
                self._is_touching = False
            
            return super().on_touch_move(touch)
        
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        if self._is_touching and touch.uid == self._touch_uid:
            self._cancel_long_press()
            self._is_touching = False
            self._touch_uid = None
            
            if self._long_press_triggered:
                return True
        
        return super().on_touch_up(touch)
    
    def _show_press_feedback(self):
        """Show visual feedback"""
        if self._highlight_instruction:
            try:
                self.canvas.after.remove(self._highlight_instruction)
            except:
                pass
        
        if self._highlight_color:
            try:
                self.canvas.after.remove(self._highlight_color)
            except:
                pass
        
        with self.canvas.after:
            self._highlight_color = Color(1, 1, 1, 0.05)
            self._highlight_instruction = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(6)]
            )
        
        self.bind(
            pos=lambda i, v: setattr(self._highlight_instruction, 'pos', v) if self._highlight_instruction else None,
            size=lambda i, v: setattr(self._highlight_instruction, 'size', v) if self._highlight_instruction else None
        )
    
    def _cancel_long_press(self):
        """Cancel long press"""
        if self._scheduled_event:
            self._scheduled_event.cancel()
            self._scheduled_event = None
        
        if self._highlight_instruction:
            try:
                self.canvas.after.remove(self._highlight_instruction)
            except:
                pass
            self._highlight_instruction = None
        
        if self._highlight_color:
            try:
                self.canvas.after.remove(self._highlight_color)
            except:
                pass
            self._highlight_color = None
    
    def _trigger_long_press(self, dt):
        """Trigger long press"""
        if self._is_touching and not self._long_press_triggered:
            self._long_press_triggered = True
            
            if self._highlight_color:
                self._highlight_color.rgba = (0.4, 0.7, 1.0, 0.15)
            
            try:
                Window.vibrate(0.05)
            except:
                pass
            
            self.dispatch('on_long_press')
    
    def on_long_press(self):
        """Event placeholder"""
        pass