# screens/activity_log_screen.py

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.app import App
from datetime import datetime

import utils.database as db
import utils.utils as utils
from widgets.common import show_popup, show_animated_popup
from widgets.long_press_row import LongPressRow


class ActivityLogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_items = []
        self.filtered_items = []
        self.current_search = ""
        self.current_sort = "Date (Newest)"
        self.show_mode = "All"
        self._items_loaded = False
    
    def on_enter(self):
        """Load items only if not already loaded"""
        if not self._items_loaded:
            self.refresh_items()
            self._items_loaded = True
    
    def refresh_items(self):
        """Load and display expenses and incomes"""
        un = App.get_running_app().logged_user
        
        # Get expenses
        exps = db.get_user_expenses(un)
        for e in exps:
            e['type'] = 'expense'
        
        # Get incomes
        incs = db.get_user_incomes(un)
        for i in incs:
            i['type'] = 'income'
        
        # Combine
        self.all_items = exps + incs
        self.apply_filters()
        self._items_loaded = True
    
    def toggle_show_mode(self):
        """Cycle through show modes: All -> Expenses -> Incomes -> All"""
        if self.show_mode == "All":
            self.show_mode = "Expenses"
        elif self.show_mode == "Expenses":
            self.show_mode = "Incomes"
        else:
            self.show_mode = "All"
        
        # Update filter button text
        if hasattr(self.ids, 'filter_button'):
            self.ids.filter_button.text = f"Show: {self.show_mode}"
        
        self.apply_filters()
    
    def on_search(self, query):
        """Handle search input"""
        self.current_search = query
        self.apply_filters()
    
    def clear_search(self):
        """Clear search input"""
        if hasattr(self.ids, 'search_input'):
            self.ids.search_input.text = ""
        self.current_search = ""
        self.apply_filters()
    
    def apply_sort(self, sort_type):
        """Apply sort to items"""
        self.current_sort = sort_type
        self.apply_filters()
    
    def apply_filters(self):
        """Apply search, filter, and sort"""
        items = self.all_items[:]
        
        # Filter by type
        if self.show_mode == "Expenses":
            items = [i for i in items if i['type'] == 'expense']
        elif self.show_mode == "Incomes":
            items = [i for i in items if i['type'] == 'income']
        
        # Search
        if self.current_search:
            q = self.current_search.lower().strip()
            items = [
                i for i in items
                if q in i['name'].lower()
                or (i['type'] == 'expense' and q in i.get('category', '').lower())
                or q in str(i['amount'])
                or q in i['date']
            ]
        
        # Sort
        if self.current_sort == "Date (Newest)":
            items = sorted(items, key=lambda x: x['date'], reverse=True)
        elif self.current_sort == "Date (Oldest)":
            items = sorted(items, key=lambda x: x['date'])
        elif self.current_sort == "Name (A-Z)":
            items = sorted(items, key=lambda x: x['name'].lower())
        elif self.current_sort == "Price (High-Low)":
            items = sorted(items, key=lambda x: x['amount'], reverse=True)
        elif self.current_sort == "Category (A-Z)":
            items = sorted(items, key=lambda x: x.get('category', '').lower())
        
        self.filtered_items = items
        self.display_items(items)
    
    def _get_date_grouping_info(self, items):
        """
        Analyze items to determine which ones are in date groups.
        Returns a dict mapping index -> {'is_grouped', 'is_first', 'is_last', 'group_size'}
        """
        if not items:
            return {}
        
        # Only apply grouping for date-based sorts
        is_date_sort = self.current_sort in ["Date (Newest)", "Date (Oldest)"]
        if not is_date_sort:
            return {i: {'is_grouped': False, 'is_first': False, 'is_last': False, 'group_size': 1} 
                    for i in range(len(items))}
        
        grouping = {}
        i = 0
        
        while i < len(items):
            current_date = items[i]['date']
            group_start = i
            group_size = 1
            
            # Find all consecutive items with the same date
            while i + 1 < len(items) and items[i + 1]['date'] == current_date:
                i += 1
                group_size += 1
            
            # Mark all items in this group
            is_grouped = group_size >= 2
            for j in range(group_start, i + 1):
                grouping[j] = {
                    'is_grouped': is_grouped,
                    'is_first': (j == group_start) and is_grouped,
                    'is_last': (j == i) and is_grouped,
                    'is_middle': (j != group_start and j != i) and is_grouped,
                    'group_size': group_size
                }
            
            i += 1
        
        return grouping
    
    def display_items(self, items):
        """Display expenses and incomes in list with date grouping"""
        if not hasattr(self.ids, 'expense_list'):
            return
        
        self.ids.expense_list.clear_widgets()
        
        if not items:
            eb = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(100), padding=dp(20))
            eb.add_widget(Label(
                text="No items found" if self.current_search else "No transactions recorded",
                color=(0.7, 0.7, 0.7, 1),
                font_size=sp(16)
            ))
            self.ids.expense_list.add_widget(eb)
        else:
            te, ti = 0, 0
            
            # Get grouping information
            grouping = self._get_date_grouping_info(items)
            
            for idx, itm in enumerate(items):
                if itm['type'] == 'expense':
                    te += itm["amount"]
                else:
                    ti += itm["amount"]
                
                # Get grouping info for this item
                group_info = grouping.get(idx, {'is_grouped': False, 'is_first': False, 
                                                 'is_last': False, 'is_middle': False})
                
                # Calculate corner radius based on position in group
                if group_info['is_grouped']:
                    if group_info['is_first']:
                        # First item: round top corners only
                        radius = [dp(12), dp(12), 0, 0]
                    elif group_info['is_last']:
                        # Last item: round bottom corners only
                        radius = [0, 0, dp(12), dp(12)]
                    else:
                        # Middle item: no rounding
                        radius = [0, 0, 0, 0]
                else:
                    # Single item: round all corners
                    radius = [dp(8)]
                
                # Create row with long press support
                row = LongPressRow(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(40),
                    padding=(dp(8), dp(4)),
                    spacing=dp(8)
                )
                row.item_data = itm
                row.bind(on_long_press=self.show_edit_delete_menu)
                
                # Background color based on type
                bgc = (0.06, 0.06, 0.06, 1) if itm['type'] == 'expense' else (0.06, 0.12, 0.08, 1)
                
                with row.canvas.before:
                    Color(*bgc)
                    row.bg_rect = RoundedRectangle(pos=row.pos, size=row.size, radius=radius)
                    row.bind(
                        pos=lambda o, v: setattr(o.bg_rect, 'pos', v),
                        size=lambda o, v: setattr(o.bg_rect, 'size', v)
                    )
                
                # Name
                nl = Label(
                    text=itm['name'],
                    size_hint_x=0.30,
                    halign="left",
                    valign="middle",
                    font_size=sp(12),
                    color=(1, 1, 1, 1)
                )
                nl.bind(size=lambda l, s: setattr(l, 'text_size', s))
                row.add_widget(nl)
                
                # Category or Income info
                if itm['type'] == 'expense':
                    cc = utils.get_category_color(itm.get('category', 'Other'))
                    ci = utils.get_category_icon(itm.get('category', 'Other'))
                    
                    cb = BoxLayout(size_hint_x=0.25, orientation="horizontal", spacing=dp(4))
                    cb.add_widget(Label(
                        text=ci,
                        size_hint_x=None,
                        width=dp(20),
                        font_size=sp(12)
                    ))
                    
                    clb = BoxLayout(size_hint_x=1)
                    with clb.canvas.before:
                        Color(*cc)
                        clb.color_rect = RoundedRectangle(pos=clb.pos, size=clb.size, radius=[dp(4)])
                        clb.bind(
                            pos=lambda o, v: setattr(o.color_rect, 'pos', v),
                            size=lambda o, v: setattr(o.color_rect, 'size', v)
                        )
                    
                    clb.add_widget(Label(
                        text=itm.get('category', 'Other'),
                        halign="center",
                        valign="middle",
                        font_size=sp(10),
                        color=(1, 1, 1, 1),
                        bold=True
                    ))
                    cb.add_widget(clb)
                    row.add_widget(cb)
                    
                    # Show income source
                    inn = "General" if not itm.get('income_id') else db.get_income_name(itm['income_id'])
                    row.add_widget(Label(
                        text=f"from: {inn}",
                        size_hint_x=0.20,
                        halign="center",
                        valign="middle",
                        font_size=sp(9),
                        color=(0.6, 0.8, 0.6, 1)
                    ))
                else:
                    # Income - show remaining percentage
                    rem = itm.get('remaining', itm['amount'])
                    pct = (rem / itm['amount'] * 100) if itm['amount'] > 0 else 0
                    row.add_widget(Label(
                        text=f"{pct:.0f}% left",
                        size_hint_x=0.45,
                        halign="center",
                        valign="middle",
                        font_size=sp(11),
                        color=(0.2, 0.9, 0.5, 1) if pct > 50 else (1.0, 0.8, 0.2, 1),
                        bold=True
                    ))
                
                # Date
                row.add_widget(Label(
                    text=itm['date'],
                    size_hint_x=0.18,
                    halign="center",
                    valign="middle",
                    font_size=sp(10),
                    color=(0.7, 0.7, 0.7, 1)
                ))
                
                # Amount
                ac = (0.2, 0.8, 0.4, 1) if itm['type'] == 'income' else (0.95, 0.35, 0.45, 1)
                al = Label(
                    text=utils.format_amount(itm['amount']),
                    size_hint_x=0.17,
                    halign="right",
                    valign="middle",
                    font_size=sp(12),
                    color=ac,
                    bold=True
                )
                al.bind(size=lambda l, s: setattr(l, 'text_size', s))
                row.add_widget(al)
                
                self.ids.expense_list.add_widget(row)
                
                # Add small spacing between groups (only after last item of a group)
                if group_info['is_grouped'] and group_info['is_last'] and idx < len(items) - 1:
                    spacer = Widget(size_hint_y=None, height=dp(4))
                    self.ids.expense_list.add_widget(spacer)
            
            # Update total label
            if hasattr(self.ids, 'total_label'):
                ct = f" ({len(items)} of {len(self.all_items)})" if self.current_search or self.show_mode != "All" else f" ({len(items)})"
                if self.show_mode == "Expenses":
                    self.ids.total_label.text = f"Total Expenses: {utils.format_amount(te)}{ct}"
                elif self.show_mode == "Incomes":
                    self.ids.total_label.text = f"Total Income: {utils.format_amount(ti)}{ct}"
                else:
                    self.ids.total_label.text = f"Income: {utils.format_amount(ti)} | Expenses: {utils.format_amount(te)}{ct}"
    
    def show_edit_delete_menu(self, row_widget):
        """Show edit/delete menu when row is long-pressed"""
        itm = row_widget.item_data
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15))
        
        typ = "Income" if itm['type'] == 'income' else "Expense"
        content.add_widget(Label(
            text=f"Manage {typ}: {itm['name']}",
            size_hint_y=None,
            height=dp(30),
            font_size=sp(16),
            bold=True,
            color=(1, 1, 1, 1)
        ))
        
        # Details
        if itm['type'] == 'expense':
            det = f"{itm.get('category', 'N/A')} • {itm['date']} • {utils.format_amount(itm['amount'])}"
        else:
            rem = itm.get('remaining', itm['amount'])
            det = f"{itm['date']} • {utils.format_amount(itm['amount'])} • {utils.format_amount(rem)} left"
        
        content.add_widget(Label(
            text=det,
            size_hint_y=None,
            height=dp(25),
            font_size=sp(12),
            color=(0.7, 0.7, 0.7, 1)
        ))
        content.add_widget(Widget(size_hint_y=None, height=dp(10)))
        
        # Edit button
        eb = Button(
            text=f"Edit {typ}",
            size_hint_y=None,
            height=dp(50),
            background_color=(0.2, 0.5, 0.8, 1),
            font_size=sp(15)
        )
        content.add_widget(eb)
        
        # Delete button
        db_btn = Button(
            text=f"🗑 Delete {typ}",
            size_hint_y=None,
            height=dp(50),
            background_color=(0.8, 0.2, 0.2, 1),
            font_size=sp(15)
        )
        content.add_widget(db_btn)
        
        # Cancel button
        cb = Button(
            text="Cancel",
            size_hint_y=None,
            height=dp(45),
            background_color=(0.3, 0.3, 0.3, 1),
            font_size=sp(14)
        )
        content.add_widget(cb)
        
        popup = Popup(
            title="",
            content=content,
            size_hint=(0.85, None),
            height=dp(320),
            separator_height=0,
            auto_dismiss=True
        )
        
        def do_edit(inst):
            popup.dismiss()
            if itm['type'] == 'expense':
                self.edit_expense(itm)
            else:
                self.edit_income(itm)
        
        def do_delete(inst):
            popup.dismiss()
            if itm['type'] == 'expense':
                self.confirm_delete_expense(itm)
            else:
                self.confirm_delete_income(itm)
        
        eb.bind(on_release=do_edit)
        db_btn.bind(on_release=do_delete)
        cb.bind(on_release=lambda x: popup.dismiss())
        show_animated_popup(popup)
    
    def edit_expense(self, exp):
        """Edit expense dialog"""
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        
        content.add_widget(Label(
            text="Name:",
            size_hint_y=None,
            height=dp(25),
            halign="left",
            color=(1, 1, 1, 1)
        ))
        ni = TextInput(text=exp['name'], multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(ni)
        
        cats = db.get_categories(App.get_running_app().logged_user)
        content.add_widget(Label(
            text="Category:",
            size_hint_y=None,
            height=dp(25),
            halign="left",
            color=(1, 1, 1, 1)
        ))
        cs = Spinner(
            text=exp.get('category', 'Other'),
            values=cats,
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(cs)
        
        content.add_widget(Label(
            text="Date (YYYY-MM-DD):",
            size_hint_y=None,
            height=dp(25),
            halign="left",
            color=(1, 1, 1, 1)
        ))
        di = TextInput(text=exp['date'], multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(di)
        
        content.add_widget(Label(
            text="Amount:",
            size_hint_y=None,
            height=dp(25),
            halign="left",
            color=(1, 1, 1, 1)
        ))
        ai = TextInput(
            text=str(exp['amount']),
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(ai)
        
        # Income spinner
        incs = db.get_user_incomes(App.get_running_app().logged_user)
        iv = ["General (No specific income)"]
        for inc in incs:
            iv.append(f"{inc['name']} (ID: {inc['id']})")
        
        cit = "General (No specific income)"
        if exp.get('income_id'):
            cit = f"{db.get_income_name(exp['income_id'])} (ID: {exp['income_id']})"
        
        content.add_widget(Label(
            text="Income Source:",
            size_hint_y=None,
            height=dp(25),
            halign="left",
            color=(1, 1, 1, 1)
        ))
        isp = Spinner(text=cit, values=iv, size_hint_y=None, height=dp(40))
        content.add_widget(isp)
        
        br = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        canb = Button(text="Cancel", background_color=(0.3, 0.3, 0.3, 1))
        savb = Button(text="Save", background_color=(0.2, 0.6, 0.8, 1))
        br.add_widget(canb)
        br.add_widget(savb)
        content.add_widget(br)
        
        popup = Popup(title="Edit Expense", content=content, size_hint=(0.85, 0.8))
        
        def do_save(inst):
            try:
                nn = ni.text.strip()
                nc = cs.text
                nd = di.text.strip()
                na = utils.parse_amount(ai.text.strip())
                nii = None
                it = isp.text
                if not it.startswith("General"):
                    nii = int(it.split("ID: ")[1].rstrip(")"))
                if not nn or not nc or not nd or na <= 0:
                    return show_popup("Error", "Please fill all fields correctly", size_hint=(0.6, 0.35))
                datetime.strptime(nd, "%Y-%m-%d")
                db.update_expense(exp['id'], nn, nc, nd, na, nii)
                popup.dismiss()
                self.refresh_items()
                App.get_running_app().refresh_all_screens()
                show_popup("Success", "Expense updated!", size_hint=(0.6, 0.35))
            except Exception as e:
                show_popup("Error", f"Failed to update: {str(e)}", size_hint=(0.6, 0.35))
        
        canb.bind(on_release=lambda x: popup.dismiss())
        savb.bind(on_release=do_save)
        show_animated_popup(popup)
    
    def edit_income(self, inc):
        """Edit income dialog"""
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        
        content.add_widget(Label(
            text="Name:",
            size_hint_y=None,
            height=dp(25),
            halign="left",
            color=(1, 1, 1, 1)
        ))
        ni = TextInput(text=inc['name'], multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(ni)
        
        content.add_widget(Label(
            text="Date (YYYY-MM-DD):",
            size_hint_y=None,
            height=dp(25),
            halign="left",
            color=(1, 1, 1, 1)
        ))
        di = TextInput(text=inc['date'], multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(di)
        
        content.add_widget(Label(
            text="Amount:",
            size_hint_y=None,
            height=dp(25),
            halign="left",
            color=(1, 1, 1, 1)
        ))
        ai = TextInput(
            text=str(inc['amount']),
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(ai)
        
        content.add_widget(Label(
            text=f"Remaining: {utils.format_amount(inc.get('remaining', inc['amount']))}",
            size_hint_y=None,
            height=dp(25),
            color=(0.7, 0.7, 0.7, 1)
        ))
        
        br = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        canb = Button(text="Cancel", background_color=(0.3, 0.3, 0.3, 1))
        savb = Button(text="Save", background_color=(0.2, 0.6, 0.8, 1))
        br.add_widget(canb)
        br.add_widget(savb)
        content.add_widget(br)
        
        popup = Popup(title="Edit Income", content=content, size_hint=(0.85, 0.65))
        
        def do_save(inst):
            try:
                nn = ni.text.strip()
                nd = di.text.strip()
                na = utils.parse_amount(ai.text.strip())
                if not nn or not nd or na <= 0:
                    return show_popup("Error", "Please fill all fields correctly", size_hint=(0.6, 0.35))
                datetime.strptime(nd, "%Y-%m-%d")
                db.update_income(inc['id'], nn, na, nd)
                popup.dismiss()
                self.refresh_items()
                App.get_running_app().refresh_all_screens()
                show_popup("Success", "Income updated!", size_hint=(0.6, 0.35))
            except Exception as e:
                show_popup("Error", f"Failed to update: {str(e)}", size_hint=(0.6, 0.35))
        
        canb.bind(on_release=lambda x: popup.dismiss())
        savb.bind(on_release=do_save)
        show_animated_popup(popup)
    
    def confirm_delete_expense(self, exp):
        """Confirm expense deletion"""
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(Label(
            text=f"Delete expense '{exp['name']}'?",
            font_size=sp(16),
            bold=True
        ))
        content.add_widget(Label(
            text="This action cannot be undone.",
            font_size=sp(13),
            color=(0.8, 0.8, 0.8, 1)
        ))
        
        br = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
        nb = Button(text="Cancel", background_color=(0.3, 0.3, 0.3, 1))
        yb = Button(text="Delete", background_color=(0.8, 0.2, 0.2, 1))
        br.add_widget(nb)
        br.add_widget(yb)
        content.add_widget(br)
        
        popup = Popup(title="Confirm Delete", content=content, size_hint=(0.8, None), height=dp(220))
        
        def do_delete(inst):
            db.delete_expense(exp["id"])
            popup.dismiss()
            self.refresh_items()
            App.get_running_app().refresh_all_screens()
        
        nb.bind(on_release=lambda x: popup.dismiss())
        yb.bind(on_release=do_delete)
        show_animated_popup(popup)
    
    def confirm_delete_income(self, inc):
        """Confirm income deletion"""
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(Label(
            text=f"Delete income '{inc['name']}'?",
            font_size=sp(16),
            bold=True
        ))
        content.add_widget(Label(
            text="All linked expenses will become 'General'.\nThis action cannot be undone.",
            font_size=sp(13),
            color=(0.8, 0.8, 0.8, 1)
        ))
        
        br = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
        nb = Button(text="Cancel", background_color=(0.3, 0.3, 0.3, 1))
        yb = Button(text="Delete", background_color=(0.8, 0.2, 0.2, 1))
        br.add_widget(nb)
        br.add_widget(yb)
        content.add_widget(br)
        
        popup = Popup(title="Confirm Delete", content=content, size_hint=(0.8, None), height=dp(240))
        
        def do_delete(inst):
            db.delete_income(inc["id"])
            popup.dismiss()
            self.refresh_items()
            App.get_running_app().refresh_all_screens()
        
        nb.bind(on_release=lambda x: popup.dismiss())
        yb.bind(on_release=do_delete)
        show_animated_popup(popup)