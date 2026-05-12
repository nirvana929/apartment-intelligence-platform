-- WeChat real rental listing import. Local/test only.
-- Includes phone numbers and WeChat IDs for local use.
-- Do not run against production.

CREATE TABLE IF NOT EXISTS external_wechat_rental_listing (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  source_type VARCHAR(32) NOT NULL DEFAULT 'WECHAT_GROUP',
  authenticity VARCHAR(32) NOT NULL DEFAULT 'REAL_POSTED',
  verification_status VARCHAR(32) NOT NULL DEFAULT 'UNVERIFIED',
  availability_status VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
  source_file VARCHAR(255) NOT NULL,
  source_group VARCHAR(128) NOT NULL,
  source_message_hash VARCHAR(80) NOT NULL,
  message_time DATETIME NULL,
  sender_alias VARCHAR(128) NULL,
  message_type VARCHAR(32) NOT NULL,
  city_name VARCHAR(64) NULL,
  district_name VARCHAR(64) NULL,
  area_label VARCHAR(128) NULL,
  metro_lines JSON NULL,
  metro_stations JSON NULL,
  layouts JSON NULL,
  rent_min INT NULL,
  rent_max INT NULL,
  payment_tags JSON NULL,
  facility_tags JSON NULL,
  rental_tags JSON NULL,
  phone_numbers JSON NULL,
  wechat_ids JSON NULL,
  contact_text TEXT NULL,
  description_text TEXT NOT NULL,
  raw_text MEDIUMTEXT NOT NULL,
  is_active TINYINT NOT NULL DEFAULT 1,
  appointable TINYINT NOT NULL DEFAULT 0,
  dedupe_key VARCHAR(80) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_external_wechat_rental_source_hash (source_message_hash),
  KEY idx_external_wechat_rental_city_district (city_name, district_name),
  KEY idx_external_wechat_rental_rent (rent_min, rent_max),
  KEY idx_external_wechat_rental_dedupe (dedupe_key)
);

INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:475019c38a33cb2009fc7817fa495956f25ae2e4cf829c909ed582f218c2f805', '2026-04-30 17:11', '林子敬15879897979', 'text', '广州市', '天河区', '黄村/棠东', '[]', '["黄村","棠东"]', '[{"layout":"单间","rent_min":480,"rent_max":null},{"layout":"一房一厅","rent_min":880,"rent_max":null},{"layout":"一房一厅","rent_min":480,"rent_max":null}]', 480, 880, '["押一付一"]', '["空调","洗衣机","冰箱","门禁","监控"]', '["房东直租","无中介费","近地铁","押一付一"]', '["15879897979"]', '["15879897979"]', '☎ 微信15879897979（免费接送看房）', '天河区黄村/棠东附近真实发布租房线索，单间480起，一房一厅880起，一房一厅480起，房东直租，无中介费，押一付一', '[烟花][烟花][烟花][烟花][烟花][烟花][烟花][烟花][烟花][烟花][烟花]
[庆祝]天河智慧城，天河老实房东[庆祝]
小新塘自建房 民用水电 押一付一

🔥精装大单间480～
🔥精装一房一厅880～
🚄地铁直达【神舟路】【科学城】【大观南路】【苏元】【萝岗】【黄村】【广百广场】【万科云城】【棠东】

✅ 配套完善：新塘街道，岑村，奥体中心，又托邦，广百各大商超市，美食街
✅ 房源亮点：精装修配空调、洗衣机、冰箱，独立厨房卫生间，WiFi覆盖 
✅ 安全省心：24小时监控，电子门禁，房东直租无中介费 

☎ 微信15879897979（免费接送看房）', 1, 0, 'sha256:cb10c26b47a60bafdae639dc1b0a498ebc025b47863bb695c3d882553263e281') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:3086d536c1a7016445b9f2a0f10bc2d9402f757e7de6c5af048b31439536214c', '2026-04-30 10:09', '胜9 18826428858', 'text', '广州市', '天河区', '科韵路/体育西/上社', '["11号线"]', '["上社","科韵路","体育西","北京路"]', '[{"layout":"单间","rent_min":499,"rent_max":null},{"layout":"一房一厅","rent_min":699,"rent_max":999}]', 499, 999, '[]', '[]', '["近地铁","家电齐全"]', '["18320287268","18826428858"]', '[]', '微信☎️：18320287268', '天河区科韵路/体育西/上社附近真实发布租房线索，单间499起，一房一厅699-999', '[玫瑰][玫瑰][玫瑰]租房不踩坑:
1：房租价格带“起”字是最贵
2：朋友圈有租房信息是中介，只有专业中介才经常发圈
3：打扮漂亮整齐是中介、套路多、本房东穿拖鞋加随便衣服
4：答非所问先让过来看房的套路多
5：租房找我，没有套路、明码标价，有啥说啥

天河区上社、体育中心位置最好大街、旺街精装新房出租，没有巷子、楼下各种购物方便，最大天河公园休闲、娱乐、散步、等等…

精装单间💰499一699元/月，民用电0.88/度

一房一厅💰699至999元/月，民用水5元/吨

体育中心、岗顶、体育西、天河城、正佳、北京路、天河软件园、沃尔沃、天盈创业园、科韵路、师范大学、南医三院、天河东、天河北、科韵路、龙口西、林和西、等等居住……

地铁🚇11号线华景路/五号线科韵路站，
公交车🚌BRT快速直达天河任何地方，设备齐全，拎包入住，
微信☎️：18320287268
18826428858', 1, 0, 'sha256:25c571b1b666c90060b06476dd20d1f5e4cc0cb5a633cddd6522162673bedf2e') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_消息.txt', '广州租房群A134-禁中介', 'sha256:bf2d6718e5a09eb5202408f445e4a4c65526e4b0eb62a601543aeab158b05bf9', '2026-05-06 16:29', 'sam房东直租', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '["4号线","13号线","21号线"]', '["黄村","珠村","科韵路","员村","体育西","珠江新城"]', '[{"layout":"单间","rent_min":499,"rent_max":null},{"layout":"一房一厅","rent_min":699,"rent_max":null},{"layout":"两房一厅","rent_min":899,"rent_max":null},{"layout":"一房一厅","rent_min":499,"rent_max":null},{"layout":"两房一厅","rent_min":699,"rent_max":null}]', 499, 899, '["押一付一"]', '["电梯"]', '["房东直租","无中介费","近地铁","民水民电","押一付一","家电齐全"]', '["19924398279"]', '["19924398279"]', '📩微信：19924398279', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间499起，一房一厅699起，两房一厅899起，一房一厅499起，房东直租，无中介费，民水民电，押一付一，家电齐全', '🔥天河黄村·房东直租·无中介费

【5-8分钟到地铁口】
✅4/21号线黄村站 13号线珠村站
✅全采光 大路边 电梯房
✅民水民电 押一付一

 
🌟10–15分钟直达：
师大暨大｜天河公园｜科韵路｜天河智慧城｜科学城｜岗顶｜石牌桥｜体育西｜珠江新城｜金融城｜员村｜潭村｜省奥体中心｜东圃摩登城｜优托邦
 
🏠户型&价格：
▫单间：499起
▫一房一厅：699起
▫两房一厅：899起
 
🚇双地铁交汇：4号线+21号线+13号线
家电齐全，拎包可住，随时看房
 
📩微信：19924398279
加微信发实拍图＋视频，诚心租房来聊～', 1, 0, 'sha256:d9afd59c208ef85d927740d7dec67db4a235f0ae189b2b70444f8e7e1e0891fd') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:c56856943edf391f70d568fe341a108e635c17a1035e43571e3e70ad1f584428', '2026-04-30 09:32', '.石井凰岗房东直租15766743745', 'text', '广州市', '天河区', '体育西', '["8号线"]', '["体育西","公园前"]', '[{"layout":"一房一厅","rent_min":599,"rent_max":null},{"layout":"两房一厅","rent_min":899,"rent_max":null},{"layout":"一房一厅","rent_min":499,"rent_max":null},{"layout":"两房一厅","rent_min":599,"rent_max":null}]', 499, 899, '[]', '["空调","洗衣机","热水器","冰箱"]', '["近地铁","家电齐全"]', '[]', '[]', NULL, '天河区体育西附近真实发布租房线索，一房一厅599起，两房一厅899起，一房一厅499起，两房一厅599起，近地铁，家电齐全', '❤ 💛💚💙💜💔💖💗💓💗
 8号线石井

地铁5-20分钟直达小平、石潭、聚龙、同德、上步、鹅掌坦、陈家祠、华林寺、公园前、西村、体育西等
 
🏠 走到地铁6至12分钟，近地铁

配有空调、洗衣机、热水器
、冰箱，家私家电齐全，卫生干净，领包入住[强]

🈶单 间 499 起
🈶一房一厅599起
🈶两房一厅899起

🌅 📣 欢迎大家加微信看实图
😘 😘咨询看房请直接加我微信
☎️ 1576674374', 1, 0, 'sha256:7049077d235c5ee3323491d54118d38f1df38e60ed229f5f0f926b711a87c0b1') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:138b9c4a58a1660889ac48e961d3e12863e19017297f47c4a9000377982ec856', '2026-04-30 15:34', '.黄村房东', 'text', '广州市', '天河区', '珠江新城/黄村/棠东', '[]', '["黄村","棠东","车陂","珠江新城"]', '[{"layout":"单间","rent_min":500,"rent_max":null},{"layout":"一房一厅","rent_min":800,"rent_max":null},{"layout":"一房一厅","rent_min":500,"rent_max":null}]', 500, 800, '["押一付一"]', '[]', '["房东直租","无中介费","近地铁","民水民电","押一付一","家电齐全"]', '["19202022159"]', '["19202022159"]', '☎️电话微信同步19202022159', '天河区珠江新城/黄村/棠东附近真实发布租房线索，单间500起，一房一厅800起，一房一厅500起，房东直租，无中介费，民水民电，押一付一，家电齐全', '[红包]广州天河4号21号黄村双地铁
房东直租无中介费，地铁BRT
靠路边，不钻深巷子安全感满满

💦4⚡0.88
精致家具 无中介费
家电齐全 拎包入住 
押一付一 民水民电
精装修环境好
🐂🍺单间500-
🐂🍺一房800-

