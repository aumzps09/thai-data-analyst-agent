-- Thai Data Analyst Agent — seed (PostgreSQL 16)
-- Olist-style e-commerce (thaified categories) + policies
BEGIN;

DROP TABLE IF EXISTS order_items, orders, products, customers, policies;

CREATE TABLE customers (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT NOT NULL,
  email TEXT,
  phone TEXT
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  category_th TEXT NOT NULL,
  price NUMERIC(12,2) NOT NULL
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_id INT REFERENCES customers(id),
  order_date DATE NOT NULL,
  status TEXT NOT NULL DEFAULT 'delivered'
);

CREATE TABLE order_items (
  order_id INT REFERENCES orders(id),
  product_id INT REFERENCES products(id),
  qty INT NOT NULL DEFAULT 1,
  PRIMARY KEY (order_id, product_id)
);

CREATE TABLE policies (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  detail TEXT NOT NULL,
  updated_at DATE NOT NULL DEFAULT CURRENT_DATE
);

INSERT INTO customers (name, city, email, phone) VALUES
 ('สมชาย ใจดี', 'กรุงเทพฯ', 'somchai@example.com', '081-234-5678'),
 ('สุดา รักษ์ไทย', 'เชียงใหม่', 'suda@example.com', '089-111-2222'),
 ('ประยูร ค้าขาย', 'ขอนแก่น', 'prayoon@example.com', '043-555-6666'),
 ('มาลี ดอกไม้', 'ภูเก็ต', 'malee@example.com', '076-777-8888'),
 ('วิชัย มั่งมี', 'กรุงเทพฯ', 'wichai@example.com', '02-123-4567');

INSERT INTO products (name, category_th, price) VALUES
 ('หม้อทอดไร้น้ำมัน', 'เครื่องใช้ไฟฟ้า', 2490),
 ('พัดลม 16 นิ้ว', 'เครื่องใช้ไฟฟ้า', 1290),
 ('เสื้อยืดคอตตอน', 'แฟชั่น', 390),
 ('กางเกงยีนส์', 'แฟชั่น', 990),
 ('ข้าวหอมมะลิ 5กก.', 'อาหาร', 320),
 ('กาแฟดริป', 'อาหาร', 450),
 ('ครีมกันแดด', 'ความงาม', 590),
 ('ลิปสติก', 'ความงาม', 490);

INSERT INTO orders (customer_id, order_date, status) VALUES
 (1, CURRENT_DATE - INTERVAL '40 days', 'delivered'),
 (2, CURRENT_DATE - INTERVAL '35 days', 'delivered'),
 (3, CURRENT_DATE - INTERVAL '20 days', 'delivered'),
 (1, CURRENT_DATE - INTERVAL '10 days', 'delivered'),
 (4, CURRENT_DATE - INTERVAL '5 days', 'delivered'),
 (5, CURRENT_DATE - INTERVAL '2 days', 'pending');

INSERT INTO order_items (order_id, product_id, qty) VALUES
 (1, 1, 1), (1, 5, 2),
 (2, 3, 3), (2, 8, 1),
 (3, 2, 1), (3, 6, 2),
 (4, 4, 1), (4, 7, 2),
 (5, 1, 2), (5, 3, 5),
 (6, 5, 1);

INSERT INTO policies (title, detail) VALUES
 ('นโยบายคืนสินค้า', 'คืนได้ภายใน 14 วัน พร้อมใบเสร็จ สินค้าต้องไม่ผ่านการใช้งาน ยกเว้นหมวดอาหาร'),
 ('นโยบายส่วนลดสมาชิก', 'สมาชิกกรุงเทพฯและปริมณฑลรับส่วนลด 5% หมวดเครื่องใช้ไฟฟ้าทุกสิ้นเดือน'),
 ('นโยบายจัดส่ง', 'จัดส่งฟรีเมื่อยอดเกิน 1000 บาท ต่างจังหวัด 2-4 วันทำการ');

COMMIT;

-- 30 คำถามตัวอย่าง (ย่อ, ฉบับเต็มใน questions_gold.jsonl):
-- 1. ยอดขายหมวดเครื่องใช้ไฟฟ้าเดือนที่แล้วเท่าไหร่
-- 2. Top 5 หมวดขายดีสุดคืออะไร
-- 3. จังหวัดไหนมีลูกค้าเยอะสุด
-- 4. นโยบายคืนสินค้าคืออะไร
