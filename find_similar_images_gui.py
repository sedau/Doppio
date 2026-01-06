"""
Find similar images with GUI for reviewing and deleting duplicates.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk, ImageOps
import argparse
from send2trash import send2trash
from image_similarity import find_similar_images


class SimilarImagesFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Similar Images Finder")
        self.root.geometry("1200x800")
        
        self.image_groups = []
        self.current_group_index = 0
        self.folder_path = None
        self.threshold = 5
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top frame for controls
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Folder:").pack(side=tk.LEFT, padx=5)
        self.folder_label = ttk.Label(control_frame, text="No folder selected", relief=tk.SUNKEN)
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(control_frame, text="Select Folder", command=self.select_folder).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Threshold:").pack(side=tk.LEFT, padx=5)
        self.threshold_var = tk.IntVar(value=5)
        threshold_spin = ttk.Spinbox(control_frame, from_=0, to=20, width=5, 
                                     textvariable=self.threshold_var)
        threshold_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Find Similar", command=self.find_similar).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.Frame(self.root, padding="10")
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="Select a folder and click 'Find Similar' to start")
        self.status_label.pack(side=tk.LEFT)
        
        # Navigation frame
        nav_frame = ttk.Frame(self.root, padding="10")
        nav_frame.pack(fill=tk.X)
        
        self.prev_button = ttk.Button(nav_frame, text="◀ Previous Group", 
                                      command=self.prev_group, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.group_label = ttk.Label(nav_frame, text="No groups found")
        self.group_label.pack(side=tk.LEFT, padx=20)
        
        self.next_button = ttk.Button(nav_frame, text="Next Group ▶", 
                                      command=self.next_group, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        action_frame = ttk.Frame(nav_frame)
        action_frame.pack(side=tk.RIGHT)
        
        ttk.Button(action_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=5)
        self.delete_button = ttk.Button(action_frame, text="🗑️ Move Selected to Recycle Bin", 
                                       command=self.delete_selected, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # Canvas with scrollbar for images
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.canvas_frame, anchor=tk.NW)
        
        self.canvas_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Images")
        if folder:
            self.folder_path = folder
            self.folder_label.config(text=folder)
            
    def find_similar(self):
        if not self.folder_path:
            messagebox.showwarning("No Folder", "Please select a folder first")
            return
            
        self.threshold = self.threshold_var.get()
        
        def update_status(message):
            self.status_label.config(text=message)
            self.root.update()
        
        # Use the extracted function
        self.image_groups = find_similar_images(
            self.folder_path, 
            self.threshold,
            progress_callback=update_status
        )
        self.current_group_index = 0
        
        if self.image_groups:
            self.status_label.config(text=f"Found {len(self.image_groups)} groups of similar images")
            self.show_current_group()
            self.prev_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="No similar images found. Try increasing the threshold.")
            self.clear_display()
            
    def show_current_group(self):
        if not self.image_groups:
            return
            
        # Clear previous display
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        group = self.image_groups[self.current_group_index]
        self.group_label.config(text=f"Group {self.current_group_index + 1} of {len(self.image_groups)} "
                                     f"({len(group.image_paths)} images)")
        
        # Display images in a grid
        columns = 3
        thumbnail_size = (300, 300)
        
        for idx, img_path in enumerate(group.image_paths):
            row = idx // columns
            col = idx % columns
            
            # Frame for each image
            img_frame = ttk.Frame(self.canvas_frame, relief=tk.RAISED, borderwidth=2)
            img_frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            try:
                # Load and resize image
                img = Image.open(img_path)
                # Fix orientation based on EXIF data
                img = ImageOps.exif_transpose(img)
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Image label
                img_label = ttk.Label(img_frame, image=photo)
                img_label.image = photo  # Keep a reference
                img_label.pack(padx=5, pady=5)
                
                # Checkbox and filename
                info_frame = ttk.Frame(img_frame)
                info_frame.pack(fill=tk.X, padx=5, pady=5)
                
                var = tk.BooleanVar(value=group.selected[idx])
                checkbox = ttk.Checkbutton(info_frame, variable=var,
                                          command=lambda i=idx, v=var: self.toggle_selection(i, v))
                checkbox.pack(side=tk.LEFT)
                
                filename = Path(img_path).name
                file_label = ttk.Label(info_frame, text=filename, wraplength=250)
                file_label.pack(side=tk.LEFT, padx=5)
                
                # File size
                size = os.path.getsize(img_path)
                size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB"
                size_label = ttk.Label(img_frame, text=size_str, foreground='gray')
                size_label.pack()
                
            except Exception as e:
                error_label = ttk.Label(img_frame, text=f"Error loading image:\n{Path(img_path).name}")
                error_label.pack()
        
        # Configure grid columns to be equal width
        for col in range(columns):
            self.canvas_frame.columnconfigure(col, weight=1, uniform='cols')
        
        self.canvas.yview_moveto(0)
        
    def toggle_selection(self, idx, var):
        if self.image_groups:
            self.image_groups[self.current_group_index].selected[idx] = var.get()
            
    def select_all(self):
        if self.image_groups:
            group = self.image_groups[self.current_group_index]
            group.selected = [True] * len(group.image_paths)
            self.show_current_group()
            
    def deselect_all(self):
        if self.image_groups:
            group = self.image_groups[self.current_group_index]
            group.selected = [False] * len(group.image_paths)
            self.show_current_group()
            
    def delete_selected(self):
        if not self.image_groups:
            return
            
        group = self.image_groups[self.current_group_index]
        selected_paths = [path for path, selected in zip(group.image_paths, group.selected) if selected]
        
        if not selected_paths:
            messagebox.showinfo("No Selection", "Please select images to delete")
            return
            
        result = messagebox.askyesno("Confirm Delete", 
                                     f"Move {len(selected_paths)} selected image(s) to Recycle Bin?")
        if result:
            try:
                for path in selected_paths:
                    send2trash(path)
                
                messagebox.showinfo("Success", f"Moved {len(selected_paths)} image(s) to Recycle Bin")
                
                # Remove deleted images from current group
                group.image_paths = [path for path, selected in zip(group.image_paths, group.selected) 
                                    if not selected]
                group.selected = [False] * len(group.image_paths)
                
                # If group now has less than 2 images, remove it
                if len(group.image_paths) < 2:
                    self.image_groups.pop(self.current_group_index)
                    if self.current_group_index >= len(self.image_groups):
                        self.current_group_index = max(0, len(self.image_groups) - 1)
                
                if self.image_groups:
                    self.show_current_group()
                else:
                    self.status_label.config(text="All groups processed!")
                    self.clear_display()
                    self.prev_button.config(state=tk.DISABLED)
                    self.next_button.config(state=tk.DISABLED)
                    self.delete_button.config(state=tk.DISABLED)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error moving files: {e}")
                
    def prev_group(self):
        if self.current_group_index > 0:
            self.current_group_index -= 1
            self.show_current_group()
            
    def next_group(self):
        if self.current_group_index < len(self.image_groups) - 1:
            self.current_group_index += 1
            self.show_current_group()
            
    def clear_display(self):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        self.group_label.config(text="No groups to display")


def main():
    parser = argparse.ArgumentParser(description='Find similar images with GUI')
    parser.add_argument('--folder', help='Path to folder containing images (optional)')
    parser.add_argument('--threshold', type=int, default=5,
                       help='Similarity threshold (default=5)')
    
    args = parser.parse_args()
    
    root = tk.Tk()
    app = SimilarImagesFinder(root)
    
    if args.folder:
        app.folder_path = args.folder
        app.folder_label.config(text=args.folder)
    
    if args.threshold:
        app.threshold_var.set(args.threshold)
    
    root.mainloop()


if __name__ == '__main__':
    main()
