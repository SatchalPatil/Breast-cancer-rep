from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context, send_from_directory
from email_workflow import generate_email_content, modify_email_content, send_email
from intent_detection import detect_user_intent
from chat_processing import process_general_chat
from document_utils import save_response_to_file
from data_analysis import read_data_file, generate_data_insights, format_analysis_output
from vlm_agent import BreastMRIAnalyzer
import os
from werkzeug.utils import secure_filename
import tempfile
import time
import json

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Initialize the VLM agent
mri_analyzer = BreastMRIAnalyzer()

# Global state (in a real app, use a proper database)
app_state = {
    'mode': 'chat',
    'email_stage': None,
    'generated_email': None,
    'last_response': '',
    'current_data': None,  # Store current data for analysis
    'current_image': None  # Store current image for analysis
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Check file type and process accordingly
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.dicom')):
            # Handle image file
            try:
                with open(filepath, 'rb') as img_file:
                    image_data = img_file.read()
                analysis = mri_analyzer.analyze_mri_scan(image_data)
                app_state['current_image'] = image_data
                app_state['last_response'] = format_image_analysis(analysis)
                return jsonify({
                    'response': app_state['last_response'],
                    'mode': 'analyze_image'
                })
            except Exception as e:
                return jsonify({
                    'error': f'Error processing image: {str(e)}'
                }), 400
        elif filename.endswith(('.csv', '.xlsx', '.xls')):
            # Handle data file
            success, result = read_data_file(filepath)
            if success:
                app_state['current_data'] = result
                insights = generate_data_insights(result)
                formatted_output = format_analysis_output(insights)
                app_state['last_response'] = formatted_output
                return jsonify({
                    'response': formatted_output,
                    'mode': 'data_analysis'
                })
            else:
                return jsonify({
                    'error': f'Error processing file: {result}'
                }), 400

        return jsonify({
            'response': f'File uploaded successfully: {filename}',
            'mode': 'chat'
        })

def format_image_analysis(analysis):
    """Format the image analysis results into a readable string."""
    if 'error' in analysis:
        return f"❌ Error: {analysis['error']}"
    
    output = "📊 Breast MRI Scan Analysis\n"
    output += "=" * 30 + "\n\n"
    
    output += f"Stage: {analysis['stage'].upper()}\n"
    output += f"Confidence: {analysis['confidence']*100:.1f}%\n\n"
    
    output += "Key Observations:\n"
    for obs in analysis['observations']:
        output += f"• {obs}\n"
    
    output += "\nDetailed Analysis:\n"
    output += analysis['raw_response']
    
    return output

@app.route('/charts/<path:filename>')
def serve_chart(filename):
    return send_from_directory('exports/charts', filename)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '').strip()
    
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    # Handle email workflow
    if app_state['mode'] == 'email':
        if app_state['email_stage'] == 'review':
            if user_input.lower() == 'yes':
                app_state['email_stage'] = 'confirm'
                return jsonify({
                    'response': 'Please provide the recipient\'s email address:',
                    'mode': 'email',
                    'stage': 'confirm'
                })
            elif user_input.lower() == 'change':
                app_state['email_stage'] = 'modify'
                return jsonify({
                    'response': 'Please provide your suggestions for modifications:',
                    'mode': 'email',
                    'stage': 'modify'
                })
            elif user_input.lower() == 'cancel':
                app_state['mode'] = 'chat'
                app_state['email_stage'] = None
                return jsonify({
                    'response': 'Email workflow cancelled. Returning to general chat.',
                    'mode': 'chat'
                })
            else:
                return jsonify({
                    'response': 'Invalid response. Reply with \'yes\', \'change\', or \'cancel\'.',
                    'mode': 'email',
                    'stage': 'review'
                })

        elif app_state['email_stage'] == 'confirm':
            try:
                recipient = user_input
                subject, body, _ = app_state['generated_email']
                send_email(recipient, subject, body)
                app_state['mode'] = 'chat'
                app_state['email_stage'] = None
                return jsonify({
                    'response': '✅ Email sent successfully!',
                    'mode': 'chat'
                })
            except Exception as e:
                return jsonify({
                    'response': f'❌ Failed to send email. Error: {str(e)}\nPlease try again with a valid email address:',
                    'mode': 'email',
                    'stage': 'confirm'
                })

        elif app_state['email_stage'] == 'modify':
            suggestions = user_input
            app_state['generated_email'] = modify_email_content(app_state['generated_email'][2], suggestions)
            subject, body, _ = app_state['generated_email']
            app_state['email_stage'] = 'review'
            return jsonify({
                'response': f'Modified Email:\nSubject: {subject}\nBody: {body}\n\nReply with \'yes\' to send, \'change\' to modify further, or \'cancel\' to abort the email workflow.',
                'mode': 'email',
                'stage': 'review'
            })

        elif app_state['email_stage'] == 'init':
            app_state['generated_email'] = generate_email_content(user_input)
            subject, body, _ = app_state['generated_email']
            app_state['email_stage'] = 'review'
            return jsonify({
                'response': f'Generated Email:\nSubject: {subject}\nBody: {body}\n\nReply with \'yes\' to send, \'change\' to modify, or \'cancel\' to abort the email workflow.',
                'mode': 'email',
                'stage': 'review'
            })

    # If not in email workflow, detect intent
    intent = detect_user_intent(user_input)

    if intent == 'email':
        if app_state['mode'] != 'email':
            app_state['mode'] = 'email'
            app_state['email_stage'] = 'init'
            return jsonify({
                'response': 'I\'ll help you with sending an email. Please provide a description for the email you want to send:',
                'mode': 'email',
                'stage': 'init'
            })

    elif intent == 'analyze':
        if app_state['mode'] != 'data_analysis':
            app_state['mode'] = 'data_analysis'
            return jsonify({
                'response': 'I\'ll help you analyze your data. Please provide the path to your CSV or Excel file:',
                'mode': 'data_analysis'
            })
        else:
            success, result = read_data_file(user_input)
            if success:
                app_state['current_data'] = result  # Store the data
                insights = generate_data_insights(result)
                formatted_output = format_analysis_output(insights)
                app_state['last_response'] = formatted_output
                return jsonify({
                    'response': formatted_output,
                    'mode': 'data_analysis'
                })
            else:
                return jsonify({
                    'response': f'❌ Error reading file: {result}\nPlease provide a valid path to a CSV or Excel file:',
                    'mode': 'data_analysis'
                })
    elif intent == 'analyze_image':
        if app_state['mode'] != 'analyze_image':
            app_state['mode'] = 'analyze_image'
            return jsonify({
                'response': 'I\'ll help you analyze a breast MRI scan. Please upload an image file (PNG, JPG, JPEG, or DICOM format):',
                'mode': 'analyze_image'
            })
        else:
            return jsonify({
                'response': 'Please upload an image file for analysis.',
                'mode': 'analyze_image'
            })
    elif intent == 'save':
        if app_state['last_response']:
            # Generate a filename with timestamp
            filename = f'analysis_report_{int(time.time())}.txt'
            
            # Create the document content
            document_content = f"Analysis Report\n{'='*50}\n\n"
            document_content += app_state['last_response']
            
            if app_state['current_data'] is not None:
                document_content += "\n\nData Summary:\n"
                document_content += f"Total Records: {len(app_state['current_data'])}\n"
                document_content += f"Columns: {', '.join(app_state['current_data'].columns)}\n"

            # Send the document immediately in the stream
            yield f'data: ' + json.dumps({
                'response': '✅ Document generated successfully!',
                'mode': app_state['mode'],
                'document': {
                    'content': document_content,
                    'filename': filename
                }
            }) + '\n\n'
            return
        else:
            response_text = '⚠️ No recent response available to save.'
            mode = app_state['mode']

    else:  # normal chat
        if app_state['mode'] != 'chat':
            app_state['mode'] = 'chat'
        response = process_general_chat(user_input)
        app_state['last_response'] = response
        return jsonify({
            'response': response,
            'mode': 'chat'
        })

