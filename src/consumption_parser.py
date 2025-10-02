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
import re

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

def extract_customer_info(input_file_path):
    """
    Extract customer information from the meter CSV file header.
    
    Args:
        input_file_path (str): Path to the input CSV file
    
    Returns:
        dict: Dictionary containing customer_name, meter_number, and other metadata
    """
    customer_info = {
        'customer_name': None,
        'meter_number': None,
        'address': None,
        'account_number': None
    }
    
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Look through the first 20 lines for customer information
        for i, line in enumerate(lines[:20]):
            line = line.strip()
            if not line:
                continue
            
            # Debug: print lines being analyzed
            print(f"Analyzing line {i+1}: {line[:100]}...")
            
            # Look for customer name patterns
            # Try different patterns, more specific first
            name_patterns = [
                # Specific Hebrew patterns with colons
                r'שם\s*לקוח\s*[:\-]\s*([א-ת\s]+[א-ת])',  # Hebrew name after "שם לקוח:"
                r'שם\s*המנוי\s*[:\-]\s*([א-ת\s]+[א-ת])',  # Hebrew name after "שם המנוי:"
                r'לקוח\s*[:\-]\s*([א-ת\s]+[א-ת])',        # Hebrew name after "לקוח:"
                
                # English patterns
                r'Customer\s*Name\s*[:\-]\s*([a-zA-Z\s]+)',
                r'Name\s*[:\-]\s*([a-zA-Z\s]+)',
                
                # CSV field patterns (look for names in quotes)
                r'"([א-ת]+\s+[א-ת]+)"',  # Hebrew first+last name in quotes
                r'"([a-zA-Z]+\s+[a-zA-Z]+)"',  # English first+last name in quotes
                
                # General patterns (fallback)
                r'שם\s*[:\-]\s*([^,\n\r]+)',
                r'שם\s*לקוח\s*[:\-]\s*([^,\n\r]+)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    name = match.group(1).strip().strip('"').strip("'").strip()
                    print(f"Found potential name: '{name}' using pattern: {pattern}")
                    
                    # Filter out common Hebrew labels and invalid names
                    invalid_names = [
                        'לקוח', 'customer', 'name', 'שם', 'מנוי', 'בעל', 'חשבון',
                        'account', 'holder', 'user', 'משתמש', 'בעלים', 'owner',
                        'נ/א', 'n/a', 'null', 'none', 'empty', 'ריק'
                    ]
                    
                    # Check if name is valid
                    if (name and 
                        len(name) > 2 and 
                        len(name) < 50 and  # Reasonable name length
                        not name.isdigit() and 
                        name.lower() not in invalid_names and
                        not any(invalid in name.lower() for invalid in invalid_names) and
                        # Must contain at least one letter (Hebrew or English)
                        re.search(r'[א-תa-zA-Z]', name)):
                        
                        print(f"Valid name found: '{name}'")
                        customer_info['customer_name'] = name
                        break
                    else:
                        print(f"Invalid name rejected: '{name}'")
            
            # Look for meter number patterns
            meter_patterns = [
                r'מונה[:\s]*(\d+)',
                r'Meter[:\s]*(\d+)',
                r'מספר\s*מונה[:\s]*(\d+)',
                r'Meter\s*Number[:\s]*(\d+)',
                r'(\d{8,12})'  # 8-12 digit numbers (common meter number format)
            ]
            
            for pattern in meter_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    meter_num = match.group(1).strip()
                    if meter_num and len(meter_num) >= 6:
                        customer_info['meter_number'] = meter_num
                        break
            
            # Look for address patterns
            address_patterns = [
                r'כתובת[:\s]*([^,\n]+)',
                r'Address[:\s]*([^,\n]+)',
                r'רחוב[:\s]*([^,\n]+)'
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    address = match.group(1).strip().strip('"').strip("'")
                    if address and len(address) > 3:
                        customer_info['address'] = address
                        break
            
            # Look for account number patterns
            account_patterns = [
                r'חשבון[:\s]*(\d+)',
                r'Account[:\s]*(\d+)',
                r'מספר\s*חשבון[:\s]*(\d+)',
                r'Account\s*Number[:\s]*(\d+)'
            ]
            
            for pattern in account_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    account = match.group(1).strip()
                    if account and len(account) >= 4:
                        customer_info['account_number'] = account
                        break
        
        # If no customer name found, try to extract from filename
        if not customer_info['customer_name']:
            filename = os.path.basename(input_file_path)
            # Look for patterns like "meter_12345_customer_name.csv"
            filename_patterns = [
                r'meter_\d+_([^_]+)',
                r'([^_\d]+)_\d+',
                r'([a-zA-Zא-ת]+)'
            ]
            
            for pattern in filename_patterns:
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    name = match.group(1).strip().replace('_', ' ')
                    if name and len(name) > 2 and not name.lower() in ['meter', 'data', 'consumption', 'csv']:
                        customer_info['customer_name'] = name
                        break
        
        # Clean up extracted data
        for key, value in customer_info.items():
            if value:
                # Remove extra whitespace and quotes
                cleaned = str(value).strip().strip('"').strip("'").strip()
                customer_info[key] = cleaned if cleaned else None
        
        print(f"Extracted customer info: {customer_info}")
        return customer_info
        
    except Exception as e:
        print(f"Error extracting customer info: {e}")
        return customer_info

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