近黄村地铁站，隔壁车陂，车陂南
通勤党福音来了——地铁半小时内珠江新城、万胜围、天河智慧城！早八不赶脚，下班少奔波~
天河公园，棠东，神舟路

隔壁商超小吃超方便，快递楼下就能拿

☎️电话微信同步19202022159
随时可以看房', 1, 0, 'sha256:d683c700fcd8e9d1ea29e583cac65aeafbf14b5534533af5b2947c9ccc4c2947') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_消息.txt', '广州租房群A134-禁中介', 'sha256:42aca79e134781a00cfcaac0620d1555db9c021422086ab8ff9b965d555e90ec', '2026-05-06 16:09', '绿豆', 'text', '广州市', '天河区', '珠江新城/科韵路/棠下', '["5号线","11号线","13号线"]', '["棠下","棠东","上社","科韵路","员村","珠江新城","琶洲"]', '[{"layout":"单间","rent_min":500,"rent_max":null},{"layout":"一房一厅","rent_min":700,"rent_max":null},{"layout":"两房一厅","rent_min":900,"rent_max":null},{"layout":"一房一厅","rent_min":500,"rent_max":null},{"layout":"两房一厅","rent_min":700,"rent_max":null}]', 500, 900, '[]', '[]', '["近地铁","采光好","独卫","阳台"]', '[]', '[]', NULL, '天河区珠江新城/科韵路/棠下附近真实发布租房线索，单间500起，一房一厅700起，两房一厅900起，一房一厅500起', '13号线🚇、棠下，棠东，上社房东

直租、大路边光线充足、中介勿扰

 🏙独立阳台、厨房、洗手间，阳光充足、格局美观、卫生整洁、

 精装单间💰 500 🈶
 一房一厅💰 700 🈶
 两房一厅💰 900 🈶

地铁11号线景路站~5号线科韵路站
 🚄🪐地铁有11号线、可快速到达员村、琶洲、珠江新城、增城广场等区域，周边还设有公交接驳线路。

📲📲微信➕13号线🚇、棠下，棠东，上社房东

直租、大路边光线充足、中介勿扰

 🏙独立阳台、厨房、洗手间，阳光充足、格局美观、卫生整洁、

 精装单间💰 500 🈶
 一房一厅💰 700 🈶
 两房一厅💰 900 🈶

地铁11号线景路站~5号线科韵路站
 🚄🪐地铁有11号线、可快速到达员村、琶洲、珠江新城、增城广场等区域，周边还设有公交接驳线路。

📲📲微信➕hhhh5555ffff', 1, 0, 'sha256:c48fe7a8c0be227f6a092c02da28a1fc2fb3c869e50d9ef3a7fdc28e96b83d3b') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:cecb54f332f117d3da424a630e8d215d112be714c8fcdfcd95f8ca888b349dbe', '2026-04-30 18:18', '三号线大石小芝', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '[]', '["科韵路","体育西","珠江新城","大石","市桥","南村万博","汉溪长隆","大学城"]', '[{"layout":"单间","rent_min":500,"rent_max":null},{"layout":"一房一厅","rent_min":800,"rent_max":null},{"layout":"一房一厅","rent_min":500,"rent_max":null}]', 500, 800, '["押一付一"]', '[]', '["无中介费","近地铁","押一付一"]', '["15302498170"]', '[]', '电话：15302498170', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间500起，一房一厅800起，一房一厅500起，无中介费，押一付一', '🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟
🌟三号线大石直租 无中介费
🌟押一付一，🉑转租 
🌟🔥单间500起 
🌟🔥一房一厅800起
🌟 
🌟大石地铁🚇15分钟左右🈚🌟一站汉溪长隆，夏滘。两站沥滘，南村万博。三站大塘，员岗。板桥，市桥，客村，鹭江，番禺广场，广州塔，珠江新城，体育西，
🌟广佛环线🚅大石站[哇]
[鼓掌]一个站到广州南站、大学城
[鼓掌]两个站到琶洲
[鼓掌]三个站到科韵路
🌟[呲牙][呲牙]欢迎大家加微信 
🌟实图👀房，免费接送👀房， 
🌟☎️☎️微信同号： 
🌟15302498170 
🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟', 1, 0, 'sha256:efd0bfffe534c34ec3cb1ed67b465fc51ae82e53a2f6062b997f53d94e187713') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:df00209f29ba3f198a49142fd4edc1000689dfcfcc374753fb51f74720f6d131', '2026-04-30 13:00', 'Gabriel', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '["4号线","21号线"]', '["黄村","棠下","车陂","科韵路","体育西","珠江新城","琶洲"]', '[{"layout":"一房一厅","rent_min":1000,"rent_max":1200},{"layout":"两房一厅","rent_min":1500,"rent_max":1680},{"layout":"一房一厅","rent_min":500,"rent_max":888},{"layout":"两房一厅","rent_min":1000,"rent_max":1200}]', 500, 1680, '["押一付一"]', '["电梯"]', '["房东直租","近地铁","民水民电","押一付一","家电齐全"]', '["15989957793"]', '["15989957793"]', '🛰️微信电话同号15989957793', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，一房一厅1000-1200，两房一厅1500-1680，一房一厅500-888，两房一厅1000-1200，房东直租，民水民电，押一付一，家电齐全', '🔥21号线/4号线黄村房东直租🔥
✔️押一付一，大路边全采光
✔️民水民电，⚡0.88一度
✔️电梯房，大路边

🚇地铁5-15分钟直达🚀
【智慧城】【金融城】【科学城】【天河公园】【珠江新城】【体育西】【岗顶】【石牌】【车陂】【棠下】【东圃】【鱼珠】【科韵路】【琶洲】

🏠单 间 500~888元/月
🏠一房一厅1000~1200元/月
🏠两房一厅1500~1680元/月

⭕家私家电齐全，拧包入住，地铁口接送看房，免费帮搬家⭕
 🛰️微信电话同号15989957793', 1, 0, 'sha256:de9e44d961c865b7eadabc8fb045ba0c38fab3d33173c5208809cc72585f0d69') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:0966b3cca7cf21d038be6965334e54346af2fbe5fff5e932e977b9ddbba4874d', '2026-04-30 11:38', '绿豆', 'text', '广州市', '天河区', '珠江新城/科韵路/棠下', '["5号线","11号线","13号线"]', '["棠下","上社","科韵路","员村","珠江新城","琶洲"]', '[{"layout":"单间","rent_min":550,"rent_max":null},{"layout":"一房一厅","rent_min":650,"rent_max":null},{"layout":"两房一厅","rent_min":900,"rent_max":null},{"layout":"一房一厅","rent_min":550,"rent_max":null},{"layout":"两房一厅","rent_min":650,"rent_max":null}]', 550, 900, '[]', '[]', '["房东直租","近地铁","采光好","独卫","阳台"]', '[]', '[]', NULL, '天河区珠江新城/科韵路/棠下附近真实发布租房线索，单间550起，一房一厅650起，两房一厅900起，一房一厅550起，房东直租', '🚇棠下13号线地铁口上社房东直租、华景路，大路边光线充足、中介勿扰

 🏙独立阳台、厨房、洗手间，阳光充足、格局美观、卫生整洁、
 
 精装单间💰550
 一房一厅💰650
 两房一厅💰900

🚇地铁11号线华景路站~5号线科韵路站
 🚄🪐地铁有11号线、可快速到达员村、琶洲、珠江新城、增城广场等区域，周边还有BRT站！步行几分钟
快速到达体育中心~岗顶~石牌桥~等市中心

📲📲微信➕hhhh5555ffff', 1, 0, 'sha256:4b2d7fd2bebb3bdddadddadcf8fe7f44cd89330a434135458994824582e727d7') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:89c8f2042783a11c74da295a7e30ef38217f502815574e4fc49ebf0ce0aa1a1d', '2026-04-30 07:30', '.马务房东直租13802925859', 'text', '广州市', '天河区', '员村', '["14号线"]', '["员村","鹤边","马务","嘉禾","新市"]', '[{"layout":"单间","rent_min":599,"rent_max":null},{"layout":"一房一厅","rent_min":799,"rent_max":null},{"layout":"两房一厅","rent_min":1299,"rent_max":null},{"layout":"一房一厅","rent_min":599,"rent_max":null},{"layout":"两房一厅","rent_min":799,"rent_max":null}]', 599, 1299, '[]', '[]', '["房东直租","近地铁","家电齐全","阳台"]', '["13802925859"]', '[]', '电话：13802925859', '天河区员村附近真实发布租房线索，单间599起，一房一厅799起，两房一厅1299起，一房一厅599起，房东直租', '[爱心]鹤边房东直租[爱心]

马务，鹤边，鹤边员村
精装公寓房，环境舒适
[庆祝][庆祝]地铁14号线[庆祝][庆祝]
直达嘉禾，彭边，马务，新市，百信广场，乐嘉路

大单间 599起（带阳台）
一房一厅 799起（带阳台）
二房一厅 1299起（带阳台）

房间配置齐全，拎包入住
酒店风格，温馨浪漫
周边生活便利，交通方便
楼下有共享单车，步行3~8分钟到地铁口

[烟花]免费看房，欢迎大家加微信看实图
微信请添加电话号码
☎️13802925859', 1, 0, 'sha256:a2ec60b1fbe18339d2add3bdca8277cad1433bf36befa4d221dbbf28641e79bb') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:c881fe610e9621b1b1830e8266aca5575c152b10ba9ca9f33999f8c423390178', '2026-04-30 10:59', '.黄村房东直租 17833470960', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '["21号线"]', '["黄村","棠下","棠东","上社","车陂","科韵路","体育西","珠江新城"]', '[{"layout":"单间","rent_min":599,"rent_max":null},{"layout":"一房一厅","rent_min":699,"rent_max":null},{"layout":"两房一厅","rent_min":1200,"rent_max":null},{"layout":"一房一厅","rent_min":599,"rent_max":null},{"layout":"两房一厅","rent_min":699,"rent_max":null}]', 599, 1200, '["押一付一"]', '["密码锁","门禁"]', '["房东直租","无中介费","近地铁","民水民电","押一付一","家电齐全","阳台"]', '["17833470960","19540007121"]', '["19540007121"]', '📞 看房微信/电话： 19540007121', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间599起，一房一厅699起，两房一厅1200起，一房一厅599起，房东直租，民水民电，押一付一', '天河黄村 4/21号线房东直租‼️

