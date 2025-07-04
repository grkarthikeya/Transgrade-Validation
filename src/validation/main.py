# #!/usr/bin/env python
# import sys
# import warnings

# from datetime import datetime

# from validation.crew import Validation

# warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# # This main file is intended to be a way for you to run your
# # crew locally, so refrain from adding unnecessary logic into this file.
# # Replace with inputs you want to test with, it will automatically
# # interpolate any tasks and agents information
# def load_file_as_string(filepath):
#     with open(filepath, 'r', encoding='utf-8') as f:
#         return f.read()


# def run():
#     """
#     Run the crew.
#     """
#     answers_path = r"C:\Users\ganes\Desktop\correction\validation\answer.txt"

#     rubrics_path = r"C:\Users\ganes\Desktop\correction\validation\rubrics.txt"
    
#     answers = load_file_as_string(answers_path)
#     rubrics = load_file_as_string(rubrics_path)

#     inputs = {
#         'answers': answers,
#         'rubrics': rubrics
#     }
    
#     try:
#         Validation().crew().kickoff(inputs=inputs)
#     except Exception as e:
#         raise Exception(f"An error occurred while running the crew: {e}")


# def train():
#     """
#     Train the crew for a given number of iterations.
#     """
#     inputs = {
#         "topic": "AI LLMs",
#         'current_year': str(datetime.now().year)
#     }
#     try:
#         Validation().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while training the crew: {e}")

# def replay():
#     """
#     Replay the crew execution from a specific task.
#     """
#     try:
#         Validation().crew().replay(task_id=sys.argv[1])

#     except Exception as e:
#         raise Exception(f"An error occurred while replaying the crew: {e}")

# def test():
#     """
#     Test the crew execution and returns the results.
#     """
#     inputs = {
#         "topic": "AI LLMs",
#         "current_year": str(datetime.now().year)
#     }
    
#     try:
#         Validation().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while testing the crew: {e}")


#!/usr/bin/env python
import sys
import os
import warnings
import requests
import logging
import json
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from validation.crew import Validation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Django API configuration
DJANGO_API_BASE_URL = "https://nasty-regions-brush.loca.lt"

# ---
# ### 🔍 Helper Functions for Django API Integration
# ---

def get_rubrics_from_keyocr(subject_id: str):
    """Retrieve rubrics from Django API using key-ocr endpoint."""
    try:
        logger.info(f"Requesting rubrics for subject_id: {subject_id}")
        
        url = f"{DJANGO_API_BASE_URL}/key-ocr/?subject_id={subject_id}"
        logger.info(f"Key-OCR API URL: {url}")
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict):
                rubrics = data.get('rubrics', '')
                if rubrics:
                    logger.info(f"Found rubrics for subject_id: {subject_id}")
                    return rubrics, None
                else:
                    return None, f"No rubrics found for subject_id: {subject_id}"
            else:
                return None, f"Unexpected response format for subject_id: {subject_id}"
        else:
            logger.error(f"Key-OCR API error: {response.status_code} - {response.text}")
            return None, f"Key-OCR API error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Key-OCR API request error: {str(e)}")
        return None, f"Key-OCR API request error: {str(e)}"

def get_scored_from_results(script_id: str):
    """Retrieve scored data from Django API using results endpoint."""
    try:
        logger.info(f"Requesting scored data for script_id: {script_id}")
        
        url = f"{DJANGO_API_BASE_URL}/results/?script_id={script_id}"
        logger.info(f"Results API URL: {url}")
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                # Get the first result record for the script
                result_data = data[0]
                scored_data = result_data.get('scored', {})
                result_id = result_data.get('result_id')
                return scored_data, result_id, None
            elif isinstance(data, dict):
                scored_data = data.get('scored', {})
                result_id = data.get('result_id')
                return scored_data, result_id, None
            else:
                return None, None, f"No scored data found for script_id: {script_id}"
        else:
            logger.error(f"Results API error: {response.status_code} - {response.text}")
            return None, None, f"Results API error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Results API request error: {str(e)}")
        return None, None, f"Results API request error: {str(e)}"

