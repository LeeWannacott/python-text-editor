import tkinter as tk
import tkinter.ttk

import tkinter.font as TkFont
from tkinter import filedialog, Toplevel,messagebox
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments import lex
from pygments.formatters import HtmlFormatter
from pygments import lexers
from python_terminal import Pipe
from python_terminal import ConsoleText
from tkinter.scrolledtext import ScrolledText
import io, hashlib, queue, sys, time, threading, traceback
from python_terminal import Console
import code
import pyautogui
import jedi
import json
import string, io,os
import idlelib




class Menubar:

    def __init__(self, parent):
        font_specs = ("ubuntu", 10)

        menubar = tk.Menu(parent.master, font=font_specs)
        parent.master.config(menu=menubar)

        file_dropdown = tk.Menu(menubar, font=font_specs, tearoff=0)
        file_dropdown.add_command(label="New File",
                                  accelerator="Ctrl+N",
                                  command=parent.new_file)
        file_dropdown.add_command(label="Open File",
                                  accelerator="Ctrl+O",
                                  command=parent.open_file)
        file_dropdown.add_command(label="Save",
                                  accelerator="Ctrl+S",
                                  command=parent.save)
        file_dropdown.add_command(label="Save As",
                                  accelerator="Ctrl+Shift+S",
                                  command=parent.save_as)
        file_dropdown.add_separator()
        file_dropdown.add_command(label="Exit",
                                  command=parent.master.destroy)


        # Button for running the code.
        run_script = tk.Menu(menubar, font=font_specs, tearoff=0)
        run_script.add_command(label="Run",
                                   command=parent.run_current_script)

        # About
        about_dropdown = tk.Menu(menubar, font=font_specs, tearoff=0)
        about_dropdown.add_command(label="About",
                                   command=self.show_about_message)

        menubar.add_cascade(label="File", menu=file_dropdown)
        menubar.add_cascade(label="About", menu=about_dropdown)
        menubar.add_cascade(label="Run", menu=run_script)




    def show_about_message(self):
        box_title = "About PyText"
        box_message = "A simple Python Text Editor"
        messagebox.showinfo(box_title, box_message)

    def show_release_notes(self):
        box_title = "Release Notes"
        box_message = "Version 0.1"
        messagebox.showinfo(box_title, box_message)

class Statusbar:

    def __init__(self, parent):

        font_specs = ("ubuntu", 12)

        self.status = tk.StringVar()
        self.status.set('Text Editor')

        label = tk.Label(parent.text, textvariable=self.status, fg="black",
                         bg="lightgrey", anchor='sw', font=font_specs)
        label.pack(side=tk.BOTTOM, fill=tk.BOTH)


    def update_status(self, *args):
        if isinstance(args[0], bool):
            self.status.set("Your File Has Been Saved!")
        else:
           pass

    def update_status2(self, *args):
        if isinstance(args[0], bool):
            if args[0] == True:
                self.status.set("Edit Mode")
            elif args[0] == False:
                self.status.set("Normal Mode")

class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None

    def attach(self, text_widget):
        self.textwidget = text_widget

    def redraw(self, *args):
        '''redraw line numbers'''
        self.delete("all")

        i = self.textwidget.index("@0,0")
        while True :
            dline= self.textwidget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2,y,anchor="nw", text=linenum)
            i = self.textwidget.index("%s+1line" % i)



class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)


        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args):
        # let the actual widget perform the requested action
        cmd = (self._orig,) + args
        result = self.tk.call(cmd)

        # generate an event if something was added or deleted,
        # or the cursor position changed
        if (args[0] in ("insert", "replace", "delete") or
            args[0:3] == ("mark", "set", "insert") or
            args[0:2] == ("xview", "moveto") or
            args[0:2] == ("xview", "scroll") or
            args[0:2] == ("yview", "moveto") or
            args[0:2] == ("yview", "scroll")
        ):
            self.event_generate("<<Change>>", when="tail")

        # return what the actual widget returned
        return result