【房东直租 0中介费】
✅精装+独立阳台
✅家电家具齐全 真正拎包入住
✅民水民电0.88+押一付一
✅电子门禁＋密码锁

💰单间 599起
💰一房一厅 699起
💰两房一厅 1200起

🚇地铁5-15分钟直达🚀
【智慧城】【金融城】【科学城】【天河公园】【珠江新城】【体育西】【岗顶】【石牌】【车陂】【棠下】【东圃】【鱼珠】【科韵路】【琶洲】
🚌 BRT快速直达:黄村/车陂/棠东/岗顶/上社/体育中心等

【生活超便利】🍜
美食小吃街、黄村市场、医院、优托邦、游乐场、天河广场全在身边

📞 看房微信/电话： 19540007121
17833470960', 1, 0, 'sha256:53e7e65c3c97e9466649820196915530c01a769ba8cdd0c777f9f85fb7690e62') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:de60e747580eca70092791a11bd6fb847fa41003cf6f792c9cb1d7a9fb23cf5f', '2026-05-01 17:17', '.珠村·三溪·车陂房东直租', 'text', '广州市', '天河区', '珠江新城/黄村/车陂', '["4号线","5号线","8号线","13号线"]', '["黄村","车陂","员村","珠江新城","大学城","客村","琶洲"]', '[{"layout":"单间","rent_min":599,"rent_max":null},{"layout":"一房一厅","rent_min":699,"rent_max":null},{"layout":"一房一厅","rent_min":599,"rent_max":null},{"layout":"两房一厅","rent_min":699,"rent_max":null}]', 599, 699, '["押一付一"]', '[]', '["近地铁","民水民电","押一付一","可短租","阳台"]', '["17811564220"]', '[]', '电话：17811564220', '天河区珠江新城/黄村/车陂附近真实发布租房线索，单间599起，一房一厅699起，一房一厅599起，两房一厅699起，民水民电，押一付一', '车陂南｜车陂｜黄村 地铁口好房直租
🚇步行3-7分钟直达4/5/13号线，天河通勤优选
💥王牌福利：民水民电｜押一付一，长租短租均可，无压力入住
🏠户型租金（全带阳台，采光通透）
▪️精品单间：599元起
▪️温馨一房一厅：699元起
▪️两房一厅：已租罄，可预约蹲转租房源
🚄高效通勤全覆盖
▫️5号线车陂/车陂南/黄村，15分钟直达珠江新城、猎德、潭村、员村核心商务区
▫️黄村4号线+8号线，快速直达琶洲、万胜围、客村、大学城
🌇成熟生活配套
紧邻东圃购物广场、时代TIT广场、保利广场、天河软件园、金融城公园
山姆、麦德龙商超加持，餐饮、购物、休闲、办公一站式满足
优质高性价比好房，通勤上班族、独居、情侣都适配
📞看房热线：17811564220
点头像加微信吧', 1, 0, 'sha256:70d6187dba9f37e588fe613f5d1ce7da8d9fe98bbfe87407e900de79ab151f3e') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:fd66eb3d5ffb8efcf8054744fcaef946154c38ceba1d8dbed76c72af26d1839e', '2026-04-30 08:03', '.A天河黄村房东19540007121', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '["21号线"]', '["黄村","棠东","上社","车陂","科韵路","员村","体育西","珠江新城"]', '[{"layout":"单间","rent_min":599,"rent_max":null},{"layout":"一房一厅","rent_min":699,"rent_max":null},{"layout":"一房一厅","rent_min":599,"rent_max":null},{"layout":"两房一厅","rent_min":699,"rent_max":null}]', 599, 699, '["押一付一"]', '["空调","洗衣机","热水器","冰箱","密码锁","门禁"]', '["房东直租","无中介费","民水民电","押一付一","采光好","阳台"]', '["17833470960","19540007121"]', '["19540007121"]', '📞 看房微信/电话：19540007121', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间599起，一房一厅699起，一房一厅599起，两房一厅699起，房东直租，民水民电，押一付一，采光好', '天河黄村 · 精品公寓｜无巷子

✅ 一手房东直租｜0中介费｜押一付一｜民水民电
💰 租金：
精装带阳台单间 599起
精装一房一厅带阳台 699起
精装两房一厅1带阳台 1200 起
🚇 交通
步行约15分钟到4/21号线黄村站
直达体育西路、珠江新城、猎德、员村、科韵路、车陂南
BRT步行3分钟，直达岗顶、上社、体育中心、车陂、棠东

🏠 配置
空调、洗衣机、热水器、冰箱齐全
独立阳台，采光好
电子门禁+密码锁，安全放心
下楼超市、菜市场、美食街、公园

📞 看房微信/电话：19540007121
17833470960', 1, 0, 'sha256:a26f89b6d22f334d2c19f35f747eccaccdc1362a644cbe4686296ef5bdb9bd63') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:a7194727bf61febeda812d7216b1e8174f6e20c496331492e10034dec6855440', '2026-04-30 07:31', '.大石地铁房东直租', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '["3号线"]', '["科韵路","体育西","珠江新城","大石","南村万博","大学城","广州南站","客村"]', '[{"layout":"一房一厅","rent_min":1100,"rent_max":1800},{"layout":"两房一厅","rent_min":1500,"rent_max":2000},{"layout":"一房一厅","rent_min":600,"rent_max":1500},{"layout":"两房一厅","rent_min":1100,"rent_max":1800}]', 600, 2000, '[]', '[]', '["房东直租","近地铁"]', '[]', '[]', NULL, '天河区珠江新城/科韵路/体育西附近真实发布租房线索，一房一厅1100-1800，两房一厅1500-2000，一房一厅600-1500，两房一厅1100-1800，房东直租', '🌈🌈🌈🌈🌈🌈🌈🌈🌈🌈
3号线大石地铁站♛房东直租

🈶单 间600 到1500
🈶一房一厅1100到1800
🈶两房一厅1500到2000

房子🏠步行到地铁8分钟内

大石地铁🚇15分钟左右🉑达南村万博、沥滘、大塘、客村、广州塔、珠江新城、体育西路、岗顶、石牌、中大、鹭江、赤岗、琶洲、磨碟沙、南洲、东晓南、石溪

广佛环线🚅大石站❗
一个站到广州南站、大学城
两个站到琶洲[强]
三个站到科韵路[强]

看房或者咨询可直接加我微信', 1, 0, 'sha256:ab09e802f8d914d4da51a9157d46001c1a0144f298c1065fed2e4728f5c01343') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:b870e5ed503781e7e7eb7ef08a7c60f31a10baa7f610d648098ce9c283ca7de0', '2026-04-30 14:35', '.天河珠村房东直租', 'text', '广州市', '天河区', '珠江新城/科韵路/黄村', '["13号线"]', '["黄村","珠村","棠下","棠东","上社","车陂","科韵路","员村"]', '[{"layout":"一房一厅","rent_min":850,"rent_max":1300},{"layout":"一房一厅","rent_min":600,"rent_max":850}]', 600, 1300, '["押一付一"]', '[]', '["无中介费","近地铁","民水民电","押一付一","家电齐全"]', '["18148963307"]', '[]', '📞18148963307（点头像加微信）', '天河区珠江新城/科韵路/黄村附近真实发布租房线索，一房一厅850-1300，一房一厅600-850，押一付一，近地铁，家电齐全', '🚇13号线天河珠村C口附近

0中介费 民水电，押一付一
0中介费 民水电，押一付一
0中介费 民水电，押一付一
 
🚇 地铁黄金线:珠江新城/猎德/员村/科韵路/车陂/鱼珠/棠下/天河公园/万胜围/大学城等
🚌 BRT快速直达:黄村/车陂/棠东/岗顶/棠下上社/体育中心等
 
 3分钟到BRT。
 近地铁走路5--10分钟左右

附近珠村夜市，吉山商业中心、奥体优托邦、珠吉装饰城，欢乐颂商场，美林天地等
 
• 🏠房型：
 单 间： 600~850
 一房一厅： 850~ 1300 
• 💰性价比高：价格实惠，周边配套全。
• 🛋拎包入住：家具家电齐全。

📞18148963307（点头像加微信）', 1, 0, 'sha256:b6cfefd81c6111ef2174397365fdad2a3a31ee5cc11e3ce0fc724c8ec267c50a') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:a70a0495774df84b80e69ca59027b786620954b18a869b76097c9a97dec8e8ce', '2026-04-30 12:56', '鱼🐟', 'text', '广州市', '天河区', '珠江新城/体育西', '[]', '["体育西","珠江新城","菊树","黄沙","上下九","昌岗","沙园","凤凰新村"]', '[{"layout":"单间","rent_min":750,"rent_max":1100},{"layout":"一房一厅","rent_min":750,"rent_max":1300},{"layout":"两房一厅","rent_min":1300,"rent_max":1800},{"layout":"一房一厅","rent_min":650,"rent_max":null},{"layout":"两房一厅","rent_min":750,"rent_max":1300}]', 650, 1800, '[]', '[]', '["房东直租","近地铁","不短租","家电齐全"]', '["18998438337"]', '["18998438337"]', '请加微信 18998438337微信', '天河区珠江新城/体育西附近真实发布租房线索，单间750-1100，一房一厅750-1300，两房一厅1300-1800，一房一厅650起，近地铁，家电齐全', '不短租~~荔湾区菊树地铁站
😘🏡自家新房出租,周边环境整洁安静
配置家电齐全领包入住，白领首选
🏡 单间750--1100家电齐全一楼650
🏡一室一厅:750-1300家电齐全
🏡两室一厅:1300--1800近地铁口
走路到菊树地铁口5分钟内，配备菜鸟驿站，附近有菜市场，麦当劳，连锁生活超市👍👍
地铁直达（十三行）【昌岗】【沙园】【凤凰新村】【北京路】【黄沙】【上下九】👉 15分钟左右🙃家具齐全拎包入住！！
地铁半小时左右到珠江新城CBD！！和体育西
 中介微商…加了不说话勿扰！！
