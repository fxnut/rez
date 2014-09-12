from rezgui.qt import QtCore, QtGui
from rezgui.mixins.StoreSizeMixin import StoreSizeMixin
from rezgui.widgets.VariantVersionsWidget import VariantVersionsWidget
from rezgui.objects.App import app


class VariantVersionsDialog(QtGui.QDialog, StoreSizeMixin):
    def __init__(self, context_model, variant, reference_variant=None, parent=None):
        config_key = "layout/window/package_versions"
        super(VariantVersionsDialog, self).__init__(parent)
        StoreSizeMixin.__init__(self, app.config, config_key)

        self.setWindowTitle("Package Versions")
        self.versions_widget = VariantVersionsWidget(
            context_model, reference_variant=reference_variant, in_window=True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.versions_widget)
        self.setLayout(layout)

        self.versions_widget.set_variant(variant)
        self.versions_widget.closeWindow.connect(self.close)
