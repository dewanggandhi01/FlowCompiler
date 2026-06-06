"""
UI Schema — Stage 3A output.

Defines the structured output for the UI portion of the Schema Generation Agent.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Enums ────────────────────────────────────────────────


class ComponentType(str, Enum):
    FORM = "form"
    TABLE = "table"
    CHART = "chart"
    CARD = "card"
    LIST = "list"
    DETAIL = "detail"
    MODAL = "modal"
    SIDEBAR = "sidebar"
    HEADER = "header"
    STATS = "stats"
    NAVIGATION = "navigation"
    SEARCH = "search"
    FILTER = "filter"
    TABS = "tabs"
    CALENDAR = "calendar"


class InputType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    SELECT = "select"
    MULTISELECT = "multiselect"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    FILE = "file"
    IMAGE = "image"
    TOGGLE = "toggle"
    PHONE = "phone"
    URL = "url"
    MONEY = "money"
    SEARCH = "search"
    HIDDEN = "hidden"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    TABLE = "table"
    METRIC = "metric"


class ValidationRuleType(str, Enum):
    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    PATTERN = "pattern"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    CUSTOM = "custom"


# ── Sub-models ───────────────────────────────────────────


class UIValidationRule(BaseModel):
    """Client-side validation rule for a form field."""
    type: ValidationRuleType
    value: Optional[str] = Field(default=None, description="Rule parameter value")
    message: str = Field(default="", description="Error message to display")


class FormField(BaseModel):
    """A single field in a form."""
    name: str = Field(..., description="Field name matching entity field")
    label: str = Field(..., description="Display label")
    input_type: InputType
    placeholder: str = Field(default="")
    required: bool = Field(default=True)
    options: list[str] = Field(default_factory=list, description="Options for select/radio/checkbox")
    default_value: Optional[str] = None
    validation_rules: list[UIValidationRule] = Field(default_factory=list)
    order: int = Field(default=0, description="Display order")
    width: str = Field(default="full", description="Width: full, half, third")


class UIForm(BaseModel):
    """A form component definition."""
    id: str = Field(..., description="Unique form identifier")
    title: str
    entity: str = Field(..., description="Entity this form creates/edits")
    submit_endpoint: str = Field(..., description="API endpoint to submit to")
    method: str = Field(default="POST")
    fields: list[FormField] = Field(default_factory=list)
    success_message: str = Field(default="Saved successfully")
    redirect_on_success: Optional[str] = None


class TableColumn(BaseModel):
    """A column in a data table."""
    key: str = Field(..., description="Data field key")
    label: str = Field(..., description="Column header label")
    sortable: bool = Field(default=True)
    filterable: bool = Field(default=False)
    width: Optional[str] = None
    format: Optional[str] = Field(default=None, description="Display format: date, currency, badge, etc.")
    link_to: Optional[str] = Field(default=None, description="Route to link to, e.g. /contacts/:id")


class TableAction(BaseModel):
    """An action available on table rows."""
    label: str
    action: str = Field(..., description="Action type: view, edit, delete, custom")
    endpoint: Optional[str] = None
    confirm: bool = Field(default=False, description="Show confirmation dialog")
    icon: str = Field(default="")


class UITable(BaseModel):
    """A data table component definition."""
    id: str = Field(..., description="Unique table identifier")
    title: str
    entity: str = Field(..., description="Entity this table displays")
    data_endpoint: str = Field(..., description="API endpoint to fetch data")
    columns: list[TableColumn] = Field(default_factory=list)
    actions: list[TableAction] = Field(default_factory=list)
    searchable: bool = Field(default=True)
    paginated: bool = Field(default=True)
    page_size: int = Field(default=20)
    default_sort: Optional[str] = None
    filters: list[str] = Field(default_factory=list, description="Filterable field names")


class ChartDataSource(BaseModel):
    """Data source for a chart."""
    endpoint: str = Field(..., description="API endpoint for chart data")
    label_field: str = Field(..., description="Field used for labels/x-axis")
    value_field: str = Field(..., description="Field used for values/y-axis")
    group_by: Optional[str] = None


class UIChart(BaseModel):
    """A chart component definition."""
    id: str = Field(..., description="Unique chart identifier")
    title: str
    chart_type: ChartType
    data_source: ChartDataSource
    description: str = Field(default="")
    width: str = Field(default="full", description="Width: full, half, third")


class ThemeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    primary_color: str = "#4F46E5"
    mode: str = "dark"
    font_family: str = "Inter"


class UIComponent(BaseModel):
    """A generic UI component within a page."""
    id: str = Field(..., description="Unique component identifier")
    type: ComponentType
    title: str = Field(default="")
    description: str = Field(default="")
    entity: str = Field(default="", description="Entity bound to this component")
    order: int = Field(default=0, description="Display order within the page")
    width: str = Field(default="full")
    ref_form: Optional[str] = Field(default=None, description="Reference to a form ID")
    ref_table: Optional[str] = Field(default=None, description="Reference to a table ID")
    ref_chart: Optional[str] = Field(default=None, description="Reference to a chart ID")


class UIPage(BaseModel):
    """A page/screen in the application."""
    id: str = Field(..., description="Unique page identifier")
    name: str
    route: str = Field(..., description="URL path")
    title: str = Field(..., description="Page title for display and SEO")
    description: str = Field(default="")
    layout: str = Field(default="default", description="Layout template: default, sidebar, full-width, dashboard")
    components: list[UIComponent] = Field(default_factory=list)
    requires_auth: bool = Field(default=True)
    allowed_roles: list[str] = Field(default_factory=list)
    parent_page: Optional[str] = Field(default=None, description="Parent page ID for breadcrumbs")


# ── Main Output ──────────────────────────────────────────


class UISchema(BaseModel):
    """
    Stage 3A Output: Complete UI schema.

    Defines all pages, components, forms, tables, and charts
    for the application's frontend.
    """
    pages: list[UIPage] = Field(default_factory=list)
    components: list[UIComponent] = Field(default_factory=list, description="Shared/reusable components")
    forms: list[UIForm] = Field(default_factory=list)
    tables: list[UITable] = Field(default_factory=list)
    charts: list[UIChart] = Field(default_factory=list)
    theme: ThemeConfig = Field(default_factory=ThemeConfig)
