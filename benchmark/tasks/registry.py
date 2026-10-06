"""
RealityBench Task Suite Registry
Central catalog for all 12 RealityBench tasks.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Any, List
from benchmark.graders.scoring import EvaluationReport

from benchmark.tasks.task_01_login import (
    TASK_SPEC as LOGIN_TASK_PROMPT, grade_login_implementation,
    NAIVE_LOGIN_CODE, ROBUST_LOGIN_CODE, realitybench_login
)
from benchmark.tasks.task_02_search import (
    TASK_SPEC as SEARCH_TASK_PROMPT, grade_search_implementation,
    NAIVE_SEARCH_CODE, ROBUST_SEARCH_CODE, realitybench_search
)
from benchmark.tasks.task_03_checkout import (
    TASK_SPEC as CHECKOUT_TASK_PROMPT, grade_checkout_implementation,
    NAIVE_CHECKOUT_CODE, ROBUST_CHECKOUT_CODE, realitybench_checkout
)
from benchmark.tasks.task_04_file_upload import (
    TASK_SPEC as FILE_UPLOAD_TASK_PROMPT, grade_file_upload_implementation,
    NAIVE_FILE_UPLOAD_CODE, ROBUST_FILE_UPLOAD_CODE, realitybench_file_upload
)
from benchmark.tasks.task_05_crud_dashboard import (
    TASK_SPEC as CRUD_TASK_PROMPT, grade_crud_dashboard_implementation as grade_crud_implementation,
    NAIVE_CRUD_CODE, ROBUST_CRUD_CODE, realitybench_crud_dashboard
)
from benchmark.tasks.task_06_booking import (
    TASK_SPEC as BOOKING_TASK_PROMPT, grade_booking_implementation,
    NAIVE_BOOKING_CODE, ROBUST_BOOKING_CODE, realitybench_booking
)
from benchmark.tasks.task_07_chat import (
    TASK_SPEC as CHAT_TASK_PROMPT, grade_chat_implementation,
    NAIVE_CHAT_CODE, ROBUST_CHAT_CODE, realitybench_chat
)
from benchmark.tasks.task_08_product_page import (
    TASK_SPEC as PRODUCT_PAGE_TASK_PROMPT, grade_product_page_implementation,
    NAIVE_PRODUCT_PAGE_CODE, ROBUST_PRODUCT_PAGE_CODE, realitybench_product_page
)
from benchmark.tasks.task_09_admin_table import (
    TASK_SPEC as ADMIN_TABLE_TASK_PROMPT, grade_admin_table_implementation,
    NAIVE_ADMIN_TABLE_CODE, ROBUST_ADMIN_TABLE_CODE, realitybench_admin_table
)
from benchmark.tasks.task_10_settings import (
    TASK_SPEC as SETTINGS_TASK_PROMPT, grade_settings_implementation,
    NAIVE_SETTINGS_CODE, ROBUST_SETTINGS_CODE, realitybench_settings
)
from benchmark.tasks.task_11_api_form import (
    TASK_SPEC as API_FORM_TASK_PROMPT, grade_api_form_implementation,
    NAIVE_API_FORM_CODE, ROBUST_API_FORM_CODE, realitybench_api_form
)
from benchmark.tasks.task_12_workflow import (
    TASK_SPEC as WORKFLOW_TASK_PROMPT, grade_workflow_implementation,
    NAIVE_WORKFLOW_CODE, ROBUST_WORKFLOW_CODE, realitybench_workflow
)


@dataclass
class TaskDefinition:
    task_id: str
    task_number: int
    name: str
    category_focus: str
    prompt: str
    grader: Callable[[str], EvaluationReport]
    kbench_task: Any
    naive_code: str
    robust_code: str


ALL_TASKS: List[TaskDefinition] = [
    TaskDefinition(
        task_id="realitybench-login",
        task_number=1,
        name="Authentication & Login",
        category_focus="Input validation, lockout feedback, credential recovery",
        prompt=LOGIN_TASK_PROMPT,
        grader=grade_login_implementation,
        kbench_task=realitybench_login,
        naive_code=NAIVE_LOGIN_CODE,
        robust_code=ROBUST_LOGIN_CODE
    ),
    TaskDefinition(
        task_id="realitybench-search",
        task_number=2,
        name="Search & Autocomplete",
        category_focus="Debouncing, empty results, 500 recovery, keyboard navigation",
        prompt=SEARCH_TASK_PROMPT,
        grader=grade_search_implementation,
        kbench_task=realitybench_search,
        naive_code=NAIVE_SEARCH_CODE,
        robust_code=ROBUST_SEARCH_CODE
    ),
    TaskDefinition(
        task_id="realitybench-checkout",
        task_number=3,
        name="Order Checkout",
        category_focus="Cart state preservation on 500, double-submit debounce, coupon bounds",
        prompt=CHECKOUT_TASK_PROMPT,
        grader=grade_checkout_implementation,
        kbench_task=realitybench_checkout,
        naive_code=NAIVE_CHECKOUT_CODE,
        robust_code=ROBUST_CHECKOUT_CODE
    ),
    TaskDefinition(
        task_id="realitybench-file-upload",
        task_number=4,
        name="File Upload",
        category_focus="Filetype filtering, size bounds, upload error feedback, debounce",
        prompt=FILE_UPLOAD_TASK_PROMPT,
        grader=grade_file_upload_implementation,
        kbench_task=realitybench_file_upload,
        naive_code=NAIVE_FILE_UPLOAD_CODE,
        robust_code=ROBUST_FILE_UPLOAD_CODE
    ),
    TaskDefinition(
        task_id="realitybench-crud-dashboard",
        task_number=5,
        name="Task CRUD Dashboard",
        category_focus="Mutation error rollback, whitespace rejection, deletion confirmation",
        prompt=CRUD_TASK_PROMPT,
        grader=grade_crud_implementation,
        kbench_task=realitybench_crud_dashboard,
        naive_code=NAIVE_CRUD_CODE,
        robust_code=ROBUST_CRUD_CODE
    ),
    TaskDefinition(
        task_id="realitybench-booking",
        task_number=6,
        name="Appointment Booking",
        category_focus="Past-date validation, slot conflict 409 recovery, form preservation",
        prompt=BOOKING_TASK_PROMPT,
        grader=grade_booking_implementation,
        kbench_task=realitybench_booking,
        naive_code=NAIVE_BOOKING_CODE,
        robust_code=ROBUST_BOOKING_CODE
    ),
    TaskDefinition(
        task_id="realitybench-chat",
        task_number=7,
        name="Live Chat Component",
        category_focus="Empty message rejection, in-thread 500 feedback, Enter key submission",
        prompt=CHAT_TASK_PROMPT,
        grader=grade_chat_implementation,
        kbench_task=realitybench_chat,
        naive_code=NAIVE_CHAT_CODE,
        robust_code=ROBUST_CHAT_CODE
    ),
    TaskDefinition(
        task_id="realitybench-product-page",
        task_number=8,
        name="Product Detail Page",
        category_focus="Out-of-stock variant disabling, broken image fallback, negative qty bounds",
        prompt=PRODUCT_PAGE_TASK_PROMPT,
        grader=grade_product_page_implementation,
        kbench_task=realitybench_product_page,
        naive_code=NAIVE_PRODUCT_PAGE_CODE,
        robust_code=ROBUST_PRODUCT_PAGE_CODE
    ),
    TaskDefinition(
        task_id="realitybench-admin-table",
        task_number=9,
        name="Admin Data Table",
        category_focus="Null/missing field resilience, empty state, pagination, header markup",
        prompt=ADMIN_TABLE_TASK_PROMPT,
        grader=grade_admin_table_implementation,
        kbench_task=realitybench_admin_table,
        naive_code=NAIVE_ADMIN_TABLE_CODE,
        robust_code=ROBUST_ADMIN_TABLE_CODE
    ),
    TaskDefinition(
        task_id="realitybench-settings",
        task_number=10,
        name="User Settings Panel",
        category_focus="Dirty state tracking, discard restoration, HTTP 500 edit preservation",
        prompt=SETTINGS_TASK_PROMPT,
        grader=grade_settings_implementation,
        kbench_task=realitybench_settings,
        naive_code=NAIVE_SETTINGS_CODE,
        robust_code=ROBUST_SETTINGS_CODE
    ),
    TaskDefinition(
        task_id="realitybench-api-form",
        task_number=11,
        name="Dependent API Form",
        category_focus="Cascading dropdowns, parent switch state reset, 500 error recovery",
        prompt=API_FORM_TASK_PROMPT,
        grader=grade_api_form_implementation,
        kbench_task=realitybench_api_form,
        naive_code=NAIVE_API_FORM_CODE,
        robust_code=ROBUST_API_FORM_CODE
    ),
    TaskDefinition(
        task_id="realitybench-workflow",
        task_number=12,
        name="Multi-Step Workflow Wizard",
        category_focus="Step validation, Back navigation state preservation, Step 3 500 retry",
        prompt=WORKFLOW_TASK_PROMPT,
        grader=grade_workflow_implementation,
        kbench_task=realitybench_workflow,
        naive_code=NAIVE_WORKFLOW_CODE,
        robust_code=ROBUST_WORKFLOW_CODE
    ),
]

TASK_MAP: Dict[str, TaskDefinition] = {t.task_id: t for t in ALL_TASKS}
