import pandas as pd
import os

def clean_extraction_results(input_csv="ai_responses_extracted.csv", output_csv="ai_responses_cleaned.csv"):
    """
    Clean the extracted AI responses CSV by removing unnecessary columns.
    Keeps: llm, full_prompt, summarized_answer, answer_length, summary_length, status, timestamp
    Removes: prompt (truncated), original_answer
    """
    try:
        # Read the CSV
        df = pd.read_csv(input_csv)
        print(f"Loaded {len(df)} rows from {input_csv}")
        
        # Define columns to keep
        columns_to_keep = [
            'llm',
            'full_prompt',
            'summarized_answer',
            'answer_length',
            'summary_length',
            'status',
            'timestamp'
        ]
        
        # Check which columns exist
        existing_columns = [col for col in columns_to_keep if col in df.columns]
        missing_columns = [col for col in columns_to_keep if col not in df.columns]
        
        if missing_columns:
            print(f"Warning: Missing columns: {missing_columns}")
        
        # Select only the columns we want to keep
        df_cleaned = df[existing_columns]
        
        # Save cleaned CSV
        df_cleaned.to_csv(output_csv, index=False)
        print(f"Cleaned data saved to {output_csv}")
        print(f"Columns kept: {list(df_cleaned.columns)}")
        print(f"Removed columns: prompt, original_answer")
        
        # Print summary statistics
        print(f"\nSummary:")
        print(f"  Total rows: {len(df_cleaned)}")
        print(f"  LLMs: {df_cleaned['llm'].unique().tolist()}")
        if 'status' in df_cleaned.columns:
            print(f"  Status breakdown:")
            print(df_cleaned['status'].value_counts().to_string(header=False))
        
        return df_cleaned
        
    except FileNotFoundError:
        print(f"Error: {input_csv} not found")
        return None
    except Exception as e:
        print(f"Error cleaning data: {e}")
        return None


if __name__ == "__main__":
    # Clean the extraction results
    clean_extraction_results()
