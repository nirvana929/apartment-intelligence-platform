-- AptGuide RAG MVP seed. Local/test only.
-- Total: 119 rooms (to reach 150 target)
-- Target districts: 天河区(30), 越秀区(22), 海珠区(26), 番禺区(19), 白云区(22)

START TRANSACTION;

-- ============================================================
-- 1. Insert seed apartments (20 apartments across 5 districts)
-- ============================================================

-- 天河区 apartments (5 apartments)
INSERT INTO apartment_info (id, name, introduction, province_id, province_name, city_id, city_name, district_id, district_name, address_detail, phone, latitude, longitude, is_release, is_deleted, create_time, update_time) VALUES
(10001, '天河智慧城公寓', '位于天河区智慧城，周边科技企业众多，适合IT从业者', 44, '广东省', 2, '广州市', 1, '天河区', '天河区高普路100号', '13800138001', 23.123456, 113.234567, 1, 0, NOW(), NOW()),
(10002, '珠江新城白领公寓', '靠近珠江新城地铁站，交通便利，周边商业配套完善', 44, '广东省', 2, '广州市', 1, '天河区', '天河区花城大道200号', '13800138002', 23.124567, 113.235678, 1, 0, NOW(), NOW()),
(10003, '天河公园学寓', '毗邻天河公园，环境优美，适合考研和学习', 44, '广东省', 2, '广州市', 1, '天河区', '天河区中山大道300号', '13800138003', 23.125678, 113.236789, 1, 0, NOW(), NOW()),
(10004, '体育中心青年社区', '靠近天河体育中心，运动设施齐全，年轻人聚集地', 44, '广东省', 2, '广州市', 1, '天河区', '天河区天河路400号', '13800138004', 23.126789, 113.237890, 1, 0, NOW(), NOW()),
(10005, '五山学生公寓', '华南理工大学附近，学术氛围浓厚，适合学生和考研族', 44, '广东省', 2, '广州市', 1, '天河区', '天河区五山路500号', '13800138005', 23.127890, 113.238901, 1, 0, NOW(), NOW());

-- 越秀区 apartments (4 apartments)
INSERT INTO apartment_info (id, name, introduction, province_id, province_name, city_id, city_name, district_id, district_name, address_detail, phone, latitude, longitude, is_release, is_deleted, create_time, update_time) VALUES
(10006, '越秀老城温馨居', '位于越秀区老城区，生活配套成熟，交通便利', 44, '广东省', 2, '广州市', 2, '越秀区', '越秀区中山六路100号', '13800138006', 23.128901, 113.239012, 1, 0, NOW(), NOW()),
(10007, '北京路步行街公寓', '紧邻北京路步行街，购物娱乐便利，适合年轻人', 44, '广东省', 2, '广州市', 2, '越秀区', '越秀区北京路200号', '13800138007', 23.129012, 113.240123, 1, 0, NOW(), NOW()),
(10008, '越秀公园旁公寓', '靠近越秀公园，环境宜人，适合注重生活品质的租客', 44, '广东省', 2, '广州市', 2, '越秀区', '越秀区解放北路300号', '13800138008', 23.130123, 113.241234, 1, 0, NOW(), NOW()),
(10009, '东风东路白领居', '东风东路上，写字楼众多，适合上班族', 44, '广东省', 2, '广州市', 2, '越秀区', '越秀区东风东路400号', '13800138009', 23.131234, 113.242345, 1, 0, NOW(), NOW());

