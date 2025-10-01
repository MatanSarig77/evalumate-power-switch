# Power Switch

A web application that helps you find the best electrical provider and plan based on your actual consumption patterns.

## Features

- 📊 **Smart Analysis**: Analyzes your electrical consumption data to identify usage patterns
- 🏆 **Plan Recommendations**: Ranks electrical plans by potential monthly savings
- 💰 **Bill Savings**: Shows percentage of total bill you can save with each plan
- 🌐 **Web Interface**: Simple, modern web interface for easy use
- 🇮🇱 **Hebrew Support**: Automatically processes Hebrew meter data from Israeli providers

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Web Application**
   ```bash
   python app.py
   ```

3. **Open Your Browser**
   Navigate to `http://localhost:5000`

4. **Upload Your Data**
   Upload your electrical meter CSV file and get instant recommendations!

## Project Structure

```
power_switch/
├── src/                          # Backend modules
│   ├── consumption_parser.py     # CSV data parser
│   └── plan_recommender.py       # Recommendation engine
├── templates/                    # HTML templates
│   ├── base.html                # Base template
│   ├── index.html               # Upload page
│   ├── results.html             # Results page
│   └── about.html               # About page
├── static/                      # Static assets
│   └── images/
│       └── logos/               # Provider logos and UI images
├── uploads/                     # Temporary file uploads
├── app.py                      # Flask web application
├── electrical_plans.csv        # Available electrical plans
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## How It Works

1. **Upload**: Upload your electrical meter CSV file (Hebrew format supported)
2. **Parse**: System automatically cleans and processes the consumption data
3. **Analyze**: Identifies active months and consumption patterns
4. **Compare**: Calculates potential savings for each available plan
5. **Recommend**: Shows ranked recommendations with detailed savings analysis

## Supported Plans

Currently supporting **Cellcom Energy (סלקום אנרג׳י)** plans:
- **חוסכים ביום** (Saving During the Day) - 15% discount, 07:00-17:00
- **חוסכים למשפחה** (Saving for Family) - 18% discount, 14:00-20:00  
- **חוסכים בלילה** (Saving at Night) - 20% discount, 23:00-07:00

## Command Line Usage

You can also use the tools directly from command line:

### Parse Consumption Data
```bash
python src/consumption_parser.py meter_data.csv
```

### Generate Recommendations
```bash
python src/plan_recommender.py meter_data_cleaned.csv electrical_plans.csv
```

## File Format

The system supports CSV files from Israeli electrical meter providers with Hebrew headers. The parser automatically:
- Removes metadata and non-relational data
- Converts Hebrew headers to English
- Combines date and time columns into proper timestamps
- Filters out incomplete months

## Development

- **Backend**: Python with pandas for data processing
- **Web Framework**: Flask for the web interface
- **Frontend**: Bootstrap 5 with custom CSS for modern UI
- **Data Processing**: Handles 15-minute interval consumption data

### Project Organization

The project follows a clean structure:
- `src/` - Core business logic modules
- `templates/` - Jinja2 HTML templates
- `static/` - CSS, images, and client-side assets
- `uploads/` - Temporary file storage (auto-cleaned)

### Development Setup

```bash
# Clone and setup
git clone <repository>
cd power_switch
pip install -r requirements.txt

# Run development server
python app.py
```

The application automatically cleans up uploaded files and uses `.gitignore` to prevent cache files from being committed.

## License

TBD

