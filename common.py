
# ============================================================
# FILE 3: widgets/common.py
# ============================================================

from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.animation import Animation

ANIMATION_POPUP = 0.2


def show_popup(title, text, size_hint=(0.6, 0.4)):
    """Show a simple popup with animation"""
    popup = Popup(title=title, content=Label(text=text), size_hint=size_hint)
    popup.open()
    Animation(opacity=1, d=ANIMATION_POPUP, t="out_quad").start(popup)
    return popup


def show_animated_popup(popup_widget, duration=ANIMATION_POPUP):
    """Show an animated popup"""
    popup_widget.opacity = 0
    popup_widget.open()
    Animation(opacity=1, d=duration, t="out_quad").start(popup_widget)
    return popup_widget
