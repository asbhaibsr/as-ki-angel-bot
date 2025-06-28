import time
from collections import deque
from pymongo import MongoClient
from config import MONGO_URI, MAX_LEARNING_MEMORY, PREMIUM_DURATION_MONTHS
import asyncio # Added for async compatibility

class Database:
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client.askiangel_db
            
            # Collections
            self.learning_data = self.db.learning_data
            self.premium_users = self.db.premium_users
            self.connected_groups = self.db.connected_groups
            self.user_stats = self.db.user_stats
            self.bot_settings = self.db.bot_settings # Ensure this collection exists or is handled
            
            print("MongoDB connected successfully!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    # Helper to run sync MongoDB operations in a separate thread
    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    async def get_group_learning_data(self, group_id):
        """Retrieves learning data for a specific group."""
        data = await self._run_in_executor(self.learning_data.find_one, {'_id': group_id})
        if data:
            # Convert lists back to deques
            data['phrases'] = deque(data.get('phrases', []), maxlen=MAX_LEARNING_MEMORY)
            data['stickers'] = deque(data.get('stickers', []), maxlen=MAX_LEARNING_MEMORY)
            data['response_patterns'] = data.get('response_patterns', {})
        else:
            # Create new learning data structure
            data = {
                '_id': group_id,
                'phrases': deque(maxlen=MAX_LEARNING_MEMORY),
                'stickers': deque(maxlen=MAX_LEARNING_MEMORY),
                'response_patterns': {},
                'last_active': time.time(),
                'created_at': time.time()
            }
            # Save initial structure
            await self._run_in_executor(self.learning_data.insert_one, {
                '_id': group_id,
                'phrases': [], # Save as list for MongoDB
                'stickers': [], # Save as list for MongoDB
                'response_patterns': {},
                'last_active': time.time(),
                'created_at': time.time()
            })
        return data

    async def save_group_learning_data(self, group_id, data):
        """Saves learning data for a specific group."""
        save_data = {
            'phrases': list(data['phrases']), # Convert deque to list for MongoDB
            'stickers': list(data['stickers']), # Convert deque to list for MongoDB
            'response_patterns': data.get('response_patterns', {}),
            'last_active': time.time()
        }
        
        await self._run_in_executor(
            self.learning_data.update_one,
            {'_id': group_id},
            {'$set': save_data},
            upsert=True
        )

    async def add_premium_user(self, user_id, months=PREMIUM_DURATION_MONTHS):
        """Adds or updates premium status for a user."""
        premium_until = time.time() + (months * 30 * 24 * 60 * 60)
        
        await self._run_in_executor(
            self.premium_users.update_one,
            {'_id': user_id},
            {'$set': {
                'premium_until': premium_until,
                'activated_at': time.time(),
                'months_purchased': months
            }},
            upsert=True
        )

    async def is_premium(self, user_id):
        """Checks if a user has an active premium subscription."""
        from config import BOT_OWNER_ID # Import here to avoid circular dependency
        
        if user_id == BOT_OWNER_ID:
            return True
            
        try:
            user_data = await self._run_in_executor(self.premium_users.find_one, {'_id': user_id})
            if user_data and user_data.get('premium_until', 0) > time.time():
                return True
        except Exception as e:
            print(f"Error checking premium status for {user_id}: {e}")
            
        return False

    async def get_premium_info(self, user_id):
        """Gets premium subscription info for a user."""
        user_data = await self._run_in_executor(self.premium_users.find_one, {'_id': user_id})
        if user_data:
            return {
                'is_premium': user_data.get('premium_until', 0) > time.time(),
                'expires_at': user_data.get('premium_until', 0),
                'activated_at': user_data.get('activated_at', 0),
                'months_purchased': user_data.get('months_purchased', 0)
            }
        return None

    async def get_connected_group_settings(self, chat_id):
        """Retrieves settings for a connected group."""
        return await self._run_in_executor(self.connected_groups.find_one, {'_id': chat_id})

    async def save_connected_group_settings(self, chat_id, settings_data):
        """Saves settings for a connected group."""
        settings_data['last_updated'] = time.time()
        
        await self._run_in_executor(
            self.connected_groups.update_one,
            {'_id': chat_id},
            {'$set': settings_data},
            upsert=True
        )

    async def update_user_stats(self, user_id, action):
        """Updates user interaction statistics."""
        await self._run_in_executor(
            self.user_stats.update_one,
            {'_id': user_id},
            {
                '$inc': {f'actions.{action}': 1, 'total_interactions': 1},
                '$set': {'last_active': time.time()} # Removed first_seen from $set, it should be set only on first create
            },
            upsert=True
        )
        # For first_seen, we might need a separate check or ensure it's set only once on upsert
        user_data = await self._run_in_executor(self.user_stats.find_one, {'_id': user_id})
        if not user_data.get('first_seen'):
            await self._run_in_executor(self.user_stats.update_one,
                {'_id': user_id},
                {'$set': {'first_seen': time.time()}}
            )


    async def get_bot_stats(self):
        """Gets overall bot statistics."""
        total_users = await self._run_in_executor(self.user_stats.count_documents, {})
        total_groups = await self._run_in_executor(self.connected_groups.count_documents, {})
        premium_users = await self._run_in_executor(self.premium_users.count_documents, {
            'premium_until': {'$gt': time.time()}
        })
        learning_groups = await self._run_in_executor(self.learning_data.count_documents, {})
        
        return {
            'total_users': total_users,
            'total_groups': total_groups,
            'premium_users': premium_users,
            'learning_groups': learning_groups
        }

# Global database instance
db = Database()
