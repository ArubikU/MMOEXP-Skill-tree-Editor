import copy
import datetime
import json
import math
import os
import re
import sys
import tkinter as tk
from collections import deque
from functools import lru_cache
from tkinter import filedialog, messagebox, ttk

import PIL.Image
import PIL.ImageTk
import yaml


def get_base_path():
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, use the directory of the executable
        return os.path.dirname(sys.executable)
    else:
        # If the application is run as a script, use the directory of the script
        return os.path.dirname(os.path.abspath(__file__))

def find_file(filename):
    # List of possible locations to search for the file
    search_paths = [
        os.path.dirname(sys.executable),  # Executable's directory
        get_base_path(),                  # Base path
        os.path.dirname(os.path.abspath(__file__)),  # script dir
        os.getcwd(),                      # Current working directory
        
    ]

    for path in search_paths:
        file_path = os.path.join(path, filename)
        if os.path.exists(file_path):
            return file_path
    
    return None  # File not found



folder = get_base_path()
log = f"{folder}\\logs\\latest.log"
logdata = []
logdata.append(f"----------------------------------------")
logdata.append(f"Folder: {folder}")
logdata.append(f"Python Version: {sys.version}")
logdata.append(f"Tkinter Version: {tk.TkVersion}")
logdata.append(f"YAML Version: {yaml.__version__}")
logdata.append(f"----------------------------------------")
logdata.append(f"")
#create logs folder if not exist
if not os.path.exists(f"{folder}\\logs"):
    os.mkdir(f"{folder}\\logs")
#verify if exist a log so rename it to the current date
if os.path.exists(log):
    time = datetime.datetime.now()
    formatedTime = time.strftime("%Y-%m-%d-%H-%M-%S")
    os.rename(log, f"{folder}\\logs\\{formatedTime}.log")
def writeLog():
    with open(log, 'w+') as file:
        for line in logdata:
            file.write(f"{line}\n")
            
def addLineLog(line):
    with open(log, 'a') as file:
        time = datetime.datetime.now()
        formatedTime = time.strftime("%Y-%m-%d %H:%M")
        file.write(f"{line} [{formatedTime}]\n")



writeLog()
        
        

if getattr(sys, 'frozen', False):
    basePath = get_base_path()

    files_to_copy = ['textures.json', 'conf.json', 'buttons.png']

    for file in files_to_copy:
        destination = os.path.join(basePath, file)
        if not os.path.exists(destination):
            source = find_file(file)
            if source:
                try:
                    with open(source, 'rb') as src_file, open(destination, 'wb') as dst_file:
                        dst_file.write(src_file.read())
                    addLineLog(f"[!] Copied {file} to {destination}")
                except IOError as e:
                    addLineLog(f"[!] Unable to copy {file}. Error: {e}")
                except Exception as e:
                    addLineLog(f"[!] Unexpected error occurred while copying {file}: {e}")
            else:
                addLineLog(f"[!] Unable to find {file} in any of the search paths.")
        else:
            addLineLog(f"[!] {file} already exists in {basePath}")
        
