from __future__ import division
import os

from rosgui.QtBindingHelper import loadUi
from QtCore import QEvent, QFile, QIODevice, QObject, QPointF, QRectF, Qt, QTextStream, Signal, SIGNAL
from QtGui import QColor, QFileDialog, QGraphicsScene, QIcon, QImage, QPainter, QWidget
from QtSvg import QSvgGenerator

import roslib
roslib.load_manifest('hip_viewer')

from rosgui_dotgraph.edge_item import EdgeItem
from rosgui_dotgraph.node_item  import NodeItem
from InteractiveGraphicsView import InteractiveGraphicsView

import hip
from hip_viewer.hip_viewer_node import HipViewerNode
from hip_viewer.colors import x11_colors

class HipViewerPlugin(QObject):

    _deferred_fit_in_view = Signal()

    def __init__(self, context):
        super(HipViewerPlugin, self).__init__(context)
        self.setObjectName('HipViewer')

        self._current_dotcode = None

        self._widget = QWidget()

        ui_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'hip_viewer.ui')
        loadUi(ui_file, self._widget, {'InteractiveGraphicsView': InteractiveGraphicsView})
        self._widget.setObjectName('HipViewerUi')
        if context.serial_number() > 1:
            self._widget.setWindowTitle(self._widget.windowTitle() + (' (%d)' % context.serial_number()))

        self._scene = QGraphicsScene()
        self._widget.graphics_view.setScene(self._scene)

        self._widget.graph_type_combo_box.insertItem(0, self.tr('infinite'), -1)
        self._widget.graph_type_combo_box.insertItem(1, self.tr('1'), 2)
        self._widget.graph_type_combo_box.insertItem(2, self.tr('2'), 3)
        self._widget.graph_type_combo_box.insertItem(3, self.tr('3'), 4)
        self._widget.graph_type_combo_box.insertItem(4, self.tr('4'), 5)
        self._widget.graph_type_combo_box.setCurrentIndex(0)

        self._widget.refresh_graph_push_button.setIcon(QIcon.fromTheme('view-refresh'))

        self._widget.highlight_connections_check_box.toggled.connect(self._redraw_graph_view)
        self._widget.auto_fit_graph_check_box.toggled.connect(self._redraw_graph_view)
        self._widget.fit_in_view_push_button.setIcon(QIcon.fromTheme('zoom-original'))
        self._widget.fit_in_view_push_button.pressed.connect(self._fit_in_view)

        self._widget.load_dot_push_button.setIcon(QIcon.fromTheme('document-open'))
        self._widget.load_dot_push_button.pressed.connect(self._load_dot)
        self._widget.save_dot_push_button.setIcon(QIcon.fromTheme('document-save-as'))
        self._widget.save_dot_push_button.pressed.connect(self._save_dot)
        self._widget.save_as_svg_push_button.setIcon(QIcon.fromTheme('document-save-as'))
        self._widget.save_as_svg_push_button.pressed.connect(self._save_svg)
        self._widget.save_as_image_push_button.setIcon(QIcon.fromTheme('image'))
        self._widget.save_as_image_push_button.pressed.connect(self._save_image)

        self._deferred_fit_in_view.connect(self._fit_in_view, Qt.QueuedConnection)
        self._deferred_fit_in_view.emit()

        context.add_widget(self._widget)

        self.connect(self, SIGNAL('update_planning_graph'), self.update_planning_graph_synchronous)

        # start the planner in a separate thread
        planning_node = HipViewerNode(ex_callback = self.update_planning_graph)
        planning_node.start()

    def save_settings(self, global_settings, perspective_settings):
        perspective_settings.set_value('graph_type_combo_box_index', self._widget.graph_type_combo_box.currentIndex())
        perspective_settings.set_value('filter_line_edit_text', self._widget.filter_line_edit.text())
        perspective_settings.set_value('quiet_check_box_state', self._widget.quiet_check_box.isChecked())
        perspective_settings.set_value('auto_fit_graph_check_box_state', self._widget.auto_fit_graph_check_box.isChecked())
        perspective_settings.set_value('highlight_connections_check_box_state', self._widget.highlight_connections_check_box.isChecked())

    def restore_settings(self, global_settings, perspective_settings):
        self._widget.graph_type_combo_box.setCurrentIndex(int(perspective_settings.value('graph_type_combo_box_index', 0)))
        self._widget.filter_line_edit.setText(perspective_settings.value('filter_line_edit_text', ''))
        self._widget.quiet_check_box.setChecked(perspective_settings.value('quiet_check_box_state', True) in [True, 'true'])
        self._widget.auto_fit_graph_check_box.setChecked(perspective_settings.value('auto_fit_graph_check_box_state', True) in [True, 'true'])
        self._widget.highlight_connections_check_box.setChecked(perspective_settings.value('highlight_connections_check_box_state', True) in [True, 'true'])

    def update_planning_graph(self, op, htree):
        self.emit(SIGNAL('update_planning_graph'), op, htree)
        
    def update_planning_graph_synchronous(self, op, htree):
        graph = hip.dot_from_plan_tree(htree)
        graph.layout('dot')
        self._update_graph_view(graph)

    def _update_graph_view(self, graph):
        self._graph  = graph
        self._redraw_graph_view()

    def _generate_tool_tip(self, url):
        if url is not None and ':' in url:
            item_type, item_path = url.split(':', 1)
            if item_type == 'node':
                tool_tip = 'Node:\n  %s' % (item_path)
                service_names = rosservice.get_service_list(node=item_path)
                if service_names:
                    tool_tip += '\nServices:'
                    for service_name in service_names:
                        try:
                            service_type = rosservice.get_service_type(service_name)
                            tool_tip += '\n  %s [%s]' % (service_name, service_type)
                        except rosservice.ROSServiceIOException, e:
                            tool_tip += '\n  %s' % (e)
                return tool_tip
            elif item_type == 'topic':
                topic_type, topic_name, _ = rostopic.get_topic_type(item_path)
                return 'Topic:\n  %s\nType:\n  %s' % (topic_name, topic_type)
        return url

    def _redraw_graph_view(self):
        self._scene.clear()

        if self._widget.highlight_connections_check_box.isChecked():
            highlight_level = 3
        else:
            highlight_level = 1

        POINTS_PER_INCH = 72

        nodes = {}
        for node in self._graph.nodes_iter():
            # decrease rect by one so that edges do not reach inside
            bounding_box = QRectF(0, 0, POINTS_PER_INCH * float(node.attr['width']) - 1.0, POINTS_PER_INCH * float(node.attr['height']) - 1.0)
            pos = node.attr['pos'].split(',')
            bounding_box.moveCenter(QPointF(float(pos[0]), -float(pos[1])))
            color_name = node.attr.get('color', None)
            if color_name is None:
                color = None
            else:
                color_name = color_name.lower()
                if color_name in x11_colors:
                    color = QColor(*x11_colors[color_name])
                else:
                    print 'Unrecognized color: %s' % color_name
                    color = None
            name = str(node)
            label = node.attr['label']
            node_item = NodeItem(highlight_level, bounding_box, label, node.attr.get('shape', 'ellipse'), color)
            #node_item.setToolTip(self._generate_tool_tip(node.attr.get('URL', None)))

            nodes[name] = node_item

        edges = {}
        for edge in self._graph.edges_iter():
            label = None
            label_center = None

            source_node = edge[0]
            destination_node = edge[1]

            # create edge with from-node and to-node
            edge_item = EdgeItem(highlight_level, edge.attr['pos'], label_center, label, nodes[source_node], nodes[destination_node])
            # symmetrically add all sibling edges with same label
            if label is not None:
                if label not in edges:
                    edges[label] = []
                for sibling in edges[label]:
                    edge_item.add_sibling_edge(sibling)
                    sibling.add_sibling_edge(edge_item)
                edges[label].append(edge_item)

            edge_item.setToolTip(self._generate_tool_tip(edge.attr.get('URL', None)))
            edge_item.add_to_scene(self._scene)

        for node_item in nodes.itervalues():
            self._scene.addItem(node_item)

        self._scene.setSceneRect(self._scene.itemsBoundingRect())
        if self._widget.auto_fit_graph_check_box.isChecked():
            self._fit_in_view()

    def _load_dot(self, file_name=None):
        if file_name is None:
            file_name, _ = QFileDialog.getOpenFileName(self._widget, self.tr('Open graph from file'), None, self.tr('DOT graph (*.dot)'))
            if file_name is None or file_name == '':
                return

        try:
            fh = open(file_name, 'rb')
            dotcode = fh.read()
            fh.close()
        except IOError:
            return

        # disable controls customizing fetched ROS graph
        self._widget.graph_type_combo_box.setEnabled(False)
        self._widget.filter_line_edit.setEnabled(False)
        self._widget.quiet_check_box.setEnabled(False)

        self._update_graph_view(dotcode)

    def _fit_in_view(self):
        self._widget.graphics_view.fitInView(self._scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def _save_dot(self):
        file_name, _ = QFileDialog.getSaveFileName(self._widget, self.tr('Save as DOT'), 'rospackgraph.dot', self.tr('DOT graph (*.dot)'))
        if file_name is None or file_name == '':
            return

        file = QFile(file_name)
        if not file.open(QIODevice.WriteOnly | QIODevice.Text):
            return

        file.write(self._current_dotcode)
        file.close()

    def _save_svg(self):
        file_name, _ = QFileDialog.getSaveFileName(self._widget, self.tr('Save as SVG'), 'rospackgraph.svg', self.tr('Scalable Vector Graphic (*.svg)'))
        if file_name is None or file_name == '':
            return

        generator = QSvgGenerator()
        generator.setFileName(file_name)
        generator.setSize((self._scene.sceneRect().size() * 2.0).toSize())

        painter = QPainter(generator)
        painter.setRenderHint(QPainter.Antialiasing)
        self._scene.render(painter)
        painter.end()

    def _save_image(self):
        file_name, _ = QFileDialog.getSaveFileName(self._widget, self.tr('Save as image'), 'rospackgraph.png', self.tr('Image (*.bmp *.jpg *.png *.tiff)'))
        if file_name is None or file_name == '':
            return

        img = QImage((self._scene.sceneRect().size() * 2.0).toSize(), QImage.Format_ARGB32_Premultiplied)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        self._scene.render(painter)
        painter.end()
        img.save(file_name)
