# data_access.py

import os
import logging
from datetime import datetime, timezone
from azure.cosmos import CosmosClient, exceptions

class CosmosDBSessionManager:
    """
    Manages session data in Azure Cosmos DB.
    """

    def __init__(self):
        """
        Initializes the CosmosDBSessionManager with Cosmos DB configuration.
        """
        # Cosmos DB configuration from environment variables
        endpoint = os.getenv("COSMOS_DB_ENDPOINT")
        key = os.getenv("COSMOS_DB_KEY")
        database_name = "askit4caredb"
        container_name = "sessionscontainer"

        # Initialize the Cosmos DB client
        self.client = CosmosClient(endpoint, key)
        self.database = self.client.get_database_client(database_name)
        self.container = self.database.get_container_client(container_name)

    def get_thread_data(self, from_number):
        """
        Retrieves thread data for a given phone number from Cosmos DB.

        Args:
            from_number (str): The user's phone number.

        Returns:
            dict or None: The thread data if found, else None.
        """
        try:
            # Query Cosmos DB for the thread data
            query = f"SELECT * FROM c WHERE c.id = '{from_number}'"
            items = list(self.container.query_items(query, enable_cross_partition_query=True))
            if items:
                logging.info(f"Thread data found for {from_number}.")
                return items[0]
            else:
                logging.info(f"No thread data found for {from_number}.")
                return None
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"Error querying Cosmos DB: {e}")
            return None

    def create_or_update_thread(self, thread_id, from_number):
        """
        Creates or updates the thread data for a given phone number in Cosmos DB.

        Args:
            thread_id (str): The thread ID associated with the conversation.
            from_number (str): The user's phone number.
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            item = {
                "id": from_number,
                "thread_id": thread_id,
                "created_date": now,
                "last_interaction": now
            }
            self.container.upsert_item(item)
            logging.info(f"Thread data updated for {from_number}.")
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"Error upserting item in Cosmos DB: {e}")

    def delete_thread(self, thread_data):
        """
        Deletes the thread data for a given user from Cosmos DB.

        Args:
            thread_data (dict): The thread data to delete.
        """
        try:
            self.container.delete_item(thread_data['id'], partition_key=thread_data['id'])
            logging.info(f"Thread data deleted for {thread_data['id']}.")
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"Error deleting item from Cosmos DB: {e}")