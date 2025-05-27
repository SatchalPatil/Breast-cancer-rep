# Breast MRI Analysis Assistant

A sophisticated AI-powered application for analyzing breast MRI scans and providing detailed medical insights. This application combines advanced visual language models (VLM) with natural language processing to deliver comprehensive analysis and reporting capabilities.

## Features

- **Breast MRI Analysis**: Upload and analyze breast MRI scans using advanced AI models
- **Interactive Chat Interface**: Natural language interaction for querying and analyzing results
- **Data Analysis**: Support for CSV and Excel file analysis with detailed insights
- **Email Integration**: Generate and send analysis reports via email
- **Document Generation**: Save analysis results as detailed reports
- **Real-time Processing**: Streamlined analysis with immediate feedback
- **Modern UI**: Clean and intuitive user interface with dark theme

## Prerequisites

- Python 3.8 or higher
- Flask
- Ollama (for intent detection)
- Required Python packages (see Installation section)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/SatchalPatil/Breast-cancer-rep.git
cd breast-report
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up Ollama:
- Install Ollama from [ollama.ai](https://ollama.ai)
- Pull the required model:
```bash
ollama pull qwen2.5:3B
```

## Project Structure    

```
breast-report/
├── app.py                 # Main Flask application
├── vlm_agent.py          # Visual Language Model for MRI analysis
├── intent_detection.py   # Intent classification system
├── data_analysis.py      # Data processing and analysis
├── email_workflow.py     # Email generation and sending
├── chat_processing.py    # Chat message processing
├── static/              # Static assets (CSS, JS)
├── templates/           # HTML templates
├── uploads/            # Temporary storage for uploaded files
└── exports/            # Generated reports and charts
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Available Features:
   - Upload breast MRI scans for analysis
   - Upload CSV/Excel files for data analysis
   - Generate and send email reports
   - Save analysis results as documents
   - Interactive chat interface for queries

## Supported File Types

- **Images**: PNG, JPG, JPEG, DICOM
- **Data Files**: CSV, XLSX, XLS

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here]

## Acknowledgments

- [Add any acknowledgments or credits here]

## Support

For support, please [add contact information or support channels] 