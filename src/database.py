#!/usr/bin/env python3
"""
Database Models for Customer Analysis Logging

This module defines the database models for logging customer analysis data.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

db = SQLAlchemy()

class CustomerAnalysis(db.Model):
    """Model for storing customer analysis data"""
    __tablename__ = 'customer_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(255), nullable=True)  # Extracted from meter file
    meter_number = db.Column(db.String(100), nullable=True)   # Meter ID if available
    analysis_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    selected_provider = db.Column(db.String(100), nullable=False)
    selected_plan = db.Column(db.String(200), nullable=False)
    monthly_savings_nis = db.Column(db.Float, nullable=False)
    monthly_savings_kwh = db.Column(db.Float, nullable=True)
    bill_savings_percentage = db.Column(db.Float, nullable=True)
    active_months_analyzed = db.Column(db.Integer, nullable=True)
    filename = db.Column(db.String(255), nullable=True)       # Original filename
    ip_address = db.Column(db.String(45), nullable=True)      # For analytics (IPv4/IPv6)
    user_agent = db.Column(db.Text, nullable=True)            # Browser info
    
    def __repr__(self):
        return f'<CustomerAnalysis {self.customer_name} - {self.selected_provider} - ₪{self.monthly_savings_nis}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'meter_number': self.meter_number,
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            'selected_provider': self.selected_provider,
            'selected_plan': self.selected_plan,
            'monthly_savings_nis': self.monthly_savings_nis,
            'monthly_savings_kwh': self.monthly_savings_kwh,
            'bill_savings_percentage': self.bill_savings_percentage,
            'active_months_analyzed': self.active_months_analyzed,
            'filename': self.filename,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

def init_db(app):
    """Initialize database with Flask app"""
    # Configure database URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Handle Railway/Heroku PostgreSQL URL format
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Use SQLite for local development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customer_analysis.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy with app
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

def log_customer_analysis(customer_name, meter_number, selected_provider, selected_plan, 
                         monthly_savings_nis, monthly_savings_kwh=None, 
                         bill_savings_percentage=None, active_months_analyzed=None,
                         filename=None, ip_address=None, user_agent=None):
    """
    Log a customer analysis to the database
    
    Args:
        customer_name (str): Customer name extracted from meter file
        meter_number (str): Meter number if available
        selected_provider (str): Selected electricity provider
        selected_plan (str): Selected electricity plan
        monthly_savings_nis (float): Monthly savings in NIS
        monthly_savings_kwh (float, optional): Monthly savings in kWh
        bill_savings_percentage (float, optional): Bill savings percentage
        active_months_analyzed (int, optional): Number of active months analyzed
        filename (str, optional): Original filename
        ip_address (str, optional): Client IP address
        user_agent (str, optional): Client user agent
    
    Returns:
        CustomerAnalysis: The created database record
    """
    try:
        analysis = CustomerAnalysis(
            customer_name=customer_name,
            meter_number=meter_number,
            selected_provider=selected_provider,
            selected_plan=selected_plan,
            monthly_savings_nis=monthly_savings_nis,
            monthly_savings_kwh=monthly_savings_kwh,
            bill_savings_percentage=bill_savings_percentage,
            active_months_analyzed=active_months_analyzed,
            filename=filename,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        print(f"Logged analysis for {customer_name}: {selected_provider} - {selected_plan} (₪{monthly_savings_nis})")
        return analysis
        
    except Exception as e:
        db.session.rollback()
        print(f"Error logging customer analysis: {e}")
        return None

def get_analysis_stats():
    """Get basic statistics about logged analyses"""
    try:
        total_analyses = CustomerAnalysis.query.count()
        total_savings = db.session.query(db.func.sum(CustomerAnalysis.monthly_savings_nis)).scalar() or 0
        avg_savings = db.session.query(db.func.avg(CustomerAnalysis.monthly_savings_nis)).scalar() or 0
        
        # Top providers
        top_providers = db.session.query(
            CustomerAnalysis.selected_provider,
            db.func.count(CustomerAnalysis.id).label('count')
        ).group_by(CustomerAnalysis.selected_provider).order_by(
            db.func.count(CustomerAnalysis.id).desc()
        ).limit(5).all()
        
        return {
            'total_analyses': total_analyses,
            'total_monthly_savings': round(total_savings, 2),
            'average_monthly_savings': round(avg_savings, 2),
            'top_providers': [{'provider': p[0], 'count': p[1]} for p in top_providers]
        }
    except Exception as e:
        print(f"Error getting analysis stats: {e}")
        return None

def get_recent_analyses(limit=50):
    """Get recent customer analyses"""
    try:
        analyses = CustomerAnalysis.query.order_by(
            CustomerAnalysis.analysis_timestamp.desc()
        ).limit(limit).all()
        
        return [analysis.to_dict() for analysis in analyses]
    except Exception as e:
        print(f"Error getting recent analyses: {e}")
        return []
