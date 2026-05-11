from contextlib import nullcontext
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase
from django.db.models import Q
from rest_framework import serializers as drf_serializers
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.performance.serializers import CreateWorkflowSerializer
from apps.performance.views import ShenzhenPropStatusViewSet
from apps.users.models import User


class CreateWorkflowSerializerTests(SimpleTestCase):
    @patch("apps.performance.serializers.User.objects.filter")
    def test_validate_items_allows_duplicate_user_ids(self, mock_user_filter):
        mock_user_filter.return_value.values_list.return_value = [1, 2]

        serializer = CreateWorkflowSerializer()

        result = serializer.validate_items(
            [
                {"user_id": 1, "ecif_cust_id": "C001", "orig_acct_id": "A001"},
                {"user_id": 1, "ecif_cust_id": "C002", "orig_acct_id": "A002"},
                {"user_id": 2, "ecif_cust_id": "C003", "orig_acct_id": "A003"},
            ]
        )

        self.assertEqual([item["user_id"] for item in result], [1, 1, 2])

    def test_validate_requires_each_account_group_kpi_prop_total_to_equal_one_hundred_when_present(self):
        serializer = CreateWorkflowSerializer()

        with self.assertRaisesMessage(
            drf_serializers.ValidationError,
            "客户[GENR-001]的业绩占比之和必须刚好等于100",
        ):
            serializer.validate(
                {
                    "business_type": "performance_claim",
                    "data_dt": date(2026, 4, 29),
                    "items": [
                        {"user_id": 1, "genr_acct_id": "GENR-001", "ecif_cust_id": "C001", "orig_acct_id": "A001", "org_code": "44030001", "kpi_prop": Decimal("60")},
                        {"user_id": 2, "genr_acct_id": "GENR-001", "ecif_cust_id": "C001", "orig_acct_id": "A001", "org_code": "44030001", "kpi_prop": Decimal("30")},
                        {"user_id": 3, "genr_acct_id": "GENR-002", "ecif_cust_id": "C002", "orig_acct_id": "A002", "org_code": "44030001", "kpi_prop": Decimal("100")},
                    ],
                }
            )

    def test_validate_rejects_mixed_org_codes(self):
        serializer = CreateWorkflowSerializer()

        with self.assertRaisesMessage(
            drf_serializers.ValidationError,
            "items中的org_code必须一致",
        ):
            serializer.validate(
                {
                    "business_type": "performance_claim",
                    "data_dt": date(2026, 4, 29),
                    "items": [
                        {"user_id": 1, "genr_acct_id": "GENR-001", "ecif_cust_id": "C001", "orig_acct_id": "A001", "org_code": "44030001", "kpi_prop": Decimal("100")},
                        {"user_id": 2, "genr_acct_id": "GENR-002", "ecif_cust_id": "C002", "orig_acct_id": "A002", "org_code": "44030005", "kpi_prop": Decimal("100")},
                    ],
                }
            )

    @patch("apps.performance.serializers.WfProcessDef.objects.filter")
    @patch("apps.performance.serializers.ShenzhenPropStatus.objects.filter")
    def test_validate_converts_kpi_prop_by_account_group_after_group_validation(
        self,
        mock_prop_status_filter,
        mock_process_filter,
    ):
        mock_prop_status_filter.return_value.exclude.return_value.exists.return_value = False
        mock_process_filter.return_value.order_by.return_value.first.return_value = SimpleNamespace(id=9)

        serializer = CreateWorkflowSerializer()

        result = serializer.validate(
            {
                "business_type": "performance_claim",
                "data_dt": date(2026, 4, 29),
                "items": [
                    {"user_id": 1, "genr_acct_id": "GENR-001", "ecif_cust_id": "C001", "orig_acct_id": "A001", "org_code": "44030001", "kpi_prop": Decimal("50")},
                    {"user_id": 2, "genr_acct_id": "GENR-001", "ecif_cust_id": "C001", "orig_acct_id": "A001", "org_code": "44030001", "kpi_prop": Decimal("50")},
                    {"user_id": 3, "genr_acct_id": "GENR-002", "ecif_cust_id": "C002", "orig_acct_id": "A002", "org_code": "44030001", "kpi_prop": Decimal("30")},
                    {"user_id": 4, "genr_acct_id": "GENR-002", "ecif_cust_id": "C002", "orig_acct_id": "A002", "org_code": "44030001", "kpi_prop": Decimal("70")},
                ],
            }
        )

        self.assertEqual([item["kpi_prop"] for item in result["items"]], [
            Decimal("0.5000"),
            Decimal("0.5000"),
            Decimal("0.3000"),
            Decimal("0.7000"),
        ])


class ShenzhenPropStatusViewSetTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin_user = User(id=1, username="admin", full_name="管理员", user_level=User.Level.ADMIN)

    def test_serialize_account_summary_maps_org_name_and_claim_fields(self):
        view = ShenzhenPropStatusViewSet()
        claim_time = datetime(2026, 4, 28, 9, 30, 0)

        result = view._serialize_account_summary(
            {
                "mng_org_id": "M001",
                "accnt_org_id": "44000001",
                "accnt_org_name": "深圳分行",
                "ecif_cust_id": "C001",
                "orig_acct_id": "A001",
                "genr_acct_id": "G001",
                "cust_name": "张三",
                "bal_year_accum": "120.0000",
                "data_dt": date(2026, 1, 12),
                "line_id_name": "公司银行条线",
                "org_code": "44030001",
                "mng_accnt_prod_name": "徽银e贷",
                "cust_type_cd": "01",
                "biz_type_cd": "02",
                "claim_flag": "0",
                "claim_time": claim_time,
                "prop_people_list": [
                    {"employee_no": "u01", "employee_name": "张三", "kpi_prop": Decimal("0.5000")},
                ],
            }
        )

        self.assertEqual(result["accnt_org_id"], "44000001")
        self.assertEqual(result["accnt_org_name"], "深圳分行")
        self.assertEqual(result["year_daily_avg"], Decimal("10.00"))
        self.assertEqual(result["line_id_name"], "公司银行条线")
        self.assertEqual(result["org_code"], "44030001")
        self.assertEqual(result["mng_accnt_prod_name"], "徽银e贷")
        self.assertEqual(result["claim_status"], "审核中")
        self.assertEqual(result["claim_time"], claim_time)
        self.assertEqual(
            result["prop_people_list"],
            [{"employee_no": "u01", "employee_name": "张三", "kpi_prop": Decimal("0.5000")}],
        )

    @patch("apps.performance.views.connection")
    @patch("apps.performance.views.OrgUnit.objects.filter")
    def test_build_account_queryset_uses_raw_sql_and_attaches_org_names(
        self,
        mock_org_filter,
        mock_connection,
    ):
        cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.description = [
            ("accnt_org_id",),
            ("ecif_cust_id",),
            ("mng_org_id",),
            ("orig_acct_id",),
            ("genr_acct_id",),
            ("cust_name",),
            ("year_daily_avg",),
            ("bal_year_accum",),
            ("data_dt",),
            ("line_id_name",),
            ("org_code",),
            ("mng_accnt_prod_name",),
            ("cust_type_cd",),
            ("biz_type_cd",),
        ]
        cursor.fetchall.return_value = [
            (
                "44000001", "C001", "44000001", "A001", "G001", "张三",
                Decimal("10.00"), Decimal("120.0000"), date(2026, 1, 12),
                "公司银行条线", "44030001", "徽银e贷", "01", "02",
            ),
            (
                "44000002", "C002", "44000002", "", "G002", "李四",
                Decimal("20.00"), Decimal("220.0000"), date(2026, 1, 12),
                "个人金融条线", "44030005", "个人产品...", "03", "04",
            ),
        ]

        org_name_queryset = MagicMock()
        org_code_queryset = MagicMock()
        mock_org_filter.return_value = org_name_queryset
        mock_org_filter.side_effect = [org_code_queryset, org_name_queryset]
        org_code_queryset.values_list.return_value.first.return_value = "44000001"
        org_name_queryset.values.return_value = [
            {"org_code": "44000001", "org_name": "深圳分行"},
            {"org_code": "44000002", "org_name": "南山支行"},
        ]

        view = ShenzhenPropStatusViewSet()
        items = view._build_account_queryset(key="C001", org_id=1, prop_status_flg="0")

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["accnt_org_name"], "深圳分行")
        self.assertEqual(items[0]["line_id_name"], "公司银行条线")
        self.assertEqual(items[0]["org_code"], "44030001")
        self.assertEqual(items[0]["mng_accnt_prod_name"], "徽银e贷")
        self.assertEqual(items[1]["line_id_name"], "个人金融条线")
        executed_sql = cursor.execute.call_args.args[0]
        self.assertIn("UNION ALL", executed_sql)
        self.assertIn("a.ACCNT_ORG_ID = %s OR a.MNG_ORG_ID = %s OR a.MNG_ORG_ID LIKE %s", executed_sql)
        self.assertIn("c.org_code = '44030005'", executed_sql)
        self.assertEqual(
            cursor.execute.call_args.args[1],
            [
                "C001", "C001", "C001", "44000001", "44000001", "%44000001",
                "C001", "C001", "C001", "44000001", "44000001", "%44000001",
            ],
        )

    @patch("apps.performance.views.ShenzhenPropStatus.objects.filter")
    def test_attach_claim_status_info_groups_latest_batch_and_excludes_invalid(self, mock_prop_status_filter):
        rows = [
            {
                "id": 1,
                "process_instance_id": 100,
                "data_dt": date(2026, 5, 1),
                "genr_acct_id": "G001",
                "cust_name": "张三",
                "ecif_cust_id": "C001",
                "orig_acct_id": "A001",
                "accounting_org_id": "44000001",
                "employee_no": "u01",
                "employee_name": "张三",
                "kpi_prop": Decimal("0.5000"),
                "prop_status_flg": "0",
                "apl_data_dt": datetime(2026, 5, 1, 9, 0, 0),
            },
            {
                "id": 2,
                "process_instance_id": 100,
                "data_dt": date(2026, 5, 1),
                "genr_acct_id": "G001",
                "cust_name": "张三",
                "ecif_cust_id": "C001",
                "orig_acct_id": "A001",
                "accounting_org_id": "44000001",
                "employee_no": "u02",
                "employee_name": "李四",
                "kpi_prop": Decimal("0.5000"),
                "prop_status_flg": "1",
                "apl_data_dt": datetime(2026, 5, 1, 10, 0, 0),
            },
            {
                "id": 3,
                "process_instance_id": 200,
                "data_dt": date(2026, 5, 2),
                "genr_acct_id": "G002",
                "cust_name": "王五",
                "ecif_cust_id": "C002",
                "orig_acct_id": "A002",
                "accounting_org_id": "44000002",
                "employee_no": "u03",
                "employee_name": "王五",
                "kpi_prop": Decimal("1.0000"),
                "prop_status_flg": "2",
                "apl_data_dt": datetime(2026, 5, 2, 10, 0, 0),
            },
        ]
        mock_prop_status_filter.return_value.values.return_value.order_by.return_value = rows

        view = ShenzhenPropStatusViewSet()
        result = view._attach_claim_status_info(
            [
                {
                    "data_dt": date(2026, 5, 1),
                    "genr_acct_id": "G001",
                },
                {
                    "data_dt": date(2026, 5, 2),
                    "genr_acct_id": "G002",
                }
            ],
            prop_status_flg="",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["claim_flag"], "1")
        self.assertEqual(result[0]["claim_time"], datetime(2026, 5, 1, 10, 0, 0))
        self.assertEqual(
            result[0]["prop_people_list"],
            [
                {"employee_no": "u01", "employee_name": "张三", "kpi_prop": Decimal("0.5000"), "data_dt": date(2026, 5, 1)},
                {"employee_no": "u02", "employee_name": "李四", "kpi_prop": Decimal("0.5000"), "data_dt": date(2026, 5, 1)},
            ],
        )

    @patch("apps.performance.views.ShenzhenPropStatusViewSet._build_account_queryset")
    @patch("apps.performance.views.ShenzhenPropStatus.objects.filter")
    def test_build_transfer_queryset_uses_prop_status_org_code_as_fallback(
        self,
        mock_prop_status_filter,
        mock_build_account_queryset,
    ):
        status_queryset = MagicMock()
        filtered_status_queryset = MagicMock()
        mock_prop_status_filter.return_value = status_queryset
        status_queryset.filter.return_value = filtered_status_queryset
        filtered_status_queryset.values.return_value.order_by.return_value = [
            {
                "id": 1,
                "process_instance_id": 100,
                "data_dt": date(2026, 5, 1),
                "genr_acct_id": "G001",
                "cust_name": "张三",
                "ecif_cust_id": "C001",
                "orig_acct_id": "A001",
                "accounting_org_id": "44000001",
                "line_org_code": "44030005",
                "employee_no": "u01",
                "employee_name": "张三",
                "kpi_prop": Decimal("1.0000"),
                "prop_status_flg": "1",
                "apl_data_dt": datetime(2026, 5, 1, 10, 0, 0),
            }
        ]

        mock_build_account_queryset.return_value = [
            {
                "mng_org_id": "44000001",
                "accnt_org_id": "44000001",
                "ecif_cust_id": "C001",
                "orig_acct_id": "",
                "genr_acct_id": "G001",
                "cust_name": "张三",
                "bal_year_accum": Decimal("120.0000"),
                "data_dt": date(2026, 5, 1),
                "year_daily_avg": Decimal("10.00"),
                "line_id_name": "个人金融条线",
                "mng_accnt_prod_name": "个人产品...",
                "cust_type_cd": "01",
                "biz_type_cd": "02",
                "org_code": "44030005",
                "mng_org_name": "深圳分行",
                "accnt_org_name": "深圳分行",
            }
        ]

        view = ShenzhenPropStatusViewSet()
        view._get_org_code = Mock(return_value="44000001")
        items = view._build_transfer_queryset(key="C001", org_id=1)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["org_code"], "44030005")
        self.assertEqual(items[0]["claim_flag"], "1")
        self.assertEqual(items[0]["line_id_name"], "个人金融条线")

    @patch("apps.performance.views.transaction.atomic", return_value=nullcontext())
    @patch("apps.performance.views.ShenzhenPropStatus.objects.bulk_create")
    @patch("apps.performance.views.OrgUnit.objects.filter")
    @patch("apps.performance.views.UserOrgRelation.objects.filter")
    @patch("apps.performance.views.User.objects.filter")
    @patch("apps.performance.views.WfTask.objects.filter")
    @patch("apps.performance.views.WorkflowRuntimeService")
    @patch("apps.performance.views.CreateWorkflowSerializer")
    def test_create_workflow_uses_shared_header_and_item_list(
        self,
        mock_serializer_cls,
        mock_service_cls,
        mock_task_filter,
        mock_user_filter,
        mock_relation_filter,
        mock_org_filter,
        mock_bulk_create,
        _mock_atomic,
    ):
        serializer = Mock()
        serializer.validated_data = {
            "process_def_id": 9,
            "action_code": "submit",
            "business_type": "performance_claim",
            "data_dt": date(2026, 4, 28),
            "items": [
                {
                    "user_id": 11,
                    "genr_acct_id": "GENR-001",
                    "ecif_cust_id": "C001",
                    "orig_acct_id": "A001",
                    "org_code": "44030001",
                    "cust_name": "客户一",
                    "kpi_prop": Decimal("50.0000"),
                    "year_base_amount": "100.00",
                },
                {
                    "user_id": 11,
                    "genr_acct_id": "GENR-002",
                    "ecif_cust_id": "C002",
                    "orig_acct_id": "A002",
                    "org_code": "44030001",
                    "cust_name": "客户二",
                    "kpi_prop": Decimal("30.0000"),
                    "year_base_amount": "200.00",
                },
                {
                    "user_id": 22,
                    "genr_acct_id": "GENR-003",
                    "ecif_cust_id": "C003",
                    "orig_acct_id": "A003",
                    "org_code": "44030001",
                    "cust_name": "客户三",
                    "kpi_prop": Decimal("20.0000"),
                    "year_base_amount": "300.00",
                },
            ],
        }
        mock_serializer_cls.return_value = serializer

        service = Mock()
        service.start_instance.return_value = SimpleNamespace(id=101)
        mock_service_cls.return_value = service
        mock_task_filter.return_value.first.return_value = SimpleNamespace(id=301)

        user_queryset = Mock()
        user_queryset.values.return_value = [
            {"id": 11, "username": "u11", "full_name": "张三"},
            {"id": 22, "username": "u22", "full_name": "李四"},
        ]
        mock_user_filter.return_value = user_queryset

        relation_queryset = Mock()
        relation_queryset.order_by.return_value = [
            SimpleNamespace(user_id=11, org_id=501),
            SimpleNamespace(user_id=22, org_id=502),
        ]
        mock_relation_filter.return_value = relation_queryset

        org_queryset = Mock()
        org_queryset.values.return_value = [
            {"id": 501, "org_code": "44000001", "org_name": "深圳分行"},
            {"id": 502, "org_code": "44000002", "org_name": "南山支行"},
        ]
        mock_org_filter.return_value = org_queryset

        request = self.factory.post("/api/performance/prop-statuses/create_workflow/", {}, format="json")
        force_authenticate(request, user=self.admin_user)

        response = ShenzhenPropStatusViewSet.as_view({"post": "create_workflow"})(request)

        self.assertEqual(response.status_code, 201)
        service.handle_task_action.assert_called_once_with(
            task_id=301,
            action_code="submit",
            operator=self.admin_user,
            selected_user_ids=[11, 22],
        )
        records = mock_bulk_create.call_args.args[0]
        self.assertEqual(len(records), 3)
        self.assertEqual([item.employee_no for item in records], ["u11", "u11", "u22"])
        self.assertEqual([item.employee_name for item in records], ["张三", "张三", "李四"])
        self.assertEqual([item.cust_name for item in records], ["客户一", "客户二", "客户三"])
        self.assertEqual([item.ecif_cust_id for item in records], ["C001", "C002", "C003"])
        self.assertEqual([item.acctn_org_name for item in records], ["深圳分行", "深圳分行", "南山支行"])
        self.assertEqual([item.line_org_code for item in records], ["44030001", "44030001", "44030001"])
        self.assertEqual(response.data["data"]["created_count"], 3)
