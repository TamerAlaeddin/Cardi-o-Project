import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from tkinter import *
from tkinter import Tk, filedialog, Button, Label, messagebox
import os
import glob
from pathlib import Path

class MainWindow:
    def __init__(self):
        # Initialize variables to hold data and selected file paths
        self.data = None
        self.selected_files = []
        self.patientDirectory = ""
        self.patientList = []
        self.groupList = []
        self.gui_elements = []

        self.root_gui()

        # Initialize variables to hold data and selected file paths
        self.data = None
        self.selected_files = []

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
            data_frames = []
            excel_files = []

            # get res .csv files from patient folders
            for csv in file_paths:
                resFile = glob.glob(csv.filePath + "/Res*.csv")
                excel_files.append(resFile[0])

            for file in excel_files:
                df = pd.read_csv(file)
                data_frames.append(df)

            self.data = pd.concat(data_frames, ignore_index=True)
            self.selected_files = excel_files  # Save the selected file paths for later use

        def calculate_metrics():
            # Calculate performance metrics from the loaded data
            if self.data is None:
                messagebox.showerror("Error", "No data loaded.")
                return None

            metrics = {}
            metrics['difference'] = self.data['HR'] - self.data['SpO2HR']
            metrics['convergence_time'] = (self.data['HR'] - self.data['SpO2HR']).abs().idxmin()
            metrics['batch_average'] = self.data[['HR', 'SpO2HR']].mean()

            return metrics

        def plot_metrics(metrics):
            # Plot the calculated metrics and display them in a matplotlib figure
            fig, axs = plt.subplots(2, 2, figsize=(12, 8))

            # Plot the difference between HR and SpO2HR
            axs[0, 0].plot(self.data['time(s)'], metrics['difference'])
            axs[0, 0].set_title('Difference between HR and SpO2HR')
            axs[0, 0].set_xlabel('Time (s)')
            axs[0, 0].set_ylabel('Difference')

            # Plot HR and SpO2HR over time
            axs[0, 1].plot(self.data['time(s)'], self.data['HR'], label='HR')
            axs[0, 1].plot(self.data['time(s)'], self.data['SpO2HR'], label='SpO2HR')
            axs[0, 1].set_title('HR and SpO2HR Over Time')
            axs[0, 1].set_xlabel('Time (s)')
            axs[0, 1].set_ylabel('Heart Rate')
            axs[0, 1].legend()

            # Plot batch averages
            axs[1, 0].bar(['Batch Average HR', 'Batch Average SpO2HR'], metrics['batch_average'])
            axs[1, 0].set_title('Batch Averages')

            axs[1, 1].axis('off')
            metrics_text = (
                f"Difference between HR and SpO2HR (mean): {metrics['difference'].mean():.2f}\n"
                f"Convergence Time: {metrics['convergence_time']} seconds\n"
                f"Batch Average HR: {metrics['batch_average']['HR']:.2f}\n"
                f"Batch Average SpO2HR: {metrics['batch_average']['SpO2HR']:.2f}"
            )
            fig.text(0.63, 0.3, metrics_text, ha='left', va='center', fontsize=12,
                     bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=1'))

            plt.tight_layout(rect=[0, 0.1, 1, 0.95])
            plt.subplots_adjust(hspace=0.3, top=0.9, bottom=0.15)
            plt.show()

        def display_metrics():
            # Display the calculated metrics
            metrics = calculate_metrics()
            if metrics:
                plot_metrics(metrics)
                # print(metrics)

        def export_to_pdf(metrics):
            # Export the calculated metrics and selected patient files to a PDF report
            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("Arial", size=14)
            pdf.cell(200, 10, txt="Performance Metrics Report", ln=True, align='C')
            pdf.ln(10)

            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Selected Patient Files:", ln=True)
            pdf.set_font("Arial", size=11)
            for file in self.selected_files:
                filename = os.path.basename(file)
                pdf.cell(200, 10, txt=filename, ln=True)

            pdf.ln(10)

            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Metrics:", ln=True)
            pdf.ln(5)
            pdf.set_font("Arial", size=11)
            pdf.cell(200, 10, txt=f"Difference between HR and SpO2HR (mean): {metrics['difference'].mean():.2f}",
                     ln=True)
            pdf.cell(200, 10, txt=f"Convergence Time: {metrics['convergence_time']} seconds", ln=True)
            pdf.cell(200, 10, txt=f"Batch Average HR: {metrics['batch_average']['HR']:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Batch Average SpO2HR: {metrics['batch_average']['SpO2HR']:.2f}", ln=True)

            # Use the first selected file name for the PDF file name
            pdf_filename = f"{os.path.splitext(os.path.basename(self.selected_files[0]))[0]}_Report.pdf"
            pdf.output(pdf_filename)

        # gui handling
        self.remove_gui(self.gui_elements)

        # eval label
        self.evalLabel = Label(root, text="Selected Patients", font=("Arial", 16))
        self.evalLabel.grid(row=0, column=0, columnspan=3, pady=10, padx=20)

        # subtitle label // re-add to self.gui_elements if uncommenting
        # self.subLabel = Label(root, text="Batch Metrics", font=("Arial", 16))
        # self.subLabel.grid(row=0, column=4, columnspan=3, pady=10, padx=20)

        # list of selected patients
        self.patients_eval = Listbox(root, height=16, width=40, border=2)
        self.patients_eval.grid(row=1, column=0, columnspan=3, rowspan=6, pady=20, padx=20)

        self.patient_eval_scrollbar = Scrollbar(root)
        self.patient_eval_scrollbar.grid(row=1, column=3)

        self.patients_eval.configure(yscrollcommand=self.patient_eval_scrollbar.set)
        self.patient_eval_scrollbar.configure(command=self.patients_eval.yview)

        # back button
        self.backButton = Button(root, text="Back to Patient Selection", command=lambda: self.select_files_gui(), font=("Arial", 12), width=22)
        self.backButton.grid(row=8, column=0)

        # view all metrics button
        self.allMetrics = Button(root, text="View All Metrics", command=lambda: display_metrics(), font=("Arial", 12), width=16)
        self.allMetrics.grid(row=3, column=8)

        # print to pdf button
        self.printPDF = Button(root, text="Print to PDF", command=lambda: export_to_pdf(calculate_metrics()), font=("Arial", 12), width=12)
        self.printPDF.grid(row=8, column=8)

        if control == 0:
            populate_patient_list(self.patientList)
            load_csv_files(self.patientList)
        else:
            populate_patient_list(self.groupList)
            load_csv_files(self.groupList)

        # display_metrics()

        self.gui_elements = [self.evalLabel,
                             self.patients_eval,
                             self.patient_eval_scrollbar,
                             self.backButton,
                             self.allMetrics,
                             self.printPDF]

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
            except ValueError:
                pass

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
        self.titleLabel.grid(row=0, column=0, columnspan=6, pady=10, padx=10)

        # list of patients under directory
        self.patients_list = Listbox(root, height=16, width=40, border=2)
        self.patients_list.grid(row=1, column=0, columnspan=3, rowspan=6, pady=20, padx=20)

        self.patient_scrollbar = Scrollbar(root)
        self.patient_scrollbar.grid(row=1, column=3)

        self.patients_list.configure(yscrollcommand=self.patient_scrollbar.set)
        self.patient_scrollbar.configure(command=self.patients_list.yview)

        self.patients_list.bind('<<ListboxSelect>>', select_patient)

        # group and ungroup buttons
        self.group_button = Button(root, text=">", command=lambda: add_patient(), width=5)
        self.group_button.grid(row=2, column=4)

        self.ungroup_button = Button(root, text="X", command=lambda: remove_patient(), width=5)
        self.ungroup_button.grid(row=4, column=4)

        # list of user selected group
        self.group_list = Listbox(root, height=16, width=40, border=2)
        self.group_list.grid(row=1, column=5, columnspan=3, rowspan=6, pady=20, padx=20)

        self.grouplist_scrollbar = Scrollbar(root)
        self.grouplist_scrollbar.grid(row=1, column=8)

        self.group_list.configure(yscrollcommand=self.grouplist_scrollbar.set)
        self.grouplist_scrollbar.configure(command=self.group_list.yview)

        self.group_list.bind('<<ListboxSelect>>', select_patient_group)

        # back button
        self.backButton = Button(root, text="Back to Directory Selection", command=lambda: self.root_gui(), font=("Arial", 12), width=22)
        self.backButton.grid(row=8, column=0)

        # evaluate all/group buttons
        self.evalAll = Button(root, text="Evaluate All", command=lambda: group_to_list(0), font=("Arial", 12), width=10)
        self.evalAll.grid(row=8, column=5, padx=10)

        self.evalGroup = Button(root, text="Evaluate Selection", command=lambda: group_to_list(1), font=("Arial", 12), width=20)
        self.evalGroup.grid(row=8, column=6)

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
                             self.evalAll]

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
        self.dirTextbox = Entry(root, textvariable=dir_text, width = 80)
        self.dirTextbox.pack()

        self.dirButton = Button(root, text="Select Directory", command=lambda : directory_select(), font=("Arial", 12), width=20)
        self.dirButton.pack()

        self.nextButton = Button(root, text="Next", command=lambda : self.check_dir(dir_text.get()), font=("Arial", 12), width=20)
        self.nextButton.pack()

        self.gui_elements = [self.titleLabel,
                             self.pleaseChooseLabel,
                             self.dirTextbox,
                             self.dirButton,
                             self.nextButton]


def main():
    global root

    root = Tk()
    root.geometry("700x400")
    window = MainWindow()

    root.mainloop()

if __name__ == '__main__':
    main()