try:

    continueProgram = True
            
    def validate(path, extra = "", filetype = "File"):
        if not os.path.exists(path):
            addLineLog(f"[!] {filetype} not found: {path} {extra}")
            return False
        else:
            addLineLog(f"[+] Loaded {filetype}: {path} {extra}")
            return True
    texturePath = f"{folder}\\textures.json"
    configPath = f"{folder}\\conf.json"

    #show a warning if the textures.json file is not found, uses system message box

    for path in [texturePath,configPath]:
        if not os.path.exists(path):
            logdata.append(f"[!] File not found: {path}")
            continueProgram = False
            break
        else:
            logdata.append(f"[+] Loaded file: {path}")


    with open(texturePath, 'r',encoding="utf-8") as file:
        json_data = json.load(file)
        
    with open(configPath, 'r',encoding="utf-8") as file:
        config_data = json.load(file)
        
        
        
    textures = {}
    try:
        material = config_data["material"]
        version = config_data["version"]
    except Exception as e:
        addLineLog(f"[!] Error loading config file: {e}")
        continueProgram = False

    def on_paste(event):
        try:
            # Getting the text from the clipboard
            clipboard_text = event.widget.clipboard_get()
            widget = event.widget  # We get the widget where the event occurred
            if isinstance(widget, tk.Entry):
                widget.insert(tk.INSERT, clipboard_text)  # Inserting into the Entry field
                
            elif isinstance(widget, tk.Text):
                widget.insert(tk.INSERT, clipboard_text)  # Inserting into a text field
        except tk.TclError:
            pass  # If the clipboard is empty or contains no text

    class AutoSuggestCombobox(ttk.Combobox):
        def __init__(self, master=None, **kwargs):
            super().__init__(master, **kwargs)
            self._completion_list = []
            self._hits = []
            self._hit_index = 0
            self.position = 0
            self.bind('<KeyRelease>', self._handle_keyrelease)
            self.bind('<FocusOut>', self._handle_focusout)
            self.bind('<FocusIn>', self._handle_focusin)
            self.bind('<Return>', self._handle_return)  # bind Enter key
            self.bind('<Down>', self._down_arrow)  # bind Up arrow key
            self.bind('<Up>', self._up_arrow)
            self.bind('<Button-1>', self._handle_click)  # bind mouse click
            master.bind("<Button-1>", self._handle_root_click)  # bind mouse click on root window
            self._popup_menu = None

        def set_completion_list(self, completion_list):
            """Set the list of possible completions."""
            self._completion_list = sorted(completion_list)
            self['values'] = self._completion_list

        def _handle_keyrelease(self, event):
            """Handle key release events."""
            value = self.get()
            cursor_index = self.index(tk.INSERT)

            if value == '':
                self._hits = self._completion_list
            else:
                # Determine the word before the cursor
                before_cursor = value[:cursor_index].rsplit(' ', 1)[-1]

                # Filter suggestions based on the word before the cursor
                self._hits = [item for item in self._completion_list if item.lower().startswith(before_cursor.lower())]

            # Ignore Down and Up arrow key presses
            if event.keysym in ['Down', 'Up', 'Return']:
                return

            if self._hits:
                self._show_popup(self._hits)


        def _show_popup(self, values):
            """Display the popup listbox."""
            if self._popup_menu:
                self._popup_menu.destroy()

            self._popup_menu = tk.Toplevel(self)
            self._popup_menu.wm_overrideredirect(True)
            self._popup_menu.config(bg='black')

            # Add a frame with a black background to create the border effect
            popup_frame = tk.Frame(self._popup_menu, bg='gray10', borderwidth=0.1)
            popup_frame.pack(padx=1, pady=(1, 1), fill='both', expand=True)

            listbox = tk.Listbox(popup_frame, borderwidth=0, relief=tk.FLAT, bg='white', selectbackground='#0078d4', bd=0, highlightbackground='black')
            scrollbar = ttk.Scrollbar(popup_frame, orient=tk.VERTICAL, command=listbox.yview)
            listbox.config(yscrollcommand=scrollbar.set)

            for value in values:
                listbox.insert(tk.END, value)

            listbox.bind("<ButtonRelease-1>", self._on_listbox_select)
            listbox.bind("<FocusOut>", self._on_listbox_focusout)
            listbox.bind("<Motion>", self._on_mouse_motion)

            # Automatically select the first entry if the mouse cursor has not yet been hovered over
            if not listbox.curselection():
                listbox.selection_set(0)

            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Adjust popup width to match entry box
            popup_width = self.winfo_width()
            self._popup_menu.geometry(f"{popup_width}x165")

            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()
            self._popup_menu.geometry(f"+{x}+{y}")

        def _on_listbox_select(self, event):
            """Select a value from the listbox."""
            widget = event.widget
            selection = widget.curselection()
            if selection:
                value = widget.get(selection[0])
                self._select_value(value)

        def _on_mouse_motion(self, event):
            """Handle mouse motion over the listbox."""
            widget = event.widget
            index = widget.nearest(event.y)
            widget.selection_clear(0, tk.END)
            widget.selection_set(index)

        def _on_listbox_focusout(self, event):
            """Handle listbox losing focus."""
            if self._popup_menu:
                self._popup_menu.destroy()
                self._popup_menu = None

        def _select_value(self, value):
            """Select a value from the popup listbox."""
            self.set(value)
            self.icursor(tk.END)  # Move cursor to the end
            self.selection_range(0, tk.END)  # Select entire text
            if self._popup_menu:
                self._popup_menu.destroy()
                self._popup_menu = None

        def _handle_focusout(self, event):
            """Handle focus out events."""
            if self._popup_menu:
                try:
                    if not self._popup_menu.winfo_containing(event.x_root, event.y_root):
                        self._popup_menu.destroy()
                        self._popup_menu = None
                except tk.TclError:
                    pass

        def _handle_focusin(self, event):
            """Handle focus in events."""
            if self._popup_menu:
                self._popup_menu.destroy()
                self._popup_menu = None

        def _handle_return(self, event):
            """Handle Enter key press."""
            if self._popup_menu:
                listbox = self._popup_menu.winfo_children()[0].winfo_children()[0]
                current_selection = listbox.curselection()
                if current_selection:
                    value = listbox.get(current_selection[0])
                    self._select_value(value)

        def _down_arrow(self, event):
            """Handle down arrow key press."""
            if self._popup_menu:
                listbox = self._popup_menu.winfo_children()[0].winfo_children()[0]
                current_selection = listbox.curselection()
                if current_selection:
                    current_index = current_selection[0]
                    next_index = (current_index + 1) % len(self._hits)
                    listbox.selection_clear(0, tk.END)
                    listbox.selection_set(next_index)
                    listbox.activate(next_index)
                    return 'break'  # prevent default behavior

        def _up_arrow(self, event):
            """Handle up arrow key press."""
            if self._popup_menu:
                listbox = self._popup_menu.winfo_children()[0].winfo_children()[0]
                current_selection = listbox.curselection()
                if current_selection:
                    current_index = current_selection[0]
                    next_index = (current_index - 1) % len(self._hits)
                    listbox.selection_clear(0, tk.END)
                    listbox.selection_set(next_index)
                    listbox.activate(next_index)
                    return 'break'  # prevent default behavior



        def _handle_click(self, event):
            """Handle mouse click events."""
            value = self.get()
            if value == '':
                self._hits = self._completion_list
            else:
                self._hits = [item for item in self._completion_list if item.lower().startswith(value.lower())]

            if self._hits:
                self._show_popup(self._hits)


        def _handle_root_click(self, event):
            """Handle mouse click events on root window."""
            if self._popup_menu:
                x, y = event.x_root, event.y_root
                x0, y0, x1, y1 = self.winfo_rootx(), self.winfo_rooty(), self.winfo_rootx() + self.winfo_width(), self.winfo_rooty() + self.winfo_height()
                if not (x0 <= x <= x1 and y0 <= y <= y1):
                    self._popup_menu.destroy()
                    self._popup_menu = None

    class SkillNode:
        def __init__(self, name, x, y, parents=None, **kwargs):
            self.name = name
            self.coordinates = {'x': x, 'y': y}
            self.parents = parents or {}
            self.additional_data = kwargs
        def get(self, key, default=None):
            return self.additional_data.get(key, default)
        def set(self, key, value):
            self.additional_data[key] = value
        def has(self, key):
            return key in self.additional_data
        def __str__(self):
            return str(self.additional_data)

    class SkillTreeEditor:

        def __init__(self, master):
            self.master = master
            self.master.title("Skill Tree Editor")
        
            with open(texturePath, 'r',encoding="utf-8") as file:
                json_data = json.load(file)
                for key, value in json_data['nodes'].items():
                    #generate a PIL image from the path of the image and the uvs
                    if validate(value['path'].replace("{{folder}}",folder), value['uvs'], "Image"):
                        tempImage = PIL.Image.open(value['path'].replace("{{folder}}",folder))
                        uvs = value['uvs']
                        #format (x,y,width,height)
                        tempTwo = tempImage.crop((uvs[0], uvs[1], uvs[0]+uvs[2], uvs[1]+uvs[3]))
                        face = round(18*2)
                        tempTwo = tempTwo.resize((face,face), resample=PIL.Image.NEAREST)
                        textures[key] = PIL.ImageTk.PhotoImage(tempTwo)
                    else:
                        #close the program if the image is not found
                        messagebox.showwarning("Error", f"Image not found: {value['path']}")
                        sys.exit()
                        
                for key, value in json_data['signs'].items():
                    #generate a PIL image from the path of the image and the uvs
                    if validate(value['path'].replace("{{folder}}",folder), value['uvs'], "Image"):
                        tempImage = PIL.Image.open(value['path'].replace("{{folder}}",folder))
                        uvs = value['uvs']
                        #format (x,y,width,height)
                        tempTwo = tempImage.crop((uvs[0], uvs[1], uvs[0]+uvs[2], uvs[1]+uvs[3]))
                        face = round(18*2)
                        tempTwo = tempTwo.resize((face,face), resample=PIL.Image.NEAREST)
                        textures[key] = PIL.ImageTk.PhotoImage(tempTwo)
                    else:
                        #close the program if the image is not found
                        messagebox.showwarning("Error", f"Image not found: {value['path']}")
                        sys.exit()
                    
                    
            self.list_colors: list = []
            self.blocked_nodes: list = []
            for key,value in json_data['nodes'].items():
                if(key == "default"):
                    continue
                self.list_colors.append(key)

            # Frame for the buttons
            button_frame = tk.Frame(master)
            button_frame.pack(side=tk.TOP, fill=tk.X)
            self.open_file_button = tk.Button(button_frame, text="Open New File", command=self.open_new_file)
            self.open_file_button.pack(side=tk.LEFT)
            self.save_button = tk.Button(button_frame, text="Save", command=self.save_data)
            self.save_button.pack(side=tk.LEFT)
            self.save_button = tk.Button(button_frame, text="Save RY", command=self.save_data_ry)
            self.save_button.pack(side=tk.LEFT)
            
            self.reset_button = tk.Button(button_frame, text="Reset", command=self.reset_to_original)
            self.reset_button.pack(side=tk.LEFT)
            
            self.undo_button = tk.Button(button_frame, text="Undo", command=self.undo)
            self.undo_button.pack(side=tk.LEFT)
            
            self.redo_button = tk.Button(button_frame, text="Redo", command=self.redo)
            self.redo_button.pack(side=tk.LEFT)
            self.add_node_button = tk.Button(button_frame, text="Add Node", command=self.open_add_node_window)
            self.add_node_button.pack(side=tk.LEFT)
            
            
            
            self.add_node_button = tk.Button(button_frame, text="🚫", command=self.switch_preview)
            self.add_node_button.pack(side=tk.LEFT)
            
            
            self.combo: AutoSuggestCombobox = AutoSuggestCombobox(button_frame)
            
            self.combo.set_completion_list(self.list_colors)
            self.combo.pack(pady=10, padx=10)
            
            

            self.detection_rectangles = {}
            
            
            self.canvas = tk.Canvas(master, width=800, height=800, bg='white')
            self.canvas.pack(expand=tk.YES, fill=tk.BOTH)

            self.canvas.focus_force()

            self.nodes: dict[(int,int),SkillNode] = {}
            self.node_matrix = {}
            self.selected_node = None
            self.node_rectangles = {}
            self.block_rectangles = {}
            self.scale = 1.1
            self.offset_x = 400
            self.offset_y = 400
            self.original_data = None
            self.grid_size = 40
            self.node_size = 30
            self.preview = False
            self.history = []
            self.future = []
            self.color_index = 0

            self.load_file_dialog()
            self.setup_blocked_nodes()
            self.draw_grid()
            self.draw_nodes()
            self.current_mouse_slot = (0, 0)
            self.canvas.bind("<Button-1>", self.select_node)
            
            
            #disabled zoom
            self.canvas.bind("<MouseWheel>", self.zoom)
            self.canvas.bind("<Motion>", self.motion_event)
            self.canvas.bind("<B1-Motion>", self.drag_canvas)
            self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
            self.canvas.bind("<Double-1>", self.double_click_event)
            
            self.master.bind_all("<w>", lambda event: self.move_selected_node(0, 1))
            self.master.bind_all("<s>", lambda event: self.move_selected_node(0, -1))
            self.master.bind_all("<a>", lambda event: self.move_selected_node(-1, 0))
            self.master.bind_all("<d>", lambda event: self.move_selected_node(1, 0))
            self.master.bind_all("<Up>", lambda event: self.move_selected_node(0, 1))
            self.master.bind_all("<Down>", lambda event: self.move_selected_node(0, -1))
            self.master.bind_all("<Left>", lambda event: self.move_selected_node(-1, 0))
            self.master.bind_all("<Right>", lambda event: self.move_selected_node(1, 0))
            self.master.bind_all("<Escape>", lambda event: self.clearSelection())
            self.master.bind_all("<Return>", lambda event: self.set_colorAttachment(self.combo.get(),True))
            self.master.bind_all("<KeyPress>", lambda event: print(event.keysym))
            self.master.bind("<Control-z>", self.undo)
            self.master.bind("<Control-y>", self.redo)
            self.bfs_path_used = []
            
            self.drag_start_x = 0
            self.drag_start_y = 0
            
        def clearSelection(self):
            self.selected_node = None
            self.selected_blocknode = None
            self.draw_nodes()
            
        def switch_preview(self):
            self.preview = not self.preview
            self.draw_nodes()

        # Example of a method to open the add node window
        def open_add_node_window(self):
            if not self.selected_node:
                messagebox.showwarning("I warned!", "Select a node.")
                return

            add_window = tk.Toplevel(self.master)
            add_window.title("Add new node")

            # The "Name" input field
            ttk.Label(add_window, text="Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
            name_entry = ttk.Entry(add_window, width=40)
            name_entry.bind("<Control-v>", on_paste)  # Binding Ctrl+V to insert
            name_entry.grid(row=0, column=1, padx=5, pady=5)
            name_entry.insert(0, "<#ffe0cb>New Node")

            # The "Rewards" input field
            ttk.Label(add_window, text="Rewards:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
            exp_entry = tk.Text(add_window, width=40, height=4)
            exp_entry.bind("<Control-v>", on_paste)  # Binding Ctrl+V to insert
            exp_entry.grid(row=1, column=1, padx=5, pady=5)
            exp_entry.insert("1.0", "stat{stat=\"COOLDOWN_REDUCTION\";amount=1;type=\"FLAT\"}")

            # The "Lore" input field
            ttk.Label(add_window, text="Lore:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
            lores_text = tk.Text(add_window, width=40, height=4)
            lores_text.bind("<Control-v>", on_paste)  # Binding Ctrl+V to insert
            lores_text.grid(row=2, column=1, padx=5, pady=5)
            lores_text.insert("1.0", "&8 Reduce the cool-down\n&8 of your skills by a +&a1%")

            # Input field "Max Level"
            ttk.Label(add_window, text="Max Level:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
            max_level_entry = ttk.Entry(add_window, width=40)
            max_level_entry.grid(row=3, column=1, padx=5, pady=5)
            max_level_entry.insert(0, "1")

            # The "Childs" input field
            ttk.Label(add_window, text="Childs:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
            max_childs = ttk.Entry(add_window, width=40)
            max_childs.grid(row=4, column=1, padx=5, pady=5)
            max_childs.insert(0, "1")

            # The "Points" input field
            ttk.Label(add_window, text="Points:").grid(row=5, column=0, sticky="e", padx=5, pady=5)
            points_entry = ttk.Entry(add_window, width=40)
            points_entry.grid(row=5, column=1, padx=5, pady=5)
            points_entry.insert(0, "1")
            fields =  {
                'name_entry': name_entry,
                'exp_entry': exp_entry,
                'lores_text': lores_text,
                'max_level_entry': max_level_entry,
                'points_entry': points_entry,
                'max_childs': max_childs,
                
            }
            # Generating data for a node
            # The button for adding a node
            ttk.Button(add_window, text="Add node", command=lambda: self.pre_add_node(
                add_window,fields
            )).grid(row=6, column=0, columnspan=2, pady=10)
        def pre_add_node(self, add_window,fields):
            
            data = {
                'name': fields['name_entry'].get(),
                'rewards': fields['exp_entry'].get("1.0", tk.END),
                'lore': fields['lores_text'].get("1.0", tk.END),
                'maxLevel': fields['max_level_entry'].get(),
                'points': fields['points_entry'].get(),
                'maxChilds': fields['max_childs'].get(),
            }
            self.add_node(
                nodeData=data,
                window=add_window
            )
            
        def add_node(self, nodeData, window):
            if self.selected_node:
                selected = self.nodes[self.selected_node]
                directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # right, up, left, down
                
                name = nodeData['name']
                experience = nodeData['rewards']
                lores = {}
                for index in range(0,len(nodeData['lore'].strip().split('\n'))):
                    lores[index] = nodeData['lore'].strip().split('\n')[index]
                max_level =int(nodeData['maxLevel'])
                points = int(nodeData['points'])
                maxChilds = int(nodeData['maxChilds'])
                
                for dx, dy in directions:
                    new_x = selected.coordinates['x'] + dx
                    new_y = selected.coordinates['y'] + dy
                    cords = (new_x, new_y)
                    if cords not in self.node_matrix:
                        new_key = f"a{len(self.nodes) + 1}"
                        new_node = SkillNode(
                            name=name,
                            x=new_x,
                            y=new_y,
                            parents={"strong": {self.selected_node: 1}},
                            is_root=False,
                            size=1,
                        )
                        
                        new_node.set("experience_table",{
                                "first_table_item": {
                                    "triggers": experience.strip().split('\n')
                                }})
                        new_node.set("lore",lores)
                        new_node.set("max-level",max_level)
                        new_node.set("point-consumed",points)
                        new_node.set("max-childer",maxChilds)
                        self.nodes[new_key] = new_node
                        self.node_matrix[(new_x, new_y)] = new_key
                        self.save_state()
                        self.draw_nodes()
                        addLineLog(f"[+] Added node: {new_key}")
                        window.destroy()
                        return
                addLineLog(f"[!] No space to add node")
                messagebox.showwarning("Warning", "There is no free space around the selected node.")
            else:
                messagebox.showwarning("Warning", "Select a node first.")
        
        def double_click_event(self, event):
            if self.selected_node:
                self.color_index = (self.color_index + 1) % len(self.list_colors)
                new_color = self.list_colors[self.color_index]
                self.set_colorAttachment(new_color)
                self.draw_nodes()
            elif self.selected_blocknode:
                self.blocked_nodes.remove(self.selected_blocknode)
                self.draw_nodes()
            else:
                #get relative position of the mouse on the grid
                x, y = self.get_mouse_grid_slot(event)
                if (x,y) not in self.node_matrix:
                    self.blocked_nodes.append((x, y))
                    self.draw_nodes()

                
            self.original_data['extra']['blocked_nodes'] = [{'x': x, 'y': y} for x, y in self.blocked_nodes]
                    

        def set_colorAttachment(self, color: str, update = False):
            if self.selected_node is not None:
                node = self.nodes[self.selected_node]
                if color in json_data['nodes']:
                    node.additional_data["display"] = {
                        "unlocked": {
                            "item": material,
                            "custom-model-data": json_data['nodes'][color]['unlocked']
                        },
                        "unlockable": {
                            "item": material,
                            "custom-model-data": json_data['nodes'][color]['unlockable']
                        },
                        "locked": {
                            "item": material,
                            "custom-model-data": json_data['nodes']['default']['locked']
                        },
                        "fully-locked": {
                            "item": material,
                            "custom-model-data": json_data['nodes']['default']['fully-locked']
                        }
                    }
                self.save_state()
            if update:
                self.draw_nodes()
        def defaultRender(self):
            self.master.focus_set()
            print("Scale: ", self.scale)
            for key, value in json_data['nodes'].items():
                #generate a PIL image from the path of the image and the uvs
                tempImage = PIL.Image.open(value['path'].replace("{{folder}}",folder))
                uvs = value['uvs']
                #format (x,y,width,height)
                tempTwo = tempImage.crop((uvs[0], uvs[1], uvs[0]+uvs[2], uvs[1]+uvs[3]))
                face = round(18*2*self.scale)
                tempTwo = tempTwo.resize((face,face), resample=PIL.Image.NEAREST)
                textures[key] = PIL.ImageTk.PhotoImage(tempTwo)
            for key, value in json_data['signs'].items():
                #generate a PIL image from the path of the image and the uvs
                tempImage = PIL.Image.open(value['path'].replace("{{folder}}",folder))
                uvs = value['uvs']
                #format (x,y,width,height)
                tempTwo = tempImage.crop((uvs[0], uvs[1], uvs[0]+uvs[2], uvs[1]+uvs[3]))
                face = round(18*2*self.scale)
                tempTwo = tempTwo.resize((face,face), resample=PIL.Image.NEAREST)
                textures[key] = PIL.ImageTk.PhotoImage(tempTwo)
            self.draw_grid()
            self.draw_nodes()
        @lru_cache(maxsize=None)
        def calculateAngle(self,start: [int, int], goal: [int, int]) -> float:
            # Calculate the differences in x and y coordinates
            delta_x = goal[0] - start[0]
            delta_y = goal[1] - start[1]

            # Use atan2 to calculate the angle (in radians)
            angle_rad = math.atan2(delta_y, delta_x)

            # Convert the angle from radians to degrees
            angle_deg = math.degrees(angle_rad)

            return angle_deg

        def is_visible(self, xcord, ycord):
            # Convert the coordinates of the node to the coordinate system of the canvas
            x = (xcord * self.grid_size * self.scale) + self.offset_x
            y = (ycord * self.grid_size * self.scale) + self.offset_y

            # Get the visible edges of the canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Define the limits of the visible area
            visible_left = 0
            visible_right = canvas_width
            visible_top = 0
            visible_bottom = canvas_height

            # Checks if the node is in the visible area of the canvas
            return (visible_left <= x <= visible_right) and (visible_top <= y <= visible_bottom)


    # Auxiliary methods for converting grid coordinates to canvas
        @lru_cache(maxsize=None)
        def canvas_x(self, x):
            return (x * self.scale) + self.offset_x

        @lru_cache(maxsize=None)
        def canvas_y(self, y):
            return (y * self.scale) + self.offset_y



        @lru_cache(maxsize=None)
        def bfs_path(self, start, goal):
            # Dynamically generates a graph
            graph = {}
            
            # Defines the size of the graph area
            area_size = 40  # For example, from -5 to 5 on both axes

            # Constructing the graph
            for x in range(-area_size, area_size + 1):
                for y in range(-area_size, area_size + 1):
                    node = (x, y)
                    graph[node] = []
                    # Adding connections to neighbors
                    for direction in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # right, down, left, up
                        neighbor = (x + direction[0], y + direction[1])
                        if(neighbor in self.blocked_nodes): continue
                        if(neighbor in self.bfs_path_used): continue
                        if neighbor in self.nodes:
                            continue
                        graph[node].append(neighbor) 

            # Initialize the queue and the came_from map
            queue = deque([start])
            came_from = {start: None}
            print(f'Start: {start}, Goal: {goal}')  # Debugging message

            while queue:
                current = queue.popleft()
                #print(f'Current: {current}')  # Debugging message

                # Scans the neighbors of the current node using the generated graph
                if current not in graph:  # Make sure the current node is in the graph
                    #print(f'Warning: Current node {current} not in graph.')  # Warning message
                    continue  # Exit if the node is not in the graph

                # Check if we have reached the goal
                if current == goal:
                    #print('Goal reached!')  # Debugging message
                    break
                
                # Add neighbors to the queue if they have not been visited
                for neighbor in graph[current]:
                    if neighbor not in came_from:  # Make sure not to visit already explored nodes
                        queue.append(neighbor)
                        came_from[neighbor] = current
                        #print(f'Added to queue: {neighbor}')  # Debugging message

            # Rebuild the road
            path = []
            current = goal
            if current not in came_from:  # If the target was not reached
                print('Goal not reachable.')  # Debugging message
                return []  # Returns an empty path if the goal was not achievable

            while current is not None:
                path.append(current)
                current = came_from[current]

            path.reverse()  # Reverse the path to get the right order
            #remove the start and end string
            for i in range(0, len(path)):
                if path[i] == start:
                    path.pop(i)
                    break
            for i in range(len(path)-1, 0, -1):
                if path[i] == goal:
                    path.pop(i)
                    break
            
            print(f'Path: {path}')  # Debugging message
            return path
        
        
        @lru_cache(maxsize=None)
        def is_valid(self,coordinate):
            # Check if the coordinate is within the grid and is not blocked by an existing node
            x, y = coordinate
            return not self.is_node_occupied(coordinate)


        @lru_cache(maxsize=None)
        def is_node_occupied(self,coordinate):
            # Check if a node already exists at the given coordinates
            return any(node.coordinates['x'] == coordinate[0] and node.coordinates['y'] == coordinate[1] for node in self.nodes.values())

        def load_file_dialog(self):
            filename = filedialog.askopenfilename(filetypes=[("YAML files", "*.yml;*.yaml")])
            if filename:
                self.load_data(filename)
                #set window title to Skill Tree Editor - filename
                simple_filename = filename.split("/")[-1]
                self.master.title(f"Skill Tree Editor - {simple_filename}")

        def setup_blocked_nodes(self):
            if 'blocked_nodes' in self.original_data['extra']:
                for node in self.original_data['extra']['blocked_nodes']:
                    self.blocked_nodes.append((node['x'], node['y']))
        def open_new_file(self):
                filename = filedialog.askopenfilename(filetypes=[("YAML files", "*.yml;*.yaml")])
                if filename:
                    #clear old data
                    self.nodes.clear()
                    self.node_matrix.clear()
                    self.blocked_nodes.clear()
                    
                    self.load_data(filename)
                    self.reset_to_original()
        def load_data(self, filename):
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    #self.original_data = yaml.safe_load(file)
                    #use normal load to preserve order and encoding
                    self.original_data = yaml.load(file, Loader=yaml.FullLoader)
                    self.nodes.clear()
                    self.node_matrix.clear()
                    if 'extra' not in self.original_data:
                        self.original_data['extra'] = {}
                        
                    for key, value in self.original_data['nodes'].items():
                        if "x" in value["coordinates"]:
                            x = value['coordinates']['x']
                            y = value['coordinates']['y']
                        else:
                            splited = value['coordinates'].split(",")
                            x = int(splited[0])
                            y = int(splited[1])
                        #make x a full int no, no decimals
                        x = round(x)
                        y = round(y)
                        name = value['name']
                        parents = value.get('parents', {})
                        additional_data = {k: v for k, v in value.items() if k not in ['name', 'coordinates', 'parents']}
                        node = SkillNode(name, x, y, parents, **additional_data)
                        self.nodes[key] = node
                        self.node_matrix[(x, y)] = key
                        self.setup_blocked_nodes()
                self.save_state()
                self.draw_nodes()
            except Exception as e:
                messagebox.showerror("Error", f"Error loading the file: {filename} with error {e}")

        def draw_grid(self):
            self.canvas.delete("grid")
            for i in range(-400, 1201, self.grid_size):
                e = i
                x1 = self.canvas_x(e)
                y1 = self.canvas_y(-400)
                x2 = x1
                y2 = self.canvas_y(1200)
                self.canvas.create_line(x1, y1, x2, y2, fill="lightgray", tags="grid")
                
                y1 = self.canvas_y(e)
                x1 = self.canvas_x(-400)
                y2 = y1
                x2 = self.canvas_x(1200)
                self.canvas.create_line(x1, y1, x2, y2, fill="lightgray", tags="grid")
            
        @lru_cache(maxsize=2)
        def create_detection_rectangle(self, xcord, ycord):
            #if self.is_visible(xcord, ycord):
            x = self.canvas_x((xcord + 0.5) * self.grid_size)
            y = self.canvas_y(-(ycord + 0.5) * self.grid_size)
            #create transparent rectangle to detect mause click
            d = self.canvas.create_rectangle(x-self.node_size/2, y-self.node_size/2, x+self.node_size/2, y+self.node_size/2, fill="", outline="", tags="filler")
            return d
        
        def draw_nodes(self):
            self.canvas.delete("node", "text", "line", "selection")
            
            
            for xcord in range(-self.grid_size,self.grid_size,1):
                for ycord in range(-self.grid_size,self.grid_size,1):
                    de = self.create_detection_rectangle(xcord, ycord)
                    if de is not None:
                        self.detection_rectangles[(xcord, ycord)] = de
                        
            # Draw lines first
            self.bfs_path_used = []
            for key, node in self.nodes.items():
                x = self.canvas_x((node.coordinates['x'] + 0.5) * self.grid_size)
                y = self.canvas_y(-(node.coordinates['y'] + 0.5) * self.grid_size)
                childcords = (node.coordinates['x'],node.coordinates['y'])
                for parent_type, parents in node.parents.items():
                    for parent in parents:
                        if parent in self.nodes:
                            parent_node = self.nodes[parent]
                            px = self.canvas_x((parent_node.coordinates['x'] + 0.5) * self.grid_size)
                            py = self.canvas_y(-(parent_node.coordinates['y'] + 0.5) * self.grid_size)
                            
                            if self.preview:
                                    path = self.bfs_path((node.coordinates['x'],node.coordinates['y']),(parent_node.coordinates['x'],parent_node.coordinates['y']))
                                    
                                    #go for every cordinate in node and get if the next location direction 
                                    #is right,left,up,down,up-right,up-left,down-right,down-left
                                    for nodepath in range(0, len(path)):
                                        self.bfs_path_used.append(path[nodepath])
                                        x,y = childcords[0],childcords[1]
                                    
                                        if nodepath-1 in range(0,len(path)):
                                            x,y = path[nodepath-1][0],path[nodepath-1][1]
                                        elif nodepath == 0:
                                            x,y = childcords[0],childcords[1]
                                        else:
                                            x,y = parent_node.coordinates['x'],parent_node.coordinates['y']
                                            
                                        direction = "right"
                                        
                                        # Coordenadas actuales
                                        currentx, currenty = path[nodepath][0], path[nodepath][1]
                                        
                                        
                                        dify = currenty-y
                                        difx = currentx-x
                                        if (dify) >= 1 and (difx) == 0:
                                            direction = "up"
                                        elif (dify) <= -1 and (difx) == 0:
                                            direction = "down"
                                        elif (dify) == 0 and (difx) >= 1:
                                            direction = "left"
                                        elif (dify) == 0 and (difx) <= -1:
                                            direction = "right"
                                        
                                        # Coordenadas anteriores
                                        if nodepath > 0:
                                            prevx, prevy = path[nodepath-1][0], path[nodepath-1][1]
                                        else:
                                            prevx, prevy = childcords[0], childcords[1]
                                        
                                        # Coordenadas siguientes
                                        if nodepath+1 < len(path):
                                            nextx, nexty = path[nodepath+1][0], path[nodepath+1][1]
                                        else:
                                            nextx, nexty = parent_node.coordinates['x'], parent_node.coordinates['y']
                                        
                                        # Deltas between the previous, current and next points
                                        dx_prev, dy_prev = currentx - prevx, currenty - prevy
                                        dx_next, dy_next = nextx - currentx, nexty - currenty
                                        
                                        castext = ""
                                        # Detect if there is a turn by comparing the changes of direction
                                        if (dx_prev != dx_next) or (dy_prev != dy_next):
                                        # print(f'Corner detected en: {currentx},{currenty}')
                                            # Logic to detect addresses
                                            if dx_prev == 0 and dy_prev == 1:  # From the bottom up
                                                if dx_next == 1 and dy_next == 0:
                                                    direction = "down-right"
                                                    castext = "#1"
                                                elif dx_next == -1 and dy_next == 0:
                                                    direction = "down-left"
                                                    castext = "#2 "
                                                else:
                                                    direction = "up"
                                                    castext = "#3"
                                            elif dx_prev == 0 and dy_prev == -1:  # From top to bottom
                                                if dx_next == 1 and dy_next == 0:
                                                    direction = "up-right"
                                                    castext = "#4"
                                                elif dx_next == -1 and dy_next == 0:
                                                    direction = "up-left"
                                                    castext = "#5"
                                                else:
                                                    direction = "down"
                                                    castext = "#6"
                                            elif dx_prev == 1 and dy_prev == 0:  # From left to right
                                                if dx_next == 0 and dy_next == 1:
                                                    direction = "up-left"
                                                    castext = "#7"
                                                elif dx_next == 0 and dy_next == -1:
                                                    direction = "down-left"
                                                    castext = "#8"
                                                else:
                                                    direction = "right"
                                                    castext = "#9"
                                            elif dx_prev == -1 and dy_prev == 0:  # From right to left
                                                if dx_next == 0 and dy_next == 1:
                                                    direction = "up-right"
                                                    castext = "#10"
                                                elif dx_next == 0 and dy_next == -1:
                                                    direction = "up-left"
                                                    castext = "#11"
                                                else:
                                                    direction = "left"
                                                    castext = "#12"
                                            else:  # Diagonal corners
                                                if dx_prev == 1 and dy_prev == 1:
                                                    direction = "up-right"
                                                    castext = "#13"
                                                elif dx_prev == -1 and dy_prev == 1:
                                                    direction = "up-left"
                                                    castext = "#14"
                                                elif dx_prev == 1 and dy_prev == -1:
                                                    direction = "down-right"
                                                    castext = "#15"
                                                elif dx_prev == -1 and dy_prev == -1:
                                                    direction = "down-left"
                                                    castext = "#16"
                                            
                                            # Assign the icon according to the detected address
                                        cordinateForImage = self.canvas_x((currentx + 0.5) * self.grid_size), self.canvas_y(-(currenty + 0.5) * self.grid_size)
                                        self.canvas.create_image(cordinateForImage[0], cordinateForImage[1], image=textures[direction], tags="node")

                                        #write debug text
                                        self.canvas.create_text(cordinateForImage[0], cordinateForImage[1], text=castext, tags="text")

                                                                        
                            else:
                                if(self.calculateAngle((node.coordinates['x'],node.coordinates['y']),(parent_node.coordinates['x'],parent_node.coordinates['y'])) % 45 == 0
                                ):
                                    self.canvas.create_line(x, y, px, py, fill="gray", width=3, tags="line")
                                else:
                                    self.canvas.create_line(x, y, px, py, fill="red", width=3, tags="line")
            
            # Then draw nodes
            for key, node in self.nodes.items():
                x = self.canvas_x((node.coordinates['x'] + 0.5) * self.grid_size)
                y = self.canvas_y(-(node.coordinates['y'] + 0.5) * self.grid_size)
                
                color = "default"
                
                if "display" in node.additional_data and "unlocked" in node.additional_data["display"]:
                    displayData = node.additional_data["display"]["unlocked"]
                    for dke, value in json_data['nodes'].items():
                        if value["unlocked"] == displayData["custom-model-data"]:
                            color = dke
                            break
                
                # Create the node image
                rect = self.canvas.create_image(x, y, image=textures[color], tags="node")
                
                self.node_rectangles[key] = rect
                
                if key == self.selected_node:
                    half_size = self.node_size*(self.scale+0.1) // 2 
                    if(color == 'default'):
                        color = 'red'
                    self.canvas.create_rectangle(x-half_size-2, y-half_size-2, x+half_size+2, y+half_size+2, outline=color, width=3, tags="selection")

            
            for node in self.blocked_nodes:
                x = self.canvas_x((node[0] + 0.5) * self.grid_size)
                y = self.canvas_y(-(node[1] + 0.5) * self.grid_size)
                blocknode = self.canvas.create_image(x, y, image=textures['blocked'], tags="node")
                print(f'The blocked Node in {node}')  # Debugging message
                self.block_rectangles[(node[0], node[1])] = blocknode

        def canvas_x(self, x):
            return (x - self.offset_x) * self.scale + self.offset_x

        def canvas_y(self, y):
            return (y - self.offset_y) * self.scale + self.offset_y

        def select_node(self, event):
            def get_selected_item(item_rectangles):
                """Returns the key of the selected item, if it is found."""
                item = self.canvas.find_closest(event.x, event.y)[0]
                for key, rect in item_rectangles.items():
                    if rect == item:
                        return key
                return None

            # We determine the nearest element and look for whether it is a node or a block
            selected_node = get_selected_item(self.node_rectangles)
            selected_blocknode = get_selected_item(self.block_rectangles)

            if selected_node is not None:
                self.selected_node = selected_node
                self.selected_blocknode = None
                print(f'A node has been selected: {self.selected_node}')
            elif selected_blocknode is not None:
                self.selected_blocknode = selected_blocknode
                self.selected_node = None
                print(f'The block node is selected: {self.selected_blocknode}')
            else:
                self.selected_node = None
                self.selected_blocknode = None
                print('Nothing is selected')

            self.draw_nodes()

            # Saving the initial coordinates for possible further dragging
            self.drag_start_x = event.x
            self.drag_start_y = event.y

        def move_selected_node(self, dx, dy):
            if self.selected_node:

                node = self.nodes[self.selected_node]
                new_x = node.coordinates['x'] + dx
                new_y = node.coordinates['y'] + dy
                cords = (new_x, new_y)
                if (cords not in self.node_matrix) or self.node_matrix[cords] == self.selected_node:
                    if(cords in self.blocked_nodes ):
                        return
                    self.save_state()
                    if((node.coordinates['x'], node.coordinates['y']) in self.node_matrix):
                        del self.node_matrix[(node.coordinates['x'], node.coordinates['y'])]
                    node.coordinates['x'] = new_x
                    node.coordinates['y'] = new_y
                    self.node_matrix[cords] = self.selected_node
                    self.draw_nodes()
                    addLineLog(f"[!] Moved node {self.selected_node} to {new_x}, {new_y}")
        def move_node(self, event):
            if self.selected_node:
                #x = (event.x - self.offset_x) // self.grid_size
                #y = (self.offset_y - event.y) // self.grid_size
                #x += 10
                #y -= 5
                mause =  self.get_mouse_grid_slot(event)
                if mause is None:
                    return
                x = mause[0]
                y = mause[1]
                if (x, y) not in self.node_matrix or self.node_matrix[(x, y)] == self.selected_node:
                    if((x,y) in self.blocked_nodes ):
                        return
                    self.nodes[self.selected_node].coordinates['x'] = x
                    self.nodes[self.selected_node].coordinates['y'] = y
                    self.draw_nodes()
                #use the move_selected_node function
                #self.move_selected_node(self.nodes[self.selected_node].coordinates['x']-x, self.nodes[self.selected_node].coordinates['y']-y)

        def zoom(self, event):
            factor = 1.1 if event.delta > 0 else 1/1.1
            old_scale = self.scale
            self.scale *= factor
            self.offset_x = event.x + (self.offset_x - event.x) * (self.scale / old_scale)
            self.offset_y = event.y + (self.offset_y - event.y) * (self.scale / old_scale)
            #self.grid_size *= factor
            #self.grid_size = round(self.grid_size)
            self.defaultRender()

        def drag_canvas(self, event):
            try:
                # If the node is not selected, move the canvas
                if self.selected_node is None:
                    # Checking for initialization of the coordinates of the beginning of the movement
                    if not hasattr(self, 'drag_start_x') or not hasattr(self, 'drag_start_y'):
                        raise AttributeError("drag_start_x or drag_start_y were not initialized")

                    # Checking that the scale is set and not equal to zero
                    if self.scale == 0:
                        raise ValueError("The scale cannot be equal to 0")

                    # Calculating the offset based on the scale
                    canvas_dx = (event.x - self.drag_start_x) * self.scale
                    canvas_dy = (event.y - self.drag_start_y) * self.scale

                    # Logging of movements
                    print(f'Dragging canvas by dx: {canvas_dx}, dy: {canvas_dy}')
                    print(f'Offsets before: X: {self.offset_x}, Y: {self.offset_y}')

                    # Updating the offsets
                    self.offset_x += canvas_dx
                    self.offset_y += canvas_dy

                    print(f'Offsets after: X: {self.offset_x}, Y: {self.offset_y}')

                    # Updating the starting coordinates for the next move
                    self.drag_start_x = event.x
                    self.drag_start_y = event.y

                    # Redrawing the canvas
                    self.defaultRender()

                # If the node is selected, move it
                else:
                    self.move_node(event)

            except AttributeError as e:
                print(f'Error: {e}')
            except ValueError as e:
                print(f'Error: {e}')

        def stop_drag(self, event):
            self.drag_start_x = 0
            self.drag_start_y = 0
            
        @lru_cache(maxsize=None)
        def get_mouse_grid_slot(self, event):
            #get closes with tag filler
            items = self.canvas.find_closest(event.x, event.y)
            maxIndex = 2
            for ide in range(0, len(items)):
                if ide > maxIndex:
                    break
                item = items[ide] 
                if(item in self.detection_rectangles.values()):
                    for key, rect in self.detection_rectangles.items():
                        if rect == item:
                            return key
                elif item in self.node_rectangles.values():
                    for key, rect in self.node_rectangles.items():
                        if rect == item:
                            return self.nodes[key].coordinates['x'], self.nodes[key].coordinates['y']
                elif item in self.block_rectangles.values():
                    for key, rect in self.block_rectangles.items():
                        if rect == item:
                            return key
            
        def motion_event(self, event):
            item = self.canvas.find_closest(event.x, event.y)[0]
            for key, rect in self.node_rectangles.items():
                if rect == item:
                    x, y = self.canvas.coords(rect)[:2]
                    self.canvas.delete("hover_text")
                    
                    otext: str = self.nodes[key].name
                    
                    #replace any <#FFFFFF> regex with ""
                    otext = re.sub(r'<#[0-9A-Fa-f]{6}>', '', otext)
                    otext += f"\n({self.nodes[key].coordinates['x']}, {self.nodes[key].coordinates['y']})"
                    otext += f"\nKey: {key}"
                    
                    self.canvas.create_text(x + self.node_size/2, y - self.node_size/2 - 10, 
                                            text=otext, tags="hover_text", anchor="sw")
                    return
            self.canvas.delete("hover_text")


        @lru_cache(maxsize=None)
        def isDistanceTwo(self,start: [int, int], goal: [int, int]) -> bool:
            # Calculate the differences in x and y coordinates
            x_diff = abs(goal[0] - start[0])
            y_diff = abs(goal[1] - start[1])

            # Check if either x or y distance is exactly two, but not both
            return (x_diff == 2 and y_diff == 0) or (x_diff == 0 and y_diff == 2)
        
        @lru_cache(maxsize=None)
        def verifyIsAdyacent(self, start: [int, int], goal: [int, int]) -> bool:
            # Calculate the differences in the x and y coordinates
            x_diff = abs(goal[0] - start[0])
            y_diff = abs(goal[1] - start[1])

            # Check if the goal is one unit away in any direction (top, down, right, left)
            # This means either:
            # - The x-coordinates are the same and the y-coordinates differ by 1 (up/down),
            # - OR the y-coordinates are the same and the x-coordinates differ by 1 (left/right).
            if (x_diff == 1 and y_diff == 0) or (x_diff == 0 and y_diff == 1):
                return True
            else:
                return False



        def save_data(self):
            save_name = filedialog.asksaveasfilename(filetypes=[("YAML files", "*.yml;*.yaml")])
            newnodes = self.nodes.copy()
            #remove all original paths
            
            for key, node in newnodes.items():
                node.set('paths', {})
                
            self.bfs_path_used = []
                
            for key, node in self.nodes.items():
                currx, curry = node.coordinates['x'], node.coordinates['y']
                #get parents
                for parent_type, parent_nodes in node.parents.items():
                    for parent_node_key, parent_node_value in parent_nodes.items():
                        parentx, parenty = newnodes[parent_node_key].coordinates['x'], newnodes[parent_node_key].coordinates['y']
                        #generate a path from parent to child , remember to check if node already exists in the position
                        print(newnodes[parent_node_key])
                        paths = newnodes[parent_node_key].get('paths', {})
                        #verify if distance between nodes is 1
                        if self.verifyIsAdyacent((parentx, parenty), (currx, curry)):
                            continue
                        else:
                            start = (parentx, parenty)
                            goal = (currx, curry)
                            path = self.bfs_path(start, goal)
                            
                            # Save the path
                            if path:
                                index = 1
                                paths[key] ={}
                                for step in path:
                                    if version == "OLD":
                                        paths[key]["path"+str(index)] = {'x': step[0], 'y': step[1]}
                                    else:
                                        paths[key]["path"+str(index)] = f'{step[0]},{step[1]}'
                                    index += 1
                        newnodes[parent_node_key].set('paths', paths)
            
            data = {'extra': self.original_data['extra'],'nodes': {key: {
                'name': node.name,
                'coordinates': node.coordinates,
                'parents': node.parents,
                **node.additional_data
            } for key, node in newnodes.items()}}
            
            for node in data['nodes']:
                if version == "NEW":
                    cords = data['nodes'][node]['coordinates']
                    data['nodes'][node]['coordinates'] = f'{cords["x"]},{cords["y"]}'
            
            self.original_data['extra'] = data['extra']
            self.original_data['nodes'] = data['nodes']
            with open(save_name, 'w', encoding='utf-8') as file:
                yaml.dump(self.original_data, file, allow_unicode=True, default_flow_style=False)
            messagebox.showinfo("Save", f"Changes saved in {save_name}")

        def save_data_ry(self):
            save_name = filedialog.asksaveasfilename(filetypes=[("YAML files", "*.yml;*.yaml")])
            newnodes = self.nodes.copy()
            #remove all original paths
            for key, node in newnodes.items():
                node.set('paths', {})
            for key, node in newnodes.items():
                currx, curry = node.coordinates['x'], node.coordinates['y']
                curry = curry * -1
                newnodes[key].coordinates['y'] = curry
            for key, node in self.nodes.items():
                currx, curry = node.coordinates['x'], node.coordinates['y']
                #get parents
                for parent_type, parent_nodes in node.parents.items():
                    for parent_node_key, parent_node_value in parent_nodes.items():
                        parentx, parenty = newnodes[parent_node_key].coordinates['x'], newnodes[parent_node_key].coordinates['y']
                        
                        #generate a path from parent to child , remember to check if node already exists in the position
                        print(newnodes[parent_node_key])
                        paths = newnodes[parent_node_key].get('paths', {})
                        #verify if distance between nodes is 1
                        if self.verifyIsAdyacent((parentx, parenty), (currx, curry)):
                            continue
                        elif self.isDistanceTwo((parentx, parenty), (currx, curry)):
                            paths[key] = {'path': {'x': currx, 'y': curry}}
                        else:
                            start = (parentx, parenty)
                            goal = (currx, curry)
                            path = self.bfs_path(start, goal)
                            # Save the path
                            if path:
                                index = 1
                                paths[key] ={}
                                for step in path:
                                    self.bfs_path_used.append(step)
                                    paths[key]["path"+str(index)] = {'x': step[0], 'y': step[1]}
                                    index += 1
                        newnodes[parent_node_key].set('paths', paths)
            
            data = {'nodes': {key: {
                'name': node.name,
                'coordinates': node.coordinates,
                'parents': node.parents,
                **node.additional_data
            } for key, node in newnodes.items()}}
            with open(save_name, 'w', encoding='utf-8') as file:
                yaml.dump(data, file,encoding='utf-8')
            messagebox.showinfo("Save", f"Changes saved in {save_name}")

        def reset_to_original(self):
            
            factor = 1;
            self.scale = 1
            self.offset_x = 0
            self.offset_y = 0
            self.grid_size = 40
            self.defaultRender()

        def save_state(self):
            self.history.append(copy.deepcopy(self.nodes))
            self.future.clear()

        def undo(self, event=None):
            if self.history:
                self.future.append(copy.deepcopy(self.nodes))
                self.nodes = self.history.pop()
                self.update_node_matrix()
                self.draw_nodes()

        def redo(self, event=None):
            if self.future:
                self.history.append(copy.deepcopy(self.nodes))
                self.nodes = self.future.pop()
                self.update_node_matrix()
                self.draw_nodes()

        def update_node_matrix(self):
            self.node_matrix.clear()
            for key, node in self.nodes.items():
                self.node_matrix[(node.coordinates['x'], node.coordinates['y'])] = key

    if __name__ == "__main__" and continueProgram:
        
        
        
        root = tk.Tk()
        editor = SkillTreeEditor(root)
        root.mainloop()
except Exception as e:
    message=""
    if hasattr(e, 'message'):
        message=e.message
    else:
        message=str(e)

    addLineLog(f'[!] Error {message}')