#!/usr/bin/env python3
"""
Electrical Plan Recommender

This module analyzes consumption data and recommends the best electrical plans
based on potential monthly savings.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
import sys
import os

class PlanRecommender:
    def __init__(self, consumption_file, plans_file):
        """
        Initialize the plan recommender with consumption and plans data.
        
        Args:
            consumption_file (str): Path to cleaned consumption CSV file
            plans_file (str): Path to electrical plans CSV file
        """
        self.consumption_file = consumption_file
        self.plans_file = plans_file
        self.consumption_data = None
        self.plans_data = None
        self.active_months = []
        
    def load_data(self):
        """Load consumption and plans data from CSV files."""
        print("Loading consumption data...")
        self.consumption_data = pd.read_csv(self.consumption_file)
        self.consumption_data['timestamp'] = pd.to_datetime(self.consumption_data['timestamp'])
        
        print("Loading plans data...")
        self.plans_data = pd.read_csv(self.plans_file)
        
        print(f"Loaded {len(self.consumption_data)} consumption records")
        print(f"Loaded {len(self.plans_data)} electrical plans")
        
    def identify_active_months(self, max_consumption_threshold=0.20):
        """
        Identify active months based on consumption levels (exclude months with <20% of max consumption).
        
        Args:
            max_consumption_threshold (float): Minimum consumption as percentage of max month
        
        Returns:
            list: List of (year, month) tuples for active months
        """
        print(f"Identifying active months with >{max_consumption_threshold*100}% of maximum monthly consumption...")
        
        # Group by year-month and calculate total consumption per month
        self.consumption_data['year_month'] = self.consumption_data['timestamp'].dt.to_period('M')
        monthly_consumption = self.consumption_data.groupby('year_month')['kwh_consumption'].sum()
        
        # Find maximum monthly consumption
        max_monthly_consumption = monthly_consumption.max()
        min_consumption_threshold = max_monthly_consumption * max_consumption_threshold
        
        active_months = []
        
        for period, consumption in monthly_consumption.items():
            year = period.year
            month = period.month
            
            consumption_percentage = consumption / max_monthly_consumption
            
            if consumption >= min_consumption_threshold:
                active_months.append((year, month))
                print(f"  {period}: {consumption:.2f} kWh ({consumption_percentage:.1%} of max) - ACTIVE")
            else:
                print(f"  {period}: {consumption:.2f} kWh ({consumption_percentage:.1%} of max) - SKIPPED (low consumption)")
        
        self.active_months = active_months
        print(f"Found {len(active_months)} active months")
        print(f"Maximum monthly consumption: {max_monthly_consumption:.2f} kWh")
        print(f"Minimum threshold: {min_consumption_threshold:.2f} kWh")
        return active_months
    
    def parse_day_range(self, day_range):
        """
        Parse day range string into list of weekday numbers.
        
        Args:
            day_range (str): Day range like "Sunday-Thursday" or "Monday-Friday"
        
        Returns:
            list: List of weekday numbers (0=Monday, 6=Sunday)
        """
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        if '-' in day_range:
            start_day, end_day = day_range.lower().split('-')
            start_num = day_mapping[start_day]
            end_num = day_mapping[end_day]
            
            if start_num <= end_num:
                return list(range(start_num, end_num + 1))
            else:
                # Handle wrap-around (e.g., Sunday-Thursday)
                return list(range(start_num, 7)) + list(range(0, end_num + 1))
        else:
            return [day_mapping[day_range.lower()]]
    
    def parse_time_range(self, time_range):
        """
        Parse time range string into start and end times.
        
        Args:
            time_range (str): Time range like "07:00-17:00" or "23:00-07:00"
        
        Returns:
            tuple: (start_hour, start_minute, end_hour, end_minute)
        """
        start_time, end_time = time_range.split('-')
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))
        
        return start_hour, start_minute, end_hour, end_minute
    
    def translate_days_to_hebrew(self, days_str):
        """
        Translate English day range to Hebrew.
        
        Args:
            days_str (str): Day range like "Sunday-Thursday"
        
        Returns:
            str: Hebrew translation
        """
        day_translations = {
            'sunday': 'ראשון',
            'monday': 'שני', 
            'tuesday': 'שלישי',
            'wednesday': 'רביעי',
            'thursday': 'חמישי',
            'friday': 'שישי',
            'saturday': 'שבת'
        }
        
        if '-' in days_str:
            start_day, end_day = days_str.lower().split('-')
            start_hebrew = day_translations.get(start_day, start_day)
            end_hebrew = day_translations.get(end_day, end_day)
            return f"{start_hebrew}-{end_hebrew}"
        else:
            return day_translations.get(days_str.lower(), days_str)
    
    def format_time_range_hebrew(self, time_str):
        """
        Format time range for Hebrew display.
        
        Args:
            time_str (str): Time range like "07:00-17:00"
        
        Returns:
            str: Formatted time range
        """
        if time_str == "00:00-23:59":
            return "24/7"
        return time_str
    
    def calculate_plan_savings(self, plan):
        """
        Calculate potential monthly savings for a specific plan.
        
        Args:
            plan (pd.Series): Plan data from plans DataFrame
        
        Returns:
            dict: Savings calculation results
        """
        # Parse plan parameters
        applicable_days = self.parse_day_range(plan['week_days_applicable'])
        start_hour, start_minute, end_hour, end_minute = self.parse_time_range(plan['hours_applicable'])
        discount_percentage = plan['price_percentage_off'] / 100
        
        # Filter consumption data for active months only
        active_consumption = self.consumption_data[
            self.consumption_data['year_month'].apply(
                lambda x: (x.year, x.month) in self.active_months
            )
        ].copy()
        
        if len(active_consumption) == 0:
            return {
                'total_consumption': 0,
                'discounted_consumption': 0,
                'monthly_savings': 0,
                'applicable_consumption_percentage': 0
            }
        
        # Add day of week and time information
        active_consumption['weekday'] = active_consumption['timestamp'].dt.weekday
        active_consumption['hour'] = active_consumption['timestamp'].dt.hour
        active_consumption['minute'] = active_consumption['timestamp'].dt.minute
        
        # Determine which consumption records are eligible for discount
        day_eligible = active_consumption['weekday'].isin(applicable_days)
        
        # Handle time eligibility (including overnight periods)
        if start_hour <= end_hour:
            # Same day time range (e.g., 07:00-17:00)
            time_eligible = (
                (active_consumption['hour'] > start_hour) |
                ((active_consumption['hour'] == start_hour) & (active_consumption['minute'] >= start_minute))
            ) & (
                (active_consumption['hour'] < end_hour) |
                ((active_consumption['hour'] == end_hour) & (active_consumption['minute'] < end_minute))
            )
        else:
            # Overnight time range (e.g., 23:00-07:00)
            time_eligible = (
                (active_consumption['hour'] > start_hour) |
                ((active_consumption['hour'] == start_hour) & (active_consumption['minute'] >= start_minute)) |
                (active_consumption['hour'] < end_hour) |
                ((active_consumption['hour'] == end_hour) & (active_consumption['minute'] < end_minute))
            )
        
        # Consumption eligible for discount
        eligible_mask = day_eligible & time_eligible
        discounted_consumption = active_consumption.loc[eligible_mask, 'kwh_consumption'].sum()
        total_consumption = active_consumption['kwh_consumption'].sum()
        
        # Calculate savings (assuming base rate of 1 unit per kWh for calculation purposes)
        # In real implementation, you'd multiply by actual electricity rate
        base_cost = total_consumption  # Simplified: 1 unit per kWh
        discounted_cost = (total_consumption - discounted_consumption) + (discounted_consumption * (1 - discount_percentage))
        total_savings = base_cost - discounted_cost
        
        # Calculate monthly average savings
        num_months = len(self.active_months)
        monthly_savings = total_savings / num_months if num_months > 0 else 0
        monthly_consumption = total_consumption / num_months if num_months > 0 else 0
        
        # Calculate percentage of total bill saved
        bill_savings_percentage = (monthly_savings / monthly_consumption * 100) if monthly_consumption > 0 else 0
        
        applicable_percentage = (discounted_consumption / total_consumption * 100) if total_consumption > 0 else 0
        
        return {
            'total_consumption': total_consumption,
            'discounted_consumption': discounted_consumption,
            'monthly_savings': monthly_savings,
            'monthly_consumption': monthly_consumption,
            'bill_savings_percentage': bill_savings_percentage,
            'applicable_consumption_percentage': applicable_percentage,
            'total_savings': total_savings,
            'num_active_months': num_months
        }
    
    def generate_recommendations(self):
        """
        Generate plan recommendations sorted by monthly savings.
        
        Returns:
            pd.DataFrame: Recommendations table with savings analysis
        """
        if self.consumption_data is None or self.plans_data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if not self.active_months:
            raise ValueError("No active months identified. Call identify_active_months() first.")
        
        print("Calculating savings for each plan...")
        
        recommendations = []
        
        for idx, plan in self.plans_data.iterrows():
            print(f"  Analyzing plan: {plan['plan_name']}")
            
            savings_data = self.calculate_plan_savings(plan)
            
            # Calculate monthly savings in NIS (0.5425 NIS per kWh * 1.18 for tax savings)
            monthly_savings_nis = round(savings_data['monthly_savings'] * 0.5425 * 1.18, 2)
            
            recommendation = {
                'provider': plan['provider'],
                'plan_name': plan['plan_name'],
                'applicable_days': self.translate_days_to_hebrew(plan['week_days_applicable']),
                'applicable_hours': self.format_time_range_hebrew(plan['hours_applicable']),
                'discount_percentage': plan['price_percentage_off'],
                'monthly_savings_kwh': round(savings_data['monthly_savings'], 2),
                'monthly_savings_nis': monthly_savings_nis,
                'bill_savings_percentage': round(savings_data['bill_savings_percentage'], 1),
                'applicable_consumption_pct': round(savings_data['applicable_consumption_percentage'], 1),
                'total_discounted_kwh': round(savings_data['discounted_consumption'], 2),
                'active_months_analyzed': savings_data['num_active_months'],
                'logo_filename': plan.get('logo_filename', ''),
                'provider_url': plan.get('provider_url', '')
            }
            
            recommendations.append(recommendation)
        
        # Create DataFrame and sort by monthly savings
        recommendations_df = pd.DataFrame(recommendations)
        recommendations_df = recommendations_df.sort_values('monthly_savings_kwh', ascending=False)
        
        return recommendations_df
    
    def get_hourly_consumption_data(self):
        """
        Generate hourly consumption data for the last 6 active months.
        
        Returns:
            dict: Hourly consumption data with months and average
        """
        if self.consumption_data is None:
            return {}
        
        # Get the last 6 active months
        sorted_active_months = sorted(self.active_months, reverse=True)[:6]
        
        # Filter consumption data for these months
        active_consumption = self.consumption_data[
            self.consumption_data['year_month'].apply(
                lambda x: (x.year, x.month) in sorted_active_months
            )
        ].copy()
        
        if len(active_consumption) == 0:
            return {}
        
        # Add hour column
        active_consumption['hour'] = active_consumption['timestamp'].dt.hour
        active_consumption['month_name'] = active_consumption['timestamp'].dt.strftime('%Y-%m')
        
        # Group by month and hour, calculate average consumption
        hourly_data = {}
        
        # Calculate data for each month
        for year, month in sorted_active_months:
            month_data = active_consumption[
                (active_consumption['timestamp'].dt.year == year) & 
                (active_consumption['timestamp'].dt.month == month)
            ]
            
            if len(month_data) > 0:
                month_name = f"{year}-{month:02d}"
                hourly_avg = month_data.groupby('hour')['kwh_consumption'].mean()
                
                # Ensure we have data for all 24 hours
                hourly_consumption = []
                for hour in range(24):
                    avg_consumption = hourly_avg.get(hour, 0)
                    hourly_consumption.append(round(avg_consumption, 3))
                
                hourly_data[month_name] = hourly_consumption
        
        # Calculate overall average across all active months
        if hourly_data:
            all_hours_data = []
            for hour in range(24):
                hour_values = [month_data[hour] for month_data in hourly_data.values() if len(month_data) > hour]
                avg_for_hour = sum(hour_values) / len(hour_values) if hour_values else 0
                all_hours_data.append(round(avg_for_hour, 3))
            
            hourly_data['average'] = all_hours_data
        
        return hourly_data
    
    def print_recommendations_table(self, recommendations_df):
        """
        Print a formatted table of recommendations.
        
        Args:
            recommendations_df (pd.DataFrame): Recommendations data
        """
        print("\n" + "="*140)
        print("ELECTRICAL PLAN RECOMMENDATIONS - SORTED BY MONTHLY SAVINGS")
        print("="*140)
        
        print(f"{'Rank':<4} {'Provider':<15} {'Plan Name':<20} {'Days':<15} {'Hours':<12} {'Discount':<8} {'Monthly Savings':<15} {'Bill Savings':<12} {'Coverage':<10}")
        print("-" * 140)
        
        for idx, row in recommendations_df.iterrows():
            rank = recommendations_df.index.get_loc(idx) + 1
            print(f"{rank:<4} {row['provider']:<15} {row['plan_name']:<20} {row['applicable_days']:<15} "
                  f"{row['applicable_hours']:<12} {row['discount_percentage']:<7}% "
                  f"{row['monthly_savings_kwh']:<14.2f} {row['bill_savings_percentage']:<11.1f}% {row['applicable_consumption_pct']:<9.1f}%")
        
        print("-" * 140)
        print(f"Analysis based on {recommendations_df.iloc[0]['active_months_analyzed']} active months")
        print("Monthly Savings: kWh units saved per month (multiply by your rate for cost savings)")
        print("Bill Savings: Percentage of total monthly bill expected to be saved")
        print("Coverage: Percentage of your consumption eligible for the discount")
        print("="*140)

def main():
    """Main function to run the plan recommender."""
    if len(sys.argv) < 3:
        print("Usage: python plan_recommender.py <consumption_csv> <plans_csv>")
        print("Example: python plan_recommender.py meter_data_cleaned.csv electrical_plans.csv")
        sys.exit(1)
    
    consumption_file = sys.argv[1]
    plans_file = sys.argv[2]
    
    # Validate input files
    if not os.path.exists(consumption_file):
        print(f"Error: Consumption file '{consumption_file}' not found")
        sys.exit(1)
    
    if not os.path.exists(plans_file):
        print(f"Error: Plans file '{plans_file}' not found")
        sys.exit(1)
    
    try:
        # Initialize recommender
        recommender = PlanRecommender(consumption_file, plans_file)
        
        # Load data
        recommender.load_data()
        
        # Identify active months
        recommender.identify_active_months()
        
        if not recommender.active_months:
            print("No active months found with sufficient data coverage (>75%)")
            sys.exit(1)
        
        # Generate recommendations
        recommendations = recommender.generate_recommendations()
        
        # Display results
        recommender.print_recommendations_table(recommendations)
        
        # Save results to CSV
        output_file = "plan_recommendations.csv"
        recommendations.to_csv(output_file, index=False)
        print(f"\nRecommendations saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
