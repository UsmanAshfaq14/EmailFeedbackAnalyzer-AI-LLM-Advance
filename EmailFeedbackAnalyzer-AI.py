import json
import csv
import re
import pandas as pd
from datetime import datetime
import io
import sys

# Add this at the beginning of your script to handle Unicode output
if sys.stdout.encoding != 'utf-8':
    try:
        # Try to set console to UTF-8 mode on Windows
        if sys.platform == 'win32':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        # If that fails, replace Unicode characters with ASCII equivalents
        pass

def validate_data(data):
    """
    Validates the input data structure and fields.
    Returns validation report and a boolean indicating success.
    """
    # Initialize validation report
    validation_report = {
        "total_emails": 0,
        "fields_per_record": 0,
        "field_validity": {
            "email_id": "missing",
            "sender": "missing",
            "timestamp": "invalid",
            "subject": "missing",
            "content": "missing",
            "sentiment_score": "invalid"
        },
        "is_valid": True,
        "error_messages": []
    }
    
    if not data or len(data) == 0:
        validation_report["is_valid"] = False
        validation_report["error_messages"].append("ERROR: No data provided.")
        return validation_report, False
    
    validation_report["total_emails"] = len(data)
    
    # Assuming all records have the same number of fields
    first_record = data[0]
    validation_report["fields_per_record"] = len(first_record)
    
    # Check all required fields in each record
    for i, record in enumerate(data):
        row_num = i + 1
        missing_fields = []
        invalid_fields = []
        
        # Check if required fields exist
        required_fields = ["email_id", "sender", "timestamp", "subject", "content", "sentiment_score"]
        for field in required_fields:
            if field not in record:
                missing_fields.append(field)
            elif field == "timestamp":
                # Validate timestamp format
                try:
                    datetime.strptime(record[field], "%Y-%m-%d %H:%M:%S")
                    validation_report["field_validity"]["timestamp"] = "valid"
                except ValueError:
                    invalid_fields.append(field)
                    validation_report["field_validity"]["timestamp"] = "invalid"
            elif field == "sentiment_score":
                # Validate sentiment score is numeric and within range
                try:
                    score = float(record[field])
                    if score < -1 or score > 1:
                        invalid_fields.append(field)
                        validation_report["field_validity"]["sentiment_score"] = "invalid"
                    else:
                        validation_report["field_validity"]["sentiment_score"] = "valid"
                except (ValueError, TypeError):
                    invalid_fields.append(field)
                    validation_report["field_validity"]["sentiment_score"] = "invalid"
            else:
                # Mark field as present
                validation_report["field_validity"][field] = "present"
        
        # Report errors if any
        if missing_fields:
            error_msg = f"ERROR: Missing required field(s): {', '.join(missing_fields)} in row {row_num}."
            validation_report["error_messages"].append(error_msg)
            validation_report["is_valid"] = False
        
        if invalid_fields:
            error_msg = f"ERROR: Invalid value for the field(s): {', '.join(invalid_fields)} in row {row_num}. Please correct and resubmit."
            validation_report["error_messages"].append(error_msg)
            validation_report["is_valid"] = False
    
    return validation_report, validation_report["is_valid"]

def parse_data(data_input):
    """
    Parses input data from CSV or JSON format.
    Returns a list of dictionaries representing email records.
    """
    try:
        # Try to parse as JSON
        if data_input.strip().startswith('{'):
            json_data = json.loads(data_input)
            if 'emails' in json_data:
                return json_data['emails']
            return json_data
        # Try to parse as CSV
        else:
            csv_reader = csv.DictReader(io.StringIO(data_input))
            return list(csv_reader)
    except Exception as e:
        return None