请加微信 18998438337微信', 1, 0, 'sha256:72519c6fbffaeb797008b58ac29743267de30ccca7fba31bbd638d54b52ee5b8') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:3d1cec26dbd51df442a9c92fa12bd8b9f2feeee87ab5cc234ee2e0456a5998f5', '2026-05-01 16:31', '.车陂南-车陂房东15902056511', 'text', '广州市', '天河区', '珠江新城/黄村/车陂', '["4号线","5号线","8号线","13号线"]', '["黄村","车陂","员村","珠江新城","大学城","客村","琶洲"]', '[{"layout":"单间","rent_min":666,"rent_max":null},{"layout":"一房一厅","rent_min":766,"rent_max":null},{"layout":"一房一厅","rent_min":666,"rent_max":null},{"layout":"两房一厅","rent_min":766,"rent_max":null}]', 666, 766, '["押一付一"]', '[]', '["近地铁","民水民电","押一付一","可短租","阳台"]', '["17811564220"]', '[]', '📞 联系方式：17811564220', '天河区珠江新城/黄村/车陂附近真实发布租房线索，单间666起，一房一厅766起，一房一厅666起，两房一厅766起，民水民电，押一付一', '车陂南/车陂/黄村地铁旁租房｜3-7分钟直达4/5/13号线
✅ 核心优势：民水民电+押一付一，步行3-7分钟到地铁口，通勤超方便！
 🉑短租🉑押一

• 精品单间 666元/月（带阳台）
• 一房一厅 766元/月（带阳台）
• 两房一厅：已租罄，可蹲转租
🚇 通勤圈速达：
• 5号线（车陂南/车陂/黄村）：15分钟直达珠江新城、猎德、潭村、员村等核心商圈

•黄村 4号线+8号线：5-15分钟到万胜围、琶洲、客村、大学城南/北等热门站点

🌆 周边配套：东圃购物广场、时代TIT广场、保利广场、天河软件园、金融城公园、山姆/麦德龙超市，吃喝玩乐办公全覆盖～

📞 联系方式：17811564220', 1, 0, 'sha256:873323e1217d5ba37e6eb14e1c219c15b27883100cf07623285f5c79ea81f63f') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:48a28fca169d23d07eaadb443d591a74a88008bdf7dcf2b86c9859b2ba258ebd', '2026-04-30 17:46', '林子敬15879897979', 'text', '广州市', '天河区', '黄村', '[]', '["黄村"]', '[{"layout":"单间","rent_min":680,"rent_max":null},{"layout":"一房一厅","rent_min":880,"rent_max":null},{"layout":"两房一厅","rent_min":1080,"rent_max":null},{"layout":"一房一厅","rent_min":680,"rent_max":null},{"layout":"两房一厅","rent_min":880,"rent_max":null}]', 680, 1080, '["押一付一"]', '["空调","洗衣机","冰箱","门禁","监控"]', '["房东直租","无中介费","近地铁","押一付一"]', '["15879897979"]', '["15879897979"]', '☎ 微信15879897979（免费接送看房）', '天河区黄村附近真实发布租房线索，单间680起，一房一厅880起，两房一厅1080起，一房一厅680起，房东直租，无中介费，押一付一', '[烟花][烟花][烟花][烟花][烟花][烟花][烟花][烟花][烟花][烟花][烟花]
[庆祝]天河智慧城，天河老实房东[庆祝]
自建房 民用水电 押一付一

🔥精装大单间680～
🔥精装一房一厅880～
🔥精装两房一厅1080～

🚄地铁直达【神舟路】【科学城】【大观南路】【苏元】【萝岗】【黄村】【广百广场】【万科云城】

✅ 配套完善：各大商超市，菜市场，美食街
✅ 房源亮点：精装修配空调、洗衣机、冰箱，独立厨房卫生间，WiFi覆盖 
✅ 安全省心：24小时监控，电子门禁，房东直租无中介费 

☎ 微信15879897979（免费接送看房）', 1, 0, 'sha256:606646ff35a33aca821913d8e77edaec63b6dd1211475cdc8202631ca73fbf38') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:d6f1d865b2ed511e5a345f0f12b9aa46d4035a7f49cc3d71544cfa1462503376', '2026-04-30 09:48', '广州房东直租', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '["5号线"]', '["棠下","棠东","上社","车陂","科韵路","员村","体育西","珠江新城"]', '[{"layout":"单间","rent_min":680,"rent_max":950},{"layout":"一房一厅","rent_min":980,"rent_max":1580},{"layout":"两房一厅","rent_min":1380,"rent_max":2400},{"layout":"一房一厅","rent_min":680,"rent_max":950},{"layout":"两房一厅","rent_min":980,"rent_max":1580},{"layout":"一房一厅","rent_min":1380,"rent_max":2400}]', 680, 2400, '[]', '["门禁","监控"]', '["房东直租","无中介费","近地铁"]', '["18620724159"]', '["18620724159"]', '点我头像添加微信 电话同步18620724159', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间680-950，一房一厅980-1580，两房一厅1380-2400，一房一厅680-950，房东直租，无中介费', '🏠 天河棠下-上社房东自建屋

5-7分钟直达BRT🚗多条BRT直通珠江新城、体育西、天河城、北京路、科韵路公司等
骑车5分钟直达🚇双地铁5号线科韵路站华景路等30分钟可达员村、潭村、车陂南、东圃等
单间680-950
一房980-1580
两房1380-2400
注：有！一楼！优惠单间跟一房一厅

✅ 配套完善：沃尔玛、天河万科广场、喜鹊茶餐厅、中山大学附属第三医院、棠东棠下小学、棠下体育中心
✅ 24小时监控，电子门禁，房东直租无中介费 

点我头像添加微信 电话同步18620724159', 1, 0, 'sha256:f511e0749cafeb044397f4b68894d2d2d3664cd7703c44c1add5f2f35d879a76') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_消息.txt', '广州租房群A134-禁中介', 'sha256:c470c02e882215e8d3ee3bf8e5b4b47a05e11ef767fec4474c364d7fc75d45e9', '2026-05-06 16:20', '车陂，车陂南房东直租13660294889', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '["4号线","5号线"]', '["黄村","车陂","科韵路","体育西","珠江新城","琶洲"]', '[{"layout":"单间","rent_min":688,"rent_max":1188},{"layout":"一房一厅","rent_min":888,"rent_max":1588},{"layout":"两房一厅","rent_min":1288,"rent_max":1888},{"layout":"一房一厅","rent_min":688,"rent_max":1188},{"layout":"两房一厅","rent_min":888,"rent_max":1588}]', 688, 1888, '["押一付一"]', '[]', '["房东直租","近地铁","民水民电","押一付一","采光好","家电齐全","阳台"]', '["13660294889"]', '[]', '🏠咨询☎️13660294889 微信同号🤝', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间688-1188，一房一厅888-1588，两房一厅1288-1888，一房一厅688-1188，房东直租，民水民电，押一付一，家电齐全，采光好', '🎆天河车陂/车陂南房东直租
🏘️精装修，采光好，大路边
👍民水民电（0.88)，押一付一 
🈶单间带阳台 688到1188
🈶一房一厅带阳台 888到1588
🈶两房一厅带阳台 1288到1888 
🚄双地铁4号线，5号线
🚶步行5分钟到地铁口
地铁直达，东圃，三溪，科韵路，潭村，猎德，珠江新城，黄村，万胜围，体育西路，石牌，琶洲…
周边：东圃购物广场一条街、时代TIT广场、ing未来印、金融城广场公园、天银贸易大厦。
家电齐全，可直接拎包入住，免费接送看房，免费帮忙搬家🤝
🏠咨询☎️13660294889 微信同号🤝', 1, 0, 'sha256:e28dd445bd5e68d57e930a0d8c1fd9db0fb7375410b36c33145e436380aea859') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:7ee4c2e13655853289909968a68e279d89e9631a698cb6756c331fd6d8b354de', '2026-05-01 16:58', '三号线大石小芝', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '["3号线"]', '["科韵路","体育西","珠江新城","大石","市桥","南村万博","汉溪长隆","大学城"]', '[{"layout":"单间","rent_min":700,"rent_max":1200},{"layout":"一房一厅","rent_min":900,"rent_max":1500},{"layout":"两房一厅","rent_min":1200,"rent_max":1800},{"layout":"一房一厅","rent_min":700,"rent_max":1200},{"layout":"两房一厅","rent_min":900,"rent_max":1500}]', 700, 1800, '["押一付一"]', '[]', '["近地铁","民水民电","押一付一","宠物友好"]', '["15302498170"]', '[]', '🛵本人免费接送，免费帮你搬微信☎️同步，15302498170', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间700-1200，一房一厅900-1500，两房一厅1200-1800，一房一厅700-1200，押一付一', '3号线大石地铁，直租
民水电，押一付一
可转租，可养猫
👣步行3-7分钟到地铁口
 
😘单间700～1200
😘一房一厅900～1500
😘两房一厅1200～1800

🚆地铁5-20分钟直达：一站汉溪长隆，夏滘。两站沥滘，南村万博。三站大塘，员岗。板桥，市桥，客村，鹭江，番禺广场，广州塔，珠江新城，体育西，
🌟广佛环线🚅大石站[哇]
[鼓掌]一个站到广州南站、大学城
[鼓掌]两个站到琶洲
[鼓掌]三个站到科韵路
🛣️全采光，大马路，无小巷
🛵本人免费接送，免费帮你搬微信☎️同步，15302498170', 1, 0, 'sha256:53c9efcd28153f14734d72add005914ddb0d58f5f1d1894bd6c61550b68d65a8') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:b256aaaffe2d6df4ec8e0fb1146352e6d907fec87c7b0b7fa84bb1b13e183bf8', '2026-04-30 09:41', '天河屋主直租不收款15989048119', 'text', '广州市', '天河区', '珠江新城/黄村', '["21号线"]', '["黄村","珠江新城","琶洲"]', '[{"layout":"单间","rent_min":700,"rent_max":900},{"layout":"一房一厅","rent_min":800,"rent_max":1500},{"layout":"两房一厅","rent_min":1400,"rent_max":1700},{"layout":"一房一厅","rent_min":700,"rent_max":900},{"layout":"两房一厅","rent_min":800,"rent_max":1500}]', 700, 1700, '[]', '[]', '["近地铁","民水民电","家电齐全","阳台"]', '["19842501945"]', '[]', '📱直租：19842501945（微信同号）', '天河区珠江新城/黄村附近真实发布租房线索，单间700-900，一房一厅800-1500，两房一厅1400-1700，一房一厅700-900，家电齐全', '🌟【天河黄村地铁口直租】🌟
 
