import sys
import logging
from email_workflow import generate_email_content, modify_email_content, send_email
from intent_detection import detect_user_intent
from chat_processing import process_general_chat
from document_utils import save_response_to_file
from data_analysis import read_data_file, generate_data_insights, format_analysis_output

# Configure logging to write to a file instead of console
logging.basicConfig(
    filename='frobeai.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    mode = "chat"
    email_stage = None
    generated_email = None
    last_response = ""  # Store the last LLM response

    print("Welcome to the FrobeAI Assistant (type 'exit' to quit)")
    print("I can help you with:")
    print("- Sending emails")
    print("- Analyzing data files")
    print("- Saving documents")
    print("- General chat and queries")

    while True:
        user_input = input("User: ").strip()
        if user_input.lower() == "exit":
            print("Goodbye!")
            sys.exit(0)

        # Handle email workflow commands first
        if mode == "email":
            if email_stage == "review":
                if user_input.lower() == "yes":
                    print("System: Please provide the recipient's email address:")
                    email_stage = "confirm"
                    continue
                elif user_input.lower() == "change":
                    print("System: Please provide your suggestions for modifications:")
                    email_stage = "modify"
                    continue
                elif user_input.lower() == "cancel":
                    print("System: Email workflow cancelled. Returning to general chat.")
                    mode = "chat"
                    email_stage = None
                    continue
                else:
                    print("System: Invalid response. Reply with 'yes', 'change', or 'cancel'.")
                    continue

            elif email_stage == "confirm":
                recipient = user_input
                try:
                    # Get the current email content
                    subject, body, _ = generated_email
                    # Send the email
                    send_email(recipient, subject, body)
                    print("System: ✅ Email sent successfully!")
                    print("System: Returning to general chat mode.")
                    mode = "chat"
                    email_stage = None
                    continue
                except Exception as e:
                    print(f"System: ❌ Failed to send email. Error: {e}")
                    print("System: Please try again with a valid email address:")
                    continue

            elif email_stage == "modify":
                suggestions = user_input
                generated_email = modify_email_content(generated_email[2], suggestions)
                subject, body, full_content = generated_email
                print("\nSystem: Modified Email:")
                print(f"Subject: {subject}")
                print(f"Body: {body}\n")
                print("System: Reply with 'yes' to send, 'change' to modify further, or 'cancel' to abort the email workflow.")
                email_stage = "review"
                continue

            elif email_stage == "init":
                generated_email = generate_email_content(user_input)
                subject, body, full_content = generated_email
                print("\nSystem: Generated Email:")
                print(f"Subject: {subject}")
                print(f"Body: {body}\n")
                print("System: Reply with 'yes' to send, 'change' to modify, or 'cancel' to abort the email workflow.")
                email_stage = "review"
                continue

        # If not in email workflow, detect intent
        intent = detect_user_intent(user_input)

        if intent == "email":
            if mode != "email":
                print("System: I'll help you with sending an email.")
                print("System: Please provide a description for the email you want to send:")
                mode = "email"
                email_stage = "init"

        elif intent == "analyze":
            if mode != "data_analysis":
                print("System: I'll help you analyze your data.")
                print("System: Please provide the path to your CSV or Excel file:")
                mode = "data_analysis"
            else:
                # Process file path
                success, result = read_data_file(user_input)
                if success:
                    print("\nSystem: Analyzing data sample...")
                    insights = generate_data_insights(result)
                    formatted_output = format_analysis_output(insights)
                    print("\nSystem: Data Analysis Results:")
                    print(formatted_output)
                    last_response = formatted_output
                    print("\nSystem: You can:")
                    print("- Ask me to analyze another file")
                    print("- Ask me to save this analysis")
                    print("- Or just chat with me about something else")
                else:
                    print(f"System: ❌ Error reading file: {result}")
                    print("System: Please provide a valid path to a CSV or Excel file:")

        elif intent == "save":
            if last_response:
                success, result = save_response_to_file(last_response)
                if success:
                    print(f"System: ✅ Document saved as '{result}'")
                else:
                    print(f"System: ❌ Failed to save document: {result}")
            else:
                print("System: ⚠️ No recent response available to save.")

        else:  # normal chat
            if mode != "chat":
                print("System: Switching to general chat mode.")
                mode = "chat"
            response = process_general_chat(user_input)
            last_response = response
            print(f"LLM: {response}")

if __name__ == "__main__":
    main()
