import tkinter as tk
from tkinter import messagebox
import sqlite3
import json

# Database setup
def setup_database():
    conn = sqlite3.connect('adventure_game.db')
    c = conn.cursor()


    c.execute("DROP TABLE IF EXISTS enemies")
    c.execute('''CREATE TABLE enemies
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  health INTEGER, 
                  attack_power INTEGER)''')


    enemy_data = [
        ("goblin", 50, 10),
    ]
    c.executemany("INSERT INTO enemies (name, health, attack_power) VALUES (?, ?, ?)", enemy_data)


    c.execute('''CREATE TABLE IF NOT EXISTS players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  progress TEXT, 
                  inventory TEXT, 
                  health INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS story
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  scene TEXT, 
                  description TEXT, 
                  choice1 TEXT, 
                  choice2 TEXT, 
                  result1 TEXT, 
                  result2 TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  description TEXT, 
                  effect TEXT)''')

    c.execute("SELECT COUNT(*) FROM story")
    if c.fetchone()[0] == 0:

        story_data = [
            ("start", "Welcome to the Adventure Game! Enter your name to begin.", "", "", "", ""),
            ("forest", "You find yourself in a dark forest. Do you go 'left' or 'right'?", "left", "right", "cave", "village"),
            ("cave", "You find a cave. Do you 'enter' or 'continue'?", "enter", "continue", "treasure", "forest"),
            ("treasure", "You discover a treasure chest!", "go-back", "open-it", "death", "treasure-2"),
            ("village", "You arrive at a village. Do you 'talk' to the villagers or 'explore'?", "talk", "explore", "quest", "forest"),
            ("quest", "A villager asks you to find a 'sword'. Do you accept?", "yes", "no", "find_sword", "village"),
            ("find_sword", "You search for the sword. Do you 'search' the forest or 'buy' it?", "search", "buy", "sword_found", "village"),
            ("sword_found", "You found the sword! Return to the village.", "return", "explore", "village", "battle"),  # Fixed: Added comma here
            ("battle", "A wild goblin appears! Do you 'attack' or 'run'?", "attack", "run", "battle_result", "forest"),
        ]
        c.executemany("INSERT INTO story (scene, description, choice1, choice2, result1, result2) VALUES (?, ?, ?, ?, ?, ?)", story_data)


        item_data = [
            ("sword", "A sharp blade.", "increase attack"),
            ("shield", "A sturdy shield.", "increase defense"),
        ]
        c.executemany("INSERT INTO items (name, description, effect) VALUES (?, ?, ?)", item_data)

    conn.commit()
    conn.close()


def save_progress(player_name, progress, inventory, health):
    conn = sqlite3.connect('adventure_game.db')
    c = conn.cursor()
    c.execute("INSERT INTO players (name, progress, inventory, health) VALUES (?, ?, ?, ?)", 
              (player_name, progress, json.dumps(inventory), health))
    conn.commit()
    conn.close()