🏠 地址：天河黄村地铁站旁（中山大道）
💰 租金：
单间700-900 
一房800-1500
两房1400-1700 三房1800-2500
（均带南向阳台+民水电
🚇 5分钟生活圈：
· 地铁4/21号线步行3分钟7站到珠江新城
正佳/天河城/太古汇15分钟
金融城/琶洲20分钟，家电齐全，拎包入住[勾引][勾引][勾引]
🌇 核心商圈：
天河路CBD | 万博商务区 | 奥体优托邦
万科广场 | 大湾区生态走廊
 
📱直租：19842501945（微信同号）', 1, 0, 'sha256:d939b972e6792ba9ee04ed6e6919b4dc8b6990f5888ef7b51def697fcdad8d51') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:ec3342eb075563e7b633753df1fe33e0c52164219e561f05328acf1efb02acea', '2026-05-01 20:32', '三号线大石小芝', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '["3号线"]', '["科韵路","体育西","珠江新城","大石","市桥","南村万博","汉溪长隆","大学城"]', '[{"layout":"单间","rent_min":700,"rent_max":1200},{"layout":"一房一厅","rent_min":800,"rent_max":1500},{"layout":"两房一厅","rent_min":1280,"rent_max":1800},{"layout":"一房一厅","rent_min":700,"rent_max":1200},{"layout":"两房一厅","rent_min":800,"rent_max":1500}]', 700, 1800, '["押一付一"]', '[]', '["近地铁","民水民电","押一付一","宠物友好"]', '["15302498170"]', '[]', '🛵本人免费接送，免费帮你搬微信☎️同步，15302498170', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间700-1200，一房一厅800-1500，两房一厅1280-1800，一房一厅700-1200，押一付一', '3号线大石地铁，直租
民水电，押一付一
可转租，可养猫
👣步行3-7分钟到地铁口
 
😘单间700～1200
😘一房一厅800～1500
😘两房一厅1280～1800

🚆地铁5-20分钟直达：一站汉溪长隆，夏滘。两站沥滘，南村万博。三站大塘，员岗。板桥，市桥，客村，鹭江，番禺广场，广州塔，珠江新城，体育西，
🌟广佛环线🚅大石站[哇]
[鼓掌]一个站到广州南站、大学城
[鼓掌]两个站到琶洲
[鼓掌]三个站到科韵路
🛣️全采光，大马路，无小巷
🛵本人免费接送，免费帮你搬微信☎️同步，15302498170', 1, 0, 'sha256:0e117ca78162428c1aaf884561f796f213296f9d28c38e0d6c217cf57d89e262') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:4f96686b0bae1f32fe14e8ba53d5232799d4d2b993d4d8d2353a9f1903f292e0', '2026-04-30 08:56', '三号线大石小芝', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '[]', '["科韵路","体育西","珠江新城","大石","南村万博","大学城","广州南站","客村"]', '[{"layout":"单间","rent_min":800,"rent_max":1500},{"layout":"一房一厅","rent_min":1050,"rent_max":1800},{"layout":"两房一厅","rent_min":1500,"rent_max":2000},{"layout":"一房一厅","rent_min":800,"rent_max":1500},{"layout":"两房一厅","rent_min":1050,"rent_max":1800}]', 800, 2000, '[]', '[]', '["房东直租","近地铁"]', '["15302498170"]', '[]', '电话：15302498170', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间800-1500，一房一厅1050-1800，两房一厅1500-2000，一房一厅800-1500，房东直租', '🥳🥳🥳🥳🥳🥳🥳🥳🥳
三号线大石地铁站 · 房东直租
😘单间800 到1500
😘一房一厅1050到1800
😘两房一厅1500到2000

房子🏠步行到地铁8分钟内

大石地铁🚇15分钟左右🉑达南村万博、沥滘、大塘、客村、广州塔、珠江新城、体育西路、岗顶、石牌、中大、鹭江、赤岗、琶洲、磨碟沙、南洲、东晓南、石溪

广佛环线🚅大石站❗
一个站到广州南站、大学城
两个站到琶洲[强]
三个站到科韵路[强]

看房或者咨询可直接加我微信❗
15302498170', 1, 0, 'sha256:f57fa29da3efd4ff30ba5c367df6347ebba916b5a0d63e2e603330cef8f60315') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:90fc83993e3d86b3c6f7e9e53ddcdf4450eaa9430ebf1c013ad1fe3882d053c8', '2026-04-30 15:40', '三号线大石小芝', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '[]', '["科韵路","体育西","珠江新城","大石","南村万博","大学城","广州南站","客村"]', '[{"layout":"单间","rent_min":800,"rent_max":1500},{"layout":"一房一厅","rent_min":1050,"rent_max":1700},{"layout":"两房一厅","rent_min":1280,"rent_max":2000},{"layout":"一房一厅","rent_min":800,"rent_max":1500},{"layout":"两房一厅","rent_min":1050,"rent_max":1700}]', 800, 2000, '["押一付一"]', '[]', '["近地铁","押一付一"]', '["15302498170"]', '[]', '电话：15302498170', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间800-1500，一房一厅1050-1700，两房一厅1280-2000，一房一厅800-1500，押一付一', '本房东来招租啦！押一付一[憨笑]
不是中介，不用交那半个月的中介费 👇
📍位置：三号线大石
💰租金：单间800-1500
 一房一厅1050-1700
 两房一厅1280-2000
大石地铁🚇15分钟左右🉑直达：南村万博、沥滘、大塘、客村、广州塔、珠江新城、体育西路、岗顶、石牌、中大、鹭江、赤岗、琶洲、磨碟沙、南洲、东晓南、石溪
广佛环线🚅大石站❗
一个站到广州南站、大学城
两个站到琶洲[强]
三个站到科韵路[强]

看房或者咨询可直接加我微信☎️
15302498170', 1, 0, 'sha256:6cf9a4d3d9c20097b0ef834dc9b0d5b57e91dcb29ece48026cb2e0fb7cf818d0') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_消息.txt', '广州租房群A134-禁中介', 'sha256:f133f1b950697003d9bcffb5ef576a2a5daac0b2386178f1a4911399012d492a', '2026-05-06 15:54', '三号线大石小芝', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '["3号线"]', '["科韵路","体育西","珠江新城","大石","市桥","南村万博","汉溪长隆","大学城"]', '[{"layout":"单间","rent_min":800,"rent_max":1400},{"layout":"一房一厅","rent_min":1050,"rent_max":1650},{"layout":"两房一厅","rent_min":1280,"rent_max":2500},{"layout":"一房一厅","rent_min":800,"rent_max":1400},{"layout":"两房一厅","rent_min":1050,"rent_max":1650}]', 800, 2500, '["押一付一"]', '[]', '["近地铁","民水民电","押一付一","宠物友好"]', '["15302498170"]', '[]', '🛵本人免费接送，免费帮你搬微信☎️同步，15302498170', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间800-1400，一房一厅1050-1650，两房一厅1280-2500，一房一厅800-1400，押一付一', '3号线大石地铁，直租
民水电，押一付一
可转租，可养猫
👣步行3-7分钟到地铁口
 
😘单间800-1400
😘一房一厅1050-1650
😘两房一厅1280-2500

🚆地铁5-20分钟直达：一站汉溪长隆，夏滘。两站沥滘，南村万博。三站大塘，员岗。板桥，市桥，客村，鹭江，番禺广场，广州塔，珠江新城，体育西，
🌟广佛环线🚅大石站[哇]
[鼓掌]一个站到广州南站、大学城
[鼓掌]两个站到琶洲
[鼓掌]三个站到科韵路
🛣️全采光，大马路，无小巷
🛵本人免费接送，免费帮你搬微信☎️同步，15302498170', 1, 0, 'sha256:e2ff529c84ac66244029b602ee3296a854c22e04311ce6133ad86f6b08df840c') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:fc12096e7fec2836dcee984a5704876a845e94d72696d8a1f24945fd02379d28', '2026-04-30 16:58', '三号线大石小芝', 'text', '广州市', '天河区', '珠江新城/科韵路/体育西', '[]', '["科韵路","体育西","珠江新城","大石","市桥","南村万博","汉溪长隆","大学城"]', '[{"layout":"单间","rent_min":800,"rent_max":1400},{"layout":"一房一厅","rent_min":1050,"rent_max":1700},{"layout":"一房一厅","rent_min":800,"rent_max":1400}]', 800, 1700, '["押一付一"]', '[]', '["无中介费","近地铁","押一付一"]', '["15302498170"]', '[]', '电话：15302498170', '天河区珠江新城/科韵路/体育西附近真实发布租房线索，单间800-1400，一房一厅1050-1700，一房一厅800-1400，无中介费，押一付一', '🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟
🌟三号线大石直租 无中介费
🌟押一付一，🉑转租 
🌟🔥单间800-1400 
🌟🔥一房一厅1050-1700
🌟 
🌟大石地铁🚇15分钟左右🈚🌟一站汉溪长隆，夏滘。两站沥滘，南村万博。三站大塘，员岗。板桥，市桥，客村，鹭江，番禺广场，广州塔，珠江新城，体育西，
🌟广佛环线🚅大石站[哇]
[鼓掌]一个站到广州南站、大学城
[鼓掌]两个站到琶洲
[鼓掌]三个站到科韵路
🌟[呲牙][呲牙]欢迎大家加微信 
🌟实图👀房，免费接送👀房， 
🌟☎️☎️微信同号： 
🌟15302498170 
🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟', 1, 0, 'sha256:1dbe0cab92839ee4df424c35757638795b243c943d8ee5d1f8c472b4715f2220') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:b55a0f2376447d6e0b0d2d04110e8fa1283d4a580acb4f0a8fb1ca3d24fc2e3c', '2026-05-01 19:46', '大沙地房东直租15812371252', 'text', '广州市', '天河区', '珠江新城/科韵路/车陂', '["5号线"]', '["车陂","科韵路","珠江新城"]', '[{"layout":"单间","rent_min":1000,"rent_max":null},{"layout":"一房一厅","rent_min":900,"rent_max":1200},{"layout":"两房一厅","rent_min":1200,"rent_max":1680},{"layout":"一房一厅","rent_min":1000,"rent_max":null},{"layout":"两房一厅","rent_min":900,"rent_max":1200}]', 900, 1680, '[]', '[]', '["近地铁"]', '["15812371252"]', '["15812371252"]', '📢 电话微信同步15812371252（欢迎加微信看实图满意再看房）', '天河区珠江新城/科韵路/车陂附近真实发布租房线索，单间1000起，一房一厅900-1200，两房一厅1200-1680，一房一厅1000起', '🚄 地铁5号线大沙地C出口，步行10分钟左右到地铁口

