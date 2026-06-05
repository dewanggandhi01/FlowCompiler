"""
UI Runtime Generator.

Converts UI schema into executable React component configurations
that can be used to automatically render a frontend application.
"""

from __future__ import annotations

from src.schemas.ui_schema import UISchema


def generate_ui_runtime(ui_schema: UISchema) -> dict:
    """
    Convert UI schema to executable React component configurations.

    Generates:
    - Page route configs
    - Form JSON configs
    - Table JSON configs
    - Chart JSON configs
    - Navigation config
    """
    routes = []
    for page in ui_schema.pages:
        routes.append({
            "path": page.route,
            "name": page.name,
            "title": page.title,
            "layout": page.layout,
            "requiresAuth": page.requires_auth,
            "allowedRoles": page.allowed_roles,
            "components": [
                {
                    "id": comp.id,
                    "type": comp.type.value if hasattr(comp.type, "value") else comp.type,
                    "title": comp.title,
                    "entity": comp.entity,
                    "props": comp.props,
                    "order": comp.order,
                    "width": comp.width,
                    "refForm": comp.ref_form,
                    "refTable": comp.ref_table,
                    "refChart": comp.ref_chart,
                }
                for comp in page.components
            ],
        })

    forms = {}
    for form in ui_schema.forms:
        forms[form.id] = {
            "title": form.title,
            "entity": form.entity,
            "submitEndpoint": form.submit_endpoint,
            "method": form.method,
            "successMessage": form.success_message,
            "redirectOnSuccess": form.redirect_on_success,
            "fields": [
                {
                    "name": f.name,
                    "label": f.label,
                    "inputType": f.input_type.value if hasattr(f.input_type, "value") else f.input_type,
                    "placeholder": f.placeholder,
                    "required": f.required,
                    "options": f.options,
                    "defaultValue": f.default_value,
                    "validationRules": [
                        {"type": r.type.value if hasattr(r.type, "value") else r.type, "value": r.value, "message": r.message}
                        for r in f.validation_rules
                    ],
                    "order": f.order,
                    "width": f.width,
                }
                for f in form.fields
            ],
        }

    tables = {}
    for table in ui_schema.tables:
        tables[table.id] = {
            "title": table.title,
            "entity": table.entity,
            "dataEndpoint": table.data_endpoint,
            "searchable": table.searchable,
            "paginated": table.paginated,
            "pageSize": table.page_size,
            "defaultSort": table.default_sort,
            "filters": table.filters,
            "columns": [
                {
                    "key": c.key,
                    "label": c.label,
                    "sortable": c.sortable,
                    "filterable": c.filterable,
                    "width": c.width,
                    "format": c.format,
                    "linkTo": c.link_to,
                }
                for c in table.columns
            ],
            "actions": [
                {
                    "label": a.label,
                    "action": a.action,
                    "endpoint": a.endpoint,
                    "confirm": a.confirm,
                    "icon": a.icon,
                }
                for a in table.actions
            ],
        }

    charts = {}
    for chart in ui_schema.charts:
        charts[chart.id] = {
            "title": chart.title,
            "chartType": chart.chart_type.value if hasattr(chart.chart_type, "value") else chart.chart_type,
            "dataSource": {
                "endpoint": chart.data_source.endpoint,
                "labelField": chart.data_source.label_field,
                "valueField": chart.data_source.value_field,
                "groupBy": chart.data_source.group_by,
            },
            "description": chart.description,
            "width": chart.width,
        }

    return {
        "routes": routes,
        "forms": forms,
        "tables": tables,
        "charts": charts,
        "theme": ui_schema.theme,
    }
