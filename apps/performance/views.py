from datetime import date, datetime
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AcctSumD, LineId, MngAccntProd, ShenzhenPropStatus, PropStatusFlg
from .serializers import ShenzhenPropStatusSerializer, CreateWorkflowSerializer
from ..workflow.models import WfTask
from ..users.models import User
from ..organization.models import OrgUnit, UserOrgRelation
from ..workflow.runtime import WorkflowRuntimeService


class ShenzhenPropStatusViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ShenzhenPropStatus.objects.all().order_by("process_instance_id", "id")
    serializer_class = ShenzhenPropStatusSerializer

    @staticmethod
    def _deduplicate_user_ids(user_ids):
        return list(dict.fromkeys(user_ids))

    @staticmethod
    def _build_claim_status(prop_status_flg):
        if prop_status_flg == "1":
            return "审核完成"
        if prop_status_flg == "0":
            return "审核中"
        if prop_status_flg == "2":
            return "认领失效"
        return "未认领"

    @staticmethod
    def _build_key_filter(key):
        return Q(ecif_cust_id=key) | Q(orig_acct_id=key) | Q(cust_name=key)

    @staticmethod
    def _get_status_sort_key(row):
        apl_data_dt = row.get("apl_data_dt")
        if apl_data_dt is None:
            return (datetime.min, row.get("id") or 0)
        if timezone.is_aware(apl_data_dt):
            apl_data_dt = timezone.localtime(apl_data_dt).replace(tzinfo=None)
        return (apl_data_dt, row.get("id") or 0)

    @staticmethod
    def _calculate_year_daily_average(data_dt, bal_year_accum):
        if not data_dt or bal_year_accum is None:
            return None

        first_day_of_year = date(data_dt.year, 1, 1)
        day_count = (data_dt - first_day_of_year).days + 1
        if day_count <= 0:
            return None

        return (Decimal(bal_year_accum) / Decimal(day_count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _serialize_account_summary(self, item):
        return {
            "mng_org_id": item.get("mng_org_id"),
            "mng_org_name": item.get("mng_org_name"),
            "accnt_org_id": item.get("accnt_org_id"),
            "accnt_org_name": item.get("accnt_org_name"),
            "ecif_cust_id": item.get("ecif_cust_id"),
            "orig_acct_id": item.get("orig_acct_id"),
            "genr_acct_id": item.get("genr_acct_id"),
            "cust_name": item.get("cust_name"),
            "year_daily_avg": (
                item.get("year_daily_avg")
                if item.get("year_daily_avg") is not None
                else self._calculate_year_daily_average(item.get("data_dt"), item.get("bal_year_accum"))
            ),
            "line_id_name": item.get("line_id_name"),
            "org_code": item.get("org_code"),
            "mng_accnt_prod_name": item.get("mng_accnt_prod_name"),
            "cust_type_cd": item.get("cust_type_cd"),
            "biz_type_cd": item.get("biz_type_cd"),
            "claim_status": self._build_claim_status(item.get("claim_flag")),
            "claim_time": item.get("claim_time"),
            "prop_people_list": item.get("prop_people_list") or [],
        }

    def _get_org_code(self, org_id):
        org_code = (
            OrgUnit.objects
            .filter(id=org_id, status=OrgUnit.Status.NORMAL)
            .values_list("org_code", flat=True)
            .first()
        )
        if not org_code:
            raise ValidationError({"message": "机构不存在或已停用"})
        return org_code

    def _attach_org_name_info(self, items):
        if not items:
            return []

        org_ids = {
            org_id
            for item in items
            for org_id in (item.get("accnt_org_id"), item.get("mng_org_id"))
            if org_id
        }
        org_name_map = {
            item["org_code"]: item["org_name"]
            for item in OrgUnit.objects.filter(
                org_code__in=org_ids,
                status=OrgUnit.Status.NORMAL,
            ).values("org_code", "org_name")
        }
        for item in items:
            item["mng_org_name"] = org_name_map.get(item.get("mng_org_id"))
            item["accnt_org_name"] = org_name_map.get(item.get("accnt_org_id"))
        return items

    def _build_account_queryset(self, *, key, org_id=None, org_code=None, **_ignored):
        org_code = org_code or self._get_org_code(org_id)

        sql = """
            SELECT *
            FROM (
                SELECT
                    a.ACCNT_ORG_ID AS accnt_org_id,
                    a.ECIF_CUST_ID AS ecif_cust_id,
                    a.MNG_ORG_ID AS mng_org_id,
                    a.ORIG_ACCT_ID AS orig_acct_id,
                    a.GENR_ACCT_ID AS genr_acct_id,
                    a.CUST_NAME AS cust_name,
                    ROUND(
                        a.BAL_YEAR_ACCUM / (DATEDIFF(a.DATA_DT, DATE_FORMAT(a.DATA_DT, '%%Y-01-01')) + 1),
                        2
                    ) AS year_daily_avg,
                    a.BAL_YEAR_ACCUM AS bal_year_accum,
                    a.DATA_DT AS data_dt,
                    c.LINE_ID_NAME AS line_id_name,
                    c.org_code AS org_code,
                    b.MNG_ACCNT_PROD_NAME AS mng_accnt_prod_name,
                    a.CUST_TYPE_CD AS cust_type_cd,
                    a.BIZ_TYPE_CD AS biz_type_cd
                FROM i01_sz_acct_sum_d AS a
                JOIN mng_accnt_prod AS b
                    ON a.MNG_ACCNT_PROD_ID = b.MNG_ACCNT_PROD_ID
                JOIN line_id AS c
                    ON a.LINE_ID = c.LINE_ID
                WHERE a.CCY_CD IN ('156', 'B02')
                  AND a.ORIG_ACCT_ID IS NOT NULL
                  AND a.LINE_ID <> 'L0205'
                  AND (a.CUST_NAME = %s OR a.ORIG_ACCT_ID = %s OR a.ECIF_CUST_ID = %s)
                  AND a.ACCNT_ORG_ID = %s
                  AND c.org_code <> '44030005'

                UNION ALL

                SELECT
                    MAX(a.ACCNT_ORG_ID) AS accnt_org_id,
                    a.ECIF_CUST_ID AS ecif_cust_id,
                    MAX(a.MNG_ORG_ID) AS mng_org_id,
                    '' AS orig_acct_id,
                    MAX(a.GENR_ACCT_ID) AS genr_acct_id,
                    MAX(a.CUST_NAME) AS cust_name,
                    ROUND(
                        SUM(a.BAL_YEAR_ACCUM) / (DATEDIFF(MAX(a.DATA_DT), DATE_FORMAT(MAX(a.DATA_DT), '%%Y-01-01')) + 1),
                        2
                    ) AS year_daily_avg,
                    SUM(a.BAL_YEAR_ACCUM) AS bal_year_accum,
                    MAX(a.DATA_DT) AS data_dt,
                    '个人金融条线' AS line_id_name,
                    c.org_code AS org_code,
                    CONCAT(MAX(b.MNG_ACCNT_PROD_NAME), '...') AS mng_accnt_prod_name,
                    MAX(a.CUST_TYPE_CD) AS cust_type_cd,
                    MAX(a.BIZ_TYPE_CD) AS biz_type_cd
                FROM i01_sz_acct_sum_d AS a
                JOIN mng_accnt_prod AS b
                    ON a.MNG_ACCNT_PROD_ID = b.MNG_ACCNT_PROD_ID
                JOIN line_id AS c
                    ON a.LINE_ID = c.LINE_ID
                WHERE a.CCY_CD IN ('156', 'B02')
                  AND a.ORIG_ACCT_ID IS NOT NULL
                  AND a.LINE_ID <> 'L0205'
                  AND (a.CUST_NAME = %s OR a.ORIG_ACCT_ID = %s OR a.ECIF_CUST_ID = %s)
                  AND a.ACCNT_ORG_ID = %s
                  AND c.org_code = '44030005'
                GROUP BY a.ECIF_CUST_ID, c.org_code
            ) AS account_rows
            ORDER BY org_code, ecif_cust_id, orig_acct_id
        """
        params = [
            key, key, key, org_code,
            key, key, key, org_code,
        ]
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [column[0] for column in cursor.description]
            items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return self._attach_org_name_info(items)

    def _attach_reference_info(self, items, *, drop_missing_reference=True):
        if not items:
            return []

        accnt_org_ids = {item.get("accnt_org_id") for item in items if item.get("accnt_org_id")}
        mng_org_ids = {item.get("mng_org_id") for item in items if item.get("mng_org_id")}
        line_ids = {item.get("line_id") for item in items if item.get("line_id")}
        mng_accnt_prod_ids = {item.get("mng_accnt_prod_id") for item in items if item.get("mng_accnt_prod_id")}
        org_ids = accnt_org_ids | mng_org_ids
        org_name_map = {
            item["org_code"]: item["org_name"]
            for item in OrgUnit.objects.filter(
                org_code__in=org_ids,
                status=OrgUnit.Status.NORMAL,
            ).values("org_code", "org_name")
        }
        line_map = {
            item["line_id"]: {
                "line_id_name": item["line_id_name"],
                "org_code": item["org_code"],
            }
            for item in LineId.objects.filter(line_id__in=line_ids).values("line_id", "line_id_name", "org_code")
        }
        mng_accnt_prod_name_map = {
            item["mng_accnt_prod_id"]: item["mng_accnt_prod_name"]
            for item in MngAccntProd.objects.filter(mng_accnt_prod_id__in=mng_accnt_prod_ids).values(
                "mng_accnt_prod_id",
                "mng_accnt_prod_name",
            )
        }

        result = []
        for item in items:
            item["mng_org_name"] = org_name_map.get(item.get("mng_org_id"))
            item["accnt_org_name"] = org_name_map.get(item.get("accnt_org_id"))
            line_info = line_map.get(item.get("line_id")) or {}
            item["line_id_name"] = line_info.get("line_id_name")
            item["org_code"] = line_info.get("org_code") or item.get("org_code")
            item["mng_accnt_prod_name"] = mng_accnt_prod_name_map.get(item.get("mng_accnt_prod_id"))
            if drop_missing_reference and (not item["line_id_name"] or not item["mng_accnt_prod_name"]):
                continue
            result.append(item)
        return result

    def _group_prop_status_queryset(self, queryset, *, group_field="genr_acct_id"):
        grouped_rows = defaultdict(list)
        for row in queryset.values(
            "id",
            "process_instance_id",
            "data_dt",
            "genr_acct_id",
            "cust_name",
            "ecif_cust_id",
            "orig_acct_id",
            "accounting_org_id",
            "line_org_code",
            "employee_no",
            "employee_name",
            "kpi_prop",
            "prop_status_flg",
            "apl_data_dt",
        ).order_by("genr_acct_id", "apl_data_dt", "id"):
            group_value = row.get(group_field)
            if group_value:
                grouped_rows[group_value].append(row)

        prop_status_map = {}
        for group_value, rows in grouped_rows.items():
            latest_row = max(rows, key=self._get_status_sort_key)
            latest_process_instance_id = latest_row.get("process_instance_id")
            if latest_process_instance_id is not None:
                current_rows = [
                    row for row in rows
                    if row.get("process_instance_id") == latest_process_instance_id
                ]
            else:
                current_rows = [latest_row]
            prop_status_map[group_value] = {
                "claim_flag": latest_row.get("prop_status_flg"),
                "claim_time": latest_row.get("apl_data_dt"),
                "cust_name": latest_row.get("cust_name"),
                "ecif_cust_id": latest_row.get("ecif_cust_id"),
                "orig_acct_id": latest_row.get("orig_acct_id"),
                "accounting_org_id": latest_row.get("accounting_org_id"),
                "line_org_code": latest_row.get("line_org_code"),
                "data_dt": latest_row.get("data_dt"),
                "prop_people_list": [
                    {
                        "employee_no": row.get("employee_no"),
                        "employee_name": row.get("employee_name"),
                        "kpi_prop": row.get("kpi_prop"),
                        "prop_status_flg": self._build_claim_status(
                            row.get("prop_status_flg")
                        ),
                        "data_dt": row.get("data_dt"),
                    }
                    for row in current_rows
                ],
            }
        return prop_status_map

    def _build_prop_status_map(self, genr_acct_ids, *, status_filter=None):
        if not genr_acct_ids:
            return {}

        queryset = ShenzhenPropStatus.objects.filter(genr_acct_id__in=genr_acct_ids)
        if status_filter:
            queryset = queryset.filter(prop_status_flg=status_filter)
        return self._group_prop_status_queryset(queryset)

    def _build_prop_status_map_by_ecif(self, ecif_cust_ids, *, status_filter=None):
        if not ecif_cust_ids:
            return {}

        queryset = ShenzhenPropStatus.objects.filter(ecif_cust_id__in=ecif_cust_ids)
        if status_filter:
            queryset = queryset.filter(prop_status_flg=status_filter)
        return self._group_prop_status_queryset(queryset, group_field="ecif_cust_id")

    def _attach_claim_status_info(self, items, *, prop_status_flg):
        if not items:
            return []

        prop_status_map = self._build_prop_status_map(
            [item.get("genr_acct_id") for item in items if item.get("genr_acct_id")]
        )
        prop_status_map_by_ecif = self._build_prop_status_map_by_ecif(
            [
                item.get("ecif_cust_id")
                for item in items
                if item.get("ecif_cust_id") and item.get("org_code") == "44030005"
            ]
        )

        result = []
        for item in items:
            prop_status_info = prop_status_map.get(item.get("genr_acct_id")) or {}
            if not prop_status_info and item.get("org_code") == "44030005":
                prop_status_info = prop_status_map_by_ecif.get(item.get("ecif_cust_id")) or {}
            claim_flag = prop_status_info.get("claim_flag")
            # if claim_flag == PropStatusFlg.INVALID:
            #     continue
            item["claim_flag"] = claim_flag
            item["claim_time"] = prop_status_info.get("claim_time")
            item["prop_people_list"] = prop_status_info.get("prop_people_list", [])
            if prop_status_flg and item["claim_flag"] != prop_status_flg:
                continue
            result.append(item)
        return result

    def _build_transfer_queryset(self, *, key, org_id):
        org_code = self._get_org_code(org_id)
        prop_status_map = self._group_prop_status_queryset(
            ShenzhenPropStatus.objects
            .filter(accounting_org_id=org_code, prop_status_flg=PropStatusFlg.YES)
        )
        if not prop_status_map:
            return []

        account_rows = self._build_account_queryset(org_id=org_id, key=key)
        account_map = {
            row["genr_acct_id"]: row
            for row in account_rows
            if row.get("genr_acct_id")
        }
        personal_line_map = {
            row["ecif_cust_id"]: row
            for row in account_rows
            if row.get("ecif_cust_id") and row.get("org_code") == "44030005"
        }

        items = []
        for genr_acct_id, prop_status_info in prop_status_map.items():
            account_item = (
                account_map.get(genr_acct_id)
                or personal_line_map.get(prop_status_info.get("ecif_cust_id"))
                or {}
            )
            items.append(
                {
                    "mng_org_id": account_item.get("mng_org_id"),
                    "accnt_org_id": account_item.get("accnt_org_id") or prop_status_info.get("accounting_org_id"),
                    "ecif_cust_id": account_item.get("ecif_cust_id") or prop_status_info.get("ecif_cust_id"),
                    "orig_acct_id": account_item.get("orig_acct_id") or prop_status_info.get("orig_acct_id"),
                    "genr_acct_id": genr_acct_id,
                    "cust_name": account_item.get("cust_name") or prop_status_info.get("cust_name"),
                    "bal_year_accum": account_item.get("bal_year_accum"),
                    "data_dt": account_item.get("data_dt") or prop_status_info.get("data_dt"),
                    "year_daily_avg": account_item.get("year_daily_avg"),
                    "line_id_name": account_item.get("line_id_name"),
                    "mng_accnt_prod_name": account_item.get("mng_accnt_prod_name"),
                    "cust_type_cd": account_item.get("cust_type_cd"),
                    "biz_type_cd": account_item.get("biz_type_cd"),
                    "claim_flag": prop_status_info.get("claim_flag"),
                    "claim_time": prop_status_info.get("claim_time"),
                    "prop_people_list": prop_status_info.get("prop_people_list", []),
                    "org_code": account_item.get("org_code") or prop_status_info.get("line_org_code"),
                    "mng_org_name": account_item.get("mng_org_name"),
                    "accnt_org_name": account_item.get("accnt_org_name"),
                }
            )

        return items

    def _get_list_params(self, request):
        prop_status_flg = (request.query_params.get("prop_status_flg") or "").strip()
        org_id = (request.query_params.get("org_id") or "").strip()
        key = (request.query_params.get("key") or "").strip()

        if not key and not org_id:
            return None, None, prop_status_flg, Response({"message": "查询成功", "data": []})

        if not key or not org_id:
            raise ValidationError({"message": "key 和 org_id 不能为空"})

        try:
            org_id = int(org_id)
        except ValueError:
            raise ValidationError({"message": "org_id 参数不合法"})

        return key, org_id, prop_status_flg, None

    def _build_list_response(self, items):
        page = self.paginate_queryset(items)
        if page is not None:
            data = [self._serialize_account_summary(item) for item in page]
            return self.get_paginated_response(data)

        data = [self._serialize_account_summary(item) for item in items]
        return Response({"message": "查询成功", "data": data})

    def _claim_list_response(self, request):
        key, org_id, prop_status_flg, empty_response = self._get_list_params(request)
        if empty_response is not None:
            return empty_response

        items = self._build_account_queryset(
            key=key,
            org_id=org_id,
        )
        account_items = self._attach_claim_status_info(items, prop_status_flg=prop_status_flg)
        return self._build_list_response(account_items)

    def list(self, request, *args, **kwargs):
        return self._claim_list_response(request)

    @action(detail=False, methods=["get"], url_path="claim-list")
    def claim_list(self, request):
        return self._claim_list_response(request)

    @action(detail=False, methods=["get"], url_path="transfer-list")
    def transfer_list(self, request):
        key, org_id, _prop_status_flg, empty_response = self._get_list_params(request)
        if empty_response is not None:
            return empty_response

        items = self._build_transfer_queryset(key=key, org_id=org_id)
        return self._build_list_response(items)

    @action(detail=False, methods=["post"], url_path="create_workflow")
    def create_workflow(self, request):
        serializer = CreateWorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items = serializer.validated_data["items"]
        workflow_user_ids = self._deduplicate_user_ids([item["user_id"] for item in items])

        users = {
            item["id"]: item
            for item in User.objects.filter(id__in=workflow_user_ids).values("id", "username", "full_name")
        }
        user_org_id_map = {}
        for relation in (
            UserOrgRelation.objects
            .filter(user_id__in=workflow_user_ids, status=UserOrgRelation.Status.NORMAL)
            .order_by("user_id", "-is_primary", "id")
        ):
            user_org_id_map.setdefault(relation.user_id, relation.org_id)

        org_map = {
            item["id"]: item
            for item in OrgUnit.objects.filter(id__in=user_org_id_map.values()).values("id", "org_code", "org_name")
        }

        # todo: 目前没有报表流程先这样过滤，后续需要根据流程定义来过滤
        org_ids = set()
        selected_user_ids = []
        for user_id in workflow_user_ids:
            org_id = user_org_id_map.get(user_id)
            if org_id is None:
                continue

            if org_id in org_ids:
                continue

            org_ids.add(org_id)
            selected_user_ids.append(user_id)

        # 判断用户所属机构中是否有属于核算机构的
        org_id = serializer.validated_data["org_id"]
        if org_id not in org_ids:
            # selected_user_ids中添加一个属于核算机构的人员
            # 该人员只是为了新增一条结构负责人审批节点分支(认领/移交流程)
            relation = (
                UserOrgRelation.objects
                .filter(org_id=org_id, status=UserOrgRelation.Status.NORMAL)
                .order_by("-is_primary", "id")
                .first()
            )
            if not relation:
                raise ValidationError({"message": "核算机构下没有可用用户"})
            selected_user_ids.append(relation.user_id)
        
        service = WorkflowRuntimeService()

        with transaction.atomic():
            # 先启动流程实例，再自动提交发起节点任务。
            instance = service.start_instance(
                process_def_id=serializer.validated_data["process_def_id"],
                applicant=request.user,
                title=serializer.validated_data.get("title"),
                business_id=serializer.validated_data.get("business_id"),
            )
            task = WfTask.objects.filter(instance_id=instance.id).first()
            if not task:
                raise ValidationError({"message": "流程发起任务不存在"})

            service.handle_task_action(
                task_id=task.id,
                action_code=serializer.validated_data["action_code"],
                operator=request.user,
                selected_user_ids=selected_user_ids,
            )

            prop_status_records = []
            now = timezone.now()
            for item in items:
                user_id = item["user_id"]
                user = users.get(user_id)
                if not user:
                    raise ValidationError({"message": f"用户[{user_id}]不存在或不可用"})
                org_id = user_org_id_map.get(user_id)
                org = org_map.get(org_id)
                prop_status_records.append(
                    ShenzhenPropStatus(
                        process_instance_id=instance.id,
                        data_dt=serializer.validated_data["data_dt"],
                        cust_name=item.get("cust_name"),
                        employee_no=user["username"],
                        employee_name=user["full_name"],
                        ecif_cust_id=item["ecif_cust_id"],
                        orig_acct_id=item["orig_acct_id"],
                        genr_acct_id=item["genr_acct_id"],
                        kpi_prop=item.get("kpi_prop"),
                        year_base_amount=item.get("year_base_amount") or 0,
                        claim_org_id=org["org_code"] if org else None,
                        claim_org_name=org["org_name"] if org else None,
                        accounting_org_id=item["accnt_org_id"],
                        accounting_org_name=item["accnt_org_name"],
                        line_org_code=item["org_code"],
                        apl_data_dt=now,
                    )
                )
            ShenzhenPropStatus.objects.bulk_create(prop_status_records)

        return Response(
            {
                "message": "流程创建成功",
                "data": {
                    "process_instance_id": instance.id,
                    "process_def_id": serializer.validated_data["process_def_id"],
                    "business_type": serializer.validated_data["business_type"],
                    "data_dt": serializer.validated_data["data_dt"],
                    "created_count": len(prop_status_records),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class OrgOptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        org_types = request.data.get("org_types", [])

        if not isinstance(org_types, list):
            raise ValidationError({"message": "org_types 参数不合法"})

        org_types = set(org_types)
        valid_org_types = set(OrgUnit.OrgType.values)
        if not org_types or not org_types.issubset(valid_org_types):
            raise ValidationError({"message": "org_types 参数不合法"})

        orgs = list(
            OrgUnit.objects
            .filter(status=OrgUnit.Status.NORMAL, org_type__in=org_types)
            .order_by("display_order", "id")
            .values("id", "org_name")
        )
        return Response({"message": "查询成功", "data": orgs})
