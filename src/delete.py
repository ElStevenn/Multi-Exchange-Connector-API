import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import random
import sys
import winsound
import json
import sqlite3
import time
import math
import socket
import threading
from itertools import cycle
from PIL import Image, ImageTk
from datetime import datetime

# ========================
#      CORE GAME CLASS
# ========================
class QuantumQuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quantum Quiz Odyssey")
        self.geometry("1400x900")
        self.configure(bg="#1A1A1A")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.current_user = None
        self.animation_phase = 0
        self.active_effects = []
        self.player_inventory = []
        self.multiplayer_mode = False
        self.server = None
        self.client = None
        
        # Initialize subsystems
        self.init_styles()
        self.init_db()
        self.load_resources()
        self.create_main_menu()
        self.bind_global_keys()
        
        # Game state variables
        self.quiz_running = False
        self.current_question = 0
        self.score = 0
        self.combo_multiplier = 1
        self.streak_counter = 0
        self.time_bonus = 0
        self.lives = 3
        self.difficulty = 1
        self.selected_categories = []
        
        # Session statistics
        self.session_stats = {
            'correct': 0,
            'incorrect': 0,
            'time_spent': 0,
            'powerups_used': 0,
            'max_streak': 0
        }

# ========================
#    DATABASE HANDLING
# ========================
    def init_db(self):
        self.db_conn = sqlite3.connect('quiz_data.db')
        self.cursor = self.db_conn.cursor()
        
        # Create tables
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY,
                            username TEXT UNIQUE,
                            password TEXT,
                            created_at DATETIME,
                            total_score INTEGER,
                            games_played INTEGER)''')
                            
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
                            id INTEGER PRIMARY KEY,
                            category TEXT,
                            difficulty INTEGER,
                            question_type TEXT,
                            question TEXT,
                            options TEXT,
                            correct_answer TEXT)''')
                            
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS leaderboard (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            score INTEGER,
                            timestamp DATETIME)''')
        
        self.db_conn.commit()

# ========================
#    RESOURCE MANAGEMENT
# ========================
    def load_resources(self):
        # Load images
        try:
            self.images = {
                'background': ImageTk.PhotoImage(Image.open('assets/space_bg.png').resize((1400,900))),
                'logo': ImageTk.PhotoImage(Image.open('assets/quantum_logo.png').resize((400,150))),
                'powerup_2x': ImageTk.PhotoImage(Image.open('assets/powerup_2x.png').resize((40,40))),
                'powerup_time': ImageTk.PhotoImage(Image.open('assets/powerup_time.png').resize((40,40))),
                'life_icon': ImageTk.PhotoImage(Image.open('assets/life_icon.png').resize((30,30)))
            }
        except FileNotFoundError:
            self.images = {}
            messagebox.showerror("Error", "Missing game assets!")

        # Load sound effects
        self.sound_enabled = True
        self.sounds = {
            'correct': lambda: winsound.PlaySound('SystemAsterisk', winsound.SND_ASYNC),
            'wrong': lambda: winsound.PlaySound('SystemHand', winsound.SND_ASYNC),
            'powerup': lambda: winsound.PlaySound('SystemExclamation', winsound.SND_ASYNC)
        }

        # Load questions from database
        self.categories = {
            'Science': self.load_questions_from_db('Science'),
            'History': self.load_questions_from_db('History'),
            'Pop Culture': self.load_questions_from_db('Pop Culture'),
            'Technology': self.load_questions_from_db('Technology')
        }

# ========================
#    USER INTERFACE
# ========================
    def init_styles(self):
        self.style = ttk.Style()
        self.style.theme_create("quantum", settings={
            "TButton": {
                "configure": {
                    "padding": 10,
                    "relief": "flat",
                    "font": ("Terminal", 12),
                    "borderwidth": 3
                },
                "map": {
                    "background": [("active", "#4A90E2"), ("!disabled", "#2D2D2D")],
                    "foreground": [("active", "#FFFFFF"), ("!disabled", "#CCCCCC")]
                }
            },
            "TLabel": {
                "configure": {
                    "font": ("Terminal", 14),
                    "background": "#1A1A1A",
                    "foreground": "#FFFFFF"
                }
            },
            "TFrame": {
                "configure": {
                    "background": "#1A1A1A"
                }
            }
        })
        self.style.theme_use("quantum")

    def create_main_menu(self):
        self.main_menu_frame = ttk.Frame(self)
        
        # Background image
        self.bg_canvas = tk.Canvas(self.main_menu_frame, width=1400, height=900)
        self.bg_canvas.create_image(0, 0, image=self.images.get('background'), anchor=tk.NW)
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Menu buttons
        menu_buttons = [
            ("New Game", self.start_new_game),
            ("Multiplayer", self.start_multiplayer_lobby),
            ("Load Game", self.load_game),
            ("Settings", self.open_settings),
            ("Leaderboard", self.show_leaderboard),
            ("Exit", self.quit)
        ]
        
        for idx, (text, command) in enumerate(menu_buttons):
            btn = ttk.Button(self.bg_canvas, text=text, command=command)
            self.bg_canvas.create_window(700, 300 + idx*60, window=btn, width=200)

        self.main_menu_frame.pack(fill=tk.BOTH, expand=True)

# ========================
#    GAME MECHANICS
# ========================
    def start_new_game(self):
        self.quiz_running = True
        self.current_question = 0
        self.score = 0
        self.lives = 3
        self.combo_multiplier = 1
        self.streak_counter = 0
        self.session_stats = {k:0 for k in self.session_stats}
        self.create_game_interface()
        self.next_question()

    def next_question(self):
        if self.current_question < 20 and self.lives > 0:
            self.display_question()
            self.start_question_timer()
            self.update_interface()
        else:
            self.end_game()

    def display_question(self):
        # Complex question display logic with multiple types
        question = self.get_next_question()
        self.current_question_data = question
        
        self.question_display.delete("all")
        self.question_display.create_text(400, 50, text=question['text'], 
                                        font=("Terminal", 16), fill="#FFFFFF")
        
        if question['type'] == 'multiple_choice':
            self.display_multiple_choice(question)
        elif question['type'] == 'true_false':
            self.display_true_false(question)
        elif question['type'] == 'image_identification':
            self.display_image_question(question)

    def check_answer(self, selected):
        # Complex answer verification system
        correct = self.current_question_data['correct']
        time_remaining = self.time_left
        
        if selected == correct:
            self.handle_correct_answer(time_remaining)
        else:
            self.handle_incorrect_answer()
        
        self.current_question += 1
        self.after(1500, self.next_question)

    def handle_correct_answer(self, time_remaining):
        base_points = self.difficulty * 100
        time_bonus = int(time_remaining * 5)
        streak_bonus = self.streak_counter * 50
        total = (base_points + time_bonus + streak_bonus) * self.combo_multiplier
        
        self.score += total
        self.streak_counter += 1
        self.session_stats['correct'] += 1
        self.session_stats['max_streak'] = max(self.session_stats['max_streak'], self.streak_counter)
        
        self.animate_score_popup(total)
        self.play_sound('correct')
        self.apply_visual_effect('particles')

    def handle_incorrect_answer(self):
        self.lives -= 1
        self.streak_counter = 0
        self.combo_multiplier = 1
        self.session_stats['incorrect'] += 1
        
        self.animate_life_loss()
        self.play_sound('wrong')
        self.apply_visual_effect('shake')

# ========================
#    ADVANCED FEATURES
# ========================
    def start_multiplayer_lobby(self):
        self.multiplayer_frame = ttk.Frame(self)
        # ... multiplayer interface components ...
        self.create_server_button = ttk.Button(self.multiplayer_frame, 
                                             text="Host Game", 
                                             command=self.start_multiplayer_server)
        self.create_server_button.pack()
        
        self.join_server_entry = ttk.Entry(self.multiplayer_frame)
        self.join_server_entry.pack()
        
        self.multiplayer_chat = tk.Text(self.multiplayer_frame, height=10)
        self.multiplayer_chat.pack()
        
        self.multiplayer_frame.pack(fill=tk.BOTH, expand=True)

    def start_multiplayer_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('localhost', 5555))
        self.server.listen()
        
        self.multiplayer_chat.insert(tk.END, "Server started on port 5555\n")
        threading.Thread(target=self.handle_multiplayer_connections, daemon=True).start()

    def handle_multiplayer_connections(self):
        while True:
            client, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        while True:
            try:
                data = client.recv(1024).decode('utf-8')
                if data:
                    self.broadcast_message(data)
            except:
                break

    def broadcast_message(self, message):
        self.multiplayer_chat.insert(tk.END, f"{message}\n")

    def apply_visual_effect(self, effect_type):
        if effect_type == 'particles':
            self.create_particle_effect()
        elif effect_type == 'shake':
            self.shake_window()
        elif effect_type == 'color_cycle':
            self.start_color_cycle()

    def create_particle_effect(self):
        particle_canvas = tk.Canvas(self.game_frame, bg='', highlightthickness=0)
        particle_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        for _ in range(50):
            x = random.randint(0, 1400)
            y = random.randint(0, 900)
            color = random.choice(['#FF6B6B', '#4ECDC4', '#FFE66D'])
            particle = particle_canvas.create_oval(x, y, x+10, y+10, fill=color)
            
            dx = random.randint(-15, 15)
            dy = random.randint(-15, 15)
            self.animate_particle(particle_canvas, particle, dx, dy, 0)
            
        self.after(1000, particle_canvas.destroy)

    def animate_particle(self, canvas, particle, dx, dy, gravity):
        canvas.move(particle, dx, dy)
        coords = canvas.coords(particle)
        
        if coords[1] < 900:
            self.after(50, self.animate_particle, canvas, particle, 
                      dx*0.9, dy+gravity+0.5, gravity+0.1)

    def shake_window(self):
        x = self.winfo_x()
        y = self.winfo_y()
        for i in range(0, 20, 5):
            self.geometry(f"+{x+i}+{y}")
            self.update()
            time.sleep(0.01)
            self.geometry(f"+{x-i}+{y}")
            self.update()
            time.sleep(0.01)
        self.geometry(f"+{x}+{y}")

# ========================
#    INVENTORY SYSTEM
# ========================
    def collect_powerup(self, powerup_type):
        self.player_inventory.append(powerup_type)
        self.update_inventory_display()

    def use_powerup(self, index):
        if index < len(self.player_inventory):
            powerup = self.player_inventory.pop(index)
            self.activate_powerup(powerup)
            self.update_inventory_display()

    def activate_powerup(self, powerup_type):
        if powerup_type == '2x':
            self.combo_multiplier *= 2
            self.apply_timed_effect('2x', 10)
        elif powerup_type == 'time':
            self.time_left += 15
            self.update_timer_display()
            
        self.play_sound('powerup')
        self.session_stats['powerups_used'] += 1

# ========================
#    SETTINGS & OPTIONS
# ========================
    def open_settings(self):
        self.settings_window = tk.Toplevel(self)
        self.settings_window.title("Quantum Settings")
        
        ttk.Label(self.settings_window, text="Audio Volume").grid(row=0, column=0)
        self.volume_scale = ttk.Scale(self.settings_window, from_=0, to=100)
        self.volume_scale.grid(row=0, column=1)
        
        ttk.Label(self.settings_window, text="Difficulty Level").grid(row=1, column=0)
        self.difficulty_combo = ttk.Combobox(self.settings_window, 
                                           values=["Novice", "Adept", "Expert", "Quantum"])
        self.difficulty_combo.grid(row=1, column=1)
        
        ttk.Button(self.settings_window, text="Save", 
                 command=self.save_settings).grid(row=2, columnspan=2)

    def save_settings(self):
        self.difficulty = ["Novice", "Adept", "Expert", "Quantum"].index(
            self.difficulty_combo.get())
        self.settings_window.destroy()

# ========================
#    PERSISTENCE & NETWORKING
# ========================
    def save_game(self):
        save_data = {
            'score': self.score,
            'current_question': self.current_question,
            'lives': self.lives,
            'inventory': self.player_inventory,
            'difficulty': self.difficulty,
            'timestamp': datetime.now().isoformat()
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".quantum",
            filetypes=[("Quantum Save Files", "*.quantum")]
        )
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(save_data, f)

    def load_game(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Quantum Save Files", "*.quantum")]
        )
        
        if filename:
            with open(filename, 'r') as f:
                save_data = json.load(f)
                
            self.score = save_data['score']
            self.current_question = save_data['current_question']
            self.lives = save_data['lives']
            self.player_inventory = save_data['inventory']
            self.difficulty = save_data['difficulty']
            
            self.start_new_game()

# ========================
#    UTILITIES & HELPERS
# ========================
    def bind_global_keys(self):
        self.bind("<F1>", self.show_help)
        self.bind("<Escape>", self.return_to_menu)
        self.bind("<Control-s>", lambda e: self.save_game())
        self.bind("<Control-l>", lambda e: self.load_game())

    def show_help(self, event=None):
        help_text = """QUANTUM QUIZ ODYSSEY - CONTROLS
F1: Show this help
Esc: Return to main menu
Ctrl+S: Quick save
Ctrl+L: Quick load
1-4: Answer selection
Space: Use powerup"""
        messagebox.showinfo("Game Help", help_text)

    def play_sound(self, sound_type):
        if self.sound_enabled and sound_type in self.sounds:
            self.sounds[sound_type]()

    def on_close(self):
        if messagebox.askokcancel("Quit", "Are you sure you want to exit?"):
            self.db_conn.close()
            self.destroy()

# ========================
#    MAIN EXECUTION
# ========================
if __name__ == "__main__":
    app = QuantumQuizApp()
    app.mainloop()