单间1000
一房一厅900～1200
两房一厅1200～1680

[强]15分钟地铁直达:珠江新城、猎德、潭村、科韵路、车陂南、三溪、东圃、文冲等
 
 📢 电话微信同步15812371252（欢迎加微信看实图满意再看房）', 1, 0, 'sha256:7a57fb971d6f78e5ae31e082dddba680fe85d108a0d525e8a53199cbe9f8895e') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:e72cad6f2648da9b06d750c0f6a011ca7d72be55afcabea5be92426f00f47599', '2026-04-30 08:54', '.荔湾西塱+天河车陂房东直租', 'text', '广州市', '海珠区', '凤凰新村/昌岗/沙园', '[]', '["西塱","坑口","芳村","黄沙","昌岗","沙园","凤凰新村","中大"]', '[{"layout":"单间","rent_min":450,"rent_max":null},{"layout":"一房一厅","rent_min":699,"rent_max":null},{"layout":"两房一厅","rent_min":900,"rent_max":null},{"layout":"一房一厅","rent_min":450,"rent_max":null},{"layout":"两房一厅","rent_min":699,"rent_max":null}]', 450, 900, '["押一付一"]', '["停车场"]', '["近地铁","押一付一","不短租","家电齐全"]', '["18027376890"]', '[]', '电话：18027376890', '海珠区凤凰新村/昌岗/沙园附近真实发布租房线索，单间450起，一房一厅699起，两房一厅900起，一房一厅450起，押一付一', '👉荔湾西塱房东18027376890
❗不短租、不短租哦
 👀 大路边，不走巷子
 公寓配置，拎包入住
 📣 大路边，采光通风好
 公交2站到地铁口
电费0.88/度，可押一付一
 
 [玫瑰]精品单间 450～
 [玫瑰] 一房一厅699～
 [玫瑰] 两房一厅900～
 
 ❗一号线 到岭南V谷科技园，珠江钢琴厂，坑口，芳村，黄沙，陈家祠，长寿路，西门口，公园前，文化公园，海珠广场 仅需15分钟
 ❗ 广佛线 地铁直达沙园，凤凰新村，中大，昌岗🎡 ，宝岗大道🎢15分钟！
❗十号线直达花围、东沙、工业大道南、东晓南、中大、滨江东路、五羊邨、杨箕东
❗❗🈶免费停车场🅿️哦', 1, 0, 'sha256:e3248ac57d26e14eed52af0920a9c6ac44c4d17852b60c506ce4fe8264651fb7') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:21445d9c74904652fc84b709f0797c13f9c740829db371dc9ee5899752f52227', '2026-04-30 08:00', '胡庆', 'text', '广州市', '海珠区', '凤凰新村/昌岗/沙园', '[]', '["菊树","芳村","黄沙","昌岗","沙园","凤凰新村"]', '[{"layout":"一房一厅","rent_min":750,"rent_max":1300},{"layout":"两房一厅","rent_min":850,"rent_max":1600},{"layout":"一房一厅","rent_min":650,"rent_max":950},{"layout":"两房一厅","rent_min":750,"rent_max":1300}]', 650, 1600, '[]', '[]', '["近地铁","采光好","家电齐全"]', '["13392660848"]', '["13392660848"]', '微信同步：13392660848（点头像加v）', '海珠区凤凰新村/昌岗/沙园附近真实发布租房线索，一房一厅750-1300，两房一厅850-1600，一房一厅650-950，两房一厅750-1300，家电齐全', '[红包]广佛线菊树地铁站

🚶🏻‍♀️步行4到5分钟到达地铁口

 🏠家电齐全带厨卫光线好大路边

🏖🏖周边商场超市，菜市场小吃街，公园学校肯德基河边等应有尽有

🚅地铁十分钟🍀直达沙园、燕岗、凤凰新村、沥滘、千灯湖、金融高新区、西朗，芳村、黄沙、陈家祠、昌岗、宝岗、文化公园、十三行、南洲、同福西、西村等等

🈶单 间 650-950
🈶1房1厅 750-1300
🈶2房1厅 850-1600
微信同步：13392660848（点头像加v）', 1, 0, 'sha256:1a27218e4042ee5631dce1ddfeddd86af83acd601d986f5864903e249809d7ce') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:275a9313345260894b74f335120e0328eb4d9e4ddc80f324c25eb845d1c329be', '2026-04-30 09:00', '.西塱附近靓房直租', 'text', '广州市', '海珠区', '凤凰新村', '[]', '["西塱","芳村","黄沙","凤凰新村","公园前"]', '[{"layout":"单间","rent_min":650,"rent_max":850},{"layout":"一房一厅","rent_min":750,"rent_max":1000},{"layout":"两房一厅","rent_min":900,"rent_max":1200},{"layout":"一房一厅","rent_min":650,"rent_max":850},{"layout":"两房一厅","rent_min":750,"rent_max":1000}]', 650, 1200, '[]', '[]', '["近地铁","家电齐全","阳台"]', '["19926090884"]', '[]', '电话：19926090884', '海珠区凤凰新村附近真实发布租房线索，单间650-850，一房一厅750-1000，两房一厅900-1200，一房一厅650-850', '西塱地铁新房火爆招租
公交直达十三行，如意坊，中山八
🍓家私齐全，拎包入住
📣 价格优惠，光线给力
单间 650-850【带阳台】
 🏬一房一厅750-1000【带阳台】
🏬两室一厅 900-1200【带阳台】
☎ 19926090884
 🚃公交15-25分钟直达十三行，西朗，鹤洞，芳村，如意坊，凤凰新村，宝业路口，🎡 宝岗大道橡胶新村，中山八路🎢
 地铁20分钟直达到黄沙，陈家祠，长寿路，公园前，西门口，文化公园，海珠广场左右哦！！', 1, 0, 'sha256:837033a5c4a477d7e5c6806388de575dcfb99dc2dd7df50164e8a7a92072343b') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:bccd94c7944fa37a8f37c8d952c7a4ac4ba1a8d7e5ca217f47268a8564b21698', '2026-05-01 17:38', '胡庆', 'text', '广州市', '海珠区', '凤凰新村/昌岗/沙园', '[]', '["菊树","芳村","黄沙","昌岗","沙园","凤凰新村"]', '[{"layout":"一房一厅","rent_min":750,"rent_max":1300},{"layout":"两房一厅","rent_min":850,"rent_max":1500},{"layout":"一房一厅","rent_min":650,"rent_max":900},{"layout":"两房一厅","rent_min":750,"rent_max":1300}]', 650, 1500, '[]', '[]', '["无中介费","近地铁","民水民电","家电齐全"]', '["13392660848"]', '["13392660848"]', '微信电话同步：13392660848（点头像加V）', '海珠区凤凰新村/昌岗/沙园附近真实发布租房线索，一房一厅750-1300，两房一厅850-1500，一房一厅650-900，两房一厅750-1300，无中介费，民水民电，家电齐全', '[红包][红包]荔湾区广佛线菊树地铁站

[红包]地铁十分钟🍀直达沙园、燕岗、凤凰新村、沥滘、千灯湖、金融高新区、西朗，芳村、黄沙、陈家祠、昌岗、宝岗、文化公园、十三行、南洲、同福西、西村等等

🚶🏻‍♀️房子步行到地铁口5分钟🚶🏻‍♀️
 [红包]家电齐全 拎包入住[红包]
 [礼物]民水民电 无中介费[礼物]
附近商场夜市公园菜鸟珠江肯德基应有尽有🌴🌴

🈶单 间 650-900
🈶一房一厅 750-1300
🈶两房一厅 850-1500
微信电话同步：13392660848（点头像加V）', 1, 0, 'sha256:3aec1c44e7357b45c45d67162dee52dce81639b2b71120b336e7404fb0dd569e') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:4d074d8316c68ebb52c99cacd51312e1e50d3ad22d7129f4ee56eac3c9b43261', '2026-04-30 12:43', '.琶洲房东直租－18825044020', 'text', '广州市', '番禺区', '大学城', '["8号线","11号线","12号线"]', '["大学城","客村","琶洲","赤岗"]', '[{"layout":"一房一厅","rent_min":880,"rent_max":1280},{"layout":"单间","rent_min":480,"rent_max":800},{"layout":"单间","rent_min":880,"rent_max":1280}]', 480, 1280, '[]', '[]', '["房东直租","近地铁"]', '["18825044020"]', '[]', '随时可以看房电话18825044020微信同号 。', '番禺区大学城附近真实发布租房线索，一房一厅880-1280，单间480-800，单间880-1280，房东直租', '[勾引] 优惠出租 [勾引]
12号线北山➕8号线琶洲
[福] 海珠区房东直租[福]
5分钟左右到地铁站

⚡电0.88，水3.75 💧 

一房一厅880-1280
单间480-800

🚇地铁直达11号线赤沙，12号线赤岗，官洲，大学城南，大学城北，赤岗塔，琶洲，天河公园，二沙岛，华师，万胜围，龙潭，广州塔等。

🚌公交车直达琶洲，磨碟沙，赤岗，客村等

