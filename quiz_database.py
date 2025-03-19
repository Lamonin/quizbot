import aiosqlite


class QuizDatabase:
    def __init__(self, db_name: str):
        self.db_name = db_name

    async def create_table(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS user_quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER, score INTEGER DEFAULT 0, last_result INTEGER DEFAULT 0)"""
            )
            await db.commit()

    async def get_quiz_index(self, user_id: str):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                "SELECT question_index FROM user_quiz_state WHERE user_id = (?)", (user_id,)
            ) as cursor:
                results = await cursor.fetchone()
                if results is not None:
                    return results[0]
                else:
                    return 0

    async def update_quiz_index(self, user_id: str, index: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT OR REPLACE INTO user_quiz_state (user_id, question_index, score, last_result) VALUES (?, ?, COALESCE((SELECT score FROM user_quiz_state WHERE user_id = ?), 0), COALESCE((SELECT last_result FROM user_quiz_state WHERE user_id = ?), 0))",
                (user_id, index, user_id, user_id),
            )
            await db.commit()

    async def increment_score(self, user_id: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "UPDATE user_quiz_state SET score = score + 1 WHERE user_id = ?",
                (user_id,),
            )
            await db.commit()

    async def reset_score(self, user_id: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT OR REPLACE INTO user_quiz_state (user_id, question_index, score, last_result) VALUES (?, 0, 0, COALESCE((SELECT last_result FROM user_quiz_state WHERE user_id = ?), 0))",
                (user_id, user_id),
            )
            await db.commit()

    async def get_score(self, user_id: str):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                "SELECT score FROM user_quiz_state WHERE user_id = ?", (user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def save_result(self, user_id: str, score: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "UPDATE user_quiz_state SET last_result = ?, score = 0, question_index = 0 WHERE user_id = ?",
                (score, user_id),
            )
            await db.commit()

    async def get_all_results(self):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                "SELECT user_id, last_result FROM user_quiz_state ORDER BY last_result DESC"
            ) as cursor:
                return await cursor.fetchall()
