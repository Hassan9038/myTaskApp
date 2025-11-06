import flet as ft
import sqlite3
import os
import pandas as pd
from datetime import date, datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "clinic.db")

# ---------------------------
# قاعدة البيانات
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_work (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_date TEXT,
            work_amount REAL,
            expense_amount REAL,
            doctor_name TEXT,
            worker_name TEXT,
            worker_amount REAL,
            withdraw_amount REAL,
            place_rent REAL,
            file_number INTEGER,
            period TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_record(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO daily_work (work_date, work_amount, expense_amount, doctor_name, worker_name, worker_amount, withdraw_amount, place_rent, file_number, period)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def get_all_records(filter_date=None, filter_doctor=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = "SELECT * FROM daily_work"
    params = []

    if filter_date and filter_doctor:
        query += " WHERE work_date=? AND doctor_name=?"
        params = [filter_date, filter_doctor]
    elif filter_date:
        query += " WHERE work_date=?"
        params = [filter_date]
    elif filter_doctor:
        query += " WHERE doctor_name=?"
        params = [filter_doctor]

    query += " ORDER BY work_date DESC, id DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def update_record(record_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE daily_work
        SET work_date=?, work_amount=?, expense_amount=?, doctor_name=?, worker_name=?, worker_amount=?, withdraw_amount=?, place_rent=?, file_number=?, period=?
        WHERE id=?
    """, (*data, record_id))
    conn.commit()
    conn.close()

def delete_record(record_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM daily_work WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

# ---------------------------
# واجهة المستخدم
# ---------------------------
def main(page: ft.Page):
    page.title = "عيادة الأسنان - تسجيل العمل اليومي"
    page.window_width = 420
    page.window_height = 780
    page.scroll = ft.ScrollMode.ALWAYS

    init_db()
    selected_ids = set()

    # رسائل مختصرة
    def show_snack(msg, color="green"):
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    # الصفحة الرئيسية
    def show_home():
        page.clean()
        page.add(
            ft.Column(
                [
                    ft.Text("📆 نظام تسجيل العمل اليومي", size=22, weight="bold", color="#4CAF50"),
                    ft.ElevatedButton("➕ إضافة عمل اليوم", on_click=lambda e: show_add_form(), width=280),
                    ft.ElevatedButton("📋 عرض السجلات", on_click=lambda e: show_records(), width=280),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=25
            )
        )
        page.update()

    # إضافة سجل
    def show_add_form():
        page.clean()
        work_date = ft.TextField(label="تاريخ اليوم", value=str(date.today()))
        work_amount = ft.TextField(label="مبلغ العمل اليوم", keyboard_type=ft.KeyboardType.NUMBER)
        expense_amount = ft.TextField(label="مبلغ الصرف", keyboard_type=ft.KeyboardType.NUMBER)
        doctor_name = ft.TextField(label="اسم الطبيب")
        worker_name = ft.Dropdown(label="اسم العامل", options=[ft.dropdown.Option("حليمة"), ft.dropdown.Option("زهرة")])
        worker_amount = ft.TextField(label="مبلغ العامل", keyboard_type=ft.KeyboardType.NUMBER)
        withdraw_amount = ft.TextField(label="مبلغ السحب (إن وجد)", keyboard_type=ft.KeyboardType.NUMBER)
        place_rent = ft.TextField(label="أجرة المكان", keyboard_type=ft.KeyboardType.NUMBER)
        file_number = ft.TextField(label="رقم الملف", keyboard_type=ft.KeyboardType.NUMBER)
        period = ft.Dropdown(label="الفترة", options=[ft.dropdown.Option("صباحي"), ft.dropdown.Option("مسائي")])

        def save_record(e):
            try:
                data = (
                    work_date.value,
                    float(work_amount.value or 0),
                    float(expense_amount.value or 0),
                    doctor_name.value,
                    worker_name.value,
                    float(worker_amount.value or 0),
                    float(withdraw_amount.value or 0),
                    float(place_rent.value or 0),
                    int(file_number.value or 0),
                    period.value
                )
            except ValueError:
                show_snack("⚠️ تحقق من صحة القيم الرقمية!", "red")
                return
            insert_record(data)
            show_snack(f"✅ تم حفظ السجل: {work_date.value}, الطبيب: {doctor_name.value}, العامل: {worker_name.value}, الفترة: {period.value}", "green")
            show_home()

        page.add(
            ft.Column(
                [
                    ft.Text("📝 إضافة سجل جديد", size=20, weight="bold"),
                    work_date, work_amount, expense_amount, doctor_name,
                    worker_name, worker_amount, withdraw_amount, place_rent, file_number, period,
                    ft.Row(
                        [
                            ft.ElevatedButton("💾 حفظ", on_click=save_record, bgcolor="#4CAF50", color="white"),
                            ft.OutlinedButton("↩️ رجوع", on_click=lambda e: show_home())
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND
                    )
                ],
                scroll=ft.ScrollMode.ALWAYS
            )
        )
        page.update()

    # تعديل سجل
    def edit_record(record):
        page.clean()
        (rid, work_date_val, work_amount_val, expense_val, doctor_val,
         worker_name_val, worker_val, withdraw_val, rent_val, file_val, period_val) = record

        work_date = ft.TextField(label="تاريخ اليوم", value=work_date_val)
        work_amount = ft.TextField(label="مبلغ العمل", value=str(work_amount_val))
        expense_amount = ft.TextField(label="مبلغ الصرف", value=str(expense_val))
        doctor_name = ft.TextField(label="اسم الطبيب", value=doctor_val)
        worker_name = ft.Dropdown(label="اسم العامل", options=[ft.dropdown.Option("حليمة"), ft.dropdown.Option("زهرة")], value=worker_name_val)
        worker_amount = ft.TextField(label="مبلغ العامل", value=str(worker_val))
        withdraw_amount = ft.TextField(label="مبلغ السحب", value=str(withdraw_val))
        place_rent = ft.TextField(label="أجرة المكان", value=str(rent_val))
        file_number = ft.TextField(label="رقم الملف", value=str(file_val))
        period = ft.Dropdown(label="الفترة", options=[ft.dropdown.Option("صباحي"), ft.dropdown.Option("مسائي")], value=period_val)

        def save_edit(e):
            try:
                data = (
                    work_date.value,
                    float(work_amount.value or 0),
                    float(expense_amount.value or 0),
                    doctor_name.value,
                    worker_name.value,
                    float(worker_amount.value or 0),
                    float(withdraw_amount.value or 0),
                    float(place_rent.value or 0),
                    int(file_number.value or 0),
                    period.value
                )
            except ValueError:
                show_snack("⚠️ تحقق من صحة القيم الرقمية!", "red")
                return

            update_record(rid, data)
            show_snack(f"✅ تم تحديث السجل رقم {rid}", "blue")
            show_records()

        page.add(
            ft.Column(
                [
                    ft.Text("✏️ تعديل السجل", size=20, weight="bold"),
                    work_date, work_amount, expense_amount, doctor_name,
                    worker_name, worker_amount, withdraw_amount, place_rent, file_number, period,
                    ft.Row(
                        [
                            ft.ElevatedButton("💾 حفظ", on_click=save_edit, bgcolor="#4CAF50", color="white"),
                            ft.OutlinedButton("↩️ رجوع", on_click=lambda e: show_records())
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND
                    )
                ],
                scroll=ft.ScrollMode.ALWAYS
            )
        )
        page.update()

    # عرض السجلات
    def show_records():
        page.clean()
        filter_date = ft.TextField(label="تاريخ البحث", width=150)
        filter_doctor = ft.TextField(label="اسم الطبيب", width=150)

        headers = ["التاريخ", "مبلغ العمل", "الصرف", "الطبيب", "العامل", "مبلغ العامل", "السحب", "أجرة المكان", "رقم الملف", "الفترة", "تحديد", "إجراءات"]
        table = ft.DataTable(columns=[ft.DataColumn(ft.Text(h)) for h in headers], rows=[])

        total_work = total_expense = total_worker = total_withdraw = total_rent = 0

        def load_table(e=None):
            nonlocal total_work, total_expense, total_worker, total_withdraw, total_rent
            table.rows.clear()
            total_work = total_expense = total_worker = total_withdraw = total_rent = 0
            records = get_all_records(filter_date.value.strip() or None, filter_doctor.value.strip() or None)
            for r in records:
                (rid, work_date_val, work_amount_val, expense_val, doctor_val,
                 worker_name_val, worker_val, withdraw_val, rent_val, file_val, period_val) = r

                # تحويل القيم الرقمية
                work_amount_val = float(work_amount_val or 0)
                expense_val = float(expense_val or 0)
                worker_val = float(worker_val or 0)
                withdraw_val = float(withdraw_val or 0)
                rent_val = float(rent_val or 0)

                total_work += work_amount_val
                total_expense += expense_val
                total_worker += worker_val
                total_withdraw += withdraw_val
                total_rent += rent_val

                # checkbox للتحديد
                checkbox = ft.Checkbox(value=(rid in selected_ids), on_change=lambda e, rid=rid: (selected_ids.add(rid) if e.control.value else selected_ids.discard(rid)))

                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(work_date_val)),
                        ft.DataCell(ft.Text(str(work_amount_val))),
                        ft.DataCell(ft.Text(str(expense_val))),
                        ft.DataCell(ft.Text(doctor_val)),
                        ft.DataCell(ft.Text(worker_name_val)),
                        ft.DataCell(ft.Text(str(worker_val))),
                        ft.DataCell(ft.Text(str(withdraw_val))),
                        ft.DataCell(ft.Text(str(rent_val))),
                        ft.DataCell(ft.Text(str(file_val))),
                        ft.DataCell(ft.Text(period_val)),
                        ft.DataCell(checkbox),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.IconButton(ft.Icons.EDIT, icon_color="blue", on_click=lambda e, rec=r: edit_record(rec)),
                                    ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda e, rid=rid: (
                                        delete_record(rid),
                                        load_table(),
                                        show_snack(f"🗑️ تم حذف السجل رقم {rid}", "orange")
                                    ))
                                ],
                                spacing=0
                            )
                        )
                    ]
                )
                table.rows.append(row)
            table.update()
            page.update()

        def delete_selected(e):
            count = len(selected_ids)
            for rid in list(selected_ids):
                delete_record(rid)
            selected_ids.clear()
            load_table()
            show_snack(f"🗑️ تم حذف {count} سجل/سجلات محددة", "orange")

        def export_excel(e):
            records = get_all_records(filter_date.value.strip() or None, filter_doctor.value.strip() or None)
            if not records:
                show_snack("⚠️ لا توجد بيانات للتصدير", "orange")
                return
            df = pd.DataFrame(records, columns=["ID","التاريخ","مبلغ العمل","الصرف","الطبيب","العامل","مبلغ العامل","السحب","أجرة المكان","رقم الملف","الفترة"])
            df = df.drop(columns=["ID"])
            filename = f"records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            show_snack(f"✅ تم تصدير الملف: {filename}")

        page.add(
            ft.Column(
                [
                    ft.Text("📋 السجلات", size=20, weight="bold"),
                    ft.Row([filter_date, filter_doctor, ft.ElevatedButton("🔍 بحث", on_click=load_table)], spacing=10),
                    ft.Row([
                        ft.ElevatedButton("🗑️ حذف المحدد", on_click=delete_selected, bgcolor="red", color="white"),
                        ft.ElevatedButton("💾 تصدير Excel", on_click=export_excel, bgcolor="#2196F3", color="white")
                    ], spacing=10),
                    table,
                    ft.ElevatedButton("↩️ رجوع", on_click=lambda e: show_home())
                ],
                scroll=ft.ScrollMode.ALWAYS,
                spacing=10
            )
        )
        load_table()
        page.update()

    show_home()

ft.app(target=main)
