import customtkinter
import pandas
import pandas as pd
import matplotlib.pyplot as plt
from customtkinter import CTkButton
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
import ttkbootstrap as tkb


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

        self.saved_cardio_threshold = 5
        self.saved_patient_threshold = 5

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
                    excelFiles = glob.glob(file + "/Res*.csv")
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

    def calculate_metrics(self, df):
        metrics = {}
        metrics['difference'] = df['HR'] - df['SpO2HR']
        metrics['convergence_time'] = (df['HR'] - df['SpO2HR']).abs().idxmin()
        metrics['batch_average'] = df[['HR', 'SpO2HR']].mean()
        return metrics

    def plot_metrics(self, df, metrics, file_name):
        fig, axs = plt.subplots(3, figsize=(6.1, 9.6))
        fig.suptitle(f"Metrics for {file_name}", fontsize=12, fontfamily='Sans Serif', color='#212121')

        # Difference between HR and SpO2HR
        axs[0].plot(df['time(s)'], metrics['difference'], color='#FF0000')
        axs[0].set_title(f" Difference between HR and SpO2HR          Mean: {metrics['difference'].mean():.2f}",
                         fontsize=11, color='#2962FF', pad=10)
        # graphing plot
        axs[0].set_xlabel('Time (s)', fontsize=9)
        axs[0].set_ylabel('Difference', fontsize=9)

        # HR and SpO2HR Over Time
        axs[1].plot(df['time(s)'], df['HR'], label='HR', color='#000000')
        axs[1].plot(df['time(s)'], df['SpO2HR'], label='SpO2HR', color='#FF0000')

        axs[1].set_title(f"HR and SpO2HR Over Time         Convergence Time: {metrics['convergence_time']} seconds",
                         fontsize=10, color='#2962FF')
        # graphing plot
        axs[1].set_xlabel('Time (s)', fontsize=9)
        axs[1].set_ylabel('Heart Rate', fontsize=9)

        # Batch Averages
        axs[2].bar(['Average HR', 'Average SpO2HR'], metrics['batch_average'],
                   color=['#000000', '#FF0000'])
        axs[2].set_title(f"Averages     Avg. HR: {metrics['batch_average']['HR']:.2f} "
                         f"      Avg. SpO2HR: {metrics['batch_average']['SpO2HR']:.2f}", fontsize=10,
                         color='#2962FF')

        plt.tight_layout(rect=[0.0, 0.03, 1.0, 0.95])
        plt.subplots_adjust(hspace=0.4)
        return fig

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

        def export_to_pdf():

            datapath = os.path.join(os.getcwd(), "Data")

            if not os.path.exists(datapath):
                os.mkdir(datapath)

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)

            for file, df in zip(self.selected_files, self.data):
                metrics = self.calculate_metrics(df)
                fig = self.plot_metrics(df, metrics, os.path.basename(file))
                img_path = os.path.join(datapath, f"{os.path.splitext(os.path.basename(file))[0]}.png")
                fig.savefig(img_path)
                plt.close(fig)

                pdf.add_page()
                pdf.image(img_path, x=10, y=10, w=190)
                os.remove(img_path)

            pdf_output_path = os.path.join(datapath, "report.pdf")
            pdf.output(pdf_output_path)

            messagebox.showinfo("Success", f"PDF Report '{pdf_output_path}' generated successfully!")

        def show_plots():
            if not self.selected_files:
                messagebox.showerror("Error", "No files selected. Please select CSV files first.")
                return

            # Only create one plot window
            if hasattr(self, 'plot_frame') and self.plot_frame.winfo_exists():
                self.plot_frame.lift()
            else:
                self.plot_frame = Toplevel()
                self.plot_frame.title("TeleSensor Graph Plot")

                # set the window
                x = (self.plot_frame.winfo_screenwidth() // 2) - (750 // 2)
                y = (self.plot_frame.winfo_screenheight() // 2) - (930 // 3)
                self.plot_frame.geometry('{}x{}+{}+{}'.format(750, 930, x, y))
                self.plot_frame.resizable(True, True)
                self.plot_frame.configure(background='white')

                btn_previous = customtkinter.CTkFrame(self.plot_frame, fg_color='#FFF')
                btn_previous.grid(row=0, column=0)

                btn_next = customtkinter.CTkFrame(self.plot_frame, fg_color='#FFF')
                btn_next.grid(row=0, column=2)

                self.plot_frame = Frame(self.plot_frame, width=745, height=930)
                self.plot_frame.grid(row=0, column=1)

                current_index = [0]

                def update_plot(index):
                    for widget in self.plot_frame.winfo_children():
                        widget.destroy()

                    fig = self.plot_metrics(self.data[index], self.calculate_metrics(self.data[index]),
                                            os.path.basename(self.selected_files[index]))
                    canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

                def next_plot():
                    if current_index[0] < len(self.selected_files) - 1:
                        current_index[0] += 1
                        update_plot(current_index[0])

                def previous_plot():
                    if current_index[0] > 0:
                        current_index[0] -= 1
                        update_plot(current_index[0])

                # Only show buttons if more than one file is uploaded
                if len(self.selected_files) >= 1:
                    # previous plot

                    customtkinter.CTkButton(btn_previous, text='Previous', width=40, height=36,
                                            fg_color="#1976D2",
                                            hover_color="#424242", corner_radius=5, command=previous_plot).pack(padx=5)

                    # next plot
                    customtkinter.CTkButton(btn_next, text='Next', width=40, height=36,
                                            fg_color="#1976D2",
                                            hover_color="#424242", corner_radius=5, command=next_plot).pack(padx=5)

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

                print(self.cardioFeed_selection)

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

        if cFeedPaths:
            for v in cFeedPaths:
                versionList.append(os.path.basename(v))

            # create list of version numbers corresponding to the same index of the path list
            for file in cFeedPaths:
                versionList_float.append(float(os.path.basename(file)[11:-4]))

            # find maximum version number
            newestVersion = os.path.basename(cFeedPaths[versionList_float.index(max(versionList_float))])
        else:
            versionList.append('N/A')
            newestVersion = 'N/A'

        # dropdown menu
        version = StringVar()
        version.set(newestVersion)

        self.dropdown = OptionMenu(root, version, *versionList)
        self.dropdown.configure(fg='black', bg='white')
        self.dropdown["menu"].configure(fg='black', bg='white')
        self.dropdown.grid(row=2, column=10)

        # CardioFeed button
        self.CFeedButton = CTkButton(root, text="Start CardioFeed", command=lambda: cardioFeed_check(),
                                     font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
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
        self.backButton = CTkButton(root, text="Back to Patient Selection", command=lambda: self.select_files_gui(),
                                    font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.backButton.grid(row=8, column=0)

        # view all metrics button
        self.allMetrics = CTkButton(root, text="View Metrics (patient data only)", command=lambda: show_plots(),
                                    font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.allMetrics.grid(row=4, column=8, columnspan=3)

        # print to pdf button
        self.printPDF = CTkButton(root, text="Print to PDF (patient data only)", command=lambda: export_to_pdf(),
                                  font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
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
                float(start)
            except ValueError:
                messagebox.showerror('Value Error', 'Input must be a float.')
                self.cardioFeed_gui(control)
                return

        else:
            try:
                float(start)
                float(duration)
            except ValueError:
                messagebox.showerror('Value Error', 'Input must be a float.')
                self.cardioFeed_gui(control)
                return

        file = self.copyCSV()

        # if there is no raw file to use with cardioFeed
        if not file:
            return

        # convert from seconds to ms
        start = float(start) * 1000
        start = str(int(start))
        if duration != '':
            duration = float(duration) * 1000
            duration = str(int(duration))

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
        else:
            self.output_list.append([float(x[1]), float(x[3]), float(x[5]), float(x[7]), float(x[9])])

    def get_plot(self):

        T = []
        HR = []
        RR = []

        for row in self.output_list[1:]:
            T.append(int(row[0]))
            HR.append(int(row[1]))
            RR.append(int(row[2]))

        return T, HR, RR

    def generate_excel(self, df):

        datapath = os.path.join(os.getcwd(), "Data")

        if not os.path.exists(datapath):
            os.mkdir(datapath)

        os.chdir(datapath)
        df.to_excel(os.path.basename(self.cardioFeed_selection) + '_output.xlsx', index=False, header=False)
        os.chdir("..")

        messagebox.showinfo("Success", f"{os.path.basename(self.cardioFeed_selection) + '_output.xlsx'} generated successfully!")

    def get_df(self):

        resFile = glob.glob(self.cardioFeed_selection + "/Res*.csv")
        data = pd.read_csv(resFile[0])

        merged_data = [['time(s)', 'Patient-HR', 'Patient-RR', 'Cardio-HR', 'Cardio-RR', 'SPO2-HR']]

        # mod ensures the data is aligned if starting from a later timestamp in cardioFeed
        mod = 0

        for index, row in data.iterrows():
            if index + 1 + mod < len(self.output_list):
                if self.output_list[index + 1 + mod][0] == row['time(s)']:
                    cardio_hr = self.output_list[index + 1 + mod][1]
                    cardio_rr = self.output_list[index + 1 + mod][2]
                else:
                    cardio_hr = ''
                    cardio_rr = ''
                    mod -= 1
            else:
                cardio_hr = ''
                cardio_rr = ''

            merged_data.append([
                row['time(s)'],
                row['HR'],
                row['RR'],
                cardio_hr,
                cardio_rr,
                row['SpO2HR']
            ])

        df = pd.DataFrame(merged_data)

        return df

    def cf_metrics(self, df, lower, upper):
        metrics = {}

        metrics['patient error'] = df[1].loc[lower:upper] - df[5].loc[lower:upper]
        metrics['cardio error'] = df[3].loc[lower:upper] - df[5].loc[lower:upper]
        metrics['RR difference'] = df[4].loc[lower:upper] - df[2].loc[lower:upper]

        patient_std = df[1].loc[lower:upper].std()
        cardio_std = df[3].loc[lower:upper].std()
        spo2_std = df[5].loc[lower:upper].std()
        cardio_std_error = cardio_std - spo2_std
        patient_std_error = patient_std - spo2_std

        return metrics, cardio_std_error, patient_std_error

    def cf_to_pdf(self, fig1, fig2, fig3):
        datapath = os.path.join(os.getcwd(), "Data")

        if not os.path.exists(datapath):
            os.mkdir(datapath)

        # get dataframe
        df = self.get_df()

        start_time = self.output_list[1][0] + 1
        end_time = len(self.output_list) - 1 + start_time - 1

        # get metrics
        metrics, cardio_std_error, patient_std_error = self.cf_metrics(df, start_time, end_time)

        cardio_accuracy_upper = metrics['cardio error'].abs().mean() + (3 * cardio_std_error)
        cardio_accuracy_lower = metrics['cardio error'].abs().mean() - (3 * cardio_std_error)
        patient_accuracy_upper = metrics['patient error'].abs().mean() + (3 * patient_std_error)
        patient_accuracy_lower = metrics['patient error'].abs().mean() - (3 * patient_std_error)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.add_page()

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(200, 10, txt=os.path.basename(self.cardioFeed_selection).split('-')[0], ln=True, align='C')

        # pass or fail
        if (abs(cardio_accuracy_upper) < self.saved_cardio_threshold and
                abs(cardio_accuracy_lower) < self.saved_cardio_threshold and
                abs(patient_accuracy_upper) < self.saved_patient_threshold and
                abs(patient_accuracy_lower) < self.saved_patient_threshold):
            pdf.set_text_color(0, 255, 0)  # green
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="PASS", ln=True, align='C')
        else:
            pdf.set_text_color(255, 0, 0)  # red
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="FAIL", ln=True, align='C')

        pdf.set_text_color(0, 0, 0)

        table_data = [
            ['Heart Rate', 'Mean Error', 'SD Error', 'Accuracy', 'Threshold'],
            ['Cardio', f"{metrics['cardio error'].abs().mean():.2f}", f"{cardio_std_error:.2f}", f"{cardio_accuracy_upper:.2f} / {cardio_accuracy_lower:.2f}", self.saved_cardio_threshold],
            ['Patient', f"{metrics['patient error'].abs().mean():.2f}", f"{patient_std_error:.2f}", f"{patient_accuracy_upper:.2f} / {patient_accuracy_lower:.2f}", self.saved_patient_threshold]
        ]

        pdf.set_font("Arial", size=12)
        for row in table_data:
            for item in row:
                pdf.cell(35, 10, str(item), border=1)
            pdf.ln()

        # Save the plots as images and insert them into the PDF
        fig_paths = [os.path.join(datapath, f"fig{i}.png") for i in range(1, 4)]
        figs = [fig1, fig2, fig3]

        for i, fig in enumerate(figs):
            pdf.add_page()
            fig_path = fig_paths[i]
            fig.savefig(fig_path)
            pdf.image(fig_path, x=10, y=30, w=pdf.w - 20)
            os.remove(fig_path)

        # Output the PDF
        pdf_path = os.path.join(datapath, os.path.basename(self.cardioFeed_selection).split('-')[0] + "_cf_plots.pdf")
        pdf.output(pdf_path)

    def next_gui(self, control):

        # make window larger
        self.set_screen(1000, 1300)

        # delete the raw file
        self.deleteCSV()

        # go back to main directory
        os.chdir('..')

        df = self.get_df()

        start_time = self.output_list[1][0] + 1
        end_time = len(self.output_list) - 1 + start_time - 1

        metrics, cardio_std_error, patient_std_error = self.cf_metrics(df, start_time, end_time)

        cardio_accuracy_upper = metrics['cardio error'].abs().mean() + (3 * cardio_std_error)
        cardio_accuracy_lower = metrics['cardio error'].abs().mean() - (3 * cardio_std_error)
        patient_accuracy_upper = metrics['patient error'].abs().mean() + (3 * patient_std_error)
        patient_accuracy_lower = metrics['patient error'].abs().mean() - (3 * patient_std_error)

        print(cardio_accuracy_upper, cardio_accuracy_lower, patient_accuracy_upper, patient_accuracy_lower)

        self.remove_gui(self.gui_elements)

        nameVar = os.path.basename(self.cardioFeed_selection).split('-')[0]

        self.topframe = Frame(root)
        self.topframe.pack(fill=X, side=TOP)

        self.title2 = Label(self.topframe, text=nameVar, font=("Arial", 18))
        self.title2.pack(side=LEFT)

        self.subtopframe = Frame(self.topframe)
        self.subtopframe.pack(side=RIGHT)

        self.statuslabel = Label(self.subtopframe, text='Status: ', font=("Arial", 18))
        self.statuslabel.grid(row=0, column=0)

        self.status = Label(self.subtopframe, text='', font=("Arial", 18), fg="green")
        self.status.grid(row=0, column=1)

        def pass_fail():
            if (abs(cardio_accuracy_upper) < self.saved_cardio_threshold and
                    abs(cardio_accuracy_lower) < self.saved_cardio_threshold and
                    abs(patient_accuracy_upper) < self.saved_patient_threshold and
                    abs(patient_accuracy_lower) < self.saved_patient_threshold):
                self.status.config(text='PASS', fg='green')
            else:
                self.status.config(text='FAIL', fg='red')

        pass_fail()

        self.tablename = Label(root, text='Error Metrics', font=("Arial", 14))
        self.tablename.pack()

        self.tableframe = Frame(root, highlightbackground='black', highlightthickness=1)
        self.tableframe.pack()

        # create cell function
        def create_cell(parent, text, row, column):
            frame = Frame(parent, highlightbackground='black', highlightthickness=1, width=20)
            frame.grid(row=row, column=column, sticky="nsew")
            label = Label(frame, text=text, font=("Arial", 14))
            label.pack(expand=True, fill=BOTH)
            return frame, label

        self.a1, self.a1l = create_cell(self.tableframe, 'HeartRate', 0, 0)
        self.a2, self.a2l = create_cell(self.tableframe, 'Mean_error', 0, 1)
        self.a3, self.a3l = create_cell(self.tableframe, 'SD_error', 0, 2)
        self.a4, self.a4l = create_cell(self.tableframe, 'Accuracy (3-sigma)', 0, 3)
        self.a5, self.a5l = create_cell(self.tableframe, 'Threshold', 0, 4)

        self.b1, self.b1l = create_cell(self.tableframe, 'Cardio', 1, 0)
        self.b2, self.b2l = create_cell(self.tableframe, f"{metrics['cardio error'].abs().mean():.2f}", 1, 1)
        self.b3, self.b3l = create_cell(self.tableframe, f"{cardio_std_error:.2f}", 1, 2)
        self.b4, self.b4l = create_cell(self.tableframe, f"{cardio_accuracy_upper:.2f} / {cardio_accuracy_lower:.2f}",
                                        1, 3)
        self.b5 = Frame(self.tableframe, highlightbackground='black', highlightthickness=1, width=20)
        self.b5.grid(row=1, column=4, sticky="nsew")

        def update_ct(event):
            try:
                self.saved_cardio_threshold = float(cardio_threshold.get())
                pass_fail()
                # then update config
            except ValueError:
                pass

        cardio_threshold = StringVar()
        cardio_threshold.set(str(self.saved_cardio_threshold))
        self.b5e = Entry(self.b5, textvariable=cardio_threshold, font=("Arial", 14))
        self.b5e.pack(expand=True, fill=BOTH)
        self.b5e.bind('<KeyRelease>', update_ct)

        self.c1, self.c1l = create_cell(self.tableframe, 'Patient', 2, 0)
        self.c2, self.c2l = create_cell(self.tableframe, f"{metrics['patient error'].abs().mean():.2f}", 2, 1)
        self.c3, self.c3l = create_cell(self.tableframe, f"{patient_std_error:.2f}", 2, 2)
        self.c4, self.c4l = create_cell(self.tableframe, f"{patient_accuracy_upper:.2f} / {patient_accuracy_lower:.2f}",
                                        2, 3)
        self.c5 = Frame(self.tableframe, highlightbackground='black', highlightthickness=1, width=20)
        self.c5.grid(row=2, column=4, sticky="nsew")

        def update_pt(event):
            try:
                self.saved_patient_threshold = float(patient_threshold.get())
                pass_fail()
                # then update config
            except ValueError:
                pass

        patient_threshold = StringVar()
        patient_threshold.set(str(self.saved_patient_threshold))
        self.c5e = Entry(self.c5, textvariable=patient_threshold, font=("Arial", 14))
        self.c5e.pack(expand=True, fill=BOTH)
        self.c5e.bind('<KeyRelease>', update_pt)

        for i in range(5):
            self.tableframe.grid_columnconfigure(i, weight=1, pad=10)

        # get cardio T, HR, and RR
        T, HR, RR = self.get_plot()

        # generate Error-HR figure
        fig = Figure(figsize=(5, 3), dpi=100)

        error_plt = fig.add_subplot(111)

        error_plt.plot(T, metrics['cardio error'], label='Cardio-HR Error')
        error_plt.plot(T, metrics['patient error'], label='Patient-HR Error')
        error_plt.legend()
        error_plt.set_xlim([0, None])
        error_plt.set_xlabel('Time (seconds)')
        error_plt.set_ylabel('Error-HR (BPM)')

        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.draw()

        # display error plot
        self.graph = canvas.get_tk_widget()
        self.graph.pack(side=TOP, fill=BOTH, expand=1)

        # ['time(s)', 'Patient-HR', 'Patient-RR', 'Cardio-HR', 'Cardio-RR', 'SPO2-HR']
        #     0             1            2             3           4             5

        # generate Heart Rate Plot
        fig2 = Figure(figsize=(5, 3), dpi=100)

        hr_plt = fig2.add_subplot(111)

        hr_plt.plot(T, df[3].loc[start_time:end_time], label='Cardio-HR')
        hr_plt.plot(T, df[1].loc[start_time:end_time], label='Patient-HR')
        hr_plt.plot(T, df[5].loc[start_time:end_time], label='SpO2-HR')
        hr_plt.legend()
        hr_plt.set_ylim([0, None])
        hr_plt.set_xlim([0, None])
        hr_plt.set_xlabel('Time (seconds)')
        hr_plt.set_ylabel('Heart Rate (BPM)')

        canvas = FigureCanvasTkAgg(fig2, master=root)
        canvas.draw()

        # display heart rate plot
        self.graph2 = canvas.get_tk_widget()
        self.graph2.pack(side=TOP, fill=BOTH, expand=1)

        # generate Respiratory Rate Plot
        fig3 = Figure(figsize=(5, 3), dpi=100)

        rr_plt = fig3.add_subplot(111)

        rr_plt.plot(T, df[4].loc[start_time:end_time], label='Cardio-RR')
        rr_plt.plot(T, df[2].loc[start_time:end_time], label='Patient-RR')
        rr_plt.legend()
        rr_plt.set_ylim([0, None])
        rr_plt.set_xlim([0, None])
        rr_plt.set_xlabel('Time (seconds)')
        rr_plt.set_ylabel('Respiratory Rate (BRPM)')

        canvas = FigureCanvasTkAgg(fig3, master=root)
        canvas.draw()

        # display respiratory rate plot
        self.graph3 = canvas.get_tk_widget()
        self.graph3.pack(side=TOP, fill=BOTH, expand=1)

        # bottom frame
        self.bottomframe = Frame(root)
        self.bottomframe.pack(fill=X, side=BOTTOM)

        # back button
        self.button2 = CTkButton(self.bottomframe, text="Back", command=lambda: self.cardioFeed_gui(control), width=80,
                                 font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.button2.pack(side='left', padx=5, pady=5)

        # align buttons to right side
        self.sub_bottomframe = Frame(self.bottomframe)
        self.sub_bottomframe.pack(side='right', padx=5, pady=5)

        # print to pdf and generate excel buttons
        self.printtoPDF = CTkButton(self.sub_bottomframe, text="Print to PDF", command=lambda: self.cf_to_pdf(fig, fig2, fig3),
                                 font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.printtoPDF.grid(row=0, column=0, padx=5)

        self.generateExcel = CTkButton(self.sub_bottomframe, text="Generate Excel File", command=lambda: self.generate_excel(df),
                                   font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.generateExcel.grid(row=0, column=1, padx=5)

        self.gui_elements = [self.title2,
                             self.button2,
                             self.graph,
                             self.topframe,
                             self.subtopframe,
                             self.statuslabel,
                             self.status,
                             self.tablename,
                             self.tableframe,
                             self.a1, self.a1l,
                             self.a2, self.a2l,
                             self.a3, self.a3l,
                             self.a4, self.a4l,
                             self.a5, self.a5l,
                             self.b1, self.b1l,
                             self.b2, self.b2l,
                             self.b3, self.b3l,
                             self.b4, self.b4l,
                             self.b5, self.b5e,
                             self.c1, self.c1l,
                             self.c2, self.c2l,
                             self.c3, self.c3l,
                             self.c4, self.c4l,
                             self.c5, self.c5e,
                             self.graph2,
                             self.graph3,
                             self.bottomframe,
                             self.sub_bottomframe,
                             self.printtoPDF,
                             self.generateExcel]

    def check_queue(self, control):
        try:
            # receive for output
            output = self.output_queue.get_nowait()
            # print(output)

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

        if self.rawFile:
            print("Copying file into directory...")
            shutil.copy(self.rawFile[0], os.getcwd() + "/cardioFeed")
            print("File copied successfully.")
            return self.rawFile[0]
        else:
            messagebox.showerror('ERROR', 'No Raw file found.')
            return

    def deleteCSV(self):
        file_to_delete = os.getcwd() + "/" + os.path.basename(self.rawFile[0])
        print("Deleting " + os.path.basename(self.rawFile[0]) + "...")

        if os.path.exists(file_to_delete):
            os.remove(file_to_delete)
            print("File deleted.")
        else:
            print("File not found.")

    def set_screen(self, width, height):
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)

        root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

    def cardioFeed_gui(self, control):

        # reset window size
        self.set_screen(700, 400)

        # reset output_list so cardioFeed can be run again
        self.output_list = [["T", "HR", "RR", "M", "S"]]

        # gui handling
        self.remove_gui(self.gui_elements)

        # cardioFeed eval label
        self.cf_title = Label(root, text="Patient Selected for CardioFeed", font=("Arial", 16))
        self.cf_title.grid(row=0, column=0, columnspan=3, pady=10, padx=20)

        # selected file label
        self.cf_selection = Label(root, text=os.path.basename(self.cardioFeed_selection), font=("Arial", 12))
        self.cf_selection.grid(row=1, column=0, columnspan=3, pady=10, padx=20)

        # choose start time
        self.start_time = Label(root, text="Start Time (s): ", font=("Arial", 12))
        self.start_time.grid(row=2, column=0, pady=20, padx=20)

        start_time_num = StringVar()
        self.start_time_box = Entry(root, textvariable=start_time_num, width=15)
        self.start_time_box.grid(row=2, column=1, pady=20, padx=20)

        # choose duration
        self.duration = Label(root, text="Duration (s): ", font=("Arial", 12))
        self.duration.grid(row=3, column=0, pady=10, padx=20)

        duration_num = StringVar()
        self.duration_box = Entry(root, textvariable=duration_num, width=15)
        self.duration_box.grid(row=3, column=1, pady=10, padx=20)

        # default behavior label
        self.zero_def = Label(root, text="Will play full duration from the start by default.", font=("Arial", 10))
        self.zero_def.grid(row=4, column=0, columnspan=2, pady=10, padx=20)

        # create .csv file from output
        # excelVar = IntVar()
        # self.create_csv = Checkbutton(root, text="Generate Excel File from Output", variable=self.excelVar, onvalue=1, offvalue=0, font=("Arial", 12))
        # self.create_csv.grid(row=5, column=0, columnspan=2, pady=10, padx=20)

        # run button
        self.run_button = CTkButton(root, text="Run",
                                    command=lambda: self.threading(start_time_num.get(), duration_num.get(), control),
                                    width=80, font=("Arial", 16), fg_color="#1976D2", hover_color="#424242",
                                    corner_radius=5)
        self.run_button.grid(row=8, column=8)

        # back button
        self.backToEval = CTkButton(root, text="Back", command=lambda: self.patient_evaluation_gui(control),
                                    width=80, font=("Arial", 16), fg_color="#1976D2", hover_color="#424242",
                                    corner_radius=5)
        self.backToEval.grid(row=8, column=0)

        self.gui_elements = [self.backToEval,
                             self.cf_title,
                             self.cf_selection,
                             self.start_time,
                             self.start_time_box,
                             self.duration,
                             self.duration_box,
                             self.zero_def,
                             self.run_button]

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
        self.titleLabel = Label(root, text="Please Select Files:", font=("Arial", 16), anchor='w')
        self.titleLabel.pack()

        self.mid_frame = Frame(root)
        self.mid_frame.pack()

        # list of patients under directory
        self.patients_frame = Frame(self.mid_frame)
        self.patients_frame.grid(row=1, column=0, columnspan=4, rowspan=5, pady=20, padx=20)

        self.patient_scrollbar = Scrollbar(self.patients_frame, orient=VERTICAL)
        self.patient_scrollbar.pack(side=RIGHT, fill=Y)

        self.patients_list = Listbox(self.patients_frame, height=16, width=40, border=2)
        self.patients_list.pack()

        self.patients_list.configure(yscrollcommand=self.patient_scrollbar.set)
        self.patient_scrollbar.configure(command=self.patients_list.yview)

        self.patients_list.bind('<<ListboxSelect>>', select_patient)

        # group and ungroup buttons
        self.group_button = CTkButton(self.mid_frame, text="Add", command=lambda: add_patient(), width=80,
                                      font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.group_button.grid(row=2, column=4)

        self.ungroup_button = CTkButton(self.mid_frame, text="Remove", command=lambda: remove_patient(), width=80,
                                        font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.ungroup_button.grid(row=4, column=4)

        # list of user selected group
        self.group_frame = Frame(self.mid_frame)
        self.group_frame.grid(row=1, column=5, columnspan=3, rowspan=5, pady=20, padx=20)

        self.grouplist_scrollbar = Scrollbar(self.group_frame, orient=VERTICAL)
        self.grouplist_scrollbar.pack(side=RIGHT, fill=Y)

        self.group_list = Listbox(self.group_frame, height=16, width=40, border=2)
        self.group_list.pack()

        self.group_list.configure(yscrollcommand=self.grouplist_scrollbar.set)
        self.grouplist_scrollbar.configure(command=self.group_list.yview)

        self.group_list.bind('<<ListboxSelect>>', select_patient_group)

        self.bottom_frame = Frame(root)
        self.bottom_frame.pack(fill=X, side=BOTTOM)

        # back button
        self.backButton = CTkButton(self.bottom_frame, text="Back", command=lambda: self.root_gui(), font=("Arial", 16),
                                    fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.backButton.pack(side='left', padx=5, pady=5)

        # sub bottom frame
        self.sub_bottom_frame = Frame(self.bottom_frame)
        self.sub_bottom_frame.pack(side='right', padx=5, pady=5)

        # evaluate all/group buttons
        self.evalAll = CTkButton(self.sub_bottom_frame, text="Evaluate All", command=lambda: group_to_list(0),
                                 font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.evalAll.grid(row=0, column=0, padx=5)

        self.evalGroup = CTkButton(self.sub_bottom_frame, text="Evaluate Selection", command=lambda: group_to_list(1),
                                   font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.evalGroup.grid(row=0, column=1, padx=5)

        self.clearGroupList = CTkButton(self.sub_bottom_frame, text="Clear Selection",
                                        command=lambda: clear_selection(), font=("Arial", 16), fg_color="#1976D2",
                                        hover_color="#424242", corner_radius=5)
        self.clearGroupList.grid(row=0, column=2, padx=5)

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
                             self.clearGroupList,
                             self.bottom_frame,
                             self.mid_frame,
                             self.sub_bottom_frame]

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
        self.titleLabel.pack(pady=5)

        # self.pleaseChooseLabel = Label(root, text="Please choose a directory:")
        # self.pleaseChooseLabel.pack()

        dir_text = StringVar()
        self.dirTextbox = Entry(root, textvariable=dir_text, width=80)
        self.dirTextbox.pack(pady=5)

        self.dirButton = CTkButton(root, text="Select Patient Directory", command=lambda: directory_select(),
                                   font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.dirButton.pack(pady=5)

        self.nextButton = CTkButton(root, text="Next", command=lambda: self.check_dir(dir_text.get()), font=("Arial", 16), fg_color="#1976D2", hover_color="#424242", corner_radius=5)
        self.nextButton.pack(pady=5)

        self.gui_elements = [self.titleLabel,
                             self.dirTextbox,
                             self.dirButton,
                             self.nextButton]


def quit():
    root.quit()
    root.destroy()


if __name__ == '__main__':
    global root

    # root = Tk()

    root = tkb.Window(themename='flatly')  # flatly, darkly

    width = 700
    height = 400

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)

    root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
    window = MainWindow()
    root.protocol("WM_DELETE_WINDOW", quit)

    root.mainloop()
