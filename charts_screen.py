from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line, Rectangle
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.app import App
from datetime import datetime
import calendar
import os
import traceback
import math

import utils.database as db
import utils.chart_utils as chart_utils
import utils.utils as utils
from widgets.interactive_charts import InteractiveBarChart


class ChartsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_expenses = []
        self.current_category_filter = None
        self.sort_mode = 'name'
        self.selected_category = None
        self._last_scroll_y = 1.0
        self._scroll_event = None
        self._charts_generated = False
        self.legend_metadata = None
        self.debug_mode = True # Enable visual debugging
    
    def generate_charts(self):
        """Generate charts with debouncing"""
        if hasattr(self, '_chart_generation_scheduled'):
            Clock.unschedule(self._chart_generation_scheduled)
        self._chart_generation_scheduled = Clock.schedule_once(
            lambda dt: self._do_generate_charts(),
            0.1
        )
    
    def _do_generate_charts(self):
        """Actually generate the charts"""
        un = App.get_running_app().logged_user
        
        try:
            mode = getattr(self, 'current_view_mode', 'Daily')
            try:
                yr = int(self.ids.year_spinner.text) if hasattr(self.ids, 'year_spinner') and self.ids.year_spinner.text else datetime.now().year
            except Exception:
                yr = datetime.now().year
            
            mo = None
            if mode == "Daily":
                mn = self.ids.month_spinner.text if hasattr(self.ids, 'month_spinner') else ""
                try:
                    mo = utils.get_month_number(mn)
                    if not (1 <= int(mo) <= 12):
                        mo = datetime.now().month
                except Exception:
                    mo = datetime.now().month
            
            exps = db.filter_expenses_by_period(un, yr, mo if mode == "Daily" else None)
            
            if mode == "Monthly":
                mt, _ = chart_utils.aggregate_by_month(exps, yr)
                lbls = [calendar.month_abbr[i+1] for i in range(12)]
                vals = mt
            else:  # Daily mode
                if not mo:
                    mo = datetime.now().month
                dt, _ = chart_utils.aggregate_by_day(exps, yr, mo)
                lbls = [str(i+1) if (i+1) % 2 == 1 else "" for i in range(len(dt))]
                vals = dt
            
            if len(lbls) != len(vals):
                if len(vals) < len(lbls):
                    vals = vals + [0] * (len(lbls) - len(vals))
                else:
                    lbls = lbls + [""] * (len(vals) - len(lbls))
            
            cw = self.ids.get('chart_widget')
            if cw:
                cw.set_data(lbls, vals, exps, year=yr, month=mo or 0, mode=mode)
            
            self.current_expenses = exps
            self.current_category_filter = None
            self.selected_category = None
            self.update_expense_table(exps)
            
            cd = chart_utils.aggregate_by_category(exps)
            if cd:
                self._generate_donut_chart(cd, title="Expenses by Category")
            else:
                if hasattr(self.ids, 'pie_image'):
                    self.ids.pie_image.source = ""
                    
        except Exception as e:
            print("Error generating charts:", e)
            print(traceback.format_exc())
    
    def on_enter(self):
        """Initialize charts screen"""
        if not self._charts_generated:
            if hasattr(self.ids, 'charts_scroll_view'):
                self.ids.charts_scroll_view.scroll_y = 1.0
            
            cy, cm = datetime.now().year, datetime.now().month
            
            if hasattr(self.ids, 'year_spinner'):
                yrs = utils.get_year_range(cy)
                self.ids.year_spinner.values = yrs if yrs else [str(cy)]
                self.ids.year_spinner.text = str(cy) if str(cy) in (yrs or []) else (yrs[0] if yrs else str(cy))
            
            if hasattr(self.ids, 'month_spinner'):
                mos = utils.get_month_list()
                self.ids.month_spinner.values = mos if mos else ["January"]
                self.ids.month_spinner.text = mos[min(max(0, cm - 1), len(mos) - 1)] if mos else "January"
            
            if not hasattr(self, 'current_view_mode'):
                self.current_view_mode = "Daily"
            
            # Update the view mode button text to match current mode
            if hasattr(self.ids, 'view_mode_button'):
                self.ids.view_mode_button.text = f"View: {self.current_view_mode}"
            
            # Set month spinner state based on initial mode
            if hasattr(self.ids, 'month_spinner'):
                self.ids.month_spinner.disabled = (self.current_view_mode == "Monthly")
            
            if hasattr(self.ids, 'chart_widget'):
                self.ids.chart_widget.bind(on_selection=self._on_bar_selection)
            
            if hasattr(self.ids, 'pie_image'):
                self.ids.pie_image.bind(on_touch_down=self._on_pie_touch)
            
            self._update_sort_button()
            
            if hasattr(self.ids, 'charts_scroll_view'):
                self.ids.charts_scroll_view.bind(scroll_y=self._on_scroll)
            
            self.generate_charts()
            self._charts_generated = True
    
    def on_leave(self):
        """Cleanup when leaving screen"""
        if hasattr(self.ids, 'month_spinner'):
            self.ids.month_spinner.disabled = True
        if self._scroll_event:
            self._scroll_event.cancel()
            self._scroll_event = None
    
    def _on_scroll(self, instance, value):
        """Monitor scroll position"""
        self._last_scroll_y = value
        if self._scroll_event:
            self._scroll_event.cancel()
        self._scroll_event = Clock.schedule_once(self._auto_snap_scroll, 0.3)
    
    def _auto_snap_scroll(self, dt):
        """Auto-snap to nearest section"""
        if not hasattr(self.ids, 'charts_scroll_view'):
            return
        sy = self._last_scroll_y
        tgt = 1.0 if sy >= 0.7 else 0.5 if sy >= 0.3 else 0.0
        if abs(sy - tgt) > 0.05:
            Animation(scroll_y=tgt, d=0.25, t='out_quad').start(self.ids.charts_scroll_view)

    def toggle_view_mode(self):
        """Toggle between Monthly and Daily view"""
        if not hasattr(self, 'current_view_mode'):
            self.current_view_mode = "Daily"

        # Cycle through modes: Daily -> Monthly -> Daily
        if self.current_view_mode == "Daily":
            self.current_view_mode = "Monthly"
        else:
            self.current_view_mode = "Daily"

        # Update button text 
        if hasattr(self.ids, 'view_mode_button'):
            self.ids.view_mode_button.text = f"View: {self.current_view_mode}"

        # Enable/disable month spinner based on mode
        if hasattr(self.ids, 'month_spinner'):
            self.ids.month_spinner.disabled = (
                self.current_view_mode == "Monthly"
            )

        self._scroll_to_top()
        self.generate_charts()
        
    def _scroll_to_top(self):
        """Scroll to top smoothly"""
        try:
            if hasattr(self.ids, 'charts_scroll_view'):
                Animation(scroll_y=1, d=0.3, t='out_quad').start(self.ids.charts_scroll_view)
        except Exception as e:
            print(f"Scroll error: {e}")
    
    def _scroll_to_position(self, position):
        """Scroll to specific position"""
        try:
            if hasattr(self.ids, 'charts_scroll_view'):
                Animation(scroll_y=position, d=0.3, t='out_quad').start(self.ids.charts_scroll_view)
        except Exception as e:
            print(f"Scroll error: {e}")
    
    def _generate_donut_chart(self, cat_data, title="Expenses by Category", explode_category=None):
        """Generate donut chart and store legend metadata"""
        try:
            expl = None
            if explode_category:
                cats = list(cat_data.keys())
                expl = [0.15 if c == explode_category else 0 for c in cats]
            
            cfig, legend_metadata = chart_utils.create_pie_chart_donut(cat_data, explode=expl)
            
            self.legend_metadata = legend_metadata
            
            if cfig:
                pp = os.path.abspath("temp_pie.png")
                chart_utils.save_figure_to_image(cfig, pp)
                
                def reload_image(dt):
                    if hasattr(self.ids, 'pie_image'):
                        self.ids.pie_image.source = ""
                        Clock.schedule_once(lambda dt: self._set_pie_source(pp), 0.05)
                
                Clock.schedule_once(reload_image, 0.1)
        except Exception as e:
            print(f"Error generating donut chart: {e}")
            print(traceback.format_exc())
    
    def _set_pie_source(self, path):
        """Set pie image source"""
        try:
            if hasattr(self.ids, 'pie_image'):
                self.ids.pie_image.source = path
                self.ids.pie_image.reload()
        except Exception as e:
            print(f"Error setting pie source: {e}")
    
    def _draw_debug_overlay(self, instance, touch, display_width, display_height, offset_x, offset_y, legend_items):
        """Draw visual debugging overlay on the image"""
        if not self.debug_mode:
            return
        
        # Clear previous debug drawings
        if hasattr(instance, 'debug_canvas'):
            instance.canvas.after.remove(instance.debug_canvas)
        
   
    
    def _on_bar_selection(self, instance, index, filtered_expenses):
        """Handle bar chart selection"""
        try:
            if index is None:
                self.selected_category = None
                self.current_expenses = db.filter_expenses_by_period(
                    App.get_running_app().logged_user,
                    int(self.ids.year_spinner.text) if hasattr(self.ids, 'year_spinner') else datetime.now().year,
                    None
                )
                self.update_expense_table(self.current_expenses)
                cd = chart_utils.aggregate_by_category(self.current_expenses)
                if cd:
                    self._generate_donut_chart(cd, title="Expenses by Category")
                return
            
            self.current_expenses = filtered_expenses or []
            self.current_category_filter = None
            self.selected_category = None
            self.update_expense_table(filtered_expenses or [])
            
            cd = chart_utils.aggregate_by_category(filtered_expenses or [])
            if not cd:
                if hasattr(self.ids, 'pie_image'):
                    self.ids.pie_image.source = ""
                return
            
            self._generate_donut_chart(cd, title="Selected Period Breakdown")
            Clock.schedule_once(lambda dt: self._scroll_to_position(0.5), 0.1)
        except Exception as e:
            print(f"Error in bar selection handler: {e}")
            print(traceback.format_exc())

    def _on_pie_touch(self, instance, touch):
        """Handle pie chart touch detection (both donut and legend)"""
        if not instance.collide_point(*touch.pos):
            return False
        if hasattr(touch, 'button') and touch.button in ['scrollup', 'scrolldown']:
            return False
        
        # Get image widget bounds
        ix, iy, iw, ih = instance.pos[0], instance.pos[1], instance.size[0], instance.size[1]
        
        # Get the actual image dimensions from the texture
        if not instance.texture:
            return False
        
        img_width = instance.texture.width
        img_height = instance.texture.height
        
        # Calculate how the image is scaled and positioned within the widget
        widget_aspect = iw / ih if ih > 0 else 1
        img_aspect = img_width / img_height if img_height > 0 else 1
        
        if widget_aspect > img_aspect:
            # Widget is wider - image is letterboxed horizontally
            display_height = ih
            display_width = ih * img_aspect
            offset_x = (iw - display_width) / 2
            offset_y = 0
        else:
            # Widget is taller - image is letterboxed vertically
            display_width = iw
            display_height = iw / img_aspect
            offset_x = 0
            offset_y = (ih - display_height) / 2
        
        # Transform touch coordinates to image space
        rel_x = touch.x - ix - offset_x
        rel_y = touch.y - iy - offset_y
        
        # Check if touch is within displayed image bounds
        if rel_x < 0 or rel_x > display_width or rel_y < 0 or rel_y > display_height:
            return False
        
        # Convert to normalized coordinates (0-1 range in image space)
        norm_x = rel_x / display_width
        norm_y = rel_y / display_height
        
     
        # Check if touch is in legend area (right half)
        if norm_x >= 0.5:
            legend_left = ix + offset_x + (display_width * 0.5)
            legend_width = display_width * 0.5
            legend_bottom = iy + offset_y
            legend_height = display_height
            
            return self._handle_legend_touch(instance, touch,
                                            legend_left, legend_bottom,
                                            legend_width, legend_height,
                                            display_width, display_height,
                                            offset_x, offset_y)
        
        # Touch is in pie area (left half)
        pie_display_left = ix + offset_x
        pie_display_width = display_width * 0.5
        pie_display_height = display_height
        
        title_padding_ratio = 0.05
        pie_drawable_top = pie_display_height * (1 - title_padding_ratio)
        pie_drawable_height = pie_drawable_top
        
        pie_diameter = min(pie_display_width, pie_drawable_height) * 0.95
        
        cx = pie_display_left + (pie_display_width / 2)
        cy = iy + offset_y + (pie_drawable_height / 2)
        
        dx = touch.x - cx
        dy = touch.y - cy
        dist = math.sqrt(dx * dx + dy * dy)
        
        outer_radius = pie_diameter / 2
        inner_radius = outer_radius * 0.55  
        
        if dist < inner_radius or dist > outer_radius:
            if self.selected_category:
                self.selected_category = None
                cd = chart_utils.aggregate_by_category(self.current_expenses)
                self._generate_donut_chart(cd, title="")
                self.update_expense_table(self.current_expenses)
            return False
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = (90 - math.degrees(angle_rad)) % 360
        
        cd = chart_utils.aggregate_by_category(self.current_expenses)
        if not cd:
            return False
        
        total = sum(cd.values())
        cumulative_angle = 0
        for category, amount in cd.items():
            slice_angle = (amount / total) * 360
            if cumulative_angle <= angle_deg < cumulative_angle + slice_angle:
                self._toggle_category_selection(category)
                break
            cumulative_angle += slice_angle
        
        return True

    def _handle_legend_touch(self, instance, touch, legend_x, legend_y, legend_width, legend_height,
                            display_width, display_height, offset_x, offset_y):
        """Handle touches in the legend area using actual matplotlib legend metadata"""
        cd = chart_utils.aggregate_by_category(self.current_expenses)
        if not cd:
            return False
        
        if not hasattr(self, 'legend_metadata') or not self.legend_metadata:
            print("Warning: No legend metadata available")
            return False
        
        metadata = self.legend_metadata
        legend_items = metadata.get('items', [])
        
        if not legend_items:
            print("Warning: No legend items in metadata")
            return False
        
        # Draw debug overlay
        if self.debug_mode:
            self._draw_debug_overlay(instance, touch, display_width, display_height, 
                                    offset_x, offset_y, legend_items)
        
        # Get image widget bounds
        ix, iy = instance.pos[0], instance.pos[1]
        
        # Transform touch coordinates to image space
        rel_x = touch.x - ix - offset_x
        rel_y = touch.y - iy - offset_y
        
        # Convert to figure coordinates (0-1 range)
        fig_x = rel_x / display_width
        fig_y = rel_y / display_height
        
        
        # Check each legend item's bounding box
        for item in legend_items:
            bbox = item['bbox']
            x0, y0, width, height = bbox
            x1 = x0 + width
            y1 = y0 + height
            
            # Add padding for easier clicking
            padding = 0.02
            x0 -= padding
            y0 -= padding
            x1 += padding
            y1 += padding
            
         
            if x0 <= fig_x <= x1 and y0 <= fig_y <= y1:
                category = item['category']       
                self._toggle_category_selection(category)
                return True
        
        print("No legend item clicked")
        if self.selected_category:
            self.selected_category = None
            cd = chart_utils.aggregate_by_category(self.current_expenses)
            self._generate_donut_chart(cd, title="")
            self.update_expense_table(self.current_expenses)
        
        return False
        
    def _toggle_category_selection(self, category):
        """Toggle selection of a category"""
        from kivy.clock import Clock
        
        cd = chart_utils.aggregate_by_category(self.current_expenses)
        
        if self.selected_category == category:
            self.selected_category = None
            self.current_category_filter = None
            self._generate_donut_chart(cd, title="")
            self.update_expense_table(self.current_expenses)
        else:
            self.selected_category = category
            self.current_category_filter = category
            filtered = [e for e in self.current_expenses if e.get('category') == category]
            self.update_expense_table(filtered)
            self._generate_donut_chart(cd, title="", explode_category=category)
            Clock.schedule_once(lambda dt: self._scroll_to_position(0.0), 0.1)

    def update_expense_table(self, expenses):
        """Update expense table display"""
        if not hasattr(self.ids, 'expense_table'):
            return
        
        self.ids.expense_table.clear_widgets()
        
        if not expenses:
            eb = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(80), padding=dp(10))
            eb.add_widget(Label(
                text="No expenses to display",
                color=(0.6, 0.6, 0.6, 1),
                font_size=sp(10)
            ))
            self.ids.expense_table.add_widget(eb)
            return
        
        for exp in expenses:
            row = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(28),
                padding=(dp(4), dp(1)),
                spacing=dp(2)
            )
            
            with row.canvas.before:
                Color(0.06, 0.06, 0.06, 1)
                row.bg_rect = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(4)])
                row.bind(
                    pos=lambda o, v: setattr(o.bg_rect, 'pos', v),
                    size=lambda o, v: setattr(o.bg_rect, 'size', v)
                )
            
            nl = Label(
                text=exp['name'],
                size_hint_x=0.30,
                halign="left",
                valign="middle",
                font_size=sp(8),
                color=(1, 1, 1, 1)
            )
            nl.bind(size=lambda l, s: setattr(l, 'text_size', s))
            row.add_widget(nl)
            
            cl = Label(
                text=exp['category'],
                size_hint_x=0.25,
                halign="left",
                valign="middle",
                font_size=sp(8),
                color=(0.8, 0.8, 0.8, 1)
            )
            cl.bind(size=lambda l, s: setattr(l, 'text_size', s))
            row.add_widget(cl)
            
            al = Label(
                text=utils.format_amount(exp['amount']),
                size_hint_x=0.25,
                halign="right",
                valign="middle",
                font_size=sp(8),
                color=(0.2, 0.8, 0.4, 1),
                bold=True
            )
            al.bind(size=lambda l, s: setattr(l, 'text_size', s))
            row.add_widget(al)
            
            self.ids.expense_table.add_widget(row)
    
    def toggle_sort_mode(self):
        """Toggle sort mode"""
        if self.sort_mode == 'name':
            self.sort_mode = 'category'
        elif self.sort_mode == 'category':
            self.sort_mode = 'amount'
        else:
            self.sort_mode = 'name'
        
        self._update_sort_button()
        self.sort_expenses(self.sort_mode)
    
    def _update_sort_button(self):
        """Update sort button text"""
        if hasattr(self.ids, 'sort_button'):
            stm = {
                'name': 'Sort by: Name',
                'category': 'Sort by: Category',
                'amount': 'Sort by: Amount'
            }
            self.ids.sort_button.text = stm.get(self.sort_mode, 'Sort by: Name')
    
    def sort_expenses(self, sort_by):
        """Sort expenses"""
        if not self.current_expenses:
            return
        
        if sort_by == 'name':
            se = sorted(self.current_expenses, key=lambda x: x.get('name', '').lower())
        elif sort_by == 'category':
            se = sorted(self.current_expenses, key=lambda x: x.get('category', '').lower())
        elif sort_by == 'amount':
            se = sorted(self.current_expenses, key=lambda x: x.get('amount', 0), reverse=True)
        else:
            se = self.current_expenses
        
        if self.current_category_filter:
            se = [e for e in se if e.get('category') == self.current_category_filter]
        
        self.update_expense_table(se)