-- 海珠区 apartments (5 apartments)
INSERT INTO apartment_info (id, name, introduction, province_id, province_name, city_id, city_name, district_id, district_name, address_detail, phone, latitude, longitude, is_release, is_deleted, create_time, update_time) VALUES
(10010, '琶洲会展公寓', '靠近琶洲会展中心，参展商务人士首选', 44, '广东省', 2, '广州市', 3, '海珠区', '海珠区新港东路100号', '13800138010', 23.132345, 113.243456, 1, 0, NOW(), NOW()),
(10011, '中山大学旁学寓', '中山大学附近，学术氛围浓厚，适合考研学生', 44, '广东省', 2, '广州市', 3, '海珠区', '海珠区新港西路200号', '13800138011', 23.133456, 113.244567, 1, 0, NOW(), NOW()),
(10012, '江南西商圈公寓', '江南西商圈内，购物餐饮便利，生活配套完善', 44, '广东省', 2, '广州市', 3, '海珠区', '海珠区江南大道中300号', '13800138012', 23.134567, 113.245678, 1, 0, NOW(), NOW()),
(10013, '客村地铁站公寓', '客村地铁站上盖，交通极其便利，通勤首选', 44, '广东省', 2, '广州市', 3, '海珠区', '海珠区新港中路400号', '13800138013', 23.135678, 113.246789, 1, 0, NOW(), NOW()),
(10014, '海珠湖畔居', '靠近海珠湖湿地公园，环境优美，适合注重生活品质的租客', 44, '广东省', 2, '广州市', 3, '海珠区', '海珠区广州大道南500号', '13800138014', 23.136789, 113.247890, 1, 0, NOW(), NOW());

-- 番禺区 apartments (3 apartments, 补充19个房间)
INSERT INTO apartment_info (id, name, introduction, province_id, province_name, city_id, city_name, district_id, district_name, address_detail, phone, latitude, longitude, is_release, is_deleted, create_time, update_time) VALUES
(10015, '大学城青年社区', '广州大学城内，学生和年轻创业者聚集地', 44, '广东省', 2, '广州市', 4, '番禺区', '番禺区大学城中环西路100号', '13800138015', 23.137890, 113.248901, 1, 0, NOW(), NOW()),
(10016, '万博商圈白领居', '万博商圈内，商业配套完善，适合上班族', 44, '广东省', 2, '广州市', 4, '番禺区', '番禺区番禺大道北200号', '13800138016', 23.138901, 113.249012, 1, 0, NOW(), NOW()),
(10017, '市桥老城温馨居', '市桥老城区，生活气息浓厚，租金实惠', 44, '广东省', 2, '广州市', 4, '番禺区', '番禺区市桥街大北路300号', '13800138017', 23.139012, 113.250123, 1, 0, NOW(), NOW());

-- 白云区 apartments (3 apartments)
INSERT INTO apartment_info (id, name, introduction, province_id, province_name, city_id, city_name, district_id, district_name, address_detail, phone, latitude, longitude, is_release, is_deleted, create_time, update_time) VALUES
(10018, '白云新城白领公寓', '白云新城核心区，新建小区，环境优美', 44, '广东省', 2, '广州市', 5, '白云区', '白云区云城东路100号', '13800138018', 23.140123, 113.251234, 1, 0, NOW(), NOW()),
(10019, '嘉禾望岗地铁公寓', '嘉禾望岗地铁站附近，2号线和3号线交汇，交通便利', 44, '广东省', 2, '广州市', 5, '白云区', '白云区嘉禾望岗大道200号', '13800138019', 23.141234, 113.252345, 1, 0, NOW(), NOW()),
(10020, '白云山脚下居', '靠近白云山风景区，空气清新，适合喜欢自然的租客', 44, '广东省', 2, '广州市', 5, '白云区', '白云区白云大道南300号', '13800138020', 23.142345, 113.253456, 1, 0, NOW(), NOW());

-- ============================================================
-- 2. Insert seed rooms (119 rooms)
-- ============================================================

