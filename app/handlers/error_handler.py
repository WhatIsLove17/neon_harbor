# from aiogram import BaseMiddleware, types
# from aiogram.dispatcher.handler import CancelHandler
# from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

# class ErrorHandlerMiddleware(LifetimeControllerMiddleware):
#     skip_patterns = ['error']

#     def __init__(self):
#         super().__init__()

#     async def handle_error(self, *args, **kwargs):
#         raise CancelHandler()

#     async def pre_process(self, obj, data, *args):
#         try:
#             return await super().pre_process(obj, data, *args)
#         except Exception as e:
#             if isinstance(obj, types.Message):
#                 await obj.answer('Произошла ошибка, пожалуйста, попробуйте позже.')
#             print(f"Exception: {e}")
#             raise CancelHandler()  # Остановка дальнейшей обработки обновления

#     async def post_process(self, obj, data, *args):
#         return await super().post_process(obj, data, *args)
