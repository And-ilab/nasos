from direct.showbase.ShowBase import ShowBase
from panda3d.core import DirectionalLight, AmbientLight, Vec4, TextNode, FrameBufferProperties, WindowProperties, \
    GraphicsPipe, Vec3
from direct.gui.DirectGui import DirectFrame, DirectLabel
from panda3d.core import CollisionTraverser, CollisionNode, CollisionHandlerQueue, CollisionRay, CollisionBox, BitMask32
from panda3d.core import Filename, TextFont, Loader
import time
from direct.gui.DirectGui import DirectScrolledFrame, DirectLabel
from panda3d.core import Texture, GraphicsOutput, Camera, NodePath, OrthographicLens
from panda3d.core import GeomNode, GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexWriter
from panda3d.core import CardMaker
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DirectScrolledFrame

class MyApp(ShowBase):
    def __init__(self):
        super().__init__()

        font = self.loader.load_font("arial.ttf")

        self.logical_parts = {
            "вентиль1": "**/COMPOUND019",
            "ручка1": "**/COMPOUND094",
            "вентиль2": "**/COMPOUND056",
            "ручка2": "**/COMPOUND366"
        }

        self.scenarios = [
            {
                'name': "Базовый сценарий",
                'steps': [
                    {'action': 'rotate_valve', 'valve': 1, 'direction': 1,
                     'message': "Открытие лафетного ствола"},
                    {'action': 'rotate_valve', 'valve': 2, 'direction': -1,
                     'message': "Подача пены"}
                ]
            },
            {
                'name': "Аварийный сценарий",
                'steps': [
                    {'action': 'rotate_valve', 'valve': 2, 'direction': 1,
                     'message': "Закрытие подачи пены"},
                    {'action': 'rotate_valve', 'valve': 1, 'direction': -1,
                     'message': "Закрытие лафетного ствола"}
                ]
            },
            {
                'name': "Тестовый сценарий",
                'steps': [
                    {'action': 'rotate_valve', 'valve': 1, 'direction': 1,
                     'message': "Тест открытия ствола"},
                    {'action': 'rotate_valve', 'valve': 1, 'direction': -1,
                     'message': "Тест закрытия ствола"}
                ]
            }
        ]



        # Свет
        dlight = DirectionalLight("dlight")
        alight = AmbientLight("alight")
        dlight.set_color(Vec4(0.8, 0.8, 0.7, 1))
        alight.set_color(Vec4(0.2, 0.2, 0.2, 1))
        render.set_light(render.attach_new_node(dlight))
        render.set_light(render.attach_new_node(alight))

        # Загрузка модели
        self.model = self.loader.load_model("Насос.obj")
        self.model.reparent_to(self.render)
        self.model.set_scale(1)
        self.cam.look_at(self.model)

        self.ctrl_pressed = False
        self.accept('control', self.set_ctrl_pressed, [True])
        self.accept('control-up', self.set_ctrl_pressed, [False])

        valve1_geom = self.model.find("**/COMPOUND019")
        valve1_handle_geom = self.model.find("**/COMPOUND094")

        # Инициализация второго вентиля
        valve2_geom = self.model.find("**/COMPOUND056")
        valve2_handle_geom = self.model.find("**/COMPOUND366")

        self.valve1_spinning = False
        self.valve2_spinning = False
        self.valve1_spin_direction = 1
        self.valve2_spin_direction = 1
        self.model.ls()
        self.log_lines = []  # Список строк для лога
        self.max_lines = 100

        self.camera_speed = 10  # Скорость движения камеры
        self.accept('w', self.move_forward)
        self.accept('s', self.move_backward)
        self.accept('a', self.move_left)
        self.accept('d', self.move_right)

        if valve1_geom.is_empty():
            print("❌ COMPOUND019 (вентиль1) не найден.")
            self.valve1 = None
        else:
            print("✅ COMPOUND019 найден.")
            min_bound, max_bound = valve1_geom.get_tight_bounds()
            center_point = (min_bound + max_bound) * 0.5

            self.valve1 = self.model.attach_new_node("valve1_assembly")
            self.valve1.set_pos(center_point)
            valve1_geom.wrt_reparent_to(self.valve1)

            if not valve1_handle_geom.is_empty():
                print("✅ Ручка вентиля1 найдена")
                valve1_handle_geom.wrt_reparent_to(self.valve1)
            else:
                print("❌ Ручка вентиля1 не найдена")

            extent = (max_bound - min_bound) * 0.5
            bounds_box = CollisionBox((0, 0, 0), extent.x, extent.y, extent.z)
            valve1_cnode = CollisionNode("valve1")
            valve1_cnode.add_solid(bounds_box)
            valve1_cnode.set_into_collide_mask(BitMask32.bit(1))
            self.valve1.attach_new_node(valve1_cnode).show()

            # Создание второго вентиля
        if valve2_geom.is_empty():
            print("❌ COMPOUND56 (вентиль2) не найден.")
            self.valve2 = None
        else:
            print("✅ COMPOUND56 найден.")
            min_bound, max_bound = valve2_geom.get_tight_bounds()
            center_point = (min_bound + max_bound) * 0.5

            self.valve2 = self.model.attach_new_node("valve2_assembly")
            self.valve2.set_pos(center_point)
            valve2_geom.wrt_reparent_to(self.valve2)

            if not valve2_handle_geom.is_empty():
                print("✅ Ручка вентиля2 найдена")
                valve2_handle_geom.wrt_reparent_to(self.valve2)
            else:
                print("❌ Ручка вентиля2 не найдена")

            extent = (max_bound - min_bound) * 0.5
            bounds_box = CollisionBox((0, 0, 0), extent.x, extent.y, extent.z)
            valve2_cnode = CollisionNode("valve2")
            valve2_cnode.add_solid(bounds_box)
            valve2_cnode.set_into_collide_mask(BitMask32.bit(1))
            self.valve2.attach_new_node(valve2_cnode).show()
            # Коллизия (пикер)
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        self.picker_ray = CollisionRay()
        self.picker_node = CollisionNode('mouseRay')
        self.picker_node.add_solid(self.picker_ray)
        self.picker_node.set_from_collide_mask(BitMask32.bit(1))
        self.picker_node.set_into_collide_mask(BitMask32.all_off())
        self.picker_np = self.camera.attach_new_node(self.picker_node)
        self.picker.add_collider(self.picker_np, self.pq)


        self.model.set_pos(0, 2500, -200)
        self.model.set_hpr(270, 255, 0)
        self.camera.set_pos(0, 0, 0)  # Камера в начале координат
        self.camera.look_at(self.model)


        # Управление мышью
        self.prev_mouse_pos = None
        self.rotation_speed = 180

        self.accept('mouse1', self.on_mouse_down)
        self.accept('mouse1-up', self.on_mouse_up)
        self.accept('wheel_up', self.on_zoom_in)
        self.accept('wheel_down', self.on_zoom_out)
        self.accept("wheel_up", self.scroll_up)
        self.accept("wheel_down", self.scroll_down)


        # Задачи
        self.taskMgr.add(self.mouse_rotate_task, "MouseRotateTask")
        "!!!"
        dr = self.win.makeDisplayRegion(0, 0.4, 0.6, 1.0)
        dr.setSort(10)

        self.closeup_cam = self.makeCamera(self.win)
        self.closeup_cam.reparentTo(self.render)
        self.closeup_cam.node().setLens(OrthographicLens())
        self.closeup_cam.node().getLens().setFilmSize(10, 10)
        self.closeup_cam.node().getLens().setNearFar(0.1, 1000)
        dr.setCamera(self.closeup_cam)
        self.closeup_cam.node().setActive(True)  # Всегда активна

        # Рамка для области просмотра
        self.closeup_frame = DirectFrame(
            frameSize=(-0.29, 0.29, -0.29, 0.29),
            frameColor=(0.1, 0.1, 0.1, 0.7),
            pos=(-0.65, 0, 0.65)
        )
        self.closeup_frame.setTransparency(1)

        # Текущий выбранный вентиль
        self.current_closeup_target = None

        # ===== НИЖНЯЯ ПАНЕЛЬ С ПРОКРУТКОЙ =====
        self.bottom_panel = DirectScrolledFrame(
            frameColor=(0, 0, 0, 0.7),
            frameSize=(-1.3, 1.3, -0.2, 0.2),
            canvasSize=(-1.25, 1.25, -5, 0.05),  # Достаточно места для прокрутки вверх
            scrollBarWidth=0.05,
            pos=(0, 0, -0.85),
            verticalScroll_relief=None,
            manageScrollBars=True
        )

        # Контейнер, куда будут добавляться текстовые лейблы
        self.log_container = self.bottom_panel.getCanvas()
        self.log_labels = []  # Список лейблов
        self.line_height = 0.07  # Отступ между строками
        self.closeup_frame.hide()

        self.current_scenario = 0
        self.current_step = 0
        self.training_mode = False

        self.add_scenario_controls()

    def move_forward(self):
        self.camera.set_y(self.camera, -self.camera_speed * globalClock.get_dt())

    def move_backward(self):
        self.camera.set_y(self.camera, self.camera_speed * globalClock.get_dt())

    def move_left(self):
        self.camera.set_x(self.camera, -self.camera_speed * globalClock.get_dt())

    def move_right(self):
        self.camera.set_x(self.camera, self.camera_speed * globalClock.get_dt())


    def scroll_up(self):
        self.bottom_panel["verticalScroll_value"] = min(
            self.bottom_panel["verticalScroll_value"] + 0.1, 1.0
        )

    def scroll_down(self):
        self.bottom_panel["verticalScroll_value"] = max(
            self.bottom_panel["verticalScroll_value"] - 0.1, 0.0
        )

    def log_to_bottom_panel(self, message):
        self.log_lines.append(message)
        if len(self.log_lines) > self.max_lines:
            self.log_lines.pop(0)

        for lbl in self.log_labels:
            lbl.destroy()
        self.log_labels = []

        for i, line in enumerate(self.log_lines):
            lbl = DirectLabel(
                parent=self.log_container,
                text=line,
                text_align=TextNode.A_center,
                text_fg=(1, 1, 1, 1),
                frameColor=(0, 0, 0, 0),
                scale=0.05,
                pos=(0, 0, -self.line_height * i),
                text_font=self.loader.load_font("arial.ttf"),
            )
            self.log_labels.append(lbl)

        # Обновляем размер холста по количеству строк
        new_bottom = min(-0.15, -self.line_height * len(self.log_lines))
        self.bottom_panel["canvasSize"] = (-1.25, 1.25, new_bottom, 0.05)

        # Автопрокрутка к последнему сообщению
        self.bottom_panel["verticalScroll_value"] = 1.0

    def set_ctrl_pressed(self, pressed):
        self.ctrl_pressed = pressed

    def show_closeup(self, valve_node):
        """Активирует камеру крупного плана на указанный вентиль"""
        if self.current_closeup_target == valve_node:
            return  # Уже показываем этот вентиль

        self.current_closeup_target = valve_node

        bounds = valve_node.getBounds()
        center = bounds.getCenter()
        center = valve_node.getRelativePoint(render, center)  # Преобразуем в глобальные координаты


        offset = Vec3(300, -600, 300)  # Можно подстроить под конкретную модель
        self.closeup_cam.setPos(center + offset)
        self.closeup_cam.lookAt(center)

        print(f"Центр вентиля: {center}")
        print(f"Позиция камеры: {self.closeup_cam.getPos()}")
        print(f"Направление камеры: {self.closeup_cam.getQuat()}")

    def hide_closeup(self, task):
        """Скрывает камеру крупного плана"""
        self.closeup_cam.node().setActive(False)
        self.closeup_frame.hide()
        return task.done

    def on_mouse_down(self):
        if self.mouseWatcherNode.has_mouse() and not self.ctrl_pressed:
            # Сохраняем текущую позицию мыши для вращения
            self.prev_mouse_pos = self.mouseWatcherNode.get_mouse()

            # Остальной код для обработки кликов на вентили
            mpos = self.mouseWatcherNode.get_mouse()
            self.picker_ray.set_from_lens(self.camNode, mpos.get_x(), mpos.get_y())
            self.picker.traverse(self.render)

            if self.pq.get_num_entries() > 0:
                self.pq.sort_entries()
                picked_entry = self.pq.get_entry(0)
                picked_np = picked_entry.get_into_node_path()
                picked_name = picked_np.get_name()

                if picked_name == "valve1" and self.valve1:
                    if not self.valve1_spinning:
                        self.start_valve_spin(1)
                        self.log_to_bottom_panel("Вращение вентиля1 запущено")
                        self.show_closeup(self.valve1)
                    return

                if picked_name == "valve2" and self.valve2:
                    if not self.valve2_spinning:
                        self.start_valve_spin(2)
                        self.log_to_bottom_panel("Вращение вентиля2 запущено")
                        self.show_closeup(self.valve2)
                    return

    def spin_valve1_task(self, task):
        if self.valve1:
            angle = 60 * globalClock.get_dt() * self.valve1_spin_direction
            self.valve1.set_p(self.valve1.get_p() + angle)
        return task.cont

    def spin_valve2_task(self, task):
        if self.valve2:
            angle = 60 * globalClock.get_dt() * self.valve2_spin_direction
            self.valve2.set_p(self.valve2.get_p() + angle)
        return task.cont


    def stop_valve_spin(self, task, valve_num):
        if valve_num == 1:
            self.taskMgr.remove("SpinValve1Task")
            self.valve1_spinning = False
            self.valve1_spin_direction *= -1
            state = "открыт" if self.valve1_spin_direction == -1 else "закрыт"
            self.closeup_frame.hide()
        else:
            self.taskMgr.remove("SpinValve2Task")
            self.valve2_spinning = False
            self.valve2_spin_direction *= -1
            state = "открыт" if self.valve2_spin_direction == -1 else "закрыт"
            self.closeup_frame.hide()

        self.log_to_bottom_panel(f"Вентиль{valve_num} {state}!")
        return task.done  # Теперь task определен

    def on_mouse_up(self):
        self.prev_mouse_pos = None

    def on_zoom_in(self):
        self.cam.set_pos(self.cam.get_pos() * 0.9)

    def on_zoom_out(self):
        self.cam.set_pos(self.cam.get_pos() * 1.1)


    def mouse_rotate_task(self, task):
        if self.mouseWatcherNode.has_mouse() and self.mouseWatcherNode.is_button_down(0):
            mouse_pos = self.mouseWatcherNode.get_mouse()

            if self.prev_mouse_pos:
                delta = mouse_pos - self.prev_mouse_pos

                if self.ctrl_pressed:
                    # Вращение модели при зажатом Ctrl
                    self.model.set_h(self.model.get_h() - delta.x * self.rotation_speed)
                    self.model.set_p(self.model.get_p() + delta.y * self.rotation_speed)
                else:
                    # Вращение камеры (первый человек)
                    heading = self.camera.get_h() - delta.x * self.rotation_speed
                    pitch = max(-90, min(90, self.camera.get_p() + delta.y * self.rotation_speed))
                    self.camera.set_hpr(heading, pitch, 0)

            self.prev_mouse_pos = mouse_pos
        else:
            self.prev_mouse_pos = None

        return task.cont

    def add_scenario_controls(self):
        """Добавляет элементы управления сценариями на нижнюю панель"""
        # Сначала создаем нижнюю панель, если она еще не создана
        if not hasattr(self, 'bottom_panel'):
            self.bottom_panel = DirectScrolledFrame(
                frameColor=(0, 0, 0, 0.7),
                frameSize=(-1.3, 1.3, -0.2, 0.2),
                canvasSize=(-1.25, 1.25, -5, 0.05),
                scrollBarWidth=0.05,
                pos=(0, 0, -0.85),
                verticalScroll_relief=None,
                manageScrollBars=True
            )
            self.log_container = self.bottom_panel.getCanvas()
            self.log_labels = []
            self.line_height = 0.07

        # Кнопка "влево" (предыдущий сценарий) - используем DirectButton
        self.prev_btn = DirectButton(
            parent=self.bottom_panel,
            text="<",
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.2, 0.7),
            scale=0.08,
            pos=(-1.1, 0, -0.05),
            relief=1,
            command=self.prev_scenario
        )

        # Кнопка "вправо" (следующий сценарий)
        self.next_btn = DirectButton(
            parent=self.bottom_panel,
            text=">",
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.2, 0.7),
            scale=0.08,
            pos=(1.1, 0, -0.05),
            relief=1,
            command=self.next_scenario
        )

        # Метка с названием текущего сценария (здесь используем DirectLabel)
        self.scenario_label = DirectLabel(
            parent=self.bottom_panel,
            text="",
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            scale=0.05,
            pos=(0, 0, -0.05)
        )

        self.update_scenario_display()

    def update_scenario_display(self):
        """Обновляет отображение текущего сценария"""
        if 0 <= self.current_scenario < len(self.scenarios):
            scenario = self.scenarios[self.current_scenario]
            self.scenario_label['text'] = f"{self.current_scenario + 1}/{len(self.scenarios)}: {scenario['name']}"

    def next_scenario(self):
        """Переключает на следующий сценарий"""
        if self.current_scenario < len(self.scenarios) - 1:
            self.current_scenario += 1
            self.current_step = 0
            self.update_scenario_display()
            self.log_to_bottom_panel(f"Загружен сценарий: {self.scenarios[self.current_scenario]['name']}")
            self.start_scenario()

    def prev_scenario(self):
        """Переключает на предыдущий сценарий"""
        if self.current_scenario > 0:
            self.current_scenario -= 1
            self.current_step = 0
            self.update_scenario_display()
            self.log_to_bottom_panel(f"Загружен сценарий: {self.scenarios[self.current_scenario]['name']}")
            self.start_scenario()

    def start_scenario(self):
        """Запускает текущий сценарий"""
        self.training_mode = True
        self.current_step = 0
        self.execute_current_step()

    def execute_current_step(self):
        """Выполняет текущий шаг сценария"""
        if not self.training_mode:
            return

        scenario = self.scenarios[self.current_scenario]
        if self.current_step < len(scenario['steps']):
            step = scenario['steps'][self.current_step]
            self.log_to_bottom_panel(f"Шаг {self.current_step + 1}: {step['message']}")

            # Здесь можно добавить автоматическое выполнение действий
            # или просто ждать, пока пользователь выполнит их вручную
            if step['action'] == 'rotate_valve':
                # Можно автоматически начать вращение или просто показать подсказку
                pass

    def on_step_completed(self):
        """Вызывается при завершении шага"""
        if not self.training_mode:
            return

        self.current_step += 1
        if self.current_step >= len(self.scenarios[self.current_scenario]['steps']):
            self.log_to_bottom_panel("Сценарий завершен!")
            self.training_mode = False
        else:
            self.execute_current_step()

    # В метод start_valve_spin добавить проверку на обучающий режим:
    def start_valve_spin(self, valve_num):
        if valve_num == 1:
            self.closeup_frame.show()
            self.valve1_spinning = True
            direction = self.valve1_spin_direction
            self.taskMgr.add(self.spin_valve1_task, "SpinValve1Task")
            self.taskMgr.doMethodLater(1.5, lambda task: self.stop_valve_spin(task, 1), "StopValve1Task")
        else:
            self.closeup_frame.show()
            self.valve2_spinning = True
            direction = self.valve2_spin_direction
            self.taskMgr.add(self.spin_valve2_task, "SpinValve2Task")
            self.taskMgr.doMethodLater(1.5, lambda task: self.stop_valve_spin(task, 2), "StopValve2Task")

        # Логирование действия
        action = "откручивается" if direction == 1 else "закручивается"
        self.log_to_bottom_panel(f"Вращение вентиля{valve_num} {action}...")

        # Проверка шага сценария, если в обучающем режиме
        if self.training_mode:
            self.check_training_step(valve_num, direction)

    def check_training_step(self, valve_num, direction):
        """Проверяет, соответствует ли действие текущему шагу сценария"""
        if not self.training_mode:
            return

        scenario = self.scenarios[self.current_scenario]
        if self.current_step < len(scenario['steps']):
            step = scenario['steps'][self.current_step]

            if (step['action'] == 'rotate_valve' and
                    step['valve'] == valve_num and
                    step['direction'] == direction):

                self.log_to_bottom_panel("Правильно! Переходим к следующему шагу.")
                self.on_step_completed()
            else:
                self.log_to_bottom_panel("Неверное действие! Следуйте инструкциям.")

app = MyApp()
app.run()