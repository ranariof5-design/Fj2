# ============================================================
# FILE 4: widgets/interactive_charts.py (UPDATED)
# ============================================================

from kivy.uix.widget import Widget
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.core.text import Label as CoreLabel
from kivy.clock import Clock
from kivy.uix.label import Label
from datetime import datetime


class InteractiveBarChart(Widget):
    """
    Lightweight Kivy widget that draws a bar chart and handles touches.
    Dispatches 'on_selection' with (selected_index_or_None, filtered_expenses_or_None)
    """
    labels = ListProperty([])
    values = ListProperty([])
    expenses = ListProperty([])
    selected_index = NumericProperty(-1)
    mode = StringProperty("Daily")
    year = NumericProperty(0)
    month = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_selection')
        self.tooltip = None
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            labels=self._redraw,
            values=self._redraw,
            selected_index=self._redraw
        )

    def set_data(self, labels, values, expenses, year=None, month=None, mode="Daily"):
        """Set chart data and redraw"""
        self.labels = labels[:] if labels is not None else []
        self.values = values[:] if values is not None else []
        self.expenses = expenses[:] if expenses is not None else []
        if year is not None:
            self.year = year
        if month is not None:
            self.month = month
        self.mode = mode or "Daily"
        self.selected_index = -1
        Clock.schedule_once(lambda dt: self._redraw(), 0)

    def _redraw(self, *args):
        """Redraw the chart"""
        self.canvas.clear()
        if not self.values or len(self.values) == 0:
            return
        
        with self.canvas:
            # Background
            Color(0.05, 0.05, 0.05, 1)
            Rectangle(pos=self.pos, size=self.size)

            pad_x = dp(16)
            bottom_pad = dp(40)
            top_available = max(self.height - bottom_pad - dp(10), dp(10))
            n = len(self.values)
            if n == 0:
                return
            
            total_w = max(self.width - pad_x * 2, dp(10))
            slot = total_w / n
            bar_w = max(slot * 0.7, dp(6))
            maxv = max(self.values) if max(self.values) > 0 else 1.0

            start_x = self.x + pad_x
            for i, val in enumerate(self.values):
                h = (val / maxv) * top_available if maxv > 0 else 0
                bx = start_x + i * slot + (slot - bar_w) / 2
                by = self.y + bottom_pad
                
                # Bar color
                if val == 0:
                    Color(0.3, 0.3, 0.3, 0.5)
                elif self.selected_index == i:
                    Color(0.95, 0.45, 0.15, 1)
                else:
                    Color(0.15, 0.6, 0.95, 1)
                
                Rectangle(pos=(bx, by), size=(bar_w, h))

                # Value text
                if val > 0:
                    txt = f"{val:,.0f}"
                    lbl = CoreLabel(text=txt, font_size=sp(8))
                    lbl.refresh()
                    tex = lbl.texture
                    tx = bx + (bar_w - tex.width) / 2
                    ty = by + h + dp(2)
                    Color(1, 1, 1, 1)
                    Rectangle(texture=tex, pos=(tx, ty), size=tex.size)

                # Label below
                label_text = str(self.labels[i]) if i < len(self.labels) else ""
                if label_text:
                    lbl2 = CoreLabel(text=label_text, font_size=sp(12))
                    lbl2.refresh()
                    tex2 = lbl2.texture
                    tx2 = bx + (bar_w - tex2.width) / 2
                    ty2 = self.y + dp(8)
                    Color(1, 1, 1, 1)
                    Rectangle(texture=tex2, pos=(tx2, ty2), size=tex2.size)

    def show_tooltip(self, idx, bx, by, bar_w, h):
        """Show tooltip on hover"""
        if self.tooltip:
            self.remove_widget(self.tooltip)
        val = self.values[idx]
        label = self.labels[idx] if idx < len(self.labels) else ""
        txt = f"{label}: {val:,.0f}"
        self.tooltip = Label(
            text=txt,
            size_hint=(None, None),
            font_size=sp(13),
            color=(1, 1, 1, 1),
            bold=True,
            background_color=(0.15, 0.15, 0.15, 0.95),
            padding=(dp(8), dp(4))
        )
        self.tooltip.pos = (bx + bar_w/2 - self.tooltip.width/2, by + h + dp(24))
        self.add_widget(self.tooltip)

    def hide_tooltip(self):
        """Hide tooltip"""
        if self.tooltip:
            self.remove_widget(self.tooltip)
            self.tooltip = None

    def on_touch_down(self, touch):
        """Handle touch down"""
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        
        pad_x = dp(16)
        n = len(self.values)
        if n == 0:
            return True
        
        total_w = max(self.width - pad_x * 2, dp(10))
        slot = total_w / n
        local_x = touch.x - (self.x + pad_x)
        idx = int(local_x // slot)
        
        if idx < 0 or idx >= n:
            return True

        if self.values[idx] == 0:
            return True

        # Toggle selection
        if self.selected_index == idx:
            self.selected_index = -1
            filtered = None
            sel = None
        else:
            self.selected_index = idx
            filtered = self._filter_expenses_for_index(idx)
            sel = idx

        self.dispatch('on_selection', sel, filtered)
        return True

    def on_touch_move(self, touch):
        """Handle touch move for tooltip"""
        if not self.collide_point(*touch.pos):
            self.hide_tooltip()
            return False
        
        pad_x = dp(16)
        n = len(self.values)
        if n == 0:
            self.hide_tooltip()
            return False
        
        total_w = max(self.width - pad_x * 2, dp(10))
        slot = total_w / n
        local_x = touch.x - (self.x + pad_x)
        idx = int(local_x // slot)
        
        if idx < 0 or idx >= n or self.values[idx] == 0:
            self.hide_tooltip()
            return False
        
        bar_w = max(slot * 0.7, dp(6))
        h = (self.values[idx] / max(self.values)) * max(self.height - dp(40) - dp(10), dp(10))
        bx = self.x + pad_x + idx * slot + (slot - bar_w) / 2
        by = self.y + dp(40)
        self.show_tooltip(idx, bx, by, bar_w, h)
        return True

    def on_touch_up(self, touch):
        """Handle touch up"""
        self.hide_tooltip()
        return super().on_touch_up(touch)

    def _filter_expenses_for_index(self, idx):
        """Filter expenses for selected bar index"""
        filtered = []
        for e in (self.expenses or []):
            ds = e.get("date", "")[:10]
            try:
                dt = datetime.strptime(ds, "%Y-%m-%d")
            except Exception:
                continue
            
            try:
                if self.mode == "Monthly":
                    month_idx = idx + 1
                    if dt.year == int(self.year) and dt.month == month_idx:
                        filtered.append(e)
                elif self.mode == "Daily":
                    day_idx = idx + 1
                    if dt.year == int(self.year) and dt.month == int(self.month) and dt.day == day_idx:
                        filtered.append(e)
             
            except Exception:
                continue
        
        return filtered

    def on_selection(self, index, expenses):
        """Event placeholder"""
        pass