class PyText(tk.Frame):

    def __init__(self, parent, _locals, exit_callback, *args, **kwargs,):
        tk.Frame.__init__(self, *args, **kwargs)
        master.title("Untitled - PyText")
        master.geometry("1200x700")

        self.master = master
        self.filename = None

        self.nb = tkinter.ttk.Notebook(master,height=700)
        self.page1 = tkinter.ttk.Frame(self.nb)
        self.page2 = tkinter.ttk.Frame(self.nb)

        font = TkFont.Font(font=("Times 14"))
        tab_width = font.measure(' ' * 8)
        # Text area
        self.text = CustomText(self.page1, font = font, tabs=tab_width,padx = 5,pady = 5,height=5)
        self.linenumbers = TextLineNumbers(self.page1, width=25)
        self.linenumbers.attach(self.text)
        self.linenumbers.pack( side="left", fill="y")

        self.scroll = tk.Scrollbar(self.text, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self.scroll.set)

        self.text.pack(side="top", fill="both", expand=True)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.nb.add(self.page1, text = 'One')
        self.nb.add(self.page2, text = 'Two')

        self.nb.pack(expand=1, fill="both")


        global syntax_highlighter
        def syntax_highlighter(event=None):

            self.text.mark_set("range_start", "1.0")
            data = self.text.get("1.0", "end-1c")

            for token, content in lex(data, PythonLexer()):
                self.text.mark_set("range_end", "range_start + %dc" % len(content))
                self.text.tag_add(str(token), "range_start", "range_end")
                self.text.mark_set("range_start", "range_end")
                self.text.tag_configure("Token.Keyword", foreground="#DD7A00")
                self.text.tag_configure("Token.Name.Builtin", foreground="#248F24")
                self.text.tag_configure("Token.Keyword.Constant", foreground="#CF7A00")
                self.text.tag_configure("Token.Literal.String.Double", foreground="#648F24")
                self.text.tag_configure("Token.Literal.String.Single", foreground="#648F24")
                self.text.tag_configure("Token.Keyword.Declaration", foreground="#CE7A00")
                self.text.tag_configure("Token.Keyword.Namespace", foreground="#CE8A80")
                self.text.tag_configure("Token.Keyword.Pseudo", foreground="#CC7B00")
                self.text.tag_configure("Token.Keyword.Reserved", foreground="#A87A00")
                self.text.tag_configure("Token.Keyword.Type", foreground="#CFFA00")
                self.text.tag_configure("Token.Name.Class", foreground="#ABF")
                self.text.tag_configure("Token.Name.Exception", foreground="#003D99")
                self.text.tag_configure("Token.Name.Function", foreground="#003D99")
                self.text.tag_configure("Token.Operator.Word", foreground="#CC7A00")
                self.text.tag_configure("Token.Comment.Single", foreground="#B80000")
                self.text.tag_configure("Token.Literal.String", foreground="#248F24")


                # print(token,content)


        self.text.bind("<<Change>>", self._on_change)
        self.text.bind("<Configure>", self._on_change)
        self.text.bind("<KeyRelease>", syntax_highlighter ,add="+")
        # self.text.bind('<KeyRelease>', self.jedi_autocomplete, add="+")

        self.menubar = Menubar(self)
        self.statusbar = Statusbar(self)



        # START OF PYTHON TERMINAL

        self.cmd = ConsoleText(self.page1, font=font, tabs=tab_width, padx=5, pady=5,height=7,bg= 'white',fg='black')
        self.cmd.pack(side= 'bottom', fill='both', expand=False)
        self.shell = code.InteractiveConsole(_locals)

        # make the enter key call the self.enter function
        self.cmd.bind("<Return>", self.enter)
        self.prompt_flag = True
        self.command_running = False
        self.exit_callback = exit_callback

        # replace all input and output
        sys.stdout = Pipe()
        sys.stderr = Pipe()
        sys.stdin = Pipe()

        self.readFromPipe(sys.stdout, "stdout")
        self.readFromPipe(sys.stderr, "stderr", foreground='red')

        self.bind_shortcuts()

    def prompt(self):
        """Add a '>>> ' to the console"""
        self.prompt_flag = True

    def readFromPipe(self, pipe: Pipe, tag_name, **kwargs):
        """Method for writing data from the replaced stdin and stdout to the console widget"""

        # write the >>>
        if self.prompt_flag and not sys.stdin.reading:
            self.cmd.prompt()
            self.prompt_flag = False

        # get data from buffer
        str_io = io.StringIO()
        while not pipe.buffer.empty():
            c = pipe.buffer.get()
            str_io.write(c)

        # write to console
        str_data = str_io.getvalue()
        if str_data:
            self.cmd.write(str_data, tag_name, "prompt_end", **kwargs)

        # loop
        self.after(50, lambda: self.readFromPipe(pipe, tag_name, **kwargs))

    def enter(self, e):
        """The <Return> key press handler"""

        if sys.stdin.reading:
            # if stdin requested, then put data in stdin instead of running a new command
            line = self.cmd.consume_last_line()
            line = line[1:] + '\n'
            sys.stdin.buffer.put(line)
            return

        # don't run multiple commands simultaneously
        if self.command_running:
            return

        # get the command text
        command = self.cmd.read_last_line()
        try:
            # compile it
            compiled = code.compile_command(command)
            is_complete_command = compiled is not None
        except (SyntaxError, OverflowError, ValueError):
            # if there is an error compiling the command, print it to the console
            self.cmd.consume_last_line()
            self.prompt()
            traceback.print_exc(0)
            return

        # if it is a complete command
        if is_complete_command:
            # consume the line and run the command
            self.cmd.consume_last_line()
            self.prompt()

            self.command_running = True

            def run_command():
                try:
                    self.shell.runcode(compiled)
                except SystemExit:
                    self.after(0, self.exit_callback)

                self.command_running = False

            threading.Thread(target=run_command).start()

    #END OF PYTHON TERMINAL

    def set_window_title(self, name=None):
        if name:
            self.master.title(name + " - PyText")
        else:
            self.master.title("Untitled - PyText")

    def new_file(self, *args):
        self.text.delete(1.0, tk.END)
        self.filename = None
        self.set_window_title()

    def open_file(self, *args):
        self.filename = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("All Files", "*.*"),
                       ("Text Files", "*.txt"),
                       ("Python Scripts", "*.py"),
                       ("Markdown Documents", "*.md"),
                       ("JavaScript Files", "*.js"),
                       ("HTML Documents", "*.html"),
                       ("CSS Documents", "*.css")])
        if self.filename:
            self.text.delete(1.0, tk.END)
            with open(self.filename, "r") as f:
                self.text.insert(1.0, f.read())

            syntax_highlighter()
            # self.syntax_highlighter()
            self.set_window_title(self.filename)

    def save(self, *args):
        if self.filename:
            try:
                textarea_content = self.text.get(1.0, tk.END)
                with open(self.filename, "w") as f:
                    f.write(textarea_content)
                self.statusbar.update_status(True)
            except Exception as e:
                print(e)
        else:
            self.save_as()

    def save_as(self, *args):
        try:
            new_file = filedialog.asksaveasfilename(
                initialfile="Untitled.txt",
                defaultextension=".txt",
                filetypes=[("All Files", "*.*"),
                           ("Text Files", "*.txt"),
                           ("Python Scripts", "*.py"),
                           ("Markdown Documents", "*.md"),
                           ("JavaScript Files", "*.js"),
                           ("HTML Documents", "*.html"),
                           ("CSS Documents", "*.css")])
            textarea_content = self.text.get(1.0, tk.END)
            with open(new_file, "w") as f:
                f.write(textarea_content)
            self.filename = new_file
            self.set_window_title(self.filename)
            self.statusbar.update_status(True)
        except Exception as e:
            print(e)

    def run_current_script(self, *args):
        if self.filename:
            exec(open(self.filename).read())
            print(self.filename)
        else:
            print('Load/save a file before running.')



    # Key mappings for Normal mode
    def go_to_start_of_word(self,*args):
        self.text.mark_set('insert', 'insert -1c wordstart')
        return "break"

    def go_to_end_of_word(self, *args):
        self.text.mark_set('insert', 'insert wordend')
        return "break"

    def go_to_start_of_line(self, *args):
        self.text.mark_set('insert', 'insert linestart')
        return "break"

    def go_to_end_of_line(self, *args):
        self.text.mark_set('insert', 'insert lineend')
        return "break"

    def go_down_one_line(self, *args):
        self.text.mark_set('insert', 'insert + 1 lines')
        return "break"

    def go_up_one_line(self, *args):
        self.text.mark_set('insert', 'insert - 1 lines')
        return "break"


    def enter_key(self,*args):
        last_char = self.text.get('insert -1c')

        if last_char == ':':
            pass

    def select(self, *args):
        pyautogui.press('shift')
        return "break"

    global counter
    counter = 0
    def normal_mode(self,*args):
        global counter

        counter +=1

        self.statusbar.update_status2(True)
        self.text.bind('<s>', self.go_to_start_of_word)
        self.text.bind('<f>', self.go_to_end_of_word)
        self.text.bind('<w>', self.go_to_start_of_line)
        self.text.bind('<r>', self.go_to_end_of_line)
        self.text.bind('<d>', self.go_down_one_line)
        self.text.bind('<e>', self.go_up_one_line)
        self.text.bind('<a>', self.select)
        if counter > 1:
            self.statusbar.update_status2(False)
            self.text.unbind('<s>')
            self.text.unbind('<f>')
            self.text.unbind('<w>')
            self.text.unbind('<r>')
            self.text.unbind('<d>')
            self.text.unbind('<e>')
            self.text.unbind('<a>')
            print(counter)
            counter = 0
            # return 'break'
        # return 'break'
    def bind_shortcuts(self):
        self.text.bind('<Control-n>', self.new_file)
        self.text.bind('<Control-o>', self.open_file)
        self.text.bind('<Control-s>', self.save)
        self.text.bind('<Control-S>', self.save_as)
        self.text.bind('<Key>', self.statusbar.update_status)
        self.text.bind("<Return>", self.enter_key)
        self.text.bind('<Escape>', self.normal_mode)
        self.text.bind('<Caps_Lock>', self.normal_mode)
        self.text.bind('<F1>',self.jedi_autocomplete)
    def _on_change(self, event):
        self.linenumbers.redraw()




    def jedi_autocomplete(self,*args):
        # print('testing')
        code = self.text.get('1.0', "end")
        line_column = self.text.index('insert').split('.')
        line, column = int(line_column[0]), int(line_column[1])

        # print(line, column)
        if self.filename:
            print('testing')
            script = jedi.Script(code=code,path=self.filename)
            completion = script.complete(line=line,column=column)
            print(completion)
        else:
            script = jedi.Script(code=code)
            completion = script.complete(line=line, column=column)

            completions = []
            for i,names in enumerate(completion):
                completions.append(completion[i].name)

            print(completion)

            # entry = AutocompleteEntryListbox(acw, width=20, completevalues=completions)
            # entry.pack(side='left')
            # Place autocomplete box on text mark location
            # https://github.com/python/cpython/blob/master/Lib/idlelib/autocomplete_w.py

            if completions:
                text = self.text
                text.see(text.index('insert'))
                x, y, cx, cy = text.bbox(text.index('insert'))
                acw = Toplevel(master)

                def key(event):
                    # print("pressed", repr(event.char))

                    key_pressed = repr(event.char)

                    if not completions:
                        print('notnone')


                    if key_pressed == "'\\r'":
                        autocomplete_selection = entry.get()
                        first_char = text.index("insert -1c wordstart")
                        last_char = text.index('insert -1c wordend')
                        self.text.delete(first_char,last_char)
                        self.text.insert(first_char,autocomplete_selection)
                        acw.destroy()
                        entry.destroy()



                        # self.text.insert(text_index,autocomplete_selection)
                        print(first_char,last_char,autocomplete_selection)

                def callback(event):
                    entry.focus_set()
                    print("clicked at", event.x, event.y)


                acw.bind("<Key>", key)
                # acw.bind("<Button-1>", callback)

                acw_width, acw_height = acw.winfo_width(), acw.winfo_height()
                text_width, text_height = text.winfo_width(), text.winfo_height()
                new_x = text.winfo_rootx() + min(x, max(0, text_width - acw_width))
                new_y = text.winfo_rooty() + y
                if (text_height - (y + cy) >= acw_height  # enough height below
                        or y < acw_height):  # not enough height above
                    # place acw below current line
                    new_y += cy
                else:
                    # place acw above current line
                    new_y -= acw_height


                acw.wm_overrideredirect(True)
                acw.wm_geometry("+%d+%d" % (new_x, new_y))


                from ttkwidgets.autocomplete import AutocompleteEntryListbox
                entry = AutocompleteEntryListbox(acw, width=20, completevalues=completions)
                entry.pack()

                return 'break'


            # master.mainloop()



if __name__ == "__main__":
    master = tk.Tk()
    pt = PyText(master,locals(), master.destroy).pack(side="top", fill="both", expand=True)
    master.mainloop()