def analyze_emails(data, keywords=None):
    """
    Analyzes email data for specified keywords.
    Performs calculations and generates analysis report.
    """
    if keywords is None:
        keywords = ["delay", "refund", "error", "broken", "complaint"]
    
    total_emails = len(data)
    results = {}
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # 1. Complaint Occurrence Count Calculation
        count = 0
        sentiment_scores = []
        
        for email in data:
            content = email["content"].lower()
            if keyword_lower in content:
                count += 1
                sentiment_scores.append(float(email["sentiment_score"]))
        
        # 2. Frequency Ratio Calculation
        frequency_ratio = (count / total_emails) * 100 if total_emails > 0 else 0
        frequency_ratio = round(frequency_ratio, 2)
        
        # 3. Average Sentiment Score Calculation
        avg_sentiment = sum(sentiment_scores) / count if count > 0 else 0
        avg_sentiment = round(avg_sentiment, 2)
        
        # 4. Complaint Classification
        classification = "Common Complaint" if frequency_ratio >= 10.00 else "Not Common Complaint"
        
        # 5. Suggested Solution Determination
        if avg_sentiment < -0.50:
            solution = "Investigate and provide prompt resolution, possibly including compensation."
        elif -0.50 <= avg_sentiment <= 0.00:
            solution = "Monitor closely and consider minor improvements."
        else:  # avg_sentiment > 0.00
            solution = "No immediate action required; continue monitoring trends."
        
        results[keyword] = {
            "count": count,
            "frequency_ratio": frequency_ratio,
            "avg_sentiment": avg_sentiment,
            "classification": classification,
            "solution": solution,
            "sentiment_scores": sentiment_scores
        }
    
    return results

def generate_validation_report(validation_report):
    """
    Generates a markdown formatted validation report.
    """
    report = "# Email Data Validation Report:\n"
    report += "## Data Structure Check:\n"
    report += f"- Total Emails Provided: {validation_report['total_emails']}\n"
    report += f"- Number of fields per record: {validation_report['fields_per_record']}\n\n"
    
    report += "## Field Validity:\n"
    for field, status in validation_report['field_validity'].items():
        report += f"- {field}: {status}\n"
    
    report += "\n## Validation Summary:\n"
    if validation_report['is_valid']:
        report += "Data validation is successful!\n"
    else:
        for error in validation_report['error_messages']:
            report += f"{error}\n"
    
    return report

