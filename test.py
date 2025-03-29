import tkinter as tk
import tkinter.font as tkFont

root = tk.Tk()
root.title("Example Window")

# Specify a font that supports the UI; changed to "latin modern roman"
custom_font = tkFont.Font(family="latin modern roman", size=12)

label = tk.Label(root, text="Hello, World!", font=custom_font)
label.pack()

root.mainloop()

# Uncomment the code below to print the list of available fonts
# root = tk.Tk()
# available_fonts = tkFont.families()
# print(available_fonts)
# root.destroy()
