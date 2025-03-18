import aiosqlite


class QuizDatabase:
    def __init__(self, db_name: str):
        self.db_name = db_name

    async def create_table(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER)"""
            )
            await db.commit()

    async def get_quiz_index(self, user_id: str):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                "SELECT question_index FROM quiz_state WHERE user_id = (?)", (user_id,)
            ) as cursor:
                results = await cursor.fetchone()
                if results is not None:
                    return results[0]
                else:
                    return 0

    async def update_quiz_index(self, user_id: str, index: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT OR REPLACE INTO quiz_state (user_id, question_index) VALUES (?, ?)",
                (user_id, index),
            )
            await db.commit()
