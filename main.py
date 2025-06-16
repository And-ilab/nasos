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

        # Задачи
        self.taskMgr.add(self.mouse_rotate_task, "MouseRotateTask")

        # Верхняя панель с названием сценария
        self.top_panel = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.7),
            frameSize=(-1.3, 1.3, -0.1, 0.1),
            pos=(0, 0, 0.9),
            #frameTexture="models/maps/noise.png"  # Текстура для фона
        )

        self.scenario_label = DirectLabel(
            parent=self.top_panel,
            text="Базовый сценарий",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            scale=0.06,
            pos=(0, 0, 0))

        self.step_label = DirectLabel(
            parent=self.top_panel,
            text="",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            scale=0.05,
            pos=(0, 0, -0.1))

        self.current_scenario = 0
        self.current_step = 0
        self.training_mode = False
        self.update_scenario_display()

        # Кнопки управления сценариями
        self.prev_btn = DirectButton(
            parent=self.top_panel,
            text="<",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.2, 0.7),
            scale=0.05,
            pos=(-1.2, 0, 0),
            relief=1,
            command=self.prev_scenario
        )

        self.next_btn = DirectButton(
            parent=self.top_panel,
            text=">",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.2, 0.7),
            scale=0.05,
            pos=(1.2, 0, 0),
            relief=1,
            command=self.next_scenario
        )

        self.start_btn = DirectButton(
            parent=self.top_panel,
            text="Старт",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.5, 0.2, 0.7),
            scale=0.05,
            pos=(0, 0, -0.2),
            relief=1,
            command=self.start_scenario
        )


    def move_forward(self):
        self.camera.set_y(self.camera, -self.camera_speed * globalClock.get_dt())

    def move_backward(self):
        self.camera.set_y(self.camera, self.camera_speed * globalClock.get_dt())

    def move_left(self):
        self.camera.set_x(self.camera, -self.camera_speed * globalClock.get_dt())

    def move_right(self):
        self.camera.set_x(self.camera, self.camera_speed * globalClock.get_dt())

    def set_ctrl_pressed(self, pressed):
        self.ctrl_pressed = pressed

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
                    return

                if picked_name == "valve2" and self.valve2:
                    if not self.valve2_spinning:
                        self.start_valve_spin(2)
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
        else:
            self.taskMgr.remove("SpinValve2Task")
            self.valve2_spinning = False
            self.valve2_spin_direction *= -1
            state = "открыт" if self.valve2_spin_direction == -1 else "закрыт"

        # Проверяем, соответствует ли действие текущему шагу сценария
        if self.training_mode:
            self.check_training_step(valve_num,
                                     -self.valve1_spin_direction if valve_num == 1 else -self.valve2_spin_direction)

        return task.done

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

    def update_scenario_display(self):
        """Обновляет отображение текущего сценария"""
        if 0 <= self.current_scenario < len(self.scenarios):
            scenario = self.scenarios[self.current_scenario]
            self.scenario_label['text'] = f"{scenario['name']}"
            self.step_label['text'] = "Нажмите Старт для начала"

    def next_scenario(self):
        """Переключает на следующий сценарий"""
        if self.current_scenario < len(self.scenarios) - 1:
            self.current_scenario += 1
            self.current_step = 0
            self.training_mode = False
            self.update_scenario_display()

    def prev_scenario(self):
        """Переключает на предыдущий сценарий"""
        if self.current_scenario > 0:
            self.current_scenario -= 1
            self.current_step = 0
            self.training_mode = False
            self.update_scenario_display()

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
            self.step_label['text'] = step['message']

    def on_step_completed(self):
        """Вызывается при завершении шага"""
        if not self.training_mode:
            return

        self.current_step += 1
        if self.current_step >= len(self.scenarios[self.current_scenario]['steps']):
            self.step_label['text'] = "Сценарий завершен!"
            self.training_mode = False
        else:
            self.execute_current_step()

    def start_valve_spin(self, valve_num):
        if valve_num == 1:
            self.valve1_spinning = True
            direction = self.valve1_spin_direction
            self.taskMgr.add(self.spin_valve1_task, "SpinValve1Task")
            self.taskMgr.doMethodLater(1.5, lambda task: self.stop_valve_spin(task, 1), "StopValve1Task")
        else:
            self.valve2_spinning = True
            direction = self.valve2_spin_direction
            self.taskMgr.add(self.spin_valve2_task, "SpinValve2Task")
            self.taskMgr.doMethodLater(1.5, lambda task: self.stop_valve_spin(task, 2), "StopValve2Task")

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

                self.step_label['text'] = "Правильно! " + step['message']
                self.on_step_completed()
            else:
                self.step_label['text'] = "Неверное действие! " + scenario['steps'][self.current_step]['message']


app = MyApp()
app.run()