def generate_analysis_report(results, total_emails):
    """
    Generates a markdown formatted analysis report.
    """
    report = "# Email Feedback Analysis Summary:\n"
    report += f"- Total Emails Evaluated: {total_emails}\n\n"
    
    for keyword, analysis in results.items():
        report += f"# Detailed Analysis per Complaint Keyword:\n"
        report += f"Keyword: {keyword}\n\n"
        
        report += "## Input Data:\n"
        report += f"- Total Emails Provided: {total_emails}\n"
        report += f"- Occurrence Count (emails containing the keyword): {analysis['count']}\n\n"
        
        report += "## Detailed Calculations:\n\n"
        
        # 1. Complaint Occurrence Count
        report += "### 1. Complaint Occurrence Count Calculation:\n"
        report += "- Explanation: Count the number of emails in which the \"content\" field includes the keyword (comparison is case-insensitive).\n"
        report += "- Process:\n"
        report += "  Step 1: Convert the \"content\" of each email to lowercase.\n"
        report += "  Step 2: Convert the keyword to lowercase.\n"
        report += "  Step 3: For each email, check if the lowercase \"content\" includes the lowercase keyword.\n"
        report += "  Step 4: If true, count that email as one occurrence.\n"
        report += f"- Final Count: {analysis['count']}\n\n"
        
        # 2. Frequency Ratio
        report += "### 2. Frequency Ratio Calculation:\n"
        report += "- Formula: $$ \\text{Frequency Ratio} = \\frac{\\text{Count}}{\\text{Total Emails}} \\times 100 $$\n"
        report += "- Calculation Steps:\n"
        report += f"  Step 1: Divide the Occurrence Count ({analysis['count']}) by the Total Emails ({total_emails}).\n"
        division_result = analysis['count'] / total_emails if total_emails > 0 else 0
        division_result = round(division_result, 4)
        report += f"  Step 2: Multiply the result ({division_result}) by 100 to convert it to a percentage.\n"
        multiplication_result = division_result * 100
        report += f"  Step 3: Round the final result ({multiplication_result}) to 2 decimal places.\n"
        report += f"- Final Frequency Ratio: {analysis['frequency_ratio']}%\n\n"
        
        # 3. Average Sentiment Score
        report += "### 3. Average Sentiment Score Calculation:\n"
        report += "- Formula: $$ \\text{Average Sentiment} = \\frac{\\sum (\\text{sentiment\\_score for emails with keyword})}{\\text{Count}} $$\n"
        report += "- Calculation Steps:\n"
        report += "  Step 1: Identify all emails containing the keyword.\n"
        report += "  Step 2: Extract the \"sentiment_score\" from each of these emails.\n"
        
        # Show detailed sentiment scores if count is not too large
        if analysis['count'] <= 10 and analysis['count'] > 0:
            sentiment_str = ", ".join([str(score) for score in analysis['sentiment_scores']])
            report += f"  Step 3: Sum all the sentiment scores ({sentiment_str}) to get the Total Sentiment.\n"
        else:
            report += "  Step 3: Sum all the sentiment scores to get the Total Sentiment.\n"
        
        total_sentiment = sum(analysis['sentiment_scores']) if analysis['count'] > 0 else 0
        total_sentiment_rounded = round(total_sentiment, 2)
        report += f"  Step 4: Divide the Total Sentiment ({total_sentiment_rounded}) by the Occurrence Count ({analysis['count']}).\n"
        
        if analysis['count'] > 0:
            division_result = total_sentiment / analysis['count']
            division_result_rounded = round(division_result, 4)
            report += f"  Step 5: Round the final result ({division_result_rounded}) to 2 decimal places.\n"
        else:
            report += "  Step 5: Since count is 0, set Average Sentiment to 0.\n"
            
        report += f"- Final Average Sentiment Score: {analysis['avg_sentiment']}\n\n"
        
        # 4. Complaint Classification
        report += "### 4. Complaint Classification:\n"
        report += "- Criteria: A complaint is classified as common if the Frequency Ratio is greater than or equal to 10.00%.\n"
        report += "- Calculation Steps:\n"
        report += f"  Step 1: Compare the calculated Frequency Ratio ({analysis['frequency_ratio']}%) to 10.00%.\n"
        # Replace Unicode greater than or equal symbol with ASCII alternative
        report += f"  Step 2: IF Frequency Ratio >= 10.00%, classify as \"Common Complaint\".\n"
        report += f"  Step 3: ELSE, classify as \"Not Common Complaint\".\n"
        report += f"- Final Classification: {analysis['classification']}\n\n"
        
        # 5. Final Recommendation
        report += "# Final Recommendation:\n"
        report += "- Criteria: The solution recommendation is based on the Average Sentiment Score.\n"
        report += "- Calculation Steps:\n"
        report += f"  Step 1: Check if the Average Sentiment Score ({analysis['avg_sentiment']}) is less than -0.50.\n"
        report += "    - IF true, suggest: \"Investigate and provide prompt resolution, possibly including compensation.\"\n"
        report += f"  Step 2: ELSE, check if the Average Sentiment Score ({analysis['avg_sentiment']}) is between -0.50 and 0.00 (inclusive).\n"
        report += "    - IF true, suggest: \"Monitor closely and consider minor improvements.\"\n"
        report += f"  Step 3: ELSE (i.e., if the Average Sentiment Score is greater than 0.00), suggest: \"No immediate action required; continue monitoring trends.\"\n"
        report += f"- Final Suggested Solution: {analysis['solution']}\n\n"
    
    return report

