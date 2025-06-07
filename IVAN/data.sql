-- Вставка ролей
INSERT INTO role (name) VALUES
('admin'),
('florist'),
('courier'),
('manager'),
('accountant');

-- Вставка пользователей
INSERT INTO "user" (username, password, role_id, can_edit, can_delete, can_view) VALUES
('director', 'director', 1, 1, 1, 1),
('florist1', 'florist123', 2, 1, 0, 1),
('courier1', 'courier123', 3, 0, 0, 1),
('manager', 'manager', 4, 1, 1, 1),
('accountant1', 'account123', 5, 0, 0, 1);

-- Вставка единиц измерения
INSERT INTO unit (name) VALUES
('шт'),
('букет'),
('упаковка'),
('кг'),
('метр');

-- Вставка типов продукции
INSERT INTO product_type (name) VALUES
('Срезанные цветы'),
('Горшечные растения'),
('Аксессуары'),
('Упаковочные материалы'),
('Удобрения');

-- Вставка условий поставки
INSERT INTO delivery_condition (name) VALUES
('Полная предоплата'),
('Оплата при получении'),
('Кредит 15 дней'),
('Кредит 30 дней'),
('Консигнация');

-- Вставка поставщиков
INSERT INTO supplier (inn, name, phone) VALUES
('123456789012', 'ООО Цветочная поляна', '+79991234567'),
('987654321098', 'АО Розовый сад', '+79997654321'),
('456789123456', 'ЗАО Орхидея', '+79993456789'),
('789123456789', 'ИП Лилия', '+79990123456'),
('321654987123', 'ООО Флора', '+79998765432');

-- Вставка продукции
INSERT INTO product (name, unit_id, type_id, condition_id) VALUES
('Роза красная', 1, 1, 1),
('Орхидея в горшке', 1, 2, 3),
('Лента атласная', 5, 3, 2),
('Упаковочная бумага', 3, 4, 2),
('Удобрение для цветов', 4, 5, 4);

-- Вставка поставок
INSERT INTO delivery (supplier_id, planned_date, actual_date, doc_number) VALUES
(1, '2025-06-01', '2025-06-01', 'FLW001'),
(2, '2025-06-02', '2025-06-02', 'FLW002'),
(3, '2025-06-03', NULL, 'FLW003'),
(4, '2025-06-03', '2025-06-03', 'FLW004'),
(5, '2025-06-04', NULL, 'FLW005');

-- Вставка продуктов в поставках
INSERT INTO product_in_delivery (product_id, delivery_id, planned_quantity, planned_price, actual_quantity, actual_price, rejection_reason) VALUES
(1, 1, 200, 60, 200, 60, NULL),
(2, 2, 15, 2500, 14, 2500, 'Поврежден горшок'),
(3, 3, 100, 25, NULL, NULL, 'Низкое качество'),
(4, 4, 50, 150, 50, 150, NULL),
(5, 5, 20, 300, 18, 300, 'Неполная партия');