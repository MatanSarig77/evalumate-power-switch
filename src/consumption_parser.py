#!/usr/bin/env python3
"""
Consumption Data Parser

This script processes electrical consumption CSV files by:
1. Removing non-relational metadata (customer info, meter details)
2. Converting Hebrew headers to English
3. Combining date and time columns into a single timestamp
4. Outputting a clean CSV with timestamp and kWh consumption columns
"""

import csv
import pandas as pd
from datetime import datetime
import os
import sys

def parse_consumption_file(input_file_path, output_file_path=None):
    """
    Parse the consumption CSV file and clean it up.
    
    Args:
        input_file_path (str): Path to the input CSV file
        output_file_path (str): Path for the output CSV file (optional)
    
    Returns:
        str: Path to the cleaned output file
    """
    
    # If no output path specified, create one based on input filename
    if output_file_path is None:
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        output_file_path = os.path.join(os.path.dirname(input_file_path), f"{base_name}_cleaned.csv")
    
    print(f"Processing file: {input_file_path}")
    
    # Read the file and find where the actual data starts
    with open(input_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Find the line with Hebrew headers (contains "תאריך")
    data_start_line = None
    for i, line in enumerate(lines):
        if 'תאריך' in line and 'צריכה' in line:
            data_start_line = i + 2  # Skip the header line and the empty line after it
            break
    
    if data_start_line is None:
        raise ValueError("Could not find the data start point in the CSV file")
    
    print(f"Found data starting at line {data_start_line + 1}")
    
    # Extract only the data rows
    data_lines = lines[data_start_line:]
    
    # Parse the data
    consumption_data = []
    
    for line_num, line in enumerate(data_lines, start=data_start_line + 1):
        line = line.strip()
        if not line:
            continue
            
        # Parse CSV line manually to handle quotes properly
        try:
            # Remove quotes and split by comma
            parts = []
            current_part = ""
            in_quotes = False
            
            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    parts.append(current_part.strip())
                    current_part = ""
                else:
                    current_part += char
            
            # Add the last part
            parts.append(current_part.strip())
            
            if len(parts) >= 3:
                date_str = parts[0].strip('"')
                time_str = parts[1].strip('"')
                consumption_str = parts[2].strip('"')
                
                # Skip empty or invalid rows
                if not date_str or not time_str:
                    continue
                
                # Parse consumption value
                try:
                    consumption = float(consumption_str) if consumption_str else 0.0
                except ValueError:
                    consumption = 0.0
                
                # Combine date and time into timestamp
                try:
                    # Parse date (DD/MM/YYYY format)
                    date_parts = date_str.split('/')
                    if len(date_parts) == 3:
                        day, month, year = date_parts
                        
                        # Parse time (HH:MM format)
                        time_parts = time_str.split(':')
                        if len(time_parts) == 2:
                            hour, minute = time_parts
                            
                            # Create datetime object
                            dt = datetime(
                                year=int(year),
                                month=int(month),
                                day=int(day),
                                hour=int(hour),
                                minute=int(minute)
                            )
                            
                            # Format as ISO timestamp
                            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                            
                            consumption_data.append({
                                'timestamp': timestamp,
                                'kwh_consumption': consumption
                            })
                            
                except (ValueError, IndexError) as e:
                    print(f"Warning: Could not parse line {line_num}: {line.strip()}")
                    continue
                    
        except Exception as e:
            print(f"Warning: Error processing line {line_num}: {e}")
            continue
    
    print(f"Processed {len(consumption_data)} data points")
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(consumption_data)
    
    # Sort by timestamp to ensure chronological order
    df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp_dt').drop('timestamp_dt', axis=1)
    
    # Save to CSV
    df.to_csv(output_file_path, index=False)
    
    print(f"Cleaned data saved to: {output_file_path}")
    print(f"Data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Total consumption: {df['kwh_consumption'].sum():.2f} kWh")
    print(f"Average consumption per reading: {df['kwh_consumption'].mean():.4f} kWh")
    
    return output_file_path

def main():
    """Main function to run the parser from command line"""
    if len(sys.argv) < 2:
        print("Usage: python consumption_parser.py <input_csv_file> [output_csv_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    try:
        output_path = parse_consumption_file(input_file, output_file)
        print(f"\nSuccess! Cleaned file created at: {output_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
