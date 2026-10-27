"""Medical theme stylesheet and visual styling for EMS Reporter.

Inspired by modern clinical / emergency hospital UI design:
- Crisp deep teal/slate dark background with medical accents
- Clean emergency teal (#0ea5e9, #14b8a6) and soft red emergency cross tones (#ef4444)
- High contrast readable typography, cards with gentle medical borders and badges
- Polished inputs, buttons, tooltips, dialogs, and tab controls
"""

MEDICAL_QSS = """
/* Global Window and Base Widget */
QMainWindow, QDialog {
    background-color: #0b131e;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Liberation Sans", "DejaVu Sans", Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    color: #e2e8f0;
    outline: none;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Header Banner */
#headerBanner {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #0f2b38, stop:0.5 #0c2130, stop:1 #091722);
    border-bottom: 2px solid #0ea5e9;
    padding: 12px 20px;
}

#headerTitle {
    color: #38bdf8;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

#headerSubtitle {
    color: #94a3b8;
    font-size: 12px;
}

#statsCard {
    background-color: #112233;
    border: 1px solid #1e3a52;
    border-radius: 8px;
    padding: 6px 14px;
}

#statsTotalBadge {
    color: #10b981;
    font-size: 15px;
    font-weight: 700;
}

/* Main Tab Widget */
QTabWidget::pane {
    border: 1px solid #162a3f;
    background-color: #0d1a29;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #102131;
    color: #94a3b8;
    padding: 10px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #162a3f;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #0284c7;
    color: #ffffff;
    border-color: #38bdf8;
}

QTabBar::tab:hover:!selected {
    background-color: #162e45;
    color: #f1f5f9;
}

/* Field Card / Group Box */
.FieldCard {
    background-color: #102235;
    border: 1px solid #1c3652;
    border-left: 4px solid #0ea5e9;
    border-radius: 8px;
    padding: 12px;
}

.FieldCard:hover {
    border-color: #0284c7;
    border-left: 4px solid #38bdf8;
    background-color: #12273e;
}

.FieldCardNumeric {
    background-color: #102235;
    border: 1px solid #1c3652;
    border-left: 4px solid #10b981;
    border-radius: 8px;
    padding: 12px;
}

.FieldCardNumeric:hover {
    border-color: #059669;
    border-left: 4px solid #34d399;
    background-color: #12273e;
}

/* Badges */
#badgeScore {
    background-color: #0f3747;
    color: #38bdf8;
    font-weight: 700;
    font-size: 13px;
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid #0284c7;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
}

#badgeNumericScore {
    background-color: #0c382b;
    color: #34d399;
    font-weight: 700;
    font-size: 13px;
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid #059669;
    selection-background-color: #059669;
    selection-color: #ffffff;
}

QLineEdit#badgeScore:focus {
    border: 1px solid #38bdf8;
    background-color: #123d50;
}

QLineEdit#badgeNumericScore:focus {
    border: 1px solid #34d399;
    background-color: #0f4233;
}

/* Buttons */
QPushButton {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #0369a1;
}

QPushButton:pressed {
    background-color: #075985;
}

QPushButton:disabled {
    background-color: #1b2f44;
    color: #64748b;
}

/* Action Button Variants */
QPushButton#primaryButton {
    background-color: #0284c7;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #0369a1;
}

QPushButton#successButton {
    background-color: #059669;
    color: #ffffff;
}

QPushButton#successButton:hover {
    background-color: #047857;
}

QPushButton#secondaryButton {
    background-color: #1b3046;
    color: #cbd5e1;
    border: 1px solid #284766;
}

QPushButton#secondaryButton:hover {
    background-color: #244160;
    color: #f8fafc;
    border-color: #38bdf8;
}

QPushButton#dangerButton {
    background-color: #991b1b;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #b91c1c;
}

QPushButton#iconButton {
    background-color: #162a3f;
    border: 1px solid #224364;
    border-radius: 5px;
    padding: 5px 9px;
    font-size: 12px;
}

QPushButton#iconButton:hover {
    background-color: #224364;
    border-color: #38bdf8;
}

/* Inputs & SpinBoxes */
QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
    background-color: #07101b;
    border: 1px solid #1e3a57;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f1f5f9;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #38bdf8;
    background-color: #091524;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    background-color: #162a3f;
    border-top-right-radius: 5px;
    border-left: 1px solid #1e3a57;
    border-bottom: 1px solid #1e3a57;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    background-color: #162a3f;
    border-bottom-right-radius: 5px;
    border-left: 1px solid #1e3a57;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #0284c7;
}

/* Combo Box */
QComboBox {
    background-color: #07101b;
    border: 1px solid #1e3a57;
    border-radius: 6px;
    padding: 6px 12px;
    color: #f1f5f9;
    min-height: 22px;
}

QComboBox:hover, QComboBox:focus {
    border: 1px solid #38bdf8;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #1e3a57;
}

QComboBox QAbstractItemView {
    background-color: #0b1725;
    border: 1px solid #1e3a57;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    color: #f1f5f9;
    padding: 4px;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #091421;
    width: 9px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #1b3550;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #0284c7;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #091421;
    height: 9px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #1b3550;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #0284c7;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Tooltips */
QToolTip {
    background-color: #0f2438;
    color: #e2e8f0;
    border: 1px solid #38bdf8;
    padding: 6px 10px;
    border-radius: 5px;
    font-size: 12px;
}

/* Status Bar */
QStatusBar {
    background-color: #07111b;
    color: #94a3b8;
    border-top: 1px solid #162a3f;
    font-size: 12px;
}
"""
