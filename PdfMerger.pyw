import re
import tkinter as tk
from tkinter import filedialog
from pypdf import PdfWriter, PdfReader
from PIL import Image, ImageOps
import os
from tkinter import ttk
from threading import Thread
import time


def extract_number(value):
    out = re.sub('[^0-9]', '', value)
    return int(out) if out != '' else 99999999999999


def sorted_by_number(values):
    return sorted(values, key=extract_number)


def sorted_alphabetically(values):
    return sorted(values)


def update_file_list():
    global files
    file_list.delete(0, tk.END)
    for file in files:
        file_list.insert(tk.END, file)


def browse_input_dir():
    global input_path, output_path, files, sorting
    input_path = filedialog.askdirectory()
    if input_path != '':
        input_var.set(input_path)
        output_path = input_path.split('/')[-1] + '.pdf'
        output_var.set(output_path)
        files = sorted_by_number(os.listdir(input_path))
        sorting = 'by_number'
        update_file_list()


def browse_output():
    global output_path, files, sorting
    temp = filedialog.asksaveasfile(filetypes=[('pdf', '*pdf'), ('all files', '*')])
    if temp is not None:
        output_path = temp.name if temp.name.find('.') != -1 else temp.name + '.pdf'
        output_var.set(output_path)


def sort_file_list_by_number():
    global files, sorting
    if sorting == 'by_number':
        files = files[::-1]
    else:
        sorting = 'by_number'
        files = sorted_by_number(files)
    update_file_list()


def sort_file_list_alphabetically():
    global files, sorting
    if sorting == 'alphabetically':
        files = files[::-1]
    else:
        sorting = 'alphabetically'
        files = sorted_alphabetically(files)
    update_file_list()


def input_width_callback(sv):
    global width
    temp = re.sub('[^0-9]', '', sv.get())
    width_var.set(temp)
    width = int(temp) if temp != '' else DEFAULT_PAGE_WIDTH


def input_height_callback(sv):
    global height
    temp = re.sub('[^0-9]', '', sv.get())
    height_var.set(temp)
    height = int(temp) if temp != '' else DEFAULT_PAGE_HEIGHT


def input_insert_callback(sv):
    global input_var
    input_var.set(input_path)


def output_insert_callback(sv):
    global output_var
    output_var.set(output_path)


def set_progress(value):
    global progress
    progress = value
    progressbar_var.set(value)
    progressbar_text.config(text=f'{value}%')


def resize_image_center(image):
    global width, height
    image = ImageOps.contain(image, (width, height))
    image_size = image.size
    w = image_size[0]
    h = image_size[1]
    out = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    box = int((width - w) / 2), int((height - h) / 2)
    out.paste(image, box)
    return out


def add_image(pdf_writer, image):
    image.save(TEMP_FILE_NAME)
    temp_pdf = PdfReader(TEMP_FILE_NAME)
    temp_page = temp_pdf.pages[0]
    pdf_writer.add_page(temp_page)


def merge_pdf():
    global pdf_merging_ongoing, thread
    pdf_merging_ongoing = True
    start_button.config(text='abort')
    width_entry.config(state=tk.DISABLED)
    height_entry.config(state=tk.DISABLED)
    input_button.config(state=tk.DISABLED)
    output_button.config(state=tk.DISABLED)
    sort_by_number_button.config(state=tk.DISABLED)
    sort_alphabetically_button.config(state=tk.DISABLED)
    set_progress(0)
    pdf_writer = PdfWriter()
    try:
        for i in range(len(files)):
            if not pdf_merging_ongoing:
                break
            file = files[i]
            file = os.path.join(input_path, file)
            image = Image.open(file)
            image = resize_image_center(image)
            add_image(pdf_writer, image)
            set_progress(int((i + 1) / (len(files)) * 100))
    except:
        raise
    if os.path.exists(TEMP_FILE_NAME):
        os.remove(TEMP_FILE_NAME)
    if pdf_merging_ongoing:
        pdf_writer.write(output_path)
    width_entry.config(state=tk.NORMAL)
    height_entry.config(state=tk.NORMAL)
    input_button.config(state=tk.NORMAL)
    output_button.config(state=tk.NORMAL)
    sort_by_number_button.config(state=tk.NORMAL)
    sort_alphabetically_button.config(state=tk.NORMAL)
    start_button.config(text='start')
    pdf_merging_ongoing = False
    thread = None


def start():
    if input_path == '' or output_path == '' or not files:
        return

    global pdf_merging_ongoing, thread
    if pdf_merging_ongoing:
        pdf_merging_ongoing = False
        return

    thread = Thread(target=merge_pdf)
    thread.start()


def on_closing():
    global pdf_merging_ongoing, thread
    if pdf_merging_ongoing:
        pdf_merging_ongoing = False
        time.sleep(0.1)
    root.destroy()


