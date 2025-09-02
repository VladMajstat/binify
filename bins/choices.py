# Категорія bin
CATEGORY_CHOICES = [
    ('NONE', 'Без категорії'),
    ('Cryptocurrency', 'Криптовалюта'),
    ('Cybersecurity', 'Кібербезпека'),
    ('Fixit', 'Виправлення'),
    ('Food', 'Їжа'),
    ('Gaming', 'Ігри'),
    ('Haiku', 'Хайку'),
    ('Help', 'Допомога'),
    ('History', 'Історія'),
    ('Housing', 'Житло'),
    ('Jokes', 'Жарти'),
    ('legal', 'Юридичні питання'),
    ('Money', 'Гроші'),
    ('Movies', 'Фільми'),
    ('Music', 'Музика'),
    ('Pets', 'Домашні тварини'),
    ('Photos', 'Фотографії'),
    ('Science', 'Наука'),
    ('Software', 'Програмне забезпечення'),
    ('Source Code', 'Вихідний код'),
    ('Spirit', 'Дух'),
    ('Sport', 'Спорт'),
    ('Travel', 'Подорожі'),
    ('TW', 'Телебачення'),
    ('Writing', 'Письмо'),
]


    # Мова для підсвітки синтаксису
LANGUAGE_CHOICES = [
    ('none', 'Без мови'),
    ('c', 'C'),
    ('c#', 'C#'),
    ('cpp', 'C++'),
    ('css', 'CSS'),
    ('html', 'HTML'),
    ('java', 'Java'),
    ('javascript', 'JavaScript'),
    ('lua', 'Lua'),
    ('objective-c', 'Objective-C'),
    ('php', 'PHP'),
    ('perl', 'Perl'),
    ('python', 'Python'),
    ('ruby', 'Ruby'),
    ('swift', 'Swift'),
]

    # Термін дії bin
EXPIRY_CHOICES = [
    ('never', 'Ніколи'),
    ('1m', '1 хвилина'),
    ('1h', '1 година'),
    ('12h', '12 годин'),
    ('1d', '1 день'),
    ('7d', '7 днів'),
    ('2w', '2 тижні'),
    ('30d', '30 днів'),
    ('6mo', '6 місяців'),
    ('1y', '1 рік'),
]

    # Доступність bin
ACCESS_CHOICES = [
    ('public', 'Публічний'),
    ('private', 'Приватний'),
]