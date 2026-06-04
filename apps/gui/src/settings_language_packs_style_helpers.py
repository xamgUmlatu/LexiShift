from __future__ import annotations

from theme_manager import readable_text_color, rgba_color


def resource_table_action_button_style(
    table_bg: str,
    table_text: str,
    table_sel_bg: str,
    panel_border: str,
    panel_bottom: str,
    accent: str,
    accent_soft: str,
    hover_text: str,
    text_color: str,
    muted_color: str,
) -> str:
    action_bg = rgba_color(table_bg, 0.48)
    action_border = rgba_color(panel_border, 0.72)
    action_hover_bg = rgba_color(accent_soft, 0.84)
    action_pressed_bg = rgba_color(table_sel_bg, 0.92)
    action_disabled_bg = rgba_color(panel_bottom, 0.38)
    action_disabled_text = readable_text_color(muted_color, panel_bottom, minimum_ratio=3.2)
    action_selected_text = readable_text_color(text_color, table_sel_bg)
    return f"""
QTableWidget QPushButton[resourceTableAction="true"] {{
  background: {action_bg};
  color: {table_text};
  border: 1px solid {action_border};
  border-radius: 5px;
  padding: 2px 8px;
  min-height: 20px;
  max-height: 24px;
  font-weight: 600;
}}
QTableWidget QPushButton[resourceTableAction="true"]:hover {{
  background: {action_hover_bg};
  color: {hover_text};
  border-color: {accent};
}}
QTableWidget QPushButton[resourceTableAction="true"]:pressed {{
  background: {action_pressed_bg};
  color: {action_selected_text};
}}
QTableWidget QPushButton[resourceTableAction="true"]:disabled {{
  background: {action_disabled_bg};
  color: {action_disabled_text};
  border-color: {action_border};
}}
"""