-- 天河区 rooms (30 rooms, 5 apartments × 6 rooms each)
INSERT INTO room_info (id, room_number, rent, apartment_id, is_release, is_deleted, create_time, update_time) VALUES
-- 天河智慧城公寓 (10001)
(200001, '101', 2800.00, 10001, 1, 0, NOW(), NOW()),
(200002, '102', 3000.00, 10001, 1, 0, NOW(), NOW()),
(200003, '201', 3200.00, 10001, 1, 0, NOW(), NOW()),
(200004, '202', 3500.00, 10001, 1, 0, NOW(), NOW()),
(200005, '301', 3800.00, 10001, 1, 0, NOW(), NOW()),
(200006, '302', 4200.00, 10001, 1, 0, NOW(), NOW()),
-- 珠江新城白领公寓 (10002)
(200007, '101', 3500.00, 10002, 1, 0, NOW(), NOW()),
(200008, '102', 3800.00, 10002, 1, 0, NOW(), NOW()),
(200009, '201', 4000.00, 10002, 1, 0, NOW(), NOW()),
(200010, '202', 4200.00, 10002, 1, 0, NOW(), NOW()),
(200011, '301', 4500.00, 10002, 1, 0, NOW(), NOW()),
(200012, '302', 4800.00, 10002, 1, 0, NOW(), NOW()),
-- 天河公园学寓 (10003)
(200013, '101', 1800.00, 10003, 1, 0, NOW(), NOW()),
(200014, '102', 2000.00, 10003, 1, 0, NOW(), NOW()),
(200015, '201', 2200.00, 10003, 1, 0, NOW(), NOW()),
(200016, '202', 2500.00, 10003, 1, 0, NOW(), NOW()),
(200017, '301', 2800.00, 10003, 1, 0, NOW(), NOW()),
(200018, '302', 3000.00, 10003, 1, 0, NOW(), NOW()),
-- 体育中心青年社区 (10004)
(200019, '101', 2200.00, 10004, 1, 0, NOW(), NOW()),
(200020, '102', 2500.00, 10004, 1, 0, NOW(), NOW()),
(200021, '201', 2800.00, 10004, 1, 0, NOW(), NOW()),
(200022, '202', 3000.00, 10004, 1, 0, NOW(), NOW()),
(200023, '301', 3200.00, 10004, 1, 0, NOW(), NOW()),
(200024, '302', 3500.00, 10004, 1, 0, NOW(), NOW()),
-- 五山学生公寓 (10005)
(200025, '101', 1500.00, 10005, 1, 0, NOW(), NOW()),
(200026, '102', 1800.00, 10005, 1, 0, NOW(), NOW()),
(200027, '201', 2000.00, 10005, 1, 0, NOW(), NOW()),
(200028, '202', 2200.00, 10005, 1, 0, NOW(), NOW()),
(200029, '301', 2500.00, 10005, 1, 0, NOW(), NOW()),
(200030, '302', 2800.00, 10005, 1, 0, NOW(), NOW());

-- 越秀区 rooms (22 rooms)
INSERT INTO room_info (id, room_number, rent, apartment_id, is_release, is_deleted, create_time, update_time) VALUES
-- 越秀老城温馨居 (10006)
(200031, '101', 1800.00, 10006, 1, 0, NOW(), NOW()),
(200032, '102', 2000.00, 10006, 1, 0, NOW(), NOW()),
(200033, '201', 2200.00, 10006, 1, 0, NOW(), NOW()),
(200034, '202', 2500.00, 10006, 1, 0, NOW(), NOW()),
(200035, '301', 2800.00, 10006, 1, 0, NOW(), NOW()),
(200036, '302', 3000.00, 10006, 1, 0, NOW(), NOW()),
-- 北京路步行街公寓 (10007)
(200037, '101', 2500.00, 10007, 1, 0, NOW(), NOW()),
(200038, '102', 2800.00, 10007, 1, 0, NOW(), NOW()),
(200039, '201', 3000.00, 10007, 1, 0, NOW(), NOW()),
(200040, '202', 3200.00, 10007, 1, 0, NOW(), NOW()),
(200041, '301', 3500.00, 10007, 1, 0, NOW(), NOW()),
(200042, '302', 3800.00, 10007, 1, 0, NOW(), NOW()),
-- 越秀公园旁公寓 (10008)
(200043, '101', 2200.00, 10008, 1, 0, NOW(), NOW()),
(200044, '102', 2500.00, 10008, 1, 0, NOW(), NOW()),
(200045, '201', 2800.00, 10008, 1, 0, NOW(), NOW()),
(200046, '202', 3000.00, 10008, 1, 0, NOW(), NOW()),
(200047, '301', 3200.00, 10008, 1, 0, NOW(), NOW()),
-- 东风东路白领居 (10009)
(200048, '101', 2800.00, 10009, 1, 0, NOW(), NOW()),
(200049, '102', 3000.00, 10009, 1, 0, NOW(), NOW()),
(200050, '201', 3200.00, 10009, 1, 0, NOW(), NOW()),
(200051, '202', 3500.00, 10009, 1, 0, NOW(), NOW()),
(200052, '301', 3800.00, 10009, 1, 0, NOW(), NOW());

