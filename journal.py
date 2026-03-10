import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import sqlite3
import os
from datetime import datetime

class JournalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Журнал оценок")
        self.root.geometry("1400x600")
        
        self.db_path = "journal.db"
        self.init_database()
        
        # Основная рамка
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Рамка для кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Добавить студента", command=self.add_student).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить студента", command=self.delete_student).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Изменить оценку", command=self.edit_grade).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Обновить таблицу", command=self.refresh_table).pack(side=tk.LEFT, padx=5)
        
        # Таблица
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создание Treeview с скроллбаром
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Определяем столбцы
        columns = ['№', 'ФИО']
        # Добавляем недели
        for week in range(1, 16):
            columns.append(f'Н{week}')
        columns.extend(['РК1', 'РК2', 'Итого'])
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, height=15, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        # Определяем заголовки и ширину столбцов
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.column('№', anchor=tk.W, width=40)
        self.tree.column('ФИО', anchor=tk.W, width=150)
        
        for week in range(1, 16):
            self.tree.column(f'Н{week}', anchor=tk.CENTER, width=50)
        
        self.tree.column('РК1', anchor=tk.CENTER, width=60)
        self.tree.column('РК2', anchor=tk.CENTER, width=60)
        self.tree.column('Итого', anchor=tk.CENTER, width=60)
        
        # Создаем заголовки
        self.tree.heading('#0', text='', anchor=tk.W)
        self.tree.heading('№', text='№', anchor=tk.W)
        self.tree.heading('ФИО', text='ФИО', anchor=tk.W)
        
        for week in range(1, 16):
            self.tree.heading(f'Н{week}', text=f'Н{week}', anchor=tk.CENTER)
        
        self.tree.heading('РК1', text='РК1', anchor=tk.CENTER)
        self.tree.heading('РК2', text='РК2', anchor=tk.CENTER)
        self.tree.heading('Итого', text='Итого', anchor=tk.CENTER)
        
        # Привязываем двойной клик для редактирования
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.refresh_table()
    
    def init_database(self):
        """Инициализация базы данных"""
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица студентов
            cursor.execute('''
                CREATE TABLE students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fio TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица оценок
            cursor.execute('''
                CREATE TABLE grades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    week INTEGER NOT NULL,
                    grade TEXT,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    UNIQUE(student_id, week)
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def get_db_connection(self):
        """Получение подключения к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_student(self):
        """Добавить нового студента"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить студента")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="ФИО студента:").pack(pady=5)
        entry = ttk.Entry(dialog, width=40)
        entry.pack(pady=5)
        
        def save():
            fio = entry.get().strip()
            if not fio:
                messagebox.showerror("Ошибка", "Введите ФИО студента")
                return
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO students (fio) VALUES (?)', (fio,))
                conn.commit()
                messagebox.showinfo("Успех", f"Студент '{fio}' добавлен")
                dialog.destroy()
                self.refresh_table()
            except sqlite3.IntegrityError:
                messagebox.showerror("Ошибка", "Студент с таким ФИО уже существует")
            finally:
                conn.close()
        
        ttk.Button(dialog, text="Добавить", command=save).pack(pady=5)
    
    def delete_student(self):
        """Удалить студента"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите студента для удаления")
            return
        
        item = selected[0]
        fio = self.tree.item(item)['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить студента '{fio}'?"):
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM students WHERE fio = ?', (fio,))
            conn.commit()
            conn.close()
            self.refresh_table()
    
    def calculate_rk1(self, grades):
        """Расчет РК1 (недели 1-7)"""
        valid_grades = []
        for i in range(7):
            grade = grades[i]
            if grade and grade != 'н.п.':
                if grade == 'н.я.':
                    valid_grades.append(0)
                else:
                    try:
                        valid_grades.append(int(grade))
                    except ValueError:
                        pass
        
        return round(sum(valid_grades) / len(valid_grades)) if valid_grades else None
    
    def calculate_rk2(self, grades):
        """Расчет РК2 (недели 8-14)"""
        valid_grades = []
        for i in range(7, 14):
            grade = grades[i]
            if grade and grade != 'н.п.':
                if grade == 'н.я.':
                    valid_grades.append(0)
                else:
                    try:
                        valid_grades.append(int(grade))
                    except ValueError:
                        pass
        
        return round(sum(valid_grades) / len(valid_grades)) if valid_grades else None
    
    def calculate_final_grade(self, rk1, rk2):
        """Расчет итоговой оценки"""
        if rk1 is not None and rk2 is not None:
            return round((rk1 + rk2) / 2)
        return None
    
    def refresh_table(self):
        """Обновить таблицу"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, fio FROM students ORDER BY id')
        students = cursor.fetchall()
        
        for idx, student in enumerate(students, 1):
            student_id = student['id']
            fio = student['fio']
            
            # Получаем оценки
            cursor.execute('SELECT week, grade FROM grades WHERE student_id = ? ORDER BY week', (student_id,))
            grade_records = cursor.fetchall()
            
            grades = {}
            for record in grade_records:
                grades[record['week']] = record['grade']
            
            # Подготавливаем данные для строки
            row_data = [idx, fio]
            grade_list = []
            
            for week in range(1, 16):
                grade = grades.get(week, '')
                row_data.append(grade)
                grade_list.append(grade)
            
            # Расчитываем РК1, РК2, итого
            rk1 = self.calculate_rk1(grade_list)
            rk2 = self.calculate_rk2(grade_list)
            final = self.calculate_final_grade(rk1, rk2)
            
            row_data.append(rk1 if rk1 is not None else '')
            row_data.append(rk2 if rk2 is not None else '')
            row_data.append(final if final is not None else '')
            
            self.tree.insert('', tk.END, values=row_data)
        
        conn.close()
    
    def on_tree_double_click(self, event):
        """Обработка двойного клика по ячейке"""
        item = self.tree.selection()
        if not item:
            return
        
        item = item[0]
        col = self.tree.identify_column(event.x)
        
        # Получаем индекс столбца
        col_index = int(col.replace('#', ''))
        
        # Можно редактировать только недели (столбцы 3-17)
        if col_index < 3 or col_index > 17:
            return
        
        week = col_index - 2  # Преобразуем индекс в номер недели
        
        # Получаем ФИО студента
        row_values = self.tree.item(item)['values']
        fio = row_values[1]
        
        self.edit_grade_for_student(fio, week)
    
    def edit_grade(self):
        """Редактировать оценку через диалог"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Изменить оценку")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="ФИО студента:").pack(pady=5)
        fio_entry = ttk.Entry(dialog, width=40)
        fio_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Номер недели (1-15):").pack(pady=5)
        week_entry = ttk.Entry(dialog, width=10)
        week_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Оценка (0-100, н.я., н.п.):").pack(pady=5)
        grade_entry = ttk.Entry(dialog, width=10)
        grade_entry.pack(pady=5)
        
        def save():
            fio = fio_entry.get().strip()
            try:
                week = int(week_entry.get())
                if week < 1 or week > 15:
                    messagebox.showerror("Ошибка", "Неделя должна быть от 1 до 15")
                    return
            except ValueError:
                messagebox.showerror("Ошибка", "Неделя должна быть числом")
                return
            
            grade = grade_entry.get().strip()
            if grade and grade not in ['н.я.', 'н.п.']:
                try:
                    grade_val = int(grade)
                    if grade_val < 0 or grade_val > 100:
                        messagebox.showerror("Ошибка", "Оценка должна быть от 0 до 100")
                        return
                except ValueError:
                    messagebox.showerror("Ошибка", "Некорректная оценка")
                    return
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Получаем ID студента
            cursor.execute('SELECT id FROM students WHERE fio = ?', (fio,))
            student = cursor.fetchone()
            
            if not student:
                messagebox.showerror("Ошибка", f"Студент '{fio}' не найден")
                conn.close()
                return
            
            student_id = student['id']
            
            if grade:
                # Вставляем или обновляем оценку
                cursor.execute('''
                    INSERT INTO grades (student_id, week, grade) VALUES (?, ?, ?)
                    ON CONFLICT(student_id, week) DO UPDATE SET grade = ?
                ''', (student_id, week, grade, grade))
            else:
                # Удаляем оценку если она пустая
                cursor.execute('DELETE FROM grades WHERE student_id = ? AND week = ?', (student_id, week))
            
            conn.commit()
            conn.close()
            messagebox.showinfo("Успех", "Оценка обновлена")
            dialog.destroy()
            self.refresh_table()
        
        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=10)
    
    def edit_grade_for_student(self, fio, week):
        """Редактировать оценку конкретного студента"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Изменить оценку - {fio} (Неделя {week})")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text=f"Оценка (0-100, н.я., н.п.):").pack(pady=10)
        grade_entry = ttk.Entry(dialog, width=10)
        grade_entry.pack(pady=5)
        
        # Получаем текущую оценку
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM students WHERE fio = ?', (fio,))
        student = cursor.fetchone()
        
        if student:
            cursor.execute('SELECT grade FROM grades WHERE student_id = ? AND week = ?', (student['id'], week))
            grade_record = cursor.fetchone()
            if grade_record and grade_record['grade']:
                grade_entry.insert(0, grade_record['grade'])
        
        conn.close()
        
        def save():
            grade = grade_entry.get().strip()
            if grade and grade not in ['н.я.', 'н.п.']:
                try:
                    grade_val = int(grade)
                    if grade_val < 0 or grade_val > 100:
                        messagebox.showerror("Ошибка", "Оценка должна быть от 0 до 100")
                        return
                except ValueError:
                    messagebox.showerror("Ошибка", "Некорректная оценка")
                    return
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM students WHERE fio = ?', (fio,))
            student = cursor.fetchone()
            
            if student:
                student_id = student['id']
                if grade:
                    cursor.execute('''
                        INSERT INTO grades (student_id, week, grade) VALUES (?, ?, ?)
                        ON CONFLICT(student_id, week) DO UPDATE SET grade = ?
                    ''', (student_id, week, grade, grade))
                else:
                    cursor.execute('DELETE FROM grades WHERE student_id = ? AND week = ?', (student_id, week))
                
                conn.commit()
            
            conn.close()
            dialog.destroy()
            self.refresh_table()
        
        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = JournalApp(root)
    root.mainloop()
