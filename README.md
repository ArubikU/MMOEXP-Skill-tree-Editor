# MMOEXP-Skill tree Editor
 A skill tree editor created for mmocore using python

## How to use

1. Clone the repository
2. Edit the textures.json to add references to your textures, and modify the custom model data to detect the textures
3. Setup your version on conf.json and your material for the skill tree
4. Run the script


## How to use the editor

### Buttons
- **Open New File**: Open a new file withouth saving the current one
- **Save**: Open a window to select where to save the file
- **Save RY**: Save the fil with inverted Y axis
- **Reset**: Reset the zoom and camera position
- **Undo** (Ctrl + Z): Undo the last action
- **Redo** (Ctrl + Y): Redo the last action
- **Add Node**: Add a new node to the tree openin a new window to set values
- **Switch Mode**: Switch mode from Line connections to Texture connections
### Dropboxes
- **Select Color**: Select the color of the node and apply whit Enter on a selected node

### Mouse
- **Left Click**: Select a node
- **Double Left Click**: switch color if a selected node, if a empty slot the editor will try to add a block
- **Drag node**: The system will try to move the node using your mouse position

### WASD / Arrow keys
- **W / Up Arrow**: Move the selected node up
- **S / Down Arrow**: Move the selected node down
- **A / Left Arrow**: Move the selected node left
- **D / Right Arrow**: Move the selected node right


# License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE) file for details
```