-- 海珠区 rooms (26 rooms)
INSERT INTO room_info (id, room_number, rent, apartment_id, is_release, is_deleted, create_time, update_time) VALUES
-- 琶洲会展公寓 (10010)
(200053, '101', 2800.00, 10010, 1, 0, NOW(), NOW()),
(200054, '102', 3000.00, 10010, 1, 0, NOW(), NOW()),
(200055, '201', 3200.00, 10010, 1, 0, NOW(), NOW()),
(200056, '202', 3500.00, 10010, 1, 0, NOW(), NOW()),
(200057, '301', 3800.00, 10010, 1, 0, NOW(), NOW()),
(200058, '302', 4200.00, 10010, 1, 0, NOW(), NOW()),
-- 中山大学旁学寓 (10011)
(200059, '101', 1500.00, 10011, 1, 0, NOW(), NOW()),
(200060, '102', 1800.00, 10011, 1, 0, NOW(), NOW()),
(200061, '201', 2000.00, 10011, 1, 0, NOW(), NOW()),
(200062, '202', 2200.00, 10011, 1, 0, NOW(), NOW()),
(200063, '301', 2500.00, 10011, 1, 0, NOW(), NOW()),
(200064, '302', 2800.00, 10011, 1, 0, NOW(), NOW()),
-- 江南西商圈公寓 (10012)
(200065, '101', 2200.00, 10012, 1, 0, NOW(), NOW()),
(200066, '102', 2500.00, 10012, 1, 0, NOW(), NOW()),
(200067, '201', 2800.00, 10012, 1, 0, NOW(), NOW()),
(200068, '202', 3000.00, 10012, 1, 0, NOW(), NOW()),
(200069, '301', 3200.00, 10012, 1, 0, NOW(), NOW()),
-- 客村地铁站公寓 (10013)
(200070, '101', 2500.00, 10013, 1, 0, NOW(), NOW()),
(200071, '102', 2800.00, 10013, 1, 0, NOW(), NOW()),
(200072, '201', 3000.00, 10013, 1, 0, NOW(), NOW()),
(200073, '202', 3200.00, 10013, 1, 0, NOW(), NOW()),
(200074, '301', 3500.00, 10013, 1, 0, NOW(), NOW()),
(200075, '302', 3800.00, 10013, 1, 0, NOW(), NOW()),
-- 海珠湖畔居 (10014)
(200076, '101', 2000.00, 10014, 1, 0, NOW(), NOW()),
(200077, '102', 2200.00, 10014, 1, 0, NOW(), NOW()),
(200078, '201', 2500.00, 10014, 1, 0, NOW(), NOW());

