# function_app.py

import azure.functions as func
import logging
from .handlers import RequestHandler
from .data_access import CosmosDBSessionManager
from .openai_service import OpenAIService
from .business_logic import BusinessLogic

# Create an instance of the Function App with anonymous HTTP access
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Initialize the components
session_manager = CosmosDBSessionManager()
openai_service = OpenAIService()
business_logic = BusinessLogic(session_manager, openai_service)
request_handler = RequestHandler(business_logic)

@app.route(route="Test01")
def Test01(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Received a message from WhatsApp.')

    try:
        # Handle the incoming request using the request_handler
        response_content, status_code = request_handler.handle_request(req)
        
        # Check the status code and construct the appropriate response
        if status_code == 200:
            return func.HttpResponse(
                response_content, 
                mimetype="application/xml", 
                status_code=200
            )
        else:
            return func.HttpResponse(
                response_content, 
                status_code=status_code
            )
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return func.HttpResponse(
            f"An error occurred: {e}", 
            status_code=500
        )