随时可以看房电话18825044020微信同号 。', 1, 0, 'sha256:76194cab826150050bf0b7f9bb030e3964451a7ecaf1cceafd9edd7a7c09c7b4') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:7e7ea0ad76cf43389383c79f09e999d521ff76acd3ef0b331e50abc9734f0b3a', '2026-04-30 21:35', '天河黄村房东直租', 'text', '广州市', '番禺区', '大学城', '["4号线","21号线"]', '["黄村","车陂","员村","大学城"]', '[{"layout":"单间","rent_min":599,"rent_max":null},{"layout":"一房一厅","rent_min":799,"rent_max":null},{"layout":"两房一厅","rent_min":990,"rent_max":null},{"layout":"一房一厅","rent_min":599,"rent_max":null},{"layout":"两房一厅","rent_min":799,"rent_max":null}]', 599, 990, '["押一付一"]', '[]', '["房东直租","近地铁","民水民电","押一付一","采光好","家电齐全","阳台"]', '["13728553649"]', '[]', '两房一厅实惠：990💰 添加微信了解房源：13728553649', '番禺区大学城附近真实发布租房线索，单间599起，一房一厅799起，两房一厅990起，一房一厅599起，房东直租，民水民电，押一付一', '❗️天河区黄村精装房出租❗️
 🏡良心房东直租，光线好，带阳台，押一付一，民水民电，长''短可租❗️，家电家具齐全，即可拎包入住坐
 BRT公交直达师大暨大、岗顶、石牌桥、体育中心15-20分钟左右
🌇 核心商圈：天河路CBD | 万博商务区 | 奥体优托邦丨万科广场 | 大湾区生态走廊
 地铁🚇21号线天河区通往增城区，员村 天河公园 黄村 天河智慧城 镇龙 增城广场🚈
 地铁🚇4号线天河区通往海珠区，黄村 车陂南 万胜围 大学城南 南沙客运站🚈
 单间特价：599💰
 一房一厅优惠价：799💰
 两房一厅实惠：990💰 添加微信了解房源：13728553649', 1, 0, 'sha256:fad4611334b42278524e6162759a571c605110d4855ca926d9ace2293830df61') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:b7fe65313226f4b1d45e76ae014eecab0b1fe0ff74192a080a2c2a5cbc1e5f75', '2026-04-30 06:34', '爱杰的可可', 'text', '广州市', '番禺区', '大学城', '["13号线"]', '["黄村","珠村","大学城","琶洲"]', '[{"layout":"单间","rent_min":699,"rent_max":null},{"layout":"单间","rent_min":599,"rent_max":null},{"layout":"一房一厅","rent_min":699,"rent_max":null}]', 599, 699, '["押一付一"]', '["密码锁"]', '["房东直租","无中介费","近地铁","民水民电","押一付一","宠物友好","采光好"]', '["15202955805"]', '[]', '📞联系方式：15202955805（微信同步）15202955805', '番禺区大学城附近真实发布租房线索，单间699起，单间599起，一房一厅699起，房东直租，无中介费，民水民电，押一付一', '天河黄村4/21珠村13号线三地铁线房东直租
✅ 步行6分钟到地铁
✅ 房东直租 无中介费
✅ 民水民电 电费才0.88/度
✅ 押一付一
 
10-20分钟直达：大观南路、小新塘、天河智慧城、科学城
5-20分钟直达：东圃摩登城、天河软件园、天河公园、万胜围、琶洲、大学城北、羊城创意产业园、金融城绿地中心等😭
 
599起拿下阳光大单间☀️
699起住一房一厅🛋️

✅ 大门密码锁 外卖能上楼 安全感拉满
✅ 免费帮忙搬家 当天就能入住
✅ 宠物友好🐱🐶 再也不用和毛孩子分开
 
支持视频看房 一切好商量！
📞联系方式：15202955805（微信同步）15202955805', 1, 0, 'sha256:cdbadce6375a457b84ce70d6193fe9bf6ce1fdd9d151c250bc0b2999df81555f') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:3b16a537841e2aec7a75051192a94aefb49ede703c27b25e488ebe7067992d5e', '2026-04-30 19:35', 'A房东直租14749228883', 'text', '广州市', '荔湾区', '上下九', '[]', '["上下九","客村","昌岗","北京路","公园前"]', '[{"layout":"单间","rent_min":300,"rent_max":450},{"layout":"一房一厅","rent_min":500,"rent_max":600},{"layout":"两房一厅","rent_min":600,"rent_max":700},{"layout":"一房一厅","rent_min":300,"rent_max":450},{"layout":"两房一厅","rent_min":500,"rent_max":600}]', 300, 700, '[]', '[]', '["房东直租","近地铁"]', '["15113830731"]', '[]', '☎ ☎15113830731(微信同号)', '荔湾区上下九附近真实发布租房线索，单间300-450，一房一厅500-600，两房一厅600-700，一房一厅300-450，房东直租', '八号线石井地铁🚇 房东直租
🚶‍♂️步行8分钟左右到地铁口🚶‍♂️

精装单间300-450元
一房一厅500-600元
两房一厅600-700元

🚄地铁直达
陈 家 祠——华林寺
文化公园——同福西
宝岗大道——昌岗
中 大——客村

🚄地铁可转1号-3号到达
西门口——公园前
农讲所——烈士陵园
黄 沙——北京路
上下九等

周边生活便利，临菜市场，大型超市
☎ ☎15113830731(微信同号)', 1, 0, 'sha256:cc34a91dadc76775827ed27218f5ac60cb5c8c39c21a5f8ed2bdaffe0e11c5c8') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:40a4bbfe2cc922e2125cb6d937a0968d73934a3aabf6220aa8766b01a0ed8daa', '2026-04-30 08:57', '.aa白云区石井房东直租！！', 'text', '广州市', '荔湾区', '上下九', '["8号线"]', '["上下九","客村","中大","北京路","公园前"]', '[{"layout":"单间","rent_min":388,"rent_max":null},{"layout":"一房一厅","rent_min":500,"rent_max":null},{"layout":"两房一厅","rent_min":800,"rent_max":null},{"layout":"一房一厅","rent_min":388,"rent_max":null},{"layout":"两房一厅","rent_min":500,"rent_max":null}]', 388, 800, '["押一付一"]', '[]', '["房东直租","无中介费","近地铁","押一付一","家电齐全","阳台"]', '["15360479938","15839416681"]', '[]', '15360479938（微信同号）', '荔湾区上下九附近真实发布租房线索，单间388起，一房一厅500起，两房一厅800起，一房一厅388起，房东直租，无中介费，押一付一，近地铁，家电齐全', '🏠🏠8号线白云石井直租🏠🏠 

✅房东直租 无中介费
✅全新精装 独立阳台
✅民用水电 押一付一
✅家电齐全 拎包入住

💰单间388起
💰一房一厅500起
💰两房一厅800起
💰三房两厅两卫 
💰一楼95㎡仓库特价880

🚇交通超方便
步行近地铁8号线
10–35分钟直达：
陈家祠、华林寺、西门口、公园前、北京路、上下九、中大、客村、白云火车站等

🏬生活配套全
楼下商业街、超市、菜市场、小吃餐馆齐全
居住舒适，性价比超高！

📞看房热线
15839416681
15360479938（微信同号）
马年好房不等人，先到先选！', 1, 0, 'sha256:91e3de507f9a662f1bd6f6812c3c93da1bbf7bf77d4664fc0339031cd556a0ff') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:9cbbdc06c8b49f5b901c664499675f389349365da2a171a41d2bd091c2364697', '2026-04-30 09:34', '15217702823房东招租', 'text', '广州市', '荔湾区', '上下九', '[]', '["上下九","客村","中大","北京路","公园前"]', '[{"layout":"单间","rent_min":399,"rent_max":null},{"layout":"一房一厅","rent_min":699,"rent_max":null},{"layout":"两房一厅","rent_min":799,"rent_max":null},{"layout":"一房一厅","rent_min":399,"rent_max":null},{"layout":"两房一厅","rent_min":699,"rent_max":null}]', 399, 799, '["押一付一"]', '["监控"]', '["近地铁","押一付一","采光好","独卫","阳台"]', '["15217702823"]', '[]', '📲📲微信➕15217702823', '荔湾区上下九附近真实发布租房线索，单间399起，一房一厅699起，两房一厅799起，一房一厅399起，押一付一', '🚄8️⃣号线滘心自家房直租💯精装公寓
 （押一付一）👣步行到地铁口3️⃣-7️⃣分钟. 可转租
 🏙独立阳台、厨房、洗手间，阳光充足、格局美观、卫生整洁、
 精装单间💰399～
 一房一厅💰699～
 两房一厅💰799～
 大三房一厅💰💰
 🤖🤖楼下~楼道~周边有监控，安全有保证
 🚄🪐地铁15到35分钟直达陈家祠、华林寺、文化公园、中大、客村等🚀
🚄🪐地铁可转1号-5号-6号到达西门口、公园前、中山八、火车站、北京路、上下九等🚀
 🚘🛣周边生活便利，临菜市场，大型超市，各种餐馆，白云湖公园⛩
📲📲微信➕15217702823', 1, 0, 'sha256:3d8a190a214b0ab12737dba9bdfcd1729120b3ee0ebd0d317059c0a6c29b4470') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:ed48b9ed6f4749e0e90917ce5e199d64ba3a107cdf3bfd94b980ff1b73ca893b', '2026-05-01 16:54', 'A房东直租14749228883', 'text', '广州市', '荔湾区', '上下九', '[]', '["上下九","客村","昌岗","北京路","公园前"]', '[{"layout":"单间","rent_min":400,"rent_max":680},{"layout":"一房一厅","rent_min":650,"rent_max":850},{"layout":"两房一厅","rent_min":1000,"rent_max":1100},{"layout":"一房一厅","rent_min":400,"rent_max":680},{"layout":"两房一厅","rent_min":650,"rent_max":850}]', 400, 1100, '[]', '[]', '["房东直租","近地铁"]', '["15113830731"]', '[]', '☎ ☎15113830731(微信同号)', '荔湾区上下九附近真实发布租房线索，单间400-680，一房一厅650-850，两房一厅1000-1100，一房一厅400-680，房东直租', '八号线石井地铁🚇 房东直租
🚶‍♂️步行8分钟左右到地铁口🚶‍♂️

精装单间400-680元
一房一厅650-850元
两房一厅1000-1100元

🚄地铁直达
陈 家 祠——华林寺
文化公园——同福西
宝岗大道——昌岗
中 大——客村

🚄地铁可转1号-3号到达
西门口——公园前
农讲所——烈士陵园
黄 沙——北京路
上下九等