-- 番禺区 rooms (19 rooms, 补充到38个)
INSERT INTO room_info (id, room_number, rent, apartment_id, is_release, is_deleted, create_time, update_time) VALUES
-- 大学城青年社区 (10015)
(200079, '101', 800.00, 10015, 1, 0, NOW(), NOW()),
(200080, '102', 950.00, 10015, 1, 0, NOW(), NOW()),
(200081, '201', 1100.00, 10015, 1, 0, NOW(), NOW()),
(200082, '202', 1200.00, 10015, 1, 0, NOW(), NOW()),
(200083, '301', 1400.00, 10015, 1, 0, NOW(), NOW()),
(200084, '302', 1600.00, 10015, 1, 0, NOW(), NOW()),
-- 万博商圈白领居 (10016)
(200085, '101', 1800.00, 10016, 1, 0, NOW(), NOW()),
(200086, '102', 2000.00, 10016, 1, 0, NOW(), NOW()),
(200087, '201', 2200.00, 10016, 1, 0, NOW(), NOW()),
(200088, '202', 2500.00, 10016, 1, 0, NOW(), NOW()),
(200089, '301', 2800.00, 10016, 1, 0, NOW(), NOW()),
(200090, '302', 3000.00, 10016, 1, 0, NOW(), NOW()),
-- 市桥老城温馨居 (10017)
(200091, '101', 1000.00, 10017, 1, 0, NOW(), NOW()),
(200092, '102', 1200.00, 10017, 1, 0, NOW(), NOW()),
(200093, '201', 1400.00, 10017, 1, 0, NOW(), NOW()),
(200094, '202', 1600.00, 10017, 1, 0, NOW(), NOW()),
(200095, '301', 1800.00, 10017, 1, 0, NOW(), NOW()),
(200096, '302', 2000.00, 10017, 1, 0, NOW(), NOW()),
(200097, '401', 2200.00, 10017, 1, 0, NOW(), NOW());

-- 白云区 rooms (22 rooms)
INSERT INTO room_info (id, room_number, rent, apartment_id, is_release, is_deleted, create_time, update_time) VALUES
-- 白云新城白领公寓 (10018)
(200098, '101', 2000.00, 10018, 1, 0, NOW(), NOW()),
(200099, '102', 2200.00, 10018, 1, 0, NOW(), NOW()),
(200100, '201', 2500.00, 10018, 1, 0, NOW(), NOW()),
(200101, '202', 2800.00, 10018, 1, 0, NOW(), NOW()),
(200102, '301', 3000.00, 10018, 1, 0, NOW(), NOW()),
(200103, '302', 3200.00, 10018, 1, 0, NOW(), NOW()),
(200104, '401', 3500.00, 10018, 1, 0, NOW(), NOW()),
-- 嘉禾望岗地铁公寓 (10019)
(200105, '101', 1500.00, 10019, 1, 0, NOW(), NOW()),
(200106, '102', 1800.00, 10019, 1, 0, NOW(), NOW()),
(200107, '201', 2000.00, 10019, 1, 0, NOW(), NOW()),
(200108, '202', 2200.00, 10019, 1, 0, NOW(), NOW()),
(200109, '301', 2500.00, 10019, 1, 0, NOW(), NOW()),
(200110, '302', 2800.00, 10019, 1, 0, NOW(), NOW()),
-- 白云山脚下居 (10020)
(200111, '101', 1800.00, 10020, 1, 0, NOW(), NOW()),
(200112, '102', 2000.00, 10020, 1, 0, NOW(), NOW()),
(200113, '201', 2200.00, 10020, 1, 0, NOW(), NOW()),
(200114, '202', 2500.00, 10020, 1, 0, NOW(), NOW()),
(200115, '301', 2800.00, 10020, 1, 0, NOW(), NOW()),
(200116, '302', 3000.00, 10020, 1, 0, NOW(), NOW()),
(200117, '401', 3200.00, 10020, 1, 0, NOW(), NOW()),
(200118, '402', 3500.00, 10020, 1, 0, NOW(), NOW()),
(200119, '501', 3800.00, 10020, 1, 0, NOW(), NOW());

-- ============================================================
-- 3. Connect rooms to labels (tags)
-- ============================================================

-- 为种子房间分配标签，确保标签覆盖目标
-- 标签 ID: 1=近地铁, 2=近公交, 3=有电梯, 4=停车场, 5=朝南, 6=朝北, 7=朝东, 10=朝西, 15=独卫, 16=阳台

-- 近地铁 (目标: 55个房间)
INSERT INTO room_label (room_id, label_id, is_deleted, create_time, update_time)
SELECT r.id, 1, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0
  AND (
    (r.apartment_id IN (10001, 10002, 10004, 10007, 10010, 10013, 10019))  -- 地铁附近的公寓
    OR (r.id % 3 = 0)  -- 其他公寓的部分房间
  )
LIMIT 55;

