# ============================================================
# FILE 5: utils/gesture_handler.py (UPDATED - if needed)
# ============================================================

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty
from kivy.clock import Clock


class SwipeDetector(Widget):
    """Detects swipe gestures on a widget"""
    swipe_threshold = NumericProperty(50)
    swipe_timeout = NumericProperty(0.5)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_swipe_left')
        self.register_event_type('on_swipe_right')
        self.register_event_type('on_swipe_up')
        self.register_event_type('on_swipe_down')
        
        self._touch_start_x = 0
        self._touch_start_y = 0
        self._touch_start_time = 0
        self._is_swiping = False
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_start_x = touch.x
            self._touch_start_y = touch.y
            self._touch_start_time = Clock.get_time()
            self._is_swiping = True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self._is_swiping:
            dx = touch.x - self._touch_start_x
            dy = touch.y - self._touch_start_y
            dt = Clock.get_time() - self._touch_start_time
            
            if dt <= self.swipe_timeout:
                abs_dx = abs(dx)
                abs_dy = abs(dy)
                
                if abs_dx > abs_dy and abs_dx > self.swipe_threshold:
                    if dx > 0:
                        self.dispatch('on_swipe_right')
                    else:
                        self.dispatch('on_swipe_left')
                elif abs_dy > abs_dx and abs_dy > self.swipe_threshold:
                    if dy > 0:
                        self.dispatch('on_swipe_up')
                    else:
                        self.dispatch('on_swipe_down')
            
            self._is_swiping = False
        
        return super().on_touch_up(touch)
    
    def on_swipe_left(self):
        pass
    
    def on_swipe_right(self):
        pass
    
    def on_swipe_up(self):
        pass
    
    def on_swipe_down(self):
        pass

