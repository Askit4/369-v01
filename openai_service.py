# openai_service.py

import os
import logging
import time
import requests

class OpenAIService:
    """
    Manages interactions with the OpenAI API, including creating threads,
    sending messages, running the assistant, and retrieving responses.
    """

    def __init__(self):
        """
        Initializes the OpenAIService with API credentials from environment variables.
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.assistant_id = os.getenv('ASSISTANT_ID')

        # Base headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2"
        }

    def create_thread(self):
        """
        Creates a new thread in the OpenAI system.

        Returns:
            str: The ID of the newly created thread.
        """
        url = "https://api.openai.com/v1/threads"
        try:
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            thread = response.json()
            thread_id = thread['id']
            logging.info(f"Thread created: {thread_id}")
            return thread_id
        except requests.exceptions.RequestException as e:
            logging.error(f"Error creating thread: {e}")
            return None

    def create_message(self, thread_id, content):
        """
        Sends a user message to the specified thread.

        Args:
            thread_id (str): The ID of the thread.
            content (str): The message content to send.
        """
        url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
        data = {
            "role": "user",
            "content": content
        }
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            message = response.json()
            logging.info(f"Message created: {message['id']}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error creating message: {e}")

    def run_assistant_on_thread(self, thread_id):
        """
        Initiates a run of the assistant on the specified thread.

        Args:
            thread_id (str): The ID of the thread.

        Returns:
            dict: The run information if successful, else None.
        """
        url = f"https://api.openai.com/v1/threads/{thread_id}/runs"
        data = {
            "assistant_id": self.assistant_id
        }
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            run = response.json()
            logging.info(f"Run started with ID: {run['id']}")
            return run
        except requests.exceptions.RequestException as e:
            logging.error(f"Error running assistant: {e}")
            return None

    def poll_run_status(self, thread_id, run_id):
        """
        Polls the status of the assistant run until it completes.

        Args:
            thread_id (str): The ID of the thread.
            run_id (str): The ID of the run.

        Returns:
            str: The final status of the run ('completed', 'failed', 'requires_action').
        """
        url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}"
        try:
            while True:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                run = response.json()

                status = run['status']
                logging.info(f"Run status: {status}")

                if status in ['completed', 'failed', 'requires_action']:
                    return status

                time.sleep(5)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error polling run status: {e}")
            return 'failed'

    def get_assistant_response(self, thread_id):
        """
        Retrieves the assistant's response from the thread messages.

        Args:
            thread_id (str): The ID of the thread.

        Returns:
            str or None: The assistant's response content if found, else None.
        """
        url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            messages = response.json()

            # Find the latest assistant message
            for message in reversed(messages['data']):
                if message['role'] == 'assistant':
                    content = message['content'][0]['text']['value']
                    return content
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error retrieving assistant response: {e}")
            return None