def move_file_up():
    global files, sorting
    temp = file_list.curselection()
    if len(temp) == 1 and temp[0] != 0:
        sorting = 'none'
        ind = temp[0]
        file_list.delete(ind)
        file_list.insert(ind - 1, files[ind])
        file_list.select_set(ind - 1)
        files[ind - 1], files[ind] = files[ind], files[ind - 1]


def move_file_down():
    global files, sorting
    temp = file_list.curselection()
    if len(temp) == 1 and temp[0] != len(files) - 1:
        sorting = 'none'
        ind = temp[0]
        file_list.delete(ind)
        file_list.insert(ind + 1, files[ind])
        file_list.select_set(ind + 1)
        files[ind], files[ind + 1] = files[ind + 1], files[ind]


def delete_file():
    global files
    temp = file_list.curselection()
    if len(temp) == 1:
        ind = temp[0]
        file_list.delete(ind)
        files.pop(ind)
        if files:
            file_list.select_set(ind if ind < len(files) else ind - 1)


def center_window(window):
    window.update_idletasks()
    w = window.winfo_width()
    h = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - w) // 2
    y = (screen_height - h) // 2
    window.geometry(f"{w}x{h}+{x}+{y}")


TEMP_FILE_NAME = '.___pdfMerger___.pdf'
DEFAULT_PAGE_WIDTH = 1800
DEFAULT_PAGE_HEIGHT = 900
width = DEFAULT_PAGE_WIDTH
height = DEFAULT_PAGE_HEIGHT
input_path = ''
output_path = ''
files = []
sorting = 'by_number'
pdf_merging_ongoing = False
progress = 0
thread = None

root = tk.Tk()
root.title('Pdf Merger')
root.geometry('422x450')
root.resizable(False, False)
center_window(root)

width_label = tk.Label(root, text='page width')
width_label.place(x=10, y=10)
width_var = tk.StringVar(value=str(DEFAULT_PAGE_WIDTH))
width_var.trace('w', lambda name, index, mode, sv=width_var: input_width_callback(width_var))
width_entry = tk.Entry(root, textvariable=width_var)
width_entry.place(x=90, y=10, width=300)

height_label = tk.Label(root, text='page height')
height_label.place(x=10, y=40)
height_var = tk.StringVar(value=str(DEFAULT_PAGE_HEIGHT))
height_var.trace('w', lambda name, index, mode, sv=height_var: input_height_callback(height_var))
height_entry = tk.Entry(root, textvariable=height_var)
height_entry.place(x=90, y=40, width=300)

input_label = tk.Label(root, text='input dir')
input_label.place(x=10, y=70)
input_var = tk.StringVar()
input_var.trace('w', lambda name, index, mode, sv=input_var: input_insert_callback(input_var))
input_entry = tk.Entry(root, textvariable=input_var, disabledbackground='white', disabledforeground='black')
input_entry.place(x=90, y=70, width=300)
input_button = tk.Button(root, text='📁', borderwidth=0, command=browse_input_dir)
input_button.place(x=396, y=68, height=20)

output_label = tk.Label(root, text='output file')
output_label.place(x=10, y=100)
output_var = tk.StringVar()
output_var.trace('w', lambda name, index, mode, sv=output_var: output_insert_callback(output_var))
output_entry = tk.Entry(root, textvariable=output_var, disabledbackground='white', disabledforeground='black')
output_entry.place(x=90, y=100, width=300)
output_button = tk.Button(root, text='📁', borderwidth=0, command=browse_output)
output_button.place(x=396, y=98, height=20)

file_list_label = tk.Label(root, text='files')
file_list_label.place(x=10, y=130)
file_list = tk.Listbox(root, justify='left', width=20, height=10)
file_list.place(x=10, y=150, width=366)
scrollbar = tk.Scrollbar(root)
scrollbar.place(x=374, y=150, height=163)
file_list.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=file_list.yview)

sort_by_number_button = tk.Button(root, text='sort by number', borderwidth=1, command=sort_file_list_by_number)
sort_by_number_button.place(x=10, y=320, width=142)

sort_alphabetically_button = tk.Button(root, text='sort alphabetically', borderwidth=1,
                                       command=sort_file_list_alphabetically)
sort_alphabetically_button.place(x=158, y=320, width=142)

up_button = tk.Button(root, text='↑', borderwidth=1, command=move_file_up)
up_button.place(x=306, y=320, width=24)

down_button = tk.Button(root, text='↓', borderwidth=1, command=move_file_down)
down_button.place(x=336, y=320, width=24)

delete_button = tk.Button(root, text='X', borderwidth=1, command=delete_file)
delete_button.place(x=366, y=320, width=24)

start_button = tk.Button(root, text='start', borderwidth=1, command=start, font=("Arial", 20))
start_button.place(x=10, y=350, width=380, height=50)

progressbar_var = tk.IntVar(value=progress)
progressbar = ttk.Progressbar(length=160, variable=progressbar_var)
progressbar.place(x=10, y=410, width=380, height=30)
progressbar_text = tk.Label(root, text='0%')
progressbar_text.place(x=390, y=415)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