def load_progress(player_name):
    conn = sqlite3.connect('adventure_game.db')
    c = conn.cursor()
    c.execute("SELECT progress, inventory, health FROM players WHERE name=?", (player_name,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0], json.loads(result[1]), result[2]
    return None, [], 100


def load_scene(scene_id):
    conn = sqlite3.connect('adventure_game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM story WHERE scene=?", (scene_id,))
    result = c.fetchone()
    conn.close()
    return result


def load_enemy(enemy_name):
    conn = sqlite3.connect('adventure_game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM enemies WHERE name=?", (enemy_name,))
    result = c.fetchone()
    conn.close()
    

    print(f"Loaded enemy: {result}")
    
    if result is None:
        raise ValueError(f"Enemy '{enemy_name}' not found in the database.")
    if len(result) != 4:
        raise ValueError(f"Invalid enemy data: {result}. Expected 4 columns.")
    
    return result

class AdventureGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Trails of felwinter")
        self.player_name = ""
        self.current_scene = "start"
        self.inventory = []
        self.health = 100
        self.enemy = None

        self.label = tk.Label(root, text="Welcome to the Trails of Felwinter!", font=("Arial", 20))
        self.label.pack(pady=20)

        self.text_area = tk.Text(root, height=10, width=50, wrap=tk.WORD)
        self.text_area.pack(pady=10)

        self.entry = tk.Entry(root, width=50)
        self.entry.pack(pady=10)

        self.button = tk.Button(root, text="Submit", command=self.process_input)
        self.button.pack(pady=10)

        self.start_game()

    def start_game(self):
        self.display_scene(self.current_scene)
        self.root.mainloop()

    def display_scene(self, scene_id):
        scene = load_scene(scene_id)
        if scene:
            self.text_area.insert(tk.END, scene[2] + "\n")
            if scene[3] and scene[4]:
                self.text_area.insert(tk.END, f"Choices: {scene[3]} or {scene[4]}\n")
            
            # Display player health during battle
            if scene_id == "battle":
                self.text_area.insert(tk.END, f"Your health: {self.health}\n")
                self.text_area.insert(tk.END, f"{self.enemy[1]}'s health: {self.enemy[2]}\n")
                self.text_area.insert(tk.END, "Type 'attack' to attack or 'run' to run away.\n")

    def process_input(self):
        user_input = self.entry.get()
        self.entry.delete(0, tk.END)

        if self.current_scene == "start":
            self.player_name = user_input
            self.text_area.insert(tk.END, f"\nWelcome, {self.player_name}!\n")
            self.current_scene = "forest"
            self.display_scene(self.current_scene)
        elif self.current_scene == "battle":
            self.handle_battle(user_input)
        else:
            scene = load_scene(self.current_scene)
            if scene:
                if user_input.lower() == scene[3]:  # Choice 1
                    self.current_scene = scene[5]
                elif user_input.lower() == scene[4]:  # Choice 2
                    self.current_scene = scene[6]
                else:
                    self.text_area.insert(tk.END, "Invalid choice. Try again.\n")
                    return
                if scene[2] == 'You found the sword! Return to the village.':
                    self.inventory='sword'
                if self.current_scene == "battle":
                    self.enemy = load_enemy("goblin")
                    self.text_area.insert(tk.END, f"A wild {self.enemy[1]} appears!\n")
                    self.text_area.insert(tk.END, f"Your health: {self.health}\n")
                    self.text_area.insert(tk.END, f"{self.enemy[1]}'s health: {self.enemy[2]}\n")
                    self.text_area.insert(tk.END, "Type 'attack' to attack or 'run' to run away.\n")
                elif self.current_scene in ["treasure", "forest"]:  # Endings or continue
                    self.display_scene(self.current_scene)
                else:
                    self.display_scene(self.current_scene)

    def handle_battle(self, user_input):
        if user_input.lower() == "attack":
            self.attack_enemy()
        elif user_input.lower() == "run":
            self.text_area.insert(tk.END, "You ran away!\n")
            self.current_scene = "forest"
            self.display_scene(self.current_scene)
        else:
            self.text_area.insert(tk.END, "Invalid choice. Type 'attack' or 'run'.\n")

    def attack_enemy(self):
        player_attack = 10  # Base attack power
        if "sword" in self.inventory:
            player_attack += 5  # Sword increases attack power

        
        self.enemy = (self.enemy[0], self.enemy[1], self.enemy[2] - player_attack,self.enemy[3])
        self.text_area.insert(tk.END, f"You attacked the {self.enemy[1]} for {player_attack} damage!\n")

        if self.enemy[2] <= 0:
            self.text_area.insert(tk.END, f"You defeated the {self.enemy[1]}!\n")
            self.current_scene = "forest"
            self.display_scene(self.current_scene)
        else:
            self.enemy_attack()

    def enemy_attack(self):
        if self.enemy is None:
            raise ValueError("No enemy is loaded. Call `load_enemy` first.")
        if len(self.enemy) < 4:
            raise ValueError(f"Invalid enemy data: {self.enemy}. Expected 4 columns.")
        
        print(f"Enemy data: {self.enemy}")
        
        enemy_attack_power = self.enemy[3]  # Use enemy's attack power (index 3)
        self.health -= enemy_attack_power
        
        print(f"Player health after attack: {self.health}")
        
        self.text_area.insert(tk.END, f"The {self.enemy[1]} attacked you for {enemy_attack_power} damage!\n")
        self.text_area.insert(tk.END, f"Your health: {self.health}\n")

        if self.health <= 0:
            self.text_area.insert(tk.END, "You died!\n")
            self.end_game("death")
        else:
            self.text_area.insert(tk.END, f"Your health: {self.health}\n")
            self.text_area.insert(tk.END, f"{self.enemy[1]}'s health: {self.enemy[2]}\n")
            self.text_area.insert(tk.END, "Type 'attack' to attack or 'run' to run away.\n")

    def end_game(self, outcome):
        if outcome == "death":
            self.text_area.insert(tk.END, "Game over! You have been defeated.\n")
        else:
            self.text_area.insert(tk.END, "Congratulations! You have won the game.\n")
        save_progress(self.player_name, outcome, self.inventory, self.health)
        messagebox.showinfo("Game Over", "The game has ended.")
        self.root.quit()

if __name__ == "__main__":
    setup_database()
    root = tk.Tk()
    game = AdventureGame(root)
    