def email_feedback_analyzer(data_input):
    """
    Main function to process input data and generate analysis reports.
    """
    # Parse the input data
    data = parse_data(data_input)
    
    if not data:
        return "ERROR: Invalid data format. Please provide data in CSV or JSON format."
    
    # Validate the data
    validation_report, is_valid = validate_data(data)
    validation_md = generate_validation_report(validation_report)
    
    if not is_valid:
        return validation_md
    
    # Analyze the data
    analysis_results = analyze_emails(data)
    
    # Generate the analysis report
    analysis_md = generate_analysis_report(analysis_results, len(data))
    
    # Combine reports
    final_report = validation_md + "\n\n" + analysis_md
    
    return final_report

def save_report_to_file(report, filename="email_feedback_analysis_report.md"):
    """
    Saves the report to a file with UTF-8 encoding.
    """
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(report)
    print(f"Report saved to {filename}")

# Example usage
if __name__ == "__main__":
    # Sample data can be provided here for testing
    sample_data = """
   {
  "emails": [
    {
      "email_id": "E420",
      "sender": "alex@example.com",
      "timestamp": "2025-03-07 17:00:00",
      "subject": "Late Delivery",
      "content": "My package was delayed due to unforeseen circumstances.",
      "sentiment_score": -0.5
    },
    {
      "email_id": "E421",
      "sender": "brian@example.com",
      "timestamp": "2025-03-07 17:05:00",
      "subject": "Refund Request",
      "content": "I need a refund because my order was delayed.",
      "sentiment_score": -0.6
    },
    {
      "email_id": "E422",
      "sender": "carla@example.com",
      "timestamp": "2025-03-07 17:10:00",
      "subject": "Checkout Issue",
      "content": "There was an error during checkout on the website.",
      "sentiment_score": -0.4
    },
    {
      "email_id": "E423",
      "sender": "derek@example.com",
      "timestamp": "2025-03-07 17:15:00",
      "subject": "Service Complaint",
      "content": "I want to file a complaint about the slow service.",
      "sentiment_score": -0.3
    },
    {
      "email_id": "E424",
      "sender": "emma@example.com",
      "timestamp": "2025-03-07 17:20:00",
      "subject": "Broken Item",
      "content": "The item I received was broken.",
      "sentiment_score": -0.8
    },
    {
      "email_id": "E425",
      "sender": "frank@example.com",
      "timestamp": "2025-03-07 17:25:00",
      "subject": "Shipping Delay",
      "content": "The shipping delay caused inconvenience.",
      "sentiment_score": -0.5
    },
    {
      "email_id": "E426",
      "sender": "gina@example.com",
      "timestamp": "2025-03-07 17:30:00",
      "subject": "Refund Inquiry",
      "content": "I am asking for a refund for my damaged product.",
      "sentiment_score": -0.7
    },
    {
      "email_id": "E427",
      "sender": "henry@example.com",
      "timestamp": "2025-03-07 17:35:00",
      "subject": "Payment Error",
      "content": "An error occurred while processing my payment.",
      "sentiment_score": -0.2
    },
    {
      "email_id": "E428",
      "sender": "irene@example.com",
      "timestamp": "2025-03-07 17:40:00",
      "subject": "Service Complaint",
      "content": "I have a complaint about the customer service.",
      "sentiment_score": -0.3
    },
    {
      "email_id": "E429",
      "sender": "jake@example.com",
      "timestamp": "2025-03-07 17:45:00",
      "subject": "Delayed and Broken",
      "content": "My order was delayed and the product arrived broken.",
      "sentiment_score": -0.9
    }
  ]
}

    """
    
    # Process the sample data
    result = email_feedback_analyzer(sample_data)
    
    # Option 1: Try to print to console (may still fail in some environments)
    try:
        print(result)
    except UnicodeEncodeError:
        print("ERROR: Unable to print to console due to UnicodeEncodeError.")