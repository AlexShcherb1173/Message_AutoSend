from django.db import models


class Message(models.Model):
    """Модель сообщения, используемого в рассылках.
    Содержит тему (subject) и текст письма (body), которые используются
    при формировании контента рассылки. Каждое сообщение может быть
    связано с одной или несколькими рассылками.
    Поля:
        subject (CharField): Тема письма, отображаемая в заголовке email.
        body (TextField): Основное содержимое письма (текст сообщения).
        created_at (DateTimeField): Дата и время создания записи.
        updated_at (DateTimeField): Дата и время последнего изменения.
    Метаданные:
        verbose_name: Название модели в единственном числе.
        verbose_name_plural: Название во множественном числе.
        ordering: Сортировка по дате создания (новые — первыми).
    Пример отображения:
        >>> str(message)
        'Расписание обновлено'  # первые 80 символов темы"""

    subject = models.CharField("Тема письма", max_length=255)
    body = models.TextField("Тело письма")

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        """Метаданные модели Message."""
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        """Возвращает строковое представление сообщения.
        Если тема не указана, возвращает "(без темы)".
        Иначе обрезает тему до 80 символов для удобного отображения
        в админке и списках.
        Returns:
            str: Краткое человекочитаемое представление сообщения."""
        return self.subject[:80] or "(без темы)"