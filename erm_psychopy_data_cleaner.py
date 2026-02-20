import pandas as pd
import glob
import os
import tkinter as tk
from tkinter import filedialog

# ============================================================
# MANUAL CONFIGURATION (Edit these values)
# ============================================================
OUTPUT_FILENAME = "ERM_cleaned_data.csv"  # Final file name
SUMMARY_MODE = True  # True: research variables only | False: include metadata
# ============================================================

def process_data_logic(directory_path, output_filename, summary_mode):
    """
    Core processing engine: cleans paths, merges trials, and reorders columns.
    This logic is identical across both versions for consistency.
    """
    csv_files = glob.glob(os.path.join(directory_path, "*.csv"))
    processed_dataframes = []

    for file in csv_files:
        try:
            # Load data and create a copy to avoid fragmentation warnings
            df = pd.read_csv(file).copy()

            # 1. Clean file paths: Remove directory prefixes (e.g., 'images\')
            for col in ['image_file', 'music_file']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r'.*\\', '', regex=True).str.replace(r'.*/', '', regex=True)

            # 2. Data Merging: Combine Practice and Experimental trial responses
            # This map links the final concept to its potential source columns in PsychoPy
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
                    # Fill missing values across practice/test columns
                    merged_series = df[valid_cols[0]]
                    for next_col in valid_cols[1:]:
                        merged_series = merged_series.fillna(df[next_col])
                    
                    # Clean 'num_' prefix and handle NaNs
                    df[new_col] = merged_series.astype(str).str.replace('num_', '', case=False).replace('nan', None)

            # 3. Define Column Ordering
            priority_columns = [
                'participant', 'order', 'set', 'trial', 'block', 'trial_block', 
                'picture_type', 'image_file', 'music_type', 'music_file', 
                'iti_duration', 'probed_trial', 'probed_iti', 'probe_start_trial', 'probe_start_iti',
                'valence', 'arousal', 'fear', 'anger', 'sadness'
            ]
            
            existing_priority = [c for c in priority_columns if c in df.columns]
            
            if summary_mode:
                # Keep ONLY priority columns
                final_df = df[existing_priority].copy()
            else:
                # Priority columns first, followed by technical metadata
                other_columns = [c for c in df.columns if c not in existing_priority]
                final_df = df[existing_priority + other_columns].copy()

            # 4. Row Cleaning: Remove non-trial rows
            final_df = final_df.dropna(subset=['trial'], how='all')
            processed_dataframes.append(final_df)

        except Exception as e:
            print(f"Error processing {file}: {e}")
    
    return processed_dataframes

def run_fast_process():
    """Main execution flow for the semi-automatic script."""
    # Initialize Tkinter only for the folder picker (hidden main window)
    root = tk.Tk()
    root.withdraw() 
    root.attributes("-topmost", True) # Force the dialog to the front

    print(f"--- Mode: {'SUMMARY' if SUMMARY_MODE else 'FULL METADATA'} ---")
    print(f"--- Configured Output: {OUTPUT_FILENAME} ---")
    
    # Prompt user for the data directory
    directory_path = filedialog.askdirectory(title='Select PsychoPy Data Folder')
    
    if directory_path:
        results = process_data_logic(directory_path, OUTPUT_FILENAME, SUMMARY_MODE)
        
        if results:
            master_df = pd.concat(results, ignore_index=True)
            final_name = OUTPUT_FILENAME if OUTPUT_FILENAME.endswith('.csv') else OUTPUT_FILENAME + '.csv'
            master_df.to_csv(final_name, index=False, encoding='utf-8-sig')
            print(f"\n[SUCCESS] Processing complete. File saved as: {final_name}")
        else:
            print("\n[ERROR] No valid data found to process.")
    else:
        print("\n[CANCELLED] No folder selected.")

    root.destroy()

if __name__ == "__main__":
    run_fast_process()