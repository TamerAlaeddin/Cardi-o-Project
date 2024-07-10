import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from tkinter import Tk, filedialog, Button, Label, messagebox, Toplevel, Frame
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PerformanceMetrics:
    def __init__(self):
        self.data = []
        self.selected_files = []

    def load_csv_files(self, file_paths):
        self.selected_files = file_paths
        for file in file_paths:
            df = pd.read_csv(file)
            self.data.append(df)

    def calculate_metrics(self, df):
        metrics = {}
        metrics['difference'] = df['HR'] - df['SpO2HR']
        metrics['convergence_time'] = (df['HR'] - df['SpO2HR']).abs().idxmin()
        metrics['batch_average'] = df[['HR', 'SpO2HR']].mean()
        return metrics

    def plot_metrics(self, df, metrics, file_name):
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
        axs[2, 0].bar(['Batch Average HR', 'Batch Average SpO2HR'], metrics['batch_average'], color=['#000000', '#FF0000'])
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

    def export_to_pdf(self):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for file, df in zip(self.selected_files, self.data):
            metrics = self.calculate_metrics(df)
            fig = self.plot_metrics(df, metrics, os.path.basename(file))
            img_path = f"{os.path.splitext(file)[0]}.png"
            fig.savefig(img_path)
            plt.close(fig)

            pdf.add_page()
            pdf.image(img_path, x=10, y=10, w=190)
            os.remove(img_path)

        pdf_filename = "Performance_Metrics_Report.pdf"
        pdf.output(pdf_filename)
        messagebox.showinfo("Success", f"PDF Report '{pdf_filename}' generated successfully!")

    def file_selection(self):
        root = Tk()
        root.withdraw()
        self.selected_files = filedialog.askopenfilenames(title="Select CSV Files", filetypes=[("CSV files", "*.csv")])
        if not self.selected_files:
            messagebox.showerror("Error", "No files selected. Please select CSV files.")
            return
        self.load_csv_files(self.selected_files)
        root.destroy()
        messagebox.showinfo("Success", "Files loaded successfully!")

    def show_plots(self):
        if not self.selected_files:
            messagebox.showerror("Error", "No files selected. Please select CSV files first.")
            return

        current_index = [0]

        def update_plot(index):
            for widget in plot_frame.winfo_children():
                widget.destroy()
            fig = self.plot_metrics(self.data[index], self.calculate_metrics(self.data[index]), os.path.basename(self.selected_files[index]))
            canvas = FigureCanvasTkAgg(fig, master=plot_frame)
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

        plot_window = Toplevel()
        plot_window.title("Performance Metrics Plots")

        plot_frame = Frame(plot_window)
        plot_frame.pack(fill='both', expand=True)

        button_frame = Frame(plot_window)
        button_frame.pack(fill='x')

        prev_button = Button(button_frame, text="Previous", command=previous_plot)
        prev_button.pack(side='left')

        next_button = Button(button_frame, text="Next", command=next_plot)
        next_button.pack(side='left')

        plot_frame.pack(fill='both', expand=True)
        button_frame.pack(fill='x')

        update_plot(current_index[0])

    def run(self):
        root = Tk()
        root.title("Performance Metrics Tool")

        Label(root, text="Performance Metrics Tool", font=("Arial", 16)).pack(pady=10)
        Button(root, text="Select Files", command=self.file_selection, font=("Arial", 12), width=20).pack(pady=5)
        Button(root, text="Show Plots", command=self.show_plots, font=("Arial", 12), width=20).pack(pady=5)
        Button(root, text="Generate Report", command=self.export_to_pdf, font=("Arial", 12), width=20).pack(pady=5)

        root.mainloop()

if __name__ == "__main__":
    PerformanceMetrics().run()
