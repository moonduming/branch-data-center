CREATE TABLE `line_id` (
	`ID` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增ID',
	`LINE_ID` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '条线编号',
	`LINE_ID_NAME` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '条线名称',
	`org_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '管理部室',
	PRIMARY KEY (`ID`)
) ENGINE = InnoDB AUTO_INCREMENT = 15 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_bin COMMENT = '条线编号表';

INSERT INTO
	shenzhen_data.line_id (LINE_ID, LINE_ID_NAME, org_code)
VALUES
	('L0101', '公司银行条线', '44030004'),
	('L0102', '投资银行条线', '44030007'),
	('L0103', '普惠金融条线', '44030004'),
	('L0104', '交易银行条线', '44030004'),
	('L0201', '个人信贷条线', '44030006'),
	('L0202', '个人金融条线', '44030005'),
	('L0203', '财富与私人银行条线', '44030005'),
	('L0204', '互联网贷款中心条线', '44030006'),
	('L0205', '信用卡条线', '44030006'),
	('L0299', '个人其它业务条线', '44030005');

INSERT INTO
	shenzhen_data.line_id (LINE_ID, LINE_ID_NAME, org_code)
VALUES
	('L0301', '金融市场条线', '44030004'),
	('L0302', '金融同业条线', '44030007'),
	('L0303', '托管业务条线', '44030007'),
	('L0105', '机构客户条线', '44030008');