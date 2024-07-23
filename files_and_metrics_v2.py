import pandas
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from tkinter import *
from tkinter import Tk, filedialog, Button, Label, messagebox, Toplevel, Frame, LEFT, RIGHT, BOTH, X, Y, TOP
import os
import glob
from pathlib import Path
import shutil
import subprocess
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import queue
from queue import Queue
import threading


class MainWindow:
    def __init__(self):
        # Initialize variables to hold data and selected file paths
        self.data = []
        self.selected_files = []
        self.patientDirectory = ""
        self.patientList = []
        self.groupList = []
        self.gui_elements = []
        self.cardioFeed_selection = ""

        self.cardioFeedExecutableName = ""

        self.cardioFeed_output = []
        self.output_queue = Queue()
        self.output_list = [["T", "HR", "RR", "M", "S"]]
        self.excelVar = IntVar()

        self.root_gui()


    def populate_patientList(self):
        self.remove_gui(self.gui_elements)

        class Patients:
            def __init__(self, fileName, filePath):
                self.fileName = fileName
                self.filePath = filePath

        def get_list(currentDirectory):
            files = glob.glob(currentDirectory)
            for file in files:
                # print(currentDirectory)
                # print(file)
                if Path(file).is_dir():
                    excelFiles = glob.glob(file + "/*.csv")
                    if len(excelFiles) > 0:
                        fileName = os.path.basename(file)
                        self.patientList.append(Patients(fileName, file))
                    else:
                        # print("\tno excel files in " + file)
                        get_list(file + "/*")

        get_list(self.patientDirectory)

        self.select_files_gui()

    def remove_gui(self, gui_elements):
        for element in gui_elements:
            element.destroy()

    def patient_evaluation_gui(self, control):

        # populate the list
        def populate_patient_list(selection):
            self.patients_eval.delete(0, END)
            for patient in selection:
                self.patients_eval.insert(END, patient.fileName)

        def load_csv_files(file_paths):
            # Load multiple CSV files and concatenate them into a single DataFrame
            excel_files = []

            # get res .csv files from patient folders
            for csv in file_paths:
                resFile = glob.glob(csv.filePath + "/Res*.csv")
                excel_files.append(resFile[0])

            self.selected_files = excel_files  # Save the selected file paths for later use
            self.data = [pd.read_csv(file) for file in excel_files]

        def calculate_metrics(df):
            metrics = {}
            metrics['difference'] = df['HR'] - df['SpO2HR']
            metrics['convergence_time'] = (df['HR'] - df['SpO2HR']).abs().idxmin()
            metrics['batch_average'] = df[['HR', 'SpO2HR']].mean()
            return metrics

        def plot_metrics(df, metrics, file_name):
            fig, axs = plt.subplots(3, 2, figsize=(12, 18))
            fig.suptitle(f"Metrics for {file_name}", fontsize=16)

            # Difference between HR and SpO2HR
            axs[0, 0].plot(df['time(s)'], metrics['difference'], color='#FF0000')
            axs[0, 0].set_title('Difference between HR and SpO2HR')
            axs[0, 0].set_xlabel('Time (s)')
            axs[0, 0].set_ylabel('Difference')

            metrics_text_1 = (
                f"Difference between HR and SpO2HR (mean): {metrics['difference'].mean():.2f}\n"
            )
            axs[0, 1].axis('off')
            axs[0, 1].text(0.1, 0.5, metrics_text_1, fontsize=12, va='center', ha='left',
                           bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=1'))

            # HR and SpO2HR Over Time
            axs[1, 0].plot(df['time(s)'], df['HR'], label='HR', color='#000000')
            axs[1, 0].plot(df['time(s)'], df['SpO2HR'], label='SpO2HR', color='#FF0000')
            axs[1, 0].set_title('HR and SpO2HR Over Time')
            axs[1, 0].set_xlabel('Time (s)')
            axs[1, 0].set_ylabel('Heart Rate')
            axs[1, 0].legend()

            metrics_text_2 = (
                f"Convergence Time: {metrics['convergence_time']} seconds\n"
            )
            axs[1, 1].axis('off')
            axs[1, 1].text(0.1, 0.5, metrics_text_2, fontsize=12, va='center', ha='left',
                           bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=1'))

            # Batch Averages
            axs[2, 0].bar(['Batch Average HR', 'Batch Average SpO2HR'], metrics['batch_average'],
                          color=['#000000', '#FF0000'])
            axs[2, 0].set_title('Batch Averages')

            metrics_text_3 = (
                f"Batch Average HR: {metrics['batch_average']['HR']:.2f}\n"
                f"Batch Average SpO2HR: {metrics['batch_average']['SpO2HR']:.2f}"
            )
            axs[2, 1].axis('off')
            axs[2, 1].text(0.1, 0.5, metrics_text_3, fontsize=12, va='center', ha='left',
                           bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=1'))

            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.subplots_adjust(hspace=0.4)
            return fig

        def export_to_pdf():
            root = Tk()
            root.withdraw()
            pdf_filename = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                        filetypes=[("PDF files", "*.pdf")],
                                                        title="Save PDF Report")
            root.destroy()
            if not pdf_filename:
                return

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)

            for file, df in zip(self.selected_files, self.data):
                metrics = calculate_metrics(df)
                fig = plot_metrics(df, metrics, os.path.basename(file))
                img_path = f"{os.path.splitext(file)[0]}.png"
                fig.savefig(img_path)
                plt.close(fig)

                pdf.add_page()
                pdf.image(img_path, x=10, y=10, w=190)
                os.remove(img_path)

            pdf.output(pdf_filename)
            messagebox.showinfo("Success", f"PDF Report '{pdf_filename}' generated successfully!")

        def show_plots():
            if not self.selected_files:
                messagebox.showerror("Error", "No files selected. Please select CSV files first.")
                return

            # Only create one plot window
            if hasattr(self, 'plot_window') and self.plot_window.winfo_exists():
                self.plot_window.lift()
            else:
                self.plot_window = Toplevel()
                self.plot_window.title("Performance Metrics Plots")
                self.plot_window.geometry("1400x1200")

                button_frame_left = Frame(self.plot_window)
                button_frame_left.pack(side=LEFT, fill=Y)

                self.plot_frame = Frame(self.plot_window)
                self.plot_frame.pack(side=LEFT, fill=BOTH, expand=True)

                button_frame_right = Frame(self.plot_window)
                button_frame_right.pack(side=RIGHT, fill=Y)

                current_index = [0]

                def update_plot(index):
                    for widget in self.plot_frame.winfo_children():
                        widget.destroy()
                    fig = plot_metrics(self.data[index], calculate_metrics(self.data[index]),
                                            os.path.basename(self.selected_files[index]))
                    canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill='both', expand=True)

                def next_plot():
                    if current_index[0] < len(self.selected_files) - 1:
                        current_index[0] += 1
                        update_plot(current_index[0])

                def previous_plot():
                    if current_index[0] > 0:
                        current_index[0] -= 1
                        update_plot(current_index[0])

                # Only show buttons if more than one file is uploaded
                if len(self.selected_files) > 1:
                    prev_button = Button(button_frame_left, text="Previous", command=previous_plot)
                    prev_button.pack(pady=10, padx=10)

                    next_button = Button(button_frame_right, text="Next", command=next_plot)
                    next_button.pack(pady=10, padx=10)

                update_plot(current_index[0])

        # change the textbox to selected patient
        def current_select(event):
            try:
                global current_selection
                index = self.patients_eval.curselection()[0]
                current_selection = self.patients_eval.get(index)

                self.selectionEntrybox.delete(0, END)
                self.selectionEntrybox.insert(END, current_selection)

                for x in self.patientList:
                    if x.fileName == current_selection:
                        self.cardioFeed_selection = x.filePath

                # print(self.cardioFeed_selection)

            except IndexError:
                pass

        def cardioFeed_check():
            if self.cardioFeed_selection == '':
                messagebox.showerror('Required Field', 'Please select a patient file to use CardioFeed.')
            else:
                # get selected version
                self.cardioFeedExecutableName = version.get()

                execFile = glob.glob("cardioFeed/" + self.cardioFeedExecutableName)

                if execFile:  # if the desired executable is in the current working directory
                    self.cardioFeed_gui(control)
                else:
                    messagebox.showerror('Required',
                                         self.cardioFeedExecutableName + ' is not in the current working directory.')

        # gui handling
        self.remove_gui(self.gui_elements)

        # eval label
        self.evalLabel = Label(root, text="Selected Patients", font=("Arial", 16))
        self.evalLabel.grid(row=0, column=0, columnspan=3, pady=10, padx=20)

        # selected patient
        self.subLabel = Label(root, text="Current Selection", font=("Arial", 12))
        self.subLabel.grid(row=0, column=8, columnspan=3, pady=0, padx=20)

        # box to display selected patient
        selection_text = StringVar()
        self.selectionEntrybox = Entry(root, textvariable=selection_text, width=50)
        self.selectionEntrybox.grid(row=1, column=8, columnspan=3, padx=20)

        # version label
        self.versionLabel = Label(root, text="Current Version: ", font=("Arial", 12))
        self.versionLabel.grid(row=2, column=8, columnspan=2, pady=0, padx=20)

        # create list of names to populate dropdown menu
        cFeedPaths = glob.glob(os.getcwd() + "/cardioFeed/cardioFeed_*.exe")

        versionList = []
        versionList_float = []

        for v in cFeedPaths:
            versionList.append(os.path.basename(v))

        # create list of version numbers corresponding to the same index of the path list
        for file in cFeedPaths:
            versionList_float.append(float(os.path.basename(file)[11:-4]))

        # find maximum version number
        newestVersion = os.path.basename(cFeedPaths[versionList_float.index(max(versionList_float))])

        # dropdown menu
        version = StringVar()
        version.set(newestVersion)

        self.dropdown = OptionMenu(root, version, *versionList)
        self.dropdown.grid(row=2, column=10)

        # CardioFeed button
        self.CFeedButton = Button(root, text="Start CardioFeed", command=lambda: cardioFeed_check(), font=("Arial", 12),
                                  width=16)
        self.CFeedButton.grid(row=3, column=8, columnspan=3)

        # list of selected patients
        self.next_patients_frame = Frame(root)
        self.next_patients_frame.grid(row=1, column=0, columnspan=3, rowspan=6, pady=20, padx=20)

        self.patient_eval_scrollbar = Scrollbar(self.next_patients_frame)
        self.patient_eval_scrollbar.pack(side=RIGHT, fill=Y)

        self.patients_eval = Listbox(self.next_patients_frame, height=16, width=40, border=2)
        self.patients_eval.pack()

        self.patients_eval.configure(yscrollcommand=self.patient_eval_scrollbar.set)
        self.patient_eval_scrollbar.configure(command=self.patients_eval.yview)

        # bind list
        self.patients_eval.bind('<<ListboxSelect>>', current_select)

        # back button
        self.backButton = Button(root, text="Back to Patient Selection", command=lambda: self.select_files_gui(),
                                 font=("Arial", 12), width=21)
        self.backButton.grid(row=8, column=0)

        # view all metrics button
        self.allMetrics = Button(root, text="View All Metrics", command=lambda: show_plots(), font=("Arial", 12),
                                 width=15)
        self.allMetrics.grid(row=4, column=8, columnspan=3)

        # print to pdf button
        self.printPDF = Button(root, text="Print to PDF", command=lambda: export_to_pdf(), font=("Arial", 12), width=12)
        self.printPDF.grid(row=8, column=10)

        if control == 0:  # evaluate all
            populate_patient_list(self.patientList)
            load_csv_files(self.patientList)
        else:  # evaluate group
            populate_patient_list(self.groupList)
            load_csv_files(self.groupList)

        # display_metrics()

        self.gui_elements = [self.evalLabel,
                             self.patients_eval,
                             self.patient_eval_scrollbar,
                             self.backButton,
                             self.allMetrics,
                             self.printPDF,
                             self.selectionEntrybox,
                             self.subLabel,
                             self.CFeedButton,
                             self.dropdown,
                             self.versionLabel,
                             self.next_patients_frame]

    def threading(self, start, duration, control):

        if start == '':
            start = "0"

        if duration == '':  # if duration is empty, exclude it from list of args
            try:
                int(start)
            except ValueError:
                messagebox.showerror('Value Error', 'Input must be an integer.')
                self.cardioFeed_gui(control)

        else:
            try:
                int(start)
                int(duration)
            except ValueError:
                messagebox.showerror('Value Error', 'Input must be an integer.')
                self.cardioFeed_gui(control)

        file = self.copyCSV()

        self.remove_gui(self.gui_elements)

        self.starting = Label(root, text="Starting...", font=("Arial", 18))
        self.starting.pack()

        self.gui_elements = [self.starting]

        self.thread = threading.Thread(target=self.cardioFeedResults, args=(file, start, duration))
        self.thread.start()

        self.check_queue(control)

    def append_to_list(self, string, control):
        x = string.split()

        # shows an error and stops reading lines from output if cardioFeed output does not start with "T "
        if x[0] != 'T':
            messagebox.showerror('ERROR', string)
            self.next_gui(control)
        else:
            self.output_list.append([x[1], x[3], x[5], x[7], x[9]])

    def get_plot(self):

        T = []
        HR = []
        RR = []

        for row in self.output_list[1:]:
            T.append(int(row[0]))
            HR.append(int(row[1]))
            RR.append(int(row[2]))

        return T, HR, RR

    def generate_excel(self):
        if self.excelVar.get() == 1:
            df = pandas.DataFrame(self.output_list)
            df.to_excel(os.path.basename(self.cardioFeed_selection) + '_output.xlsx')

    def next_gui(self, control):

        # delete the raw file
        self.deleteCSV()

        # go back to main directory
        os.chdir('..')

        # generate excel file
        self.generate_excel()

        self.remove_gui(self.gui_elements)

        self.title2 = Label(root, text="Plot generated.", font=("Arial", 18))
        self.title2.pack()

        fig = Figure(figsize=(5, 3), dpi=100)
        T, HR, RR = self.get_plot()

        plt = fig.add_subplot(111)

        plt.plot(T, HR, label="HR")
        plt.plot(T, RR, label="RR")
        plt.legend()

        plt.set_ylim([0, None])

        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.draw()

        # display final plot
        self.graph = canvas.get_tk_widget()
        self.graph.pack(side=TOP, fill=BOTH, expand=1)

        self.button2 = Button(root, text="Back", command=lambda: self.cardioFeed_gui(control), font=("Arial", 12))
        self.button2.pack(pady=30)

        self.gui_elements = [self.title2,
                             self.button2,
                             self.graph]

    def check_queue(self, control):
        try:
            # receive for output
            output = self.output_queue.get_nowait()

            # append output to list
            self.append_to_list(output, control)

            # generate plot
            fig = Figure(figsize=(5, 3), dpi=100)
            T, HR, RR = self.get_plot()

            ax = fig.add_subplot(111)

            ax.plot(T, HR, label="HR")
            ax.plot(T, RR, label="RR")
            ax.legend()

            ax.set_ylim([0, None])

            canvas = FigureCanvasTkAgg(fig, master=root)
            canvas.draw()

            # remove previous GUI
            self.remove_gui(self.gui_elements)

            self.title2 = Label(root, text="Plotting...", font=("Arial", 18))
            self.title2.pack()

            # display new plot
            self.graph = canvas.get_tk_widget()
            self.graph.pack(side=TOP, fill=BOTH, expand=1)

            self.gui_elements = [self.title2,
                                 self.graph]
        except queue.Empty:
            pass

        # once the thread stops execution, move to next_gui
        if self.thread.is_alive():
            root.after(200, lambda: self.check_queue(control))
        else:
            self.next_gui(control)

    def cardioFeedResults(self, file, start, duration):
        def execute(cmd):
            popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
            for stdout_line in iter(popen.stdout.readline, ""):
                yield stdout_line
            popen.stdout.close()
            return_code = popen.wait()
            if return_code:
                print("Done.")

        os.chdir(os.getcwd() + "/cardioFeed")

        print("Starting CardioFeed...")

        if duration == '':
            args = [self.cardioFeedExecutableName, "-q", os.path.basename(file), start]
        else:
            args = [self.cardioFeedExecutableName, "-q", os.path.basename(file), start, duration]

        print(args)

        for path in execute(args):
            if path != '\n':
                new_string = path[:-1]
                self.output_queue.put(new_string)

    def copyCSV(self):  # copy the selected file to the cwd
        self.rawFile = glob.glob(self.cardioFeed_selection + "/Raw*.csv")
        print("Copying file into directory...")
        shutil.copy(self.rawFile[0], os.getcwd() + "/cardioFeed")
        print("File copied successfully.")
        return self.rawFile[0]

    def deleteCSV(self):
        file_to_delete = os.getcwd() + "/" + os.path.basename(self.rawFile[0])
        print("Deleting " + os.path.basename(self.rawFile[0]) + "...")

        if os.path.exists(file_to_delete):
            os.remove(file_to_delete)
            print("File deleted.")
        else:
            print("File not found.")

    def cardioFeed_gui(self, control):

        # gui handling
        self.remove_gui(self.gui_elements)

        # cardioFeed eval label
        self.cf_title = Label(root, text="Patient Selected for CardioFeed", font=("Arial", 16))
        self.cf_title.grid(row=0, column=0, columnspan=3, pady=10, padx=20)

        # selected file label
        self.cf_selection = Label(root, text=os.path.basename(self.cardioFeed_selection), font=("Arial", 12))
        self.cf_selection.grid(row=1, column=0, columnspan=3, pady=10, padx=20)

        # choose start time
        self.start_time = Label(root, text="Start Time (ms): ", font=("Arial", 12))
        self.start_time.grid(row=2, column=0, pady=20, padx=20)

        start_time_num = StringVar()
        self.start_time_box = Entry(root, textvariable=start_time_num, width=15)
        self.start_time_box.grid(row=2, column=1, pady=20, padx=20)

        # choose duration
        self.duration = Label(root, text="Duration (ms): ", font=("Arial", 12))
        self.duration.grid(row=3, column=0, pady=10, padx=20)

        duration_num = StringVar()
        self.duration_box = Entry(root, textvariable=duration_num, width=15)
        self.duration_box.grid(row=3, column=1, pady=10, padx=20)

        # default behavior label
        self.zero_def = Label(root, text="Will play full duration from the start by default.", font=("Arial", 10))
        self.zero_def.grid(row=4, column=0, columnspan=2, pady=10, padx=20)

        # create .csv file from output
        # excelVar = IntVar()
        self.create_csv = Checkbutton(root, text="Generate Excel File from Output", variable=self.excelVar, onvalue=1, offvalue=0, font=("Arial", 12))
        self.create_csv.grid(row=5, column=0, columnspan=2, pady=10, padx=20)

        # run button
        self.run_button = Button(root, text="Run", command=lambda: self.threading(start_time_num.get(), duration_num.get(), control), font=("Arial", 12), width=6)
        self.run_button.grid(row=8, column=8)

        # back button
        self.backToEval = Button(root, text="Back", command=lambda: self.patient_evaluation_gui(control),
                                 font=("Arial", 12), width=6)
        self.backToEval.grid(row=8, column=0)

        self.gui_elements = [self.backToEval,
                             self.cf_title,
                             self.cf_selection,
                             self.start_time,
                             self.start_time_box,
                             self.duration,
                             self.duration_box,
                             self.zero_def,
                             self.run_button,
                             self.create_csv]

    def select_files_gui(self):

        # populate the list
        def populate_patient_list():
            self.patients_list.delete(0, END)
            for patient in self.patientList:
                self.patients_list.insert(END, patient.fileName)

        def select_patient(event):
            try:
                global patient_selection
                index = self.patients_list.curselection()[0]
                patient_selection = self.patients_list.get(index)
                # print(self.patientList[index].fileName + "\t\t\t" + patient_selection)
            except IndexError:
                pass

        def select_patient_group(event):
            try:
                global patient_selection_group
                index = self.group_list.curselection()[0]
                patient_selection_group = self.group_list.get(index)
                # print(patient_selection_group)
            except IndexError:
                pass

        def add_patient():
            self.group_list.insert(END, patient_selection)
            # print(patient_selection)

        def remove_patient():
            try:
                index = self.group_list.get(0, END).index(patient_selection_group)
                self.group_list.delete(index)
            except (NameError, ValueError):
                pass

        def clear_selection():
            self.group_list.delete(0, END)

        def group_to_list(control):

            for patient in self.group_list.get(0, END):
                for x in self.patientList:
                    if x.fileName == patient:
                        self.groupList.append(x)

            if not self.groupList and control == 1:
                pass
            else:
                self.patient_evaluation_gui(control)  # evaluate as group

            # for obj in self.groupList:
            #     print(obj.fileName + "\t\t\t" + obj.filePath)

        def populate_group_list():
            for obj in self.groupList:
                self.group_list.insert(END, obj.fileName)
            # clear groupList so there aren't extra patients if evaluate is selected again
            self.groupList.clear()

        # gui handling
        self.remove_gui(self.gui_elements)

        # title label
        self.titleLabel = Label(root, text="Please Select Files", font=("Arial", 16))
        self.titleLabel.grid(row=0, column=0, columnspan=8, pady=10, padx=10)

        # list of patients under directory
        self.patients_frame = Frame(root)
        self.patients_frame.grid(row=1, column=0, columnspan=4, rowspan=6, pady=20, padx=20)

        self.patient_scrollbar = Scrollbar(self.patients_frame, orient=VERTICAL)
        self.patient_scrollbar.pack(side=RIGHT, fill=Y)

        self.patients_list = Listbox(self.patients_frame, height=16, width=40, border=2)
        self.patients_list.pack()

        self.patients_list.configure(yscrollcommand=self.patient_scrollbar.set)
        self.patient_scrollbar.configure(command=self.patients_list.yview)

        self.patients_list.bind('<<ListboxSelect>>', select_patient)

        # group and ungroup buttons
        self.group_button = Button(root, text=">", command=lambda: add_patient(), width=5)
        self.group_button.grid(row=2, column=4)

        self.ungroup_button = Button(root, text="X", command=lambda: remove_patient(), width=5)
        self.ungroup_button.grid(row=4, column=4)

        # list of user selected group
        self.group_frame = Frame(root)
        self.group_frame.grid(row=1, column=5, columnspan=3, rowspan=6, pady=20, padx=20)

        self.grouplist_scrollbar = Scrollbar(self.group_frame, orient=VERTICAL)
        self.grouplist_scrollbar.pack(side=RIGHT, fill=Y)

        self.group_list = Listbox(self.group_frame, height=16, width=40, border=2)
        self.group_list.pack()

        self.group_list.configure(yscrollcommand=self.grouplist_scrollbar.set)
        self.grouplist_scrollbar.configure(command=self.group_list.yview)

        self.group_list.bind('<<ListboxSelect>>', select_patient_group)

        # back button
        self.backButton = Button(root, text="Back to Directory Selection", command=lambda: self.root_gui(),
                                 font=("Arial", 12), width=22)
        self.backButton.grid(row=8, column=0)

        # evaluate all/group buttons
        self.evalAll = Button(root, text="Evaluate All", command=lambda: group_to_list(0), font=("Arial", 12), width=10)
        self.evalAll.grid(row=8, column=3, columnspan=2)

        self.evalGroup = Button(root, text="Evaluate Selection", command=lambda: group_to_list(1), font=("Arial", 12),
                                width=16)
        self.evalGroup.grid(row=8, column=5, padx=10)

        self.clearGroupList = Button(root, text="Clear Selection", command=lambda: clear_selection(), font=("Arial", 12), width=14)
        self.clearGroupList.grid(row=8, column=6)

        populate_patient_list()
        populate_group_list()

        self.gui_elements = [self.titleLabel,
                             self.backButton,
                             self.patients_list,
                             self.group_list,
                             self.patient_scrollbar,
                             self.grouplist_scrollbar,
                             self.group_button,
                             self.ungroup_button,
                             self.evalGroup,
                             self.evalAll,
                             self.group_frame,
                             self.patients_frame,
                             self.clearGroupList]

    def check_dir(self, directory):

        # print("directory is: " + directory)

        if directory == '':
            messagebox.showerror('Required Field', 'Please select a directory.')
            self.root_gui()
        else:
            self.patientDirectory = directory
            # clear groupList in case a different directory is chosen
            self.groupList.clear()
            self.populate_patientList()

    def root_gui(self):
        self.remove_gui(self.gui_elements)
        self.patientList.clear()

        def directory_select():
            root = Tk()
            root.withdraw()
            self.patientDirectory = filedialog.askdirectory()

            self.dirTextbox.delete(0, END)
            self.dirTextbox.insert(END, self.patientDirectory)

        root.title("Performance Metrics Tool")

        self.titleLabel = Label(root, text="Performance Metrics Tool", font=("Arial", 16))
        self.titleLabel.pack(pady=10)

        self.pleaseChooseLabel = Label(root, text="Please choose a directory:")
        self.pleaseChooseLabel.pack()

        dir_text = StringVar()
        self.dirTextbox = Entry(root, textvariable=dir_text, width=80)
        self.dirTextbox.pack()

        self.dirButton = Button(root, text="Select Directory", command=lambda: directory_select(), font=("Arial", 12),
                                width=20)
        self.dirButton.pack()

        self.nextButton = Button(root, text="Next", command=lambda: self.check_dir(dir_text.get()), font=("Arial", 12),
                                 width=20)
        self.nextButton.pack()

        self.gui_elements = [self.titleLabel,
                             self.pleaseChooseLabel,
                             self.dirTextbox,
                             self.dirButton,
                             self.nextButton]


def quit():
    root.quit()
    root.destroy()


if __name__ == '__main__':
    global root

    root = Tk()
    root.geometry("700x450")
    window = MainWindow()
    root.protocol("WM_DELETE_WINDOW", quit)

    root.mainloop()
