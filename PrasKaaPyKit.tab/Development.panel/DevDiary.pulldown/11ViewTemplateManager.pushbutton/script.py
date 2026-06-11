# -*- coding: utf-8 -*-
"""View Template Manager - Console Output with Collapsible Sections"""

__title__ = "View Template\nManager"
__author__ = "PrasKaaPyKit"
__doc__ = "List all View Templates and their assigned Views in the console."

from pyrevit import HOST_APP, DB, script

doc    = HOST_APP.doc
output = script.get_output()

output.print_md("# View Template Manager")

all_views = list(DB.FilteredElementCollector(doc).OfClass(DB.View))

# Collect templates and views
template_map      = {}  # tid -> (name, element_id)
views_by_template = {}  # tid -> [(view_name, view_type, element_id)]

for v in all_views:
    if v.IsTemplate:
        tid = v.Id.Value
        template_map[tid] = (v.Name, v.Id)
        views_by_template[tid] = []

for v in all_views:
    if not v.IsTemplate:
        try:
            tid = v.ViewTemplateId.Value
            if tid in views_by_template:
                vtype = str(v.ViewType).replace("_", " ")
                views_by_template[tid].append((v.Name, vtype, v.Id))
        except Exception:
            pass

for tid in views_by_template:
    views_by_template[tid].sort(key=lambda x: x[0])

# Stats
total    = len(template_map)
used     = sum(1 for tid in template_map if views_by_template.get(tid))
not_used = total - used

output.print_html(
    "<p style='color:#aaa; margin:4px 0 12px 0'>"
    "&#128196; <b style='color:#E0E0FF'>{}</b> templates &nbsp;|&nbsp; "
    "<b style='color:#7C7CFF'>{}</b> in use &nbsp;|&nbsp; "
    "<b style='color:#888'>{}</b> not used"
    "</p>".format(total, used, not_used)
)
output.print_md("---")

# Sort: used first, then not used
sorted_templates = (
    sorted([(tid, d) for tid, d in template_map.items() if     views_by_template.get(tid)], key=lambda x: x[1][0]) +
    sorted([(tid, d) for tid, d in template_map.items() if not views_by_template.get(tid)], key=lambda x: x[1][0])
)

for tid, (tname, t_eid) in sorted_templates:
    views = views_by_template.get(tid, [])
    count = len(views)

    if count > 0:
        # linkify semua view IDs sekaligus -> select all views pakai template ini
        all_view_ids = [v_eid for _, _, v_eid in views]
        select_all_link = output.linkify(all_view_ids, title="[select all views]")

        rows = "".join(
            "<li style='padding:3px 0'>{} "
            "<span style='color:#666; font-size:0.85em'>[{}]</span></li>".format(
                output.linkify(v_eid, title=vname), vtype
            )
            for vname, vtype, v_eid in views
        )
        output.print_html(
            "<details>"
            "<summary style='cursor:pointer; padding:4px 0'>"
            "{} &nbsp;<b>{}</b> &nbsp;"
            "<span style='color:#7C7CFF; font-size:0.9em'>&#9646; {} views</span>"
            "</summary>"
            "<ul style='margin:4px 0 8px 24px'>{}</ul>"
            "</details>".format(
                select_all_link, tname, count, rows
            )
        )
    else:
        output.print_html(
            "<p style='margin:2px 0; color:#666'>"
            "<span style='color:#444'>[no views]</span>"
            " &nbsp;<span style='color:#555'>{}</span> &nbsp;"
            "<span style='color:#444; font-size:0.85em'>— not used</span>"
            "</p>".format(tname)
        )

output.print_md("---")
output.print_md("*{} View Templates found.*".format(total))