@app.route('/api/chat_stream', methods=['POST'])
def chat_stream():
    # Access request data before entering the generator
    data = request.json
    user_input = data.get('message', '').strip() if data else ''

    def generate_streamed_response(user_input):
        if not user_input:
            yield 'data: {"error": "No message provided"}\n\n'
            return

        response_text = None
        mode = 'chat'
        chart_data = None

        if app_state['mode'] == 'email':
            if app_state['email_stage'] == 'review':
                if user_input.lower() == 'yes':
                    response_text = 'Please provide the recipient\'s email address:'
                    mode = 'email'
                elif user_input.lower() == 'change':
                    response_text = 'Please provide your suggestions for modifications:'
                    mode = 'email'
                elif user_input.lower() == 'cancel':
                    response_text = 'Email workflow cancelled. Returning to general chat.'
                    mode = 'chat'
                else:
                    response_text = 'Invalid response. Reply with \'yes\', \'change\', or \'cancel\'.'
                    mode = 'email'
            elif app_state['email_stage'] == 'confirm':
                try:
                    recipient = user_input
                    subject, body, _ = app_state['generated_email']
                    send_email(recipient, subject, body)
                    response_text = '✅ Email sent successfully!'
                    mode = 'chat'
                except Exception as e:
                    response_text = f'❌ Failed to send email. Error: {str(e)}\nPlease try again with a valid email address:'
                    mode = 'email'
            elif app_state['email_stage'] == 'modify':
                suggestions = user_input
                app_state['generated_email'] = modify_email_content(app_state['generated_email'][2], suggestions)
                subject, body, _ = app_state['generated_email']
                response_text = f'Modified Email:\nSubject: {subject}\nBody: {body}\n\nReply with \'yes\' to send, \'change\' to modify further, or \'cancel\' to abort the email workflow.'
                mode = 'email'
            elif app_state['email_stage'] == 'init':
                app_state['generated_email'] = generate_email_content(user_input)
                subject, body, _ = app_state['generated_email']
                response_text = f'Generated Email:\nSubject: {subject}\nBody: {body}\n\nReply with \'yes\' to send, \'change\' to modify, or \'cancel\' to abort the email workflow.'
                mode = 'email'
        else:
            intent = detect_user_intent(user_input)
            if intent == 'email':
                if app_state['mode'] != 'email':
                    response_text = 'I\'ll help you with sending an email. Please provide a description for the email you want to send:'
                    mode = 'email'
            elif intent == 'analyze':
                if app_state['mode'] != 'data_analysis':
                    response_text = 'I\'ll help you analyze your data. Please provide the path to your CSV or Excel file:'
                    mode = 'data_analysis'
                else:
                    success, result = read_data_file(user_input)
                    if success:
                        app_state['current_data'] = result
                        insights = generate_data_insights(result)
                        formatted_output = format_analysis_output(insights)
                        app_state['last_response'] = formatted_output
                        response_text = formatted_output
                        mode = 'data_analysis'
                    else:
                        response_text = f'❌ Error reading file: {result}\nPlease provide a valid path to a CSV or Excel file:'
                        mode = 'data_analysis'
            elif intent == 'analyze_image':
                if app_state['mode'] != 'analyze_image':
                    response_text = 'I\'ll help you analyze a breast MRI scan. Please upload an image file (PNG, JPG, JPEG, or DICOM format):'
                    mode = 'analyze_image'
                else:
                    response_text = 'Please upload an image file for analysis.'
                    mode = 'analyze_image'
            elif intent == 'save':
                if app_state['last_response']:
                    filename = f'analysis_report_{int(time.time())}.txt'
                    document_content = f"Analysis Report\n{'='*50}\n\n"
                    document_content += app_state['last_response']
                    if app_state['current_data'] is not None:
                        document_content += "\n\nData Summary:\n"
                        document_content += f"Total Records: {len(app_state['current_data'])}\n"
                        document_content += f"Columns: {', '.join(app_state['current_data'].columns)}\n"
                    # Stream the document as a whole at the end
                    yield f'data: ' + json.dumps({
                        'response': '✅ Document generated successfully!',
                        'mode': app_state['mode'],
                        'document': {
                            'content': document_content,
                            'filename': filename
                        }
                    }) + '\n\n'
                    return
                else:
                    response_text = '⚠️ No recent response available to save.'
                    mode = app_state['mode']
            else:
                if app_state['mode'] != 'chat':
                    app_state['mode'] = 'chat'
                response_text = process_general_chat(user_input)
                app_state['last_response'] = response_text
                mode = 'chat'

        # Then stream the response text
        if response_text:
            for i in range(0, len(response_text), 20):
                chunk = response_text[i:i+20]
                yield f'data: ' + json.dumps({
                    'response': chunk,
                    'mode': mode
                }) + '\n\n'
                time.sleep(0.04)

    return Response(stream_with_context(generate_streamed_response(user_input)), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True) 