-- 朝南 (目标: 45个房间)
INSERT INTO room_label (room_id, label_id, is_deleted, create_time, update_time)
SELECT r.id, 5, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0
  AND r.id % 3 = 0
LIMIT 45;

-- 独卫 (目标: 60个房间)
INSERT INTO room_label (room_id, label_id, is_deleted, create_time, update_time)
SELECT r.id, 15, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0
  AND r.id % 2 = 0
LIMIT 60;

-- 阳台 (为部分房间添加)
INSERT INTO room_label (room_id, label_id, is_deleted, create_time, update_time)
SELECT r.id, 16, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0
  AND r.id % 4 = 0
LIMIT 30;

-- ============================================================
-- 4. Connect rooms to facilities
-- ============================================================

-- 设施 ID: 28=空调, 29=洗衣机, 30=冰箱, 48=书桌, 49=WIFI, 50=床, 51=沙发, 52=微波炉, 53=油烟机

-- 空调 (所有房间)
INSERT INTO room_facility (room_id, facility_id, is_deleted, create_time, update_time)
SELECT r.id, 28, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0;

-- WIFI (所有房间)
INSERT INTO room_facility (room_id, facility_id, is_deleted, create_time, update_time)
SELECT r.id, 49, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0;

-- 床 (所有房间)
INSERT INTO room_facility (room_id, facility_id, is_deleted, create_time, update_time)
SELECT r.id, 50, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0;

-- 洗衣机 (大部分房间)
INSERT INTO room_facility (room_id, facility_id, is_deleted, create_time, update_time)
SELECT r.id, 29, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0
  AND r.id % 3 != 0;

-- 书桌 (适合考研的房间)
INSERT INTO room_facility (room_id, facility_id, is_deleted, create_time, update_time)
SELECT r.id, 48, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0
  AND r.apartment_id IN (10003, 10005, 10011, 10015);  -- 学生公寓

-- ============================================================
-- 5. Connect rooms to payment types
-- ============================================================

-- 支付类型 ID: 6=月付, 7=季付, 8=半年付, 10=年付

-- 月付 (目标: 80个房间)
INSERT INTO room_payment_type (room_id, payment_type_id, is_deleted, create_time, update_time)
SELECT r.id, 6, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0
  AND r.id % 2 = 0
LIMIT 80;

-- 季付 (大部分房间)
INSERT INTO room_payment_type (room_id, payment_type_id, is_deleted, create_time, update_time)
SELECT r.id, 7, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0;

-- 半年付 (部分房间)
INSERT INTO room_payment_type (room_id, payment_type_id, is_deleted, create_time, update_time)
SELECT r.id, 8, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0
  AND r.rent >= 2000
LIMIT 50;

-- 年付 (高端房间)
INSERT INTO room_payment_type (room_id, payment_type_id, is_deleted, create_time, update_time)
SELECT r.id, 10, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0
  AND r.rent >= 3000
LIMIT 30;

-- ============================================================
-- 6. Connect rooms to lease terms
-- ============================================================

-- 租期 ID: 1=1个月, 3=3个月, 4=6个月, 6=12个月

-- 1个月租期 (目标: 25个房间，可短租)
INSERT INTO room_lease_term (room_id, lease_term_id, is_deleted, create_time, update_time)
SELECT r.id, 1, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0
  AND r.id % 5 = 0
LIMIT 25;

-- 3个月租期 (大部分房间)
INSERT INTO room_lease_term (room_id, lease_term_id, is_deleted, create_time, update_time)
SELECT r.id, 3, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0;

-- 6个月租期 (大部分房间)
INSERT INTO room_lease_term (room_id, lease_term_id, is_deleted, create_time, update_time)
SELECT r.id, 4, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0;

-- 12个月租期 (大部分房间)
INSERT INTO room_lease_term (room_id, lease_term_id, is_deleted, create_time, update_time)
SELECT r.id, 6, 0, NOW(), NOW()
FROM room_info r
WHERE r.id BETWEEN 200001 AND 200119
  AND r.is_deleted = 0;

COMMIT;
