import pandas as pd
import glob
import os
import tkinter as tk
from tkinter import filedialog, messagebox

def process_experiment_data(event=None):
    """
    Core function to clean, merge, and reorganize PsychoPy output files.
    Handles directory selection, data cleaning, and CSV generation.
    """
    output_filename = entry_filename.get()
    summary_mode = var_clean_mode.get()
    
    # Validate filename input
    if not output_filename or output_filename == ".csv":
        messagebox.showwarning("Input Error", "Please enter a valid name for the output file.")
        return

    # User selects the 'data' directory
    directory_path = filedialog.askdirectory(title='Select PsychoPy Data Folder')
    if not directory_path:
        return

    # Fetch all CSV files in the selected folder
    csv_files = glob.glob(os.path.join(directory_path, "*.csv"))
    processed_dataframes = []

    for file in csv_files:
        try:
            # Load data and create a copy to prevent memory fragmentation warnings
            raw_df = pd.read_csv(file)
            df = raw_df.copy() 

            # 1. Clean file paths: Remove directory prefixes (e.g., 'images\')
            for col in ['image_file', 'music_file']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r'.*\\', '', regex=True).str.replace(r'.*/', '', regex=True)

            # 2. DATA MERGING: Combine Practice and Experimental trial responses
            # We merge these into clean, single-concept columns
            merging_map = {
                'valence': ['valence_resp.keys', 'practice_valence_resp.keys'],
                'arousal': ['arousal_resp.keys', 'practice_arousal_resp.keys'],
                'fear':    ['fear_resp.keys',    'practice_fear_resp.keys'],
                'anger':   ['anger_resp.keys',   'practice_anger_resp.keys'],
                'sadness': ['sadness_resp.keys', 'practice_sadness_resp.keys']
            }

            for new_col, source_cols in merging_map.items():
                valid_cols = [c for c in source_cols if c in df.columns]
                if valid_cols:
                    # Efficiently fill missing values across columns
                    merged_series = df[valid_cols[0]]
                    for next_col in valid_cols[1:]:
                        merged_series = merged_series.fillna(df[next_col])
                    
                    # Clean 'num_' prefix from keyboard responses and handle NaNs
                    df[new_col] = merged_series.astype(str).str.replace('num_', '', case=False).replace('nan', None)

            # 3. DEFINE COLUMN ORDERING
            priority_columns = [
                'participant', 'order', 'set', 'trial', 'block', 'trial_block', 
                'picture_type', 'image_file', 'music_type', 'music_file', 
                'iti_duration', 'probed_trial', 'probed_iti', 'probe_start_trial', 'probe_start_iti',
                'valence', 'arousal', 'fear', 'anger', 'sadness'
            ]

            # Check which priority columns exist in current dataframe
            existing_priority = [c for c in priority_columns if c in df.columns]
            
            if summary_mode:
                # Keep ONLY priority columns
                final_df = df[existing_priority].copy()
            else:
                # Priority columns first, followed by technical metadata
                other_columns = [c for c in df.columns if c not in existing_priority]
                final_df = df[existing_priority + other_columns].copy()

            # 4. ROW CLEANING: Remove non-trial rows (e.g., instructions/welcome screens)
            final_df = final_df.dropna(subset=['trial'], how='all')
            processed_dataframes.append(final_df)

        except Exception as e:
            print(f"Error processing {file}: {e}")

    # Final Compilation and Export
    if processed_dataframes:
        master_df = pd.concat(processed_dataframes, ignore_index=True)
        if not output_filename.endswith('.csv'): 
            output_filename += '.csv'
        
        master_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        messagebox.showinfo("Success", f"Processing Complete!\nFile saved as: {output_filename}")
        root.destroy()
    else:
        messagebox.showerror("Error", "No valid data was found to process.")

# --- GUI Setup ---
root = tk.Tk()
root.title("PsychoPy Data Processor - ERM Experiment")
root.geometry("500x340")

# Input Section
tk.Label(root, text="Output Filename:", font=('Arial', 10, 'bold')).pack(pady=10)
entry_filename = tk.Entry(root, width=45)
entry_filename.insert(0, ".csv")
entry_filename.pack(pady=5)

# Automatic focus for user efficiency
entry_filename.focus_set() 
entry_filename.icursor(0)  
root.bind('<Return>', process_experiment_data)

# Options Section
var_clean_mode = tk.BooleanVar(value=True) 
tk.Checkbutton(root, text="Enable Summary Mode\n(Removes technical metadata, keeps research variables)", 
               variable=var_clean_mode, justify="left").pack(pady=15)

# Execution Button
tk.Button(root, text="📂 Select Folder & Process", command=process_experiment_data, 
          bg="#AA80F1", fg="white", font=('Arial', 11, 'bold'), padx=20, pady=10).pack(pady=10)

# Footer / Credits
footer = tk.Frame(root)
footer.pack(side="bottom", fill="x", padx=10, pady=10)

lbl_credits = tk.Label(footer, text="Code by Santiago Correa-Iriarte, MPAGER Lab.", 
                        font=('Arial', 8, 'italic'), fg="gray")
lbl_credits.pack(side="left")

root.mainloop()