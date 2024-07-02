import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from tkinter import Tk, filedialog, Button, Label, messagebox
import os

class PerformanceMetrics:
    def __init__(self):
        # Initialize variables to hold data and selected file paths
        self.data = None
        self.selected_files = []

    def load_csv_files(self, file_paths):
        # Load multiple CSV files and concatenate them into a single DataFrame
        data_frames = []
        for file in file_paths:
            df = pd.read_csv(file)
            data_frames.append(df)
        self.data = pd.concat(data_frames, ignore_index=True)
        self.selected_files = file_paths  # Save the selected file paths for later use

    def calculate_metrics(self):
        # Calculate performance metrics from the loaded data
        if self.data is None:
            messagebox.showerror("Error", "No data loaded. Please select CSV files first.")
            return None

        metrics = {}
        metrics['difference'] = self.data['HR'] - self.data['SpO2HR']
        metrics['convergence_time'] = (self.data['HR'] - self.data['SpO2HR']).abs().idxmin()
        metrics['batch_average'] = self.data[['HR', 'SpO2HR']].mean()

        return metrics

    def plot_metrics(self, metrics):
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

    def export_to_pdf(self, metrics):
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
        pdf.cell(200, 10, txt=f"Difference between HR and SpO2HR (mean): {metrics['difference'].mean():.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Convergence Time: {metrics['convergence_time']} seconds", ln=True)
        pdf.cell(200, 10, txt=f"Batch Average HR: {metrics['batch_average']['HR']:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Batch Average SpO2HR: {metrics['batch_average']['SpO2HR']:.2f}", ln=True)

        # Use the first selected file name for the PDF file name
        pdf_filename = f"{os.path.splitext(os.path.basename(self.selected_files[0]))[0]}_Report.pdf"
        pdf.output(pdf_filename)
        messagebox.showinfo("Success", f"PDF Report '{pdf_filename}' generated successfully!")

    def file_selection(self):
        # Open a file dialog for selecting CSV files and load the selected files
        root = Tk()
        root.withdraw()
        self.selected_files = filedialog.askopenfilenames(title="Select CSV Files", filetypes=[("CSV files", "*.csv")])
        if not self.selected_files:
            messagebox.showerror("Error", "No files selected. Please select CSV files.")
            return
        self.load_csv_files(self.selected_files)
        root.destroy()
        messagebox.showinfo("Success", "Files loaded successfully!")

    def run(self):
        # Create the GUI for selecting files and calculating metrics
        root = Tk()
        root.title("Performance Metrics Tool")

        Label(root, text="Performance Metrics Tool", font=("Arial", 16)).pack(pady=10)

        Button(root, text="Select Files", command=self.file_selection, font=("Arial", 12), width=20).pack(pady=5)
        Button(root, text="Calculate Metrics", command=self.display_metrics, font=("Arial", 12), width=20).pack(pady=5)

        root.mainloop()

    def display_metrics(self):
        # Display the calculated metrics and generate a PDF report
        metrics = self.calculate_metrics()
        if metrics:
            self.plot_metrics(metrics)
            self.export_to_pdf(metrics)


if __name__ == "__main__":
    PerformanceMetrics().run()
