# ============================================================
# FILE 2: widgets/nav_button.py
# ============================================================

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, BooleanProperty


class NavButton(ButtonBehavior, BoxLayout):
    """Navigation button widget for sidebar"""
    icon = StringProperty("")
    full_text = StringProperty("")
    active = BooleanProperty(False)