"""Smooth scrolling QScrollArea implementation."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QScrollArea


class SmoothScrollArea(QScrollArea):
    """QScrollArea with smooth easing wheel scroll animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_value = 0
        self._anim = QPropertyAnimation(self.verticalScrollBar(), b"value", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return

        vbar = self.verticalScrollBar()
        current = vbar.value()

        # If animation is running, build up from current target
        start_val = self._target_value if self._anim.state() == QPropertyAnimation.Running else current
        num_steps = delta / 120.0
        # Scroll roughly 80 pixels per mouse wheel click
        new_target = int(start_val - num_steps * 80)
        new_target = max(vbar.minimum(), min(vbar.maximum(), new_target))

        self._target_value = new_target
        self._anim.stop()
        self._anim.setStartValue(current)
        self._anim.setEndValue(new_target)
        self._anim.start()
        event.accept()
