#!/usr/bin/env python3
"""
Power Switch Web Application

A Flask web app for electrical plan recommendations based on consumption data.
"""

import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from src.consumption_parser import parse_consumption_file, extract_customer_info
from src.plan_recommender import PlanRecommender
from src.database import init_db, log_customer_analysis, get_analysis_stats
import tempfile
import shutil

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
init_db(app)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with upload form."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process recommendations."""
    if 'consumption_file' not in request.files:
        flash('לא נבחר קובץ', 'error')
        return redirect(request.url)
    
    file = request.files['consumption_file']
    
    if file.filename == '':
        flash('לא נבחר קובץ', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('אנא העלה קובץ CSV', 'error')
        return redirect(url_for('index'))
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the file
        flash('הקובץ הועלה בהצלחה! מעבד את הנתונים שלך...', 'info')
        
        # Parse consumption data
        with tempfile.NamedTemporaryFile(mode='w', suffix='_cleaned.csv', delete=False) as temp_file:
            cleaned_file_path = temp_file.name
        
        try:
            # Extract customer information before parsing
            customer_info = extract_customer_info(filepath)
            
            parse_consumption_file(filepath, cleaned_file_path)
            
            # Generate recommendations
            plans_file = 'electrical_plans.csv'
            recommender = PlanRecommender(cleaned_file_path, plans_file)
            recommender.load_data()
            recommender.identify_active_months()
            
            if not recommender.active_months:
                flash('לא נמצאו חודשים פעילים בנתונים שלך. אנא בדוק את קובץ הצריכה.', 'error')
                return redirect(url_for('index'))
            
            recommendations = recommender.generate_recommendations()
            
            # Get hourly consumption data for chart
            hourly_data = recommender.get_hourly_consumption_data()
            
            # Convert to dict for template
            recommendations_data = recommendations.to_dict('records')
            
            # Log the analysis (best recommendation)
            if recommendations_data:
                best_plan = recommendations_data[0]  # First recommendation is the best
                try:
                    log_customer_analysis(
                        customer_name=customer_info.get('customer_name', 'Unknown'),
                        meter_number=customer_info.get('meter_number'),
                        selected_provider=best_plan.get('provider', 'Unknown'),
                        selected_plan=best_plan.get('plan_name', 'Unknown'),
                        monthly_savings_nis=float(best_plan.get('monthly_savings_nis', 0)),
                        monthly_savings_kwh=float(best_plan.get('monthly_savings_kwh', 0)) if best_plan.get('monthly_savings_kwh') else None,
                        bill_savings_percentage=float(best_plan.get('bill_savings_percentage', 0)) if best_plan.get('bill_savings_percentage') else None,
                        active_months_analyzed=len(recommender.active_months),
                        filename=filename,
                        ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
                        user_agent=request.headers.get('User-Agent')
                    )
                except Exception as log_error:
                    print(f"Failed to log analysis: {log_error}")
            
            # Clean up temporary files
            os.unlink(filepath)
            os.unlink(cleaned_file_path)
            
            return render_template('results.html', 
                                 recommendations=recommendations_data,
                                 active_months=len(recommender.active_months),
                                 filename=filename,
                                 hourly_data=hourly_data)
            
        except Exception as e:
            # Clean up files on error
            if os.path.exists(filepath):
                os.unlink(filepath)
            if os.path.exists(cleaned_file_path):
                os.unlink(cleaned_file_path)
            raise e
            
    except Exception as e:
        flash(f'שגיאה בעיבוד הקובץ: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/demo')
def demo():
    """Demo route using the sample CSV file in the repo."""
    try:
        # Use the existing cleaned CSV file in the repo
        sample_file = 'meter_23278570_LP_18-9-2025_cleaned.csv'
        
        if not os.path.exists(sample_file):
            flash('קובץ הדוגמא לא נמצא', 'error')
            return redirect(url_for('index'))
        
        flash('משתמש בקובץ דוגמא! מעבד את הנתונים...', 'info')
        
        # Extract customer information from demo file
        customer_info = extract_customer_info(sample_file)
        
        # Generate recommendations using the sample file
        plans_file = 'electrical_plans.csv'
        recommender = PlanRecommender(sample_file, plans_file)
        recommender.load_data()
        recommender.identify_active_months()
        
        if not recommender.active_months:
            flash('לא נמצאו חודשים פעילים בקובץ הדוגמא.', 'error')
            return redirect(url_for('index'))
        
        recommendations = recommender.generate_recommendations()
        
        # Get hourly consumption data for chart
        hourly_data = recommender.get_hourly_consumption_data()
        
        # Convert to dict for template
        recommendations_data = recommendations.to_dict('records')
        
        # Log the demo analysis (best recommendation)
        if recommendations_data:
            best_plan = recommendations_data[0]  # First recommendation is the best
            try:
                log_customer_analysis(
                    customer_name=customer_info.get('customer_name', 'Demo User'),
                    meter_number=customer_info.get('meter_number'),
                    selected_provider=best_plan.get('provider', 'Unknown'),
                    selected_plan=best_plan.get('plan_name', 'Unknown'),
                    monthly_savings_nis=float(best_plan.get('monthly_savings_nis', 0)),
                    monthly_savings_kwh=float(best_plan.get('monthly_savings_kwh', 0)) if best_plan.get('monthly_savings_kwh') else None,
                    bill_savings_percentage=float(best_plan.get('bill_savings_percentage', 0)) if best_plan.get('bill_savings_percentage') else None,
                    active_months_analyzed=len(recommender.active_months),
                    filename='קובץ דוגמא',
                    ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
                    user_agent=request.headers.get('User-Agent')
                )
            except Exception as log_error:
                print(f"Failed to log demo analysis: {log_error}")
        
        return render_template('results.html', 
                             recommendations=recommendations_data,
                             active_months=len(recommender.active_months),
                             filename='קובץ דוגמא',
                             hourly_data=hourly_data)
        
    except Exception as e:
        flash(f'שגיאה בעיבוד קובץ הדוגמא: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/about')
def about():
    """About page explaining how the service works."""
    return render_template('about.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

@app.route('/sitemap.xml')
def sitemap():
    """Serve sitemap for search engines."""
    return send_from_directory('static', 'sitemap.xml', mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    """Serve robots.txt for search engines."""
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')

@app.route('/admin/stats')
def admin_stats():
    """Admin route to view analysis statistics (basic auth recommended in production)."""
    try:
        stats = get_analysis_stats()
        if stats:
            return jsonify(stats)
        else:
            return jsonify({'error': 'Unable to retrieve stats'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard with nice HTML interface."""
    try:
        stats = get_analysis_stats()
        return render_template('admin_dashboard.html', stats=stats)
    except Exception as e:
        return render_template('admin_dashboard.html', stats=None, error=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)

