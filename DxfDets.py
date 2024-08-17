import tkinter as tk
import math
import ezdxf
from ezdxf import bbox
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import shapely
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


from tkinter import ttk, filedialog, messagebox
from svg2dxf import svg_to_dxf
import os

# Create the root window
root = tk.Tk()

# Set window properties
root.title("DXF Viewer")
root.geometry("800x600")  # Width x Height

def show_message(title, message):
    messagebox.showinfo(title, message)

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("DXF files", "*.dxf"), ("SVG files", "*.svg")])
    if file_path:
        open_file(file_path)
scale_factor = 1
# Function to handle the drop event
def open_file(file_path):
    scale_factor = 1
    print(f"File selected: {file_path}")
    if not os.access(file_path, os.R_OK):
        show_message("Error", f"Cannot read file {file_path}. Check if the file exists and you have read permissions.")
        return
    if (file_path.endswith('.svg')):
        show_message("Error", f"we do not support svg files")
        return
        #doc = svg_to_dxf(file_path, dpi=int(dpi_entry.get()))
        #scale_factor = 25.4 / int(dpi_entry.get())
    else:
        doc = ezdxf.readfile(file_path)
    render_dxf(doc)
    calculateDetails(doc, tree, scale_factor)

def calculateDetails(doc, tree, scale_factor):
    UNIT_TO_MM = 1
    print("Calculating details...")
    msp = doc.modelspace()
    
    perimeters = []
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')
    box = bbox.extents(msp)
    min_x = box.extmin[0]
    max_x = box.extmax[0]
    min_y = box.extmin[1]
    max_y = box.extmax[1]
    for entity in msp:
        perimeter = 0
        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            perimeter = math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2)
        elif entity.dxftype() == 'CIRCLE':
            radius = entity.dxf.radius
            perimeter = 2 * math.pi * radius
        elif entity.dxftype() == 'ARC':
            radius = entity.dxf.radius
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)
            angle = end_angle - start_angle
            if angle < 0:
                angle += 2 * math.pi
            perimeter = radius * angle
        elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
            path = ezdxf.path.make_path(entity)
            vertices = list(path.flattening(0.01))
            polygon = shapely.geometry.Polygon(vertices)
            area = polygon.area
            perimeter = polygon.length
            print(f"Area = {area:.3f}, Perimeter = {perimeter:.3f}")
            
        # Convert perimeter to millimeters
        perimeter_mm = perimeter * UNIT_TO_MM
        perimeters.append({'type': entity.dxftype(), 'perimeter_mm': perimeter_mm})
    
    totalPerimeter = 0
    pierceCount = 0
    for p in perimeters:
        pierceCount += 1
        totalPerimeter += p['perimeter_mm']
    
    # Calculate width and height
    width = max_x - min_x
    height = max_y - min_y

    clear_tree()
    tree.insert('', 'end', values=('Cut Distance', totalPerimeter * scale_factor))
    tree.insert('', 'end', values=('Pierce Count', pierceCount * scale_factor))
    tree.insert('', 'end', values=('Part Width', width * scale_factor))
    tree.insert('', 'end', values=('Part Height', height * scale_factor))

def render_dxf(doc):
    print("Rendering DXF...")
    # Clear the previous drawing
    for widget in bottom_frame.winfo_children():
        widget.destroy()
    
    # Render the new drawing
    msp = doc.modelspace()
    fig: plt.Figure = plt.figure()
    ax: plt.Axes = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp, finalize=True)
    ax.set_aspect('equal')
    ax.autoscale()
    canvas = FigureCanvasTkAgg(fig, master=bottom_frame)
    bottom_frame.grid_rowconfigure(0, weight=1)
    bottom_frame.grid_columnconfigure(0, weight=1)
    canvas.draw()
    canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
    plt.close(fig)


def clear_tree():
    for item in tree.get_children():
        tree.delete(item)

def copy_all_to_clipboard():
    clipboard_text = ""
    for item in tree.get_children():
        values = tree.item(item, 'values')
        clipboard_text += "\t".join(values) + "\n"
    root.clipboard_clear()
    root.clipboard_append(clipboard_text)

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(2, weight=2)

top_frame = tk.Frame(root)
top_frame.grid(row=0, column=0, sticky='ew')

middle_frame = tk.Frame(root)
middle_frame.grid(row=1, column=0, sticky='ew')

bottom_frame = tk.Frame(root)
bottom_frame.grid(row=2, column=0, sticky='nsew')

open_button = tk.Button(top_frame, text="Open File", command=select_file)
open_button.pack(side='left', pady=10)

copy_button = tk.Button(middle_frame, text="Copy All", command=copy_all_to_clipboard)

# Create a table using ttk.Treeview
columns = ('Parameter', 'Value')
tree = ttk.Treeview(middle_frame, columns=columns, show='headings', height=4)

# Define headings
tree.heading('Parameter', text='Parameter')
tree.heading('Value', text='Value')

# Insert rows
tree.insert('', 'end', values=('Cut Distance', "tbd"))
tree.insert('', 'end', values=('Pierce Count', "tbd"))
tree.insert('', 'end', values=('Part Width', "tbd"))
tree.insert('', 'end', values=('Part Height', "tbd"))

# Pack the table at the bottom of the window
tree.pack(side='top', fill='both', expand=True)  
copy_button.pack(side='bottom')

# Add SVG Import Setting DPI label and text box
#dpi_label = tk.Label(top_frame, text="SVG Import Setting DPI")
#dpi_label.pack(side='left', padx=10, pady=10)

#dpi_entry = tk.Entry(top_frame)
#dpi_entry.insert(0, "72")
#dpi_entry.pack(side='left', padx=10, pady=10)


# Run the main event loop
root.mainloop()