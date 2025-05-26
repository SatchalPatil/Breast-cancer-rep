def save_response_to_file(content, filename="generated_report.txt"):
    """
    Saves the provided content to a .txt file.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
        return True, filename
    except Exception as e:
        return False, str(e)
