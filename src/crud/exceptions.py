class AdminNotFound(Exception):
    def __init__(self, tg_id) -> None:
        super().__init__(f'Админ с telegram_id: {tg_id} не найден!')
