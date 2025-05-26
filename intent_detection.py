import logging
import ollama

# Get the logger for this module
logger = logging.getLogger(__name__)

def detect_user_intent(user_input):
    """
    Detects whether the user intends to send an email, save a document, analyze data, analyze image, or just chat.
    Returns one of: 'email', 'save', 'analyze', 'analyze_image', or 'normal'.
    """
    intent_prompt = (
    "You are an intent detection assistant for a virtual AI agent. Your task is to understand the user's intent "
    "based on their input. The user may want to either send an email, save the assistant's response into a document, "
    "analyze data from a file, analyze a breast MRI scan image, or simply engage in a normal chat.\n\n"

    "Your job is to classify the intent into ONE of the following categories by responding with only one word:\n"
    "- 'email' → If the user is trying to draft, compose, send, or discuss sending an email.\n"
    "- 'save' → If the user wants to save the assistant's response as a report, note, document, summary, or file.\n"
    "- 'analyze' → If the user wants to analyze data, upload a file for analysis, or get insights from data.\n"
    "- 'analyze_image' → If the user wants to analyze a breast MRI scan image or upload an image for analysis.\n"
    "- 'normal' → For all general queries or conversational input that do not involve the above intents.\n\n"

    "Here are examples to guide your judgment:\n"
    "Example 1: I want to send an update to my boss about the project → email\n"
    "Example 2: Can you create a summary report and save it for me? → save\n"
    "Example 3: Tell me a joke → normal\n"
    "Example 4: Generate an email to HR about my resignation → email\n"
    "Example 5: Save this summary to a text file → save\n"
    "Example 6: What's the capital of France? → normal\n"
    "Example 7: Email a proposal to the client → email\n"
    "Example 8: Store this conversation in a file → save\n"
    "Example 9: Who won the cricket match yesterday? → normal\n"
    "Example 10: I want to download this response → save\n"
    "Example 11: Can you analyze this CSV file for me? → analyze\n"
    "Example 12: I want to upload an Excel file for data insights → analyze\n"
    "Example 13: Help me understand this dataset → analyze\n"
    "Example 14: What insights can you get from this data? → analyze\n"
    "Example 15: I need to analyze some sales data → analyze\n"
    "Example 16: Can you analyze this breast MRI scan? → analyze_image\n"
    "Example 17: I want to upload an MRI image for analysis → analyze_image\n"
    "Example 18: What stage is this breast cancer scan showing? → analyze_image\n"
    "Example 19: Please analyze this medical image → analyze_image\n"
    "Example 20: Tell me about this breast MRI scan → analyze_image\n\n"
    
    f"Now analyze the following user input:\nUser Input: {user_input}\n\n"
    "Your response (only one word - email, save, analyze, analyze_image, or normal):"
    )

    try:
        response = ollama.chat(model='qwen2.5:3B', messages=[{"role": "user", "content": intent_prompt}])
        intent = response['message']['content'].strip().lower()
        logger.debug(f"Detected intent: {intent}")
        return intent
    except Exception as e:
        logger.error(f"Intent detection failed: {e}")
        return 'normal'
