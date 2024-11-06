# handlers.py

import logging
from twilio.twiml.messaging_response import MessagingResponse

class RequestHandler:
    """
    Handles incoming HTTP requests and processes them using business logic.
    """

    def __init__(self, business_logic):
        """
        Initializes the RequestHandler with the given business logic instance.
        
        Args:
            business_logic (BusinessLogic): An instance of the BusinessLogic class.
        """
        self.business_logic = business_logic

    def handle_request(self, req):
        """
        Processes the incoming HTTP request and returns an appropriate response.
        
        Args:
            req (func.HttpRequest): The incoming HTTP request from Azure Functions.
        
        Returns:
            tuple: A tuple containing the response content (str) and the HTTP status code (int).
        """
        # Extract 'From' and 'Body' from the request form data
        from_number = req.form.get('From')
        body = req.form.get('Body')

        # Check if 'From' and 'Body' are present
        if not from_number or not body:
            logging.error("Missing 'From' or 'Body' in the request.")
            return "Faltan los campos 'From' o 'Body' en la solicitud.", 400

        logging.info(f"Received message from {from_number}: {body}")

        # Process the message using the business logic
        result = self.business_logic.process_message(from_number, body)

        # Handle different possible outcomes from processing the message
        if result == "ask_user":
            # Create a Twilio response asking the user to choose between continuing or starting new
            response = MessagingResponse()
            message = response.message("Hace más de 3 días que no nos contactas. ¿Deseas iniciar una nueva conversación o continuar la anterior?")
            message.add_body("Responde con 'CONTINUAR' o 'NUEVA CONVERSACIÓN'.")
            logging.info(f"Asked user {from_number} to choose between continuing or starting new.")
            return str(response), 200

        elif result == "requires_action":
            # Create a Twilio response requesting more information from the user
            response = MessagingResponse()
            response.message("El asistente necesita más información para continuar. ¿Podrías proporcionar más detalles?")
            logging.info(f"Requested more information from {from_number}.")
            return str(response), 200

        elif result:
            # Create a Twilio response with the assistant's reply
            response = MessagingResponse()
            response.message(result)
            logging.info(f"Sent response to {from_number}: {result}")
            return str(response), 200

        else:
            # If no response from the assistant, return an error
            logging.warning("No content in the assistant's response.")
            return "No hubo respuesta del asistente.", 500