def save_graded_output(result_id: str, graded_output: str):
    """Save graded output to the Django API results endpoint."""
    try:
        url = f"{DJANGO_API_BASE_URL}/results/"
        logger.info(f"Saving graded output to: {url}")
        
        # Try to parse graded_output as JSON, otherwise store as string
        try:
            graded_json = json.loads(graded_output) if isinstance(graded_output, str) else graded_output
        except json.JSONDecodeError:
            graded_json = {"graded_output": str(graded_output)}
        
        payload = {
            "result_id": result_id,
            "graded": graded_json
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(f"Successfully saved graded output for result_id: {result_id}")
            return True, response.json()
        else:
            logger.error(f"Failed to save graded output: {response.status_code} - {response.text}")
            return False, f"API error: {response.status_code} - {response.text}"
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error saving graded output: {str(e)}")
        return False, f"API request error: {str(e)}"

# ---
# ### 🧠 Core Processing Logic
# ---

def run_validation(script_id: str, subject_id: str):
    """Run validation pipeline: get rubrics from key-ocr, get scored from results, save output to graded field."""
    try:
        # Get rubrics from key-ocr endpoint
        rubrics, rubrics_error = get_rubrics_from_keyocr(subject_id)
        if rubrics_error:
            return False, rubrics_error

        if not rubrics:
            return False, f"No rubrics found for subject_id: {subject_id}"

        # Get scored data from results endpoint
        scored_data, result_id, scored_error = get_scored_from_results(script_id)
        if scored_error:
            return False, scored_error

        if not scored_data:
            return False, f"No scored data found for script_id: {script_id}"

        if not result_id:
            return False, f"No result_id found for script_id: {script_id}"

        # Prepare inputs for validation crew
        inputs = {
            'answers': json.dumps(scored_data) if isinstance(scored_data, dict) else str(scored_data),
            'rubrics': rubrics
        }

        logger.info(f"Processing validation for script_id: {script_id}, subject_id: {subject_id}")
        logger.info(f"Scored data type: {type(scored_data)}, Rubrics length: {len(rubrics)}")

        print("\n" + "="*80)
        print("📊 SCORED DATA:")
        print("="*80)
        print(json.dumps(scored_data, indent=2) if isinstance(scored_data, dict) else scored_data)
        print("="*80)
        print("📋 RUBRICS:")
        print("="*80)
        print(rubrics)
        print("="*80 + "\n")

        # Run validation crew
        validation_result = Validation().crew().kickoff(inputs=inputs)

        # Token Usage
        print(f"\nToken Usage:\n{result.token_usage}\n")
        
        # Convert result to string for storage
        graded_output = str(validation_result)
        
        logger.info("Validation crew completed successfully")

        print("\n" + "="*80)
        print("✅ GRADED OUTPUT:")
        print("="*80)
        print(graded_output)
        print("="*80 + "\n")

        # Save graded output to the graded field
        save_success, save_message = save_graded_output(result_id, graded_output)
        if not save_success:
            logger.error(f"Failed to save graded output: {save_message}")
            return False, f"Validation completed but failed to save: {save_message}"

        logger.info(f"Validation completed successfully for script_id: {script_id}")
        return True, f"Success: Graded output saved for script_id {script_id}."

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        return False, f"Error: {str(e)}"

# ---
# ### 🚀 Flask Application
# ---

def run():
    """Start the Flask application for the validation system."""
    app = Flask(__name__)
    app.secret_key = 'validation_system_secret_key'
    CORS(app, origins=['http://localhost:3000'])

    @app.route('/')
    def index():
        """Root endpoint with API information."""
        return jsonify({
            "message": "Validation API is running",
            "endpoints": {
                "validate": "/validate/<script_id>/<subject_id>",
                "test_data": "/test/<script_id>/<subject_id>",
                "health_check": "/health"
            },
            "description": "Retrieves rubrics from key-ocr and scored data from results, processes with validation crew, saves output to graded field"
        })

    @app.route('/validate/<script_id>/<subject_id>', methods=['GET'])
    def validate_route(script_id, subject_id):
        """Endpoint to run validation for a given script_id and subject_id."""
        if not script_id or not subject_id:
            return jsonify({
                "status": "error", 
                "message": "Both script_id and subject_id are required"
            }), 400

        logger.info(f"Processing validation for script_id: {script_id}, subject_id: {subject_id}")
        success, message = run_validation(script_id, subject_id)

        return jsonify({
            "status": "success" if success else "error",
            "script_id": str(script_id),
            "subject_id": str(subject_id),
            "message": message,
            "operation": "validation"
        }), 200 if success else 500

    @app.route('/test/<script_id>/<subject_id>')
    def test_data_route(script_id, subject_id):
        """Test endpoint to check data retrieval for debugging."""
        logger.info(f"Testing data retrieval for script_id: {script_id}, subject_id: {subject_id}")
        
        try:
            # Test rubrics retrieval from key-ocr
            rubrics, rubrics_error = get_rubrics_from_keyocr(subject_id)
            
            # Test scored data retrieval from results
            scored_data, result_id, scored_error = get_scored_from_results(script_id)
            
            return jsonify({
                "script_id": str(script_id),
                "subject_id": str(subject_id),
                "rubrics_data": {
                    "rubrics_length": len(rubrics) if rubrics else 0,
                    "rubrics_preview": str(rubrics)[:200] if rubrics else "None/Empty",
                    "error": rubrics_error
                },
                "scored_data": {
                    "scored_type": str(type(scored_data)),
                    "scored_preview": str(scored_data)[:200] if scored_data else "None/Empty",
                    "result_id": result_id,
                    "error": scored_error
                },
                "data_flow": "key-ocr (rubrics) + results (scored) → validation crew → results (graded)"
            })
                
        except Exception as e:
            logger.error(f"Error in test_data_route: {str(e)}")
            return jsonify({
                "script_id": str(script_id),
                "subject_id": str(subject_id),
                "error": f"Exception occurred: {str(e)}"
            })

    @app.route('/health')
    def health_check():
        """Health check endpoint to verify Django API connectivity."""
        try:
            response = requests.get(f"{DJANGO_API_BASE_URL}/", timeout=5)
            if response.status_code == 200:
                return jsonify({
                    "status": "healthy", 
                    "django_api": "connected",
                    "django_url": DJANGO_API_BASE_URL,
                    "services": ["validation", "django_integration"]
                })
            else:
                return jsonify({
                    "status": "unhealthy", 
                    "django_api": "error", 
                    "details": f"Status: {response.status_code}"
                })
        except Exception as e:
            return jsonify({
                "status": "unhealthy", 
                "django_api": "disconnected", 
                "error": str(e)
            })

    # Run Flask app
    port = int(os.environ.get('PORT', 7000))
    app.run(host='0.0.0.0', port=port, debug=False)

# ---
# ### 🧭 Main Entry Point
# ---

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "run":
        run()
    else:
        print("Usage: python integrated_main.py run")
        print("\nAvailable endpoints:")
        print("  GET /validate/<script_id>/<subject_id>     - Validate student answers")
        print("  GET /test/<script_id>/<subject_id>         - Test data retrieval")
        print("  GET /health                                - Health check")