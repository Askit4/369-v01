# business_logic.py

import logging
from datetime import datetime, timezone, timedelta

DAYS_FOR_SESSION_CONTINUE = 3
MONTHS_FOR_SESSION_DELETE = 6

class BusinessLogic:
    """
    Contains the core business logic for processing messages and managing sessions.
    """

    def __init__(self, session_manager, openai_service):
        """
        Initializes the BusinessLogic with the given session manager and OpenAI service.
        
        Args:
            session_manager (CosmosDBSessionManager): Instance managing Cosmos DB sessions.
            openai_service (OpenAIService): Instance managing interactions with OpenAI API.
        """
        self.session_manager = session_manager
        self.openai_service = openai_service

    def process_message(self, from_number, body):
        """
        Processes the incoming message and determines the appropriate action.
        
        Args:
            from_number (str): The sender's phone number.
            body (str): The message content.
        
        Returns:
            str or None: The assistant's response, a directive, or None if an error occurs.
        """
        # Retrieve thread data for the user
        thread_data = self.session_manager.get_thread_data(from_number)
        now = datetime.now(timezone.utc)

        if thread_data:
            last_interaction = datetime.fromisoformat(thread_data['last_interaction'])
            delta_days = (now - last_interaction).days

            if delta_days < DAYS_FOR_SESSION_CONTINUE:
                # Continue with the existing thread
                thread_id = thread_data['thread_id']
                status = "continue"
                logging.info(f"Continuing session for {from_number}.")
            elif delta_days < MONTHS_FOR_SESSION_DELETE * 30:
                # Ask the user if they want to continue or start new
                thread_id = thread_data['thread_id']
                status = "ask_user"
                logging.info(f"Asking {from_number} whether to continue or start new.")
                return "ask_user"
            else:
                # Delete old thread data and start new
                self.session_manager.delete_thread(thread_data)
                thread_id = None
                status = "new"
                logging.info(f"Deleted old session for {from_number}. Starting new session.")
        else:
            # No existing thread data; start a new session
            thread_id = None
            status = "new"
            logging.info(f"No existing session for {from_number}. Starting new session.")

        if status == "new":
            # Create a new thread and update session data
            thread_id = self.openai_service.create_thread()
            if not thread_id:
                logging.error("Failed to create a new thread.")
                return None
            self.session_manager.create_or_update_thread(thread_id, from_number)

        # Send the user's message to the thread
        self.openai_service.create_message(thread_id, body)

        # Run the assistant on the thread
        run = self.openai_service.run_assistant_on_thread(thread_id)
        if not run:
            logging.error("Failed to start assistant run.")
            return None

        # Poll the run status until completion
        run_status = self.openai_service.poll_run_status(thread_id, run['id'])

        if run_status == 'requires_action':
            # Assistant needs more information from the user
            logging.info(f"Assistant requires action from {from_number}.")
            return "requires_action"
        elif run_status == 'failed':
            logging.error("Assistant run failed.")
            return None

        # Retrieve the assistant's response
        assistant_response = self.openai_service.get_assistant_response(thread_id)
        if assistant_response:
            # Update the last interaction time
            self.session_manager.create_or_update_thread(thread_id, from_number)
            return assistant_response
        else:
            logging.warning("No response from assistant.")
            return None