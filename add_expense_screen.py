# screens/add_expense_screen.py

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Ellipse, RoundedRectangle
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.app import App
from datetime import datetime

import utils.database as db
import utils.utils as utils
from widgets.common import show_popup, show_animated_popup


class AddExpenseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_expense_mode = True  # True = Expense, False = Income
    
    def on_enter(self):
        """Initialize screen when entering"""
        un = App.get_running_app().logged_user
        
        # Setup category spinner
        if hasattr(self.ids, 'category_spinner'):
            cats = db.get_categories(un)
            self.ids.category_spinner.values = cats
            if cats:
                self.ids.category_spinner.text = cats[0]
        
        # Setup income spinner
        if hasattr(self.ids, 'income_spinner'):
            self.refresh_income_spinner()
        
        # Set default date
        if hasattr(self.ids, 'date_input'):
            self.ids.date_input.text = utils.get_current_date()
        
        # Update mode display
        self.update_mode_display()
        
        # Scroll to top
        def scroll_to_top(dt):
            for w in self.walk():
                if w.__class__.__name__ == 'ScrollView':
                    w.scroll_y = 1.0
                    break
        Clock.schedule_once(scroll_to_top, 0.1)
            
    def toggle_mode(self):
        """Toggle between Expense and Income mode"""
        self.is_expense_mode = not self.is_expense_mode
        self.update_mode_display()

    def update_mode_display(self):
        """Update UI based on current mode"""
        # Update mode button text
        if hasattr(self.ids, 'mode_button'):
            mode_text = "Expense" if self.is_expense_mode else "Income"
            self.ids.mode_button.text = f"Type: {mode_text}"

        # Show/hide category row (only for expenses)
        if hasattr(self.ids, 'category_row'):
            if self.is_expense_mode:
                self.ids.category_row.opacity = 1
                self.ids.category_row.disabled = False
                self.ids.category_row.height = dp(80)
                for c in self.ids.category_row.children:
                    c.disabled = False
            else:
                self.ids.category_row.disabled = True
                self.ids.category_row.opacity = 0
                self.ids.category_row.height = 0
                for c in self.ids.category_row.children:
                    c.disabled = True

        # Show/hide income row
        if hasattr(self.ids, 'income_row'):
            if self.is_expense_mode:
                self.ids.income_row.opacity = 1
                self.ids.income_row.disabled = False
                self.ids.income_row.height = dp(80)
                for c in self.ids.income_row.children:
                    c.disabled = False
            else:
                self.ids.income_row.disabled = True
                self.ids.income_row.opacity = 0
                self.ids.income_row.height = 0
                for c in self.ids.income_row.children:
                    c.disabled = True

        # Reset scroll and update name input
        def reset_scroll_and_input(dt):
            # Scroll to top
            for w in self.walk():
                if w.__class__.__name__ == 'ScrollView':
                    w.scroll_y = 1.0
                    break

            # Update name input
            if hasattr(self.ids, 'name_input'):
                self.ids.name_input.disabled = False
                self.ids.name_input.opacity = 1

                if self.is_expense_mode:
                    self.ids.name_input.hint_text = (
                        "e.g., Lunch, Gas, Groceries"
                    )
                else:
                    self.ids.name_input.hint_text = (
                        "e.g., Salary, Allowance, Bonus"
                    )

        Clock.schedule_once(reset_scroll_and_input, 0.15)    
        
        # Reset scroll and update name input
        def reset_scroll_and_input(dt):
            # Scroll to top
            for w in self.walk():
                if w.__class__.__name__ == 'ScrollView':
                    w.scroll_y = 1.0
                    break
            
            # Update name input
            if hasattr(self.ids, 'name_input'):
                self.ids.name_input.disabled = False
                self.ids.name_input.opacity = 1
                
                # Update hint text based on mode
                if self.is_expense_mode:
                    self.ids.name_input.hint_text = "e.g., Lunch, Gas, Groceries"
                else:
                    self.ids.name_input.hint_text = "e.g., Salary, Allowance, Bonus"
        
        Clock.schedule_once(reset_scroll_and_input, 0.15)
    
    def refresh_income_spinner(self):
        """Refresh the income spinner with current incomes"""
        if not hasattr(self.ids, 'income_spinner'):
            return
        
        un = App.get_running_app().logged_user
        incs = db.get_user_incomes(un)
        
        iv = ["General (No specific income)"]
        for inc in incs:
            if inc['remaining'] > 0:
                iv.append(f"{inc['name']} (₱{inc['remaining']:.2f} left)")
        
        self.ids.income_spinner.values = iv
        self.ids.income_spinner.text = iv[0]
    
    def save_entry(self):
        """Save expense or income"""
        if self.is_expense_mode:
            self.save_expense()
        else:
            self.save_income()
    
    def save_expense(self):
        """Save expense with income tracking"""
        app = App.get_running_app()
        un = app.logged_user
        
        nm = self.ids.name_input.text.strip() or "Expense"
        cat = self.ids.category_spinner.text
        dt = self.ids.date_input.text.strip()
        amt_str = self.ids.amount_input.text.strip()
        
        if not cat or not amt_str:
            return show_popup("Error", "Please fill category and amount")
        
        # Validate date
        try:
            datetime.strptime(dt, "%Y-%m-%d")
        except ValueError:
            return show_popup("Error", "Invalid date format. Use YYYY-MM-DD")
        
        # Validate amount
        try:
            amt = utils.parse_amount(amt_str)
            if amt <= 0:
                raise ValueError("Amount must be positive")
        except Exception as e:
            return show_popup("Error", str(e))
        
        # Get selected income
        inc_id = None
        if hasattr(self.ids, 'income_spinner'):
            it = self.ids.income_spinner.text
            if not it.startswith("General"):
                inn = it.split(" (")[0]
                incs = db.get_user_incomes(un)
                for inc in incs:
                    if inc['name'] == inn:
                        inc_id = inc['id']
                        if inc['remaining'] < amt:
                            return show_popup(
                                "Warning",
                                f"Not enough remaining in {inn}!\n"
                                f"Remaining: {utils.format_amount(inc['remaining'])}\n"
                                f"Expense: {utils.format_amount(amt)}"
                            )
                        break
        
        # Save expense
        db.add_expense(un, nm, cat, dt, amt, inc_id)
        show_popup("Success", "Expense saved!")
        
        # Refresh all screens
        app.refresh_all_screens()
        
        # Clear inputs
        self.ids.name_input.text = ""
        self.ids.amount_input.text = ""
        self.ids.date_input.text = utils.get_current_date()
        self.refresh_income_spinner()
    
    def save_income(self):
        """Save income"""
        app = App.get_running_app()
        un = app.logged_user
        
        nm = self.ids.name_input.text.strip()
        dt = self.ids.date_input.text.strip()
        amt_str = self.ids.amount_input.text.strip()
        
        if not nm:
            return show_popup("Error", "Please enter income name")
        
        if not amt_str:
            return show_popup("Error", "Please enter amount")
        
        # Validate date
        try:
            datetime.strptime(dt, "%Y-%m-%d")
        except ValueError:
            return show_popup("Error", "Invalid date format. Use YYYY-MM-DD")
        
        # Validate amount
        try:
            amt = utils.parse_amount(amt_str)
            if amt <= 0:
                raise ValueError("Amount must be positive")
        except Exception as e:
            return show_popup("Error", str(e))
        
        # Save income
        db.add_income(un, nm, amt, dt)
        show_popup("Success", "Income added!")
        
        # Refresh all screens
        app.refresh_all_screens()
        
        # Clear inputs
        self.ids.name_input.text = ""
        self.ids.amount_input.text = ""
        self.ids.date_input.text = utils.get_current_date()
    
    def add_new_category(self):
        """Add new category"""
        un = App.get_running_app().logged_user
        
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        ci = TextInput(hint_text="Category name", multiline=False)
        br = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        sub, can = Button(text="Add"), Button(text="Cancel")
        br.add_widget(can)
        br.add_widget(sub)
        content.add_widget(ci)
        content.add_widget(br)
        
        popup = Popup(title="Add Category", content=content, size_hint=(0.7, 0.4))
        
        def do_submit(inst):
            cn = ci.text.strip().title()
            if cn:
                if db.add_category(un, cn):
                    cats = db.get_categories(un)
                    self.ids.category_spinner.values = cats
                    self.ids.category_spinner.text = cn
                    popup.dismiss()
                else:
                    show_popup("Error", "Category already exists")
            else:
                popup.dismiss()
        
        can.bind(on_release=lambda x: popup.dismiss())
        sub.bind(on_release=do_submit)
        show_animated_popup(popup)