周边生活便利，临菜市场，大型超市
☎ ☎15113830731(微信同号)', 1, 0, 'sha256:3d69dcd75d571e9c128d3b88c86ea7bfb96170e192d3380c95557a1b9f5bc75d') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:d484859334ee4733b74151999a9bb3ec62489535829f76bebe60860b58743b7e', '2026-04-30 13:15', '.A8号线石井房东直租  中介勿扰', 'text', '广州市', '荔湾区', '上下九', '[]', '["上下九","客村","昌岗","北京路","公园前"]', '[{"layout":"单间","rent_min":450,"rent_max":550},{"layout":"一房一厅","rent_min":600,"rent_max":780},{"layout":"两房一厅","rent_min":900,"rent_max":1000},{"layout":"一房一厅","rent_min":450,"rent_max":550},{"layout":"两房一厅","rent_min":600,"rent_max":780}]', 450, 1000, '[]', '[]', '["房东直租","近地铁"]', '["17324261696"]', '[]', '电话：17324261696', '荔湾区上下九附近真实发布租房线索，单间450-550，一房一厅600-780，两房一厅900-1000，一房一厅450-550，房东直租', '八号线石井地铁🚇 房东直租
🚶‍♂步行8分钟左右到地铁口🚶‍♂
 
 

精装单间450-550元
一房一厅600-780元
两房一厅900-1000元

🚄地铁直达
鹅掌旦——西村、彩虹桥
陈 家 祠——华林寺
文化公园——同福西
宝岗大道——昌岗
中 大——客村

🚄地铁可转1号-3号-5号到达
广州火车站——三元里
越秀公园——纪念堂
西门口——公园前
农讲所——烈士陵园
黄 沙——北京路
上下九等

周边生活便利，临菜市场，大型超市
☎ ☎17324261696（信同号)', 1, 0, 'sha256:5216f53c2ebbdf676517449329fbd31f6eb7331874c168b2b7512273bc3eb207') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:90968566a78da590a743829df2cfd71dc7287cdede2071e338471701bf8ac371', '2026-04-30 14:58', '.石井凰岗房东直租15766743745', 'text', '广州市', '荔湾区', '上下九', '["8号线"]', '["上下九"]', '[{"layout":"单间","rent_min":500,"rent_max":null},{"layout":"单间","rent_min":550,"rent_max":null},{"layout":"一房一厅","rent_min":600,"rent_max":null},{"layout":"两房一厅","rent_min":880,"rent_max":null},{"layout":"一房一厅","rent_min":550,"rent_max":null},{"layout":"两房一厅","rent_min":600,"rent_max":null}]', 500, 880, '[]', '[]', '["房东直租","近地铁","家电齐全","阳台"]', '["15766743745"]', '[]', '详细了解，点击我头像，直接添加，随时欢迎看房，微信加15766743745', '荔湾区上下九附近真实发布租房线索，单间500起，单间550起，一房一厅600起，两房一厅880起，房东直租，近地铁，家电齐全', '🌹房东直租🌷
8号线石井出租房
单间500起
复式单间550起
一房一厅600起
两房一厅880起
家具齐全、[福]拎包入住，交通方便，旁边有公交站，靠近地铁站
精品装修、[發]环境优美，卫生干净，无巷子

直达小坪，石潭，鹅掌坦，上步，同德，陈家祠，聚龙，上下九，文化公园，华林寺等几分钟

独立阳台，无遮挡，家电齐全
 详细了解，点击我头像，直接添加，随时欢迎看房，微信加15766743745', 1, 0, 'sha256:03a5aa022d205b0afc5ecc493dace43500fa0f2b46d175dd8fdf16e9c7e1c45b') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:95aa86c5290dd4060e636077a90f0007ce2e8f5b22d1b1d8f404009539e827aa', '2026-04-30 14:01', '李新  租房群号', 'text', '广州市', '荔湾区', '上下九/黄沙', '["5号线","6号线"]', '["沙贝","横沙","黄沙","上下九","北京路","淘金","小北"]', '[{"layout":"单间","rent_min":500,"rent_max":750},{"layout":"一房一厅","rent_min":799,"rent_max":1199},{"layout":"两房一厅","rent_min":999,"rent_max":1399},{"layout":"一房一厅","rent_min":500,"rent_max":750},{"layout":"两房一厅","rent_min":799,"rent_max":1199}]', 500, 1399, '[]', '[]', '["近地铁","民水民电","可短租"]', '["17772089703","19068458278"]', '["17772089703"]', '电话：17772089703、19068458278；微信：17772089703', '荔湾区上下九/黄沙附近真实发布租房线索，单间500-750，一房一厅799-1199，两房一厅999-1399，一房一厅500-750，民水民电', '🚄6号线沙贝、横沙本地房东
 精装靓房首租
民水民电 釆光好 可短租
 单间：500-750
 一房一厅：799-1199
 二房一厅：999-1399

步行到地铁口6-8分钟
地铁5-20分钟可达 >坦尾 >如意坊 >黄沙 >文化公园 >一德路 >海珠广场 >北京路 >上下九 >十三行
可直转5号线 10-25分钟内到 >中山八 >西村 >广州火车站 >小北 >淘金

微信/电话同号：
17772089703
19068458278（免费看房）', 1, 0, 'sha256:6df6a43a8fc205b0ddd8487528e16e95e8f2f0f795ca01e13e3d17ff0f0443f3') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:22fa2467fb54319ee8bf44e3a8dfd6eb31c1128751d664282e95d164d60459d8', '2026-04-30 23:50', '李新  租房群号', 'text', '广州市', '荔湾区', '上下九/黄沙', '["5号线","6号线"]', '["沙贝","横沙","黄沙","上下九","北京路","淘金","小北"]', '[{"layout":"单间","rent_min":600,"rent_max":780},{"layout":"一房一厅","rent_min":799,"rent_max":1199},{"layout":"一房一厅","rent_min":600,"rent_max":780}]', 600, 1199, '[]', '[]', '["近地铁","民水民电","可短租"]', '["17772089703","19068458278"]', '["17772089703"]', '电话：17772089703、19068458278；微信：17772089703', '荔湾区上下九/黄沙附近真实发布租房线索，单间600-780，一房一厅799-1199，一房一厅600-780，民水民电', '🚄6号线沙贝、横沙本地房东
 精装靓房首租
民水民电 釆光好 可短租
 单间：600-780
 一房一厅：799-1199
步行到地铁口6-8分钟
地铁5-20分钟可达 >坦尾 >如意坊 >黄沙 >文化公园 >一德路 >海珠广场 >北京路 >上下九 >十三行
可直转5号线 10-25分钟内到 >中山八 >西村 >广州火车站 >小北 >淘金

微信/电话同号：
17772089703
19068458278（免费看房）', 1, 0, 'sha256:72bb1b5e1bcbfa99ef158cbf4643067a232581236fc13364765e4c9b0a6b89c7') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
INSERT INTO external_wechat_rental_listing (source_type, authenticity, verification_status, availability_status, source_file, source_group, source_message_hash, message_time, sender_alias, message_type, city_name, district_name, area_label, metro_lines, metro_stations, layouts, rent_min, rent_max, payment_tags, facility_tags, rental_tags, phone_numbers, wechat_ids, contact_text, description_text, raw_text, is_active, appointable, dedupe_key) VALUES ('WECHAT_GROUP', 'REAL_POSTED', 'UNVERIFIED', 'UNKNOWN', '../../参考资料/微信租房消息/广州租房群A134_全部消息.txt', '广州租房群A134-禁中介', 'sha256:3e780e63bd2eb84faac02f8056155f011292827b43076762ffd63e988001e02e', '2026-04-30 16:08', '金沙洲直租15820650238', 'text', '广州市', '荔湾区', '上下九/黄沙', '["6号线"]', '["横沙","黄沙","上下九","北京路"]', '[{"layout":"单间","rent_min":699,"rent_max":null},{"layout":"一房一厅","rent_min":899,"rent_max":null},{"layout":"两房一厅","rent_min":1280,"rent_max":null},{"layout":"一房一厅","rent_min":699,"rent_max":null},{"layout":"两房一厅","rent_min":899,"rent_max":null}]', 699, 1280, '[]', '[]', '["近地铁","采光好","家电齐全","阳台"]', '["15813316359","19068521738"]', '[]', '电话：15813316359、19068521738', '荔湾区上下九/黄沙附近真实发布租房线索，单间699起，一房一厅899起，两房一厅1280起，一房一厅699起，家电齐全', '🚅6号线横沙直租🚅
🏃‍♀步行8一10分钟，精装修，阳光房，环境舒适、家具家电齐全，拎包入住，民用水电、精装房🏠

 单间：699起🈶阳台
一房一厅：899起🈶
阳台
两房一厅：1280起🈶阳台
地铁直达🚅【河沙】【坦尾】【黄沙】【如意坊】【文化公园】【海珠广场】【一德路】【北京路】上下九、中山第二附属医院等
🎉欢迎大家微信🎉
☎15813316359
 19068521738
禁养宠物', 1, 0, 'sha256:9022e7d41129fa6dac56a1f819e7bee7f86fbeb9aef785aa70eea4a953df44a1') ON DUPLICATE KEY UPDATE source_type=VALUES(source_type), authenticity=VALUES(authenticity), verification_status=VALUES(verification_status), availability_status=VALUES(availability_status), source_file=VALUES(source_file), source_group=VALUES(source_group), message_time=VALUES(message_time), sender_alias=VALUES(sender_alias), message_type=VALUES(message_type), city_name=VALUES(city_name), district_name=VALUES(district_name), area_label=VALUES(area_label), metro_lines=VALUES(metro_lines), metro_stations=VALUES(metro_stations), layouts=VALUES(layouts), rent_min=VALUES(rent_min), rent_max=VALUES(rent_max), payment_tags=VALUES(payment_tags), facility_tags=VALUES(facility_tags), rental_tags=VALUES(rental_tags), phone_numbers=VALUES(phone_numbers), wechat_ids=VALUES(wechat_ids), contact_text=VALUES(contact_text), description_text=VALUES(description_text), raw_text=VALUES(raw_text), is_active=VALUES(is_active), appointable=VALUES(appointable), dedupe_key=VALUES(dedupe_key);
