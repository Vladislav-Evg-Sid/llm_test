from docx.table import Table as WordTable
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml import parse_xml
from docx.shared import Inches


def optimize_table_column_weight(table: WordTable) -> None:
    tbl = table._tbl
    tblPr = tbl.tblPr
    
    for elem in tblPr.xpath('.//w:tblLayout'):
        tblPr.remove(elem)
    
    autofit_xml = parse_xml(
        '<w:tblLayout xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:type="autofit"/>'
    )
    tblPr.append(autofit_xml)
    
    auto_adjust_columns_to_content(table)
    set_minimal_cell_margins(tblPr)
    
    for row in table.rows:
        row.height_rule = WD_ROW_HEIGHT_RULE.AUTO
        row.height = None
    
    compact_cell_formatting(table)


def auto_adjust_columns_to_content(table: WordTable) -> None:
    if not table.rows or not table.columns:
        return
    
    # Собираем максимальную длину текста в каждом столбце
    max_text_length = [0] * len(table.columns)
    
    for i, column in enumerate(table.columns):
        max_len = 0
        for cell in column.cells:
            # Считаем самую длинную строку в ячейке (учитывая переносы)
            lines = cell.text.strip().split('\n')
            for line in lines:
                line_len = len(line.strip())
                # Коэффициенты для разных типов данных
                try:
                    # Если число - можно уже
                    float(line.replace(',', '.'))
                    line_len = min(line_len, 12)  # Числа ограничиваем
                except:
                    pass
                max_len = max(max_len, line_len)
        max_text_length[i] = max_len
    
    # Если все нули, выходим
    if sum(max_text_length) == 0:
        return
    
    # Распределяем ширину пропорционально длине текста
    total_chars = sum(max_text_length)
    
    # Предполагаемая ширина таблицы (6 дюймов для компактности)
    table_width_inches = 6.0
    char_width_inch = 0.09  # Примерная ширина символа при 9pt шрифте
    
    for i, column in enumerate(table.columns):
        if max_text_length[i] > 0:
            # Ширина пропорциональна содержимому
            width_inches = max_text_length[i] * char_width_inch
            # Но не менее 0.5 и не более 2.5 дюймов
            width_inches = max(0.5, min(width_inches, 2.5))
            column.width = Inches(width_inches)


def set_minimal_cell_margins(tblPr) -> None:
    # Удаляем старые отступы
    for elem in tblPr.xpath('.//w:tblCellMar'):
        tblPr.remove(elem)
    
    # Добавляем минимальные отступы
    cell_margins_xml = parse_xml(
        '<w:tblCellMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:top w:w="50" w:type="dxa"/>'      # ~0.05"
        '<w:left w:w="50" w:type="dxa"/>'     # ~0.05"
        '<w:bottom w:w="50" w:type="dxa"/>'   # ~0.05"
        '<w:right w:w="50" w:type="dxa"/>'    # ~0.05"
        '</w:tblCellMar>'
    )
    tblPr.append(cell_margins_xml)


def compact_cell_formatting(table: WordTable) -> None:
    from docx.shared import Pt
    
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                # Минимальные отступы между абзацами
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0  # Одинарный интервал
                
                # Выравнивание по центру для компактности
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # Уменьшаем шрифт если нужно
                for run in paragraph.runs:
                    if run.font.size and run.font.size.pt > 9:
                        run.font.size = Pt(9)