import pandas as pd
from typing import Tuple, List, Dict
import os
import ollama
import logging

# Get the logger for this module
logger = logging.getLogger(__name__)

def read_data_file(file_path: str) -> Tuple[bool, pd.DataFrame]:
    """
    Read CSV or Excel file and return the first 4 rows as a sample.
    """
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            return False, "Unsupported file format. Please upload a CSV or Excel file."
        
        return True, df.head(4)
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return False, str(e)

def generate_data_insights(df: pd.DataFrame) -> Dict:
    """
    Generate insights and suggested queries using Ollama model.
    """
    # Convert DataFrame to a readable string format
    data_str = df.to_string()
    columns_info = "\n".join([f"- {col}: {dtype}" for col, dtype in df.dtypes.items()])
    
    structured_prompt = (
        "You are a data analysis expert. Analyze the following data sample and provide insights and suggested queries.\n\n"
        "Data Sample:\n"
        f"{data_str}\n\n"
        "Column Information:\n"
        f"{columns_info}\n\n"
        "Please provide:\n"
        "1. A brief analysis of the data structure and potential insights\n"
        "2. A list of 5-7 specific, actionable queries that would help understand the data better\n"
        "3. Suggestions for what kind of visualizations might be useful\n\n"
        "Format your response as follows:\n"
        "ANALYSIS:\n"
        "<your analysis>\n\n"
        "SUGGESTED QUERIES:\n"
        "- <query 1>\n"
        "- <query 2>\n"
        "...\n\n"
        "VISUALIZATION SUGGESTIONS:\n"
        "- <suggestion 1>\n"
        "- <suggestion 2>\n"
        "..."
    )
    
    try:
        response = ollama.chat(model='qwen2.5:3B', messages=[{"role": "user", "content": structured_prompt}])
        insights = response['message']['content']
        logger.info("Data insights generated successfully")
        
        # Parse the response into sections
        sections = {
            "analysis": "",
            "queries": [],
            "visualizations": []
        }
        
        current_section = None
        for line in insights.split('\n'):
            if line.startswith('ANALYSIS:'):
                current_section = 'analysis'
                continue
            elif line.startswith('SUGGESTED QUERIES:'):
                current_section = 'queries'
                continue
            elif line.startswith('VISUALIZATION SUGGESTIONS:'):
                current_section = 'visualizations'
                continue
            
            if current_section == 'analysis':
                sections['analysis'] += line + '\n'
            elif current_section == 'queries' and line.strip().startswith('-'):
                sections['queries'].append(line.strip()[2:])
            elif current_section == 'visualizations' and line.strip().startswith('-'):
                sections['visualizations'].append(line.strip()[2:])
        
        return sections
        
    except Exception as e:
        logger.error(f"Error generating data insights: {e}")
        return {
            "analysis": "Error generating insights.",
            "queries": ["Error generating queries."],
            "visualizations": ["Error generating visualization suggestions."]
        }

def format_analysis_output(insights: Dict) -> str:
    """
    Format the analysis results into a readable string.
    """
    output = "📊 Data Analysis Results:\n\n"
    
    output += "🔍 Analysis:\n"
    output += insights['analysis'].strip() + "\n\n"
    
    output += "❓ Suggested Queries:\n"
    for query in insights['queries']:
        output += f"- {query}\n"
    
    output += "\n📈 Visualization Suggestions:\n"
    for viz in insights['visualizations']:
        output += f"- {viz}\n"
    
    return output 