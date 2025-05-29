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
import math


class MyApp(ShowBase):
    def __init__(self):
        super().__init__()

        font = self.loader.load_font("arial.ttf")

        self.logical_parts = {
            "вентиль1": "**/COMPOUND019",
            "ручка1": "**/COMPOUND094",
            "вентиль2": "**/COMPOUND056",
            "ручка2": "**/COMPOUND366",
            "вентиль3": "**/COMPOUND034",
            "ручка3": "**/COMPOUND089",
            "вентиль4": "**/COMPOUND020",
            "ручка4": "**/COMPOUND071",
            "рычаг": "**/COMPOUND073",
            "рычаг2": "**/COMPOUND065",
        }

        self.scenarios = [
            {
                'name': "Базовый сценарий",
                'steps': [
                    {'action': 'rotate_valve', 'valve': 1, 'direction': 1,
                     'message': "Открытие лафетного ствола"},
                    {'action': 'rotate_valve', 'valve': 3, 'direction': 1,
                     'message': "Регулировка давления"},
                    {'action': 'rotate_valve', 'valve': 5, 'direction': 1,
                     'message': "Активация основного насоса"},
                ]
            },
            {
                'name': "Аварийный сценарий",
                'steps': [
                    {'action': 'rotate_valve', 'valve': 2, 'direction': -1,
                     'message': "Закрытие подачи пены"},
                    {'action': 'rotate_valve', 'valve': 6, 'direction': 1,
                     'message': "Активация аварийного насоса"},
                    {'action': 'rotate_valve', 'valve': 4, 'direction': -1,
                     'message': "Сброс давления"}
                ]
            },
            {
                'name': "Тестовый сценарий",
                'steps': [
                    {'action': 'rotate_valve', 'valve': 1, 'direction': 1,
                     'message': "Тест открытия ствола"},
                    {'action': 'rotate_valve', 'valve': 1, 'direction': -1,
                     'message': "Тест закрытия ствола"},
                    {'action': 'rotate_valve', 'valve': 3, 'direction': 1,
                     'message': "Тест регулировки давления"}
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

        # Инициализация вентилей
        valve1_geom = self.model.find("**/COMPOUND019")
        valve1_handle_geom = self.model.find("**/COMPOUND094")
        valve2_geom = self.model.find("**/COMPOUND056")
        valve2_handle_geom = self.model.find("**/COMPOUND366")
        valve3_geom = self.model.find("**/COMPOUND034")
        valve3_handle_geom = self.model.find("**/COMPOUND089")
        valve4_geom = self.model.find("**/COMPOUND020")
        valve4_handle_geom = self.model.find("**/COMPOUND071")
        valve5_geom = self.model.find("**/COMPOUND073")
        valve5_top_geom = self.model.find("**/COMPOUND111")  # Верхняя часть рычага 5
        valve6_geom = self.model.find("**/COMPOUND065")

        self.valve1_spinning = False
        self.valve2_spinning = False
        self.valve3_spinning = False
        self.valve4_spinning = False
        self.valve5_moving = False
        self.valve6_moving = False
        self.valve1_spin_direction = 1
        self.valve2_spin_direction = 1
        self.valve3_spin_direction = 1
        self.valve4_spin_direction = 1

        # Инициализация вентиля 1
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

        # Инициализация вентиля 2
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

        if valve3_geom.is_empty():
            print("❌ COMPOUND034 (вентиль3) не найден.")
            self.valve3 = None
        else:
            print("✅ COMPOUND034 найден.")
            min_bound, max_bound = valve3_geom.get_tight_bounds()
            center_point = (min_bound + max_bound) * 0.5

            self.valve3 = self.model.attach_new_node("valve3_assembly")
            self.valve3.set_pos(center_point)
            valve3_geom.wrt_reparent_to(self.valve3)

            if not valve3_handle_geom.is_empty():
                print("✅ Ручка вентиля3 найдена")
                valve3_handle_geom.wrt_reparent_to(self.valve3)
            else:
                print("❌ Ручка вентиля3 не найдена")

            extent = (max_bound - min_bound) * 0.5
            bounds_box = CollisionBox((0, 0, 0), extent.x, extent.y, extent.z)
            valve3_cnode = CollisionNode("valve3")
            valve3_cnode.add_solid(bounds_box)
            valve3_cnode.set_into_collide_mask(BitMask32.bit(1))
            self.valve3.attach_new_node(valve3_cnode).show()

        if valve4_geom.is_empty():
            print("❌ COMPOUND020 (вентиль4) не найден.")
            self.valve4 = None
        else:
            print("✅ COMPOUND020 найден.")
            min_bound, max_bound = valve4_geom.get_tight_bounds()
            center_point = (min_bound + max_bound) * 0.5

            self.valve4 = self.model.attach_new_node("valve4_assembly")
            self.valve4.set_pos(center_point)
            valve4_geom.wrt_reparent_to(self.valve4)

            if not valve4_handle_geom.is_empty():
                print("✅ Ручка вентиля4 найдена")
                valve4_handle_geom.wrt_reparent_to(self.valve4)
            else:
                print("❌ Ручка вентиля4 не найдена")

            extent = (max_bound - min_bound) * 0.5
            bounds_box = CollisionBox((0, 0, 0), extent.x, extent.y, extent.z)
            valve4_cnode = CollisionNode("valve4")
            valve4_cnode.add_solid(bounds_box)
            valve4_cnode.set_into_collide_mask(BitMask32.bit(1))
            self.valve4.attach_new_node(valve4_cnode).show()

        # Инициализация рычага 5
        if valve5_geom.is_empty():
            print("❌ COMPOUND073 (рычаг5) не найден.")
            self.valve5 = None
            self.valve5_pivot = None
        else:
            print("✅ COMPOUND073 найден.")

            # Находим болт COMPOUND489
            bolt_geom = self.model.find("**/COMPOUND489")
            if bolt_geom.is_empty():
                print("❌ Болт COMPOUND489 не найден, используем нижнюю точку")
                min_bound, max_bound = valve5_geom.get_tight_bounds()
                pivot_point = Vec3(
                    (min_bound.x + max_bound.x) * 0.5,
                    (min_bound.y + max_bound.y) * 0.5,
                    min_bound.z
                )
            else:
                print("✅ Болт COMPOUND489 найден")
                bolt_min, bolt_max = bolt_geom.get_tight_bounds()
                pivot_point = (bolt_min + bolt_max) * 0.5

            # Создаем узел для вращения в точке болта
            self.valve5_pivot = self.model.attach_new_node("valve5_pivot")
            self.valve5_pivot.set_pos(pivot_point)

            # Создаем узел для самого рычага
            self.valve5 = self.valve5_pivot.attach_new_node("valve5")
            valve5_geom.reparent_to(self.valve5)

            # Прикрепляем верхнюю часть к рычагу
            if not valve5_top_geom.is_empty():
                print("✅ Верхняя часть рычага5 найдена")
                valve5_top_geom.wrt_reparent_to(self.valve5)
            else:
                print("❌ Верхняя часть рычага5 не найдена")

            # Смещаем геометрию так, чтобы болт был в начале координат
            valve5_geom.set_pos(-pivot_point)
            if not valve5_top_geom.is_empty():
                valve5_top_geom.set_pos(-pivot_point)

            # Начальное положение - вертикально (0°)
            self.valve5_pivot.set_p(0)
            self.valve5_target_angle = 90  # Целевой угол - горизонтально (90°)
            self.valve5_moving = False

            # Настройка коллизии - создаем коллизию в узле valve5 (а не valve5_pivot)
            min_bound, max_bound = valve5_geom.get_tight_bounds()
            extent = (max_bound - min_bound) * 0.5
            center = Vec3(0, 0, 0)  # Центр относительно valve5 (уже смещенного)
            bounds_box = CollisionBox(center, extent.x, extent.y, extent.z)
            valve5_cnode = CollisionNode("valve5")
            valve5_cnode.add_solid(bounds_box)
            valve5_cnode.set_into_collide_mask(BitMask32.bit(1))
            self.valve5.attach_new_node(valve5_cnode).show()

        # Инициализация рычага 6
        if valve6_geom.is_empty():
            print("❌ COMPOUND065 (рычаг6) не найден.")
            self.valve6 = None
            self.valve6_pivot = None
        else:
            print("✅ COMPOUND065 найден.")

            # Находим болт COMPOUND389
            bolt_geom = self.model.find("**/COMPOUND389")
            if bolt_geom.is_empty():
                print("❌ Болт COMPOUND389 не найден, используем нижнюю точку")
                min_bound, max_bound = valve6_geom.get_tight_bounds()
                pivot_point = Vec3(
                    (min_bound.x + max_bound.x) * 0.5,
                    (min_bound.y + max_bound.y) * 0.5,
                    min_bound.z
                )
            else:
                print("✅ Болт COMPOUND389 найден")
                bolt_min, bolt_max = bolt_geom.get_tight_bounds()
                pivot_point = (bolt_min + bolt_max) * 0.5

            # Создаем узел для вращения в точке болта
            self.valve6_pivot = self.model.attach_new_node("valve6_pivot")
            self.valve6_pivot.set_pos(pivot_point)

            # Создаем узел для самого рычага
            self.valve6 = self.valve6_pivot.attach_new_node("valve6")
            valve6_geom.reparent_to(self.valve6)

            # Смещаем геометрию так, чтобы болт был в начале координат
            valve6_geom.set_pos(-pivot_point)

            # Начальное положение - вертикально (0°)
            self.valve6_pivot.set_p(0)
            self.valve6_target_angle = 90  # Целевой угол - горизонтально (90°)
            self.valve6_moving = False

            # Настройка коллизии
            min_bound, max_bound = valve6_geom.get_tight_bounds()
            extent = (max_bound - min_bound) * 0.5
            center = Vec3(0, 0, 0)  # Центр относительно valve6 (уже смещенного)
            bounds_box = CollisionBox(center, extent.x, extent.y, extent.z)
            valve6_cnode = CollisionNode("valve6")
            valve6_cnode.add_solid(bounds_box)
            valve6_cnode.set_into_collide_mask(BitMask32.bit(1))
            self.valve6.attach_new_node(valve6_cnode).show()

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
        self.camera.set_pos(0, 0, 0)
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

        # Нижняя панель с названием сценария (поднята выше)
        self.bottom_panel = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.7),
            frameSize=(-1.5, 1.5, -0.15, 0.15),  # Увеличена по ширине и высоте
            pos=(0, 0, -0.85),  # Поднята ещё выше
        )

        self.scenario_label = DirectLabel(
            parent=self.bottom_panel,
            text="Базовый сценарий",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            scale=0.06,
            pos=(0, 0, 0.03))  # Текст немного выше в панели

        self.step_label = DirectLabel(
            parent=self.bottom_panel,
            text="",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            scale=0.05,
            pos=(0, 0, -0.07))  # Текст шага немного ниже

        self.current_scenario = 0
        self.current_step = 0
        self.training_mode = False
        self.auto_mode = False
        self.update_scenario_display()
        self.prev_btn = DirectButton(
            parent=self.bottom_panel,
            text="<",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.2, 0.7),
            scale=0.05,
            pos=(-1.4, 0, 0),  # Сдвинута левее
            relief=1,
            command=self.prev_scenario
        )

        self.next_btn = DirectButton(
            parent=self.bottom_panel,
            text=">",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.2, 0.7),
            scale=0.05,
            pos=(1.4, 0, 0),  # Сдвинута правее
            relief=1,
            command=self.next_scenario
        )

        # Кнопка Старт над панелью (поднята выше)
        self.start_btn = DirectButton(
            parent=self.aspect2d,
            text="Старт",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.5, 0.2, 0.7),
            scale=0.05,
            pos=(0, 0, -0.75),  # Поднята выше
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
            self.prev_mouse_pos = self.mouseWatcherNode.get_mouse()

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

                if picked_name == "valve3" and self.valve3:
                    if not self.valve3_spinning:
                        self.start_valve_spin(3)
                    return

                if picked_name == "valve4" and self.valve4:
                    if not self.valve4_spinning:
                        self.start_valve_spin(4)
                    return

                if picked_name == "valve5" and self.valve5 and not self.valve5_moving:
                    self.start_valve_spin(5)
                    return

                if picked_name == "valve6" and self.valve6 and not self.valve6_moving:
                    self.start_valve_spin(6)
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

    def spin_valve3_task(self, task):
        if self.valve3:
            angle = 60 * globalClock.get_dt() * self.valve3_spin_direction
            self.valve3.set_hpr(self.valve3.get_h() + angle, self.valve3.get_p(), self.valve3.get_r())
        return task.cont

    def spin_valve4_task(self, task):
        if self.valve4:
            angle = 60 * globalClock.get_dt() * self.valve4_spin_direction
            self.valve4.set_hpr(self.valve4.get_h() + angle, self.valve4.get_p(), self.valve4.get_r())
        return task.cont

    def move_valve5_task(self, task):
        if not self.valve5_pivot:
            return task.done

        current_angle = self.valve5_pivot.get_p()
        target_angle = self.valve5_target_angle
        speed = 180  # градусов в секунду

        # Плавное движение к целевому углу
        delta = min(speed * globalClock.get_dt(), abs(target_angle - current_angle))
        new_angle = current_angle + delta * (1 if target_angle > current_angle else -1)
        self.valve5_pivot.set_p(new_angle)

        # Если достигли цели
        if abs(new_angle - target_angle) < 0.1:
            self.valve5_moving = False
            # Переключаем целевой угол между 0 и 90 градусами
            self.valve5_target_angle = 0 if target_angle == 90 else 90

            if self.training_mode:
                self.check_training_step(5, 1)
            return task.done

        return task.cont

    def move_valve6_task(self, task):
        if not self.valve6_pivot:
            return task.done

        current_angle = self.valve6_pivot.get_p()
        target_angle = self.valve6_target_angle
        speed = 180  # градусов в секунду

        # Плавное движение к целевому углу
        delta = min(speed * globalClock.get_dt(), abs(target_angle - current_angle))
        new_angle = current_angle + delta * (1 if target_angle > current_angle else -1)
        self.valve6_pivot.set_p(new_angle)

        # Если достигли цели
        if abs(new_angle - target_angle) < 0.1:
            self.valve6_moving = False
            # Переключаем целевой угол между 0 и 90 градусами
            self.valve6_target_angle = 0 if target_angle == 90 else 90

            if self.training_mode:
                self.check_training_step(6, 1)
            return task.done

        return task.cont

    def stop_valve_spin(self, task, valve_num):
        if valve_num == 1:
            self.taskMgr.remove("SpinValve1Task")
            self.valve1_spinning = False
            self.valve1_spin_direction *= -1
        elif valve_num == 2:
            self.taskMgr.remove("SpinValve2Task")
            self.valve2_spinning = False
            self.valve2_spin_direction *= -1
        elif valve_num == 3:
            self.taskMgr.remove("SpinValve3Task")
            self.valve3_spinning = False
            self.valve3_spin_direction *= -1
        elif valve_num == 4:
            self.taskMgr.remove("SpinValve4Task")
            self.valve4_spinning = False
            self.valve4_spin_direction *= -1

        if self.training_mode and not self.auto_mode:
            self.check_training_step(valve_num,
                                     -self.valve1_spin_direction if valve_num == 1 else
                                     -self.valve2_spin_direction if valve_num == 2 else
                                     -self.valve3_spin_direction if valve_num == 3 else
                                     -self.valve4_spin_direction if valve_num == 4 else 0)
        elif self.auto_mode:
            self.on_step_completed()

        return task.done

    def on_mouse_up(self):
        self.prev_mouse_pos = None

    def on_zoom_in(self):
        self.camera_distance = max(self.min_distance, self.camera_distance - self.zoom_speed * globalClock.get_dt())
        self.update_camera_position()

    def on_zoom_out(self):
        self.camera_distance = min(self.max_distance, self.camera_distance + self.zoom_speed * globalClock.get_dt())
        self.update_camera_position()

    def reset_camera(self):
        h = math.radians(self.camera.get_h())
        p = math.radians(self.camera.get_p())
        x = self.model.get_x() + self.camera_distance * math.sin(h) * math.cos(p)
        y = self.model.get_y() - self.camera_distance * math.cos(h) * math.cos(p)
        z = self.model.get_z() + self.camera_distance * math.sin(p)

        self.camera.set_pos(x, y, z)
        self.camera.look_at(self.model)

    def mouse_rotate_task(self, task):
        if self.mouseWatcherNode.has_mouse():
            mouse_pos = self.mouseWatcherNode.get_mouse()

            if self.mouseWatcherNode.is_button_down(0):
                if self.prev_mouse_pos:
                    delta = mouse_pos - self.prev_mouse_pos

                    if self.alt_pressed:
                        h = self.camera.get_h() - delta.x * self.orbit_speed * globalClock.get_dt()
                        p = min(85, max(-85, self.camera.get_p() + delta.y * self.orbit_speed * globalClock.get_dt()))
                        self.camera.set_hpr(h, p, 0)
                        self.update_camera_position()
                    else:
                        self.model.set_h(self.model.get_h() - delta.x * self.rotate_speed * globalClock.get_dt())
                        self.model.set_p(
                            min(85, max(-85, self.model.get_p() + delta.y * self.rotate_speed * globalClock.get_dt())))

                self.prev_mouse_pos = mouse_pos
            else:
                self.prev_mouse_pos = None

        return task.cont

    def update_camera_position(self):
        h = math.radians(self.camera.get_h())
        p = math.radians(self.camera.get_p())

        x = self.cam_target.get_x() + self.camera_distance * math.sin(h) * math.cos(p)
        y = self.cam_target.get_y() - self.camera_distance * math.cos(h) * math.cos(p)
        z = self.cam_target.get_z() + self.camera_distance * math.sin(p)

        self.camera.set_pos(x, y, z)
        self.camera.look_at(self.cam_target)

    def update_scenario_display(self):
        if 0 <= self.current_scenario < len(self.scenarios):
            scenario = self.scenarios[self.current_scenario]
            self.scenario_label['text'] = f"{scenario['name']}"
            self.step_label['text'] = "Нажмите Старт для начала"

    def next_scenario(self):
        if self.current_scenario < len(self.scenarios) - 1:
            self.current_scenario += 1
            self.current_step = 0
            self.training_mode = False
            self.auto_mode = False
            self.update_scenario_display()

    def prev_scenario(self):
        if self.current_scenario > 0:
            self.current_scenario -= 1
            self.current_step = 0
            self.training_mode = False
            self.auto_mode = False
            self.update_scenario_display()

    def start_scenario(self):
        self.training_mode = True
        self.auto_mode = True
        self.current_step = 0
        self.execute_current_step()

    def execute_current_step(self):
        if not self.training_mode or not self.auto_mode:
            return

        scenario = self.scenarios[self.current_scenario]
        if self.current_step < len(scenario['steps']):
            step = scenario['steps'][self.current_step]
            self.step_label['text'] = step['message']

            if step['action'] == 'rotate_valve':
                valve_num = step['valve']
                direction = step['direction']

                if valve_num == 1:
                    self.valve1_spin_direction = direction
                    self.start_valve_spin(1)
                elif valve_num == 2:
                    self.valve2_spin_direction = direction
                    self.start_valve_spin(2)
                elif valve_num == 3:
                    self.valve3_spin_direction = direction
                    self.start_valve_spin(3)
                elif valve_num == 4:
                    self.valve4_spin_direction = direction
                    self.start_valve_spin(4)
                elif valve_num == 5:
                    self.start_valve_spin(5)
                elif valve_num == 6:
                    self.start_valve_spin(6)

    def on_step_completed(self):
        if not self.training_mode:
            return

        self.current_step += 1
        if self.current_step >= len(self.scenarios[self.current_scenario]['steps']):
            self.step_label['text'] = "Сценарий завершен!"
            self.training_mode = False
            self.auto_mode = False
        else:
            if self.auto_mode:
                self.execute_current_step()
            else:
                self.execute_current_step()

    def start_valve_spin(self, valve_num):
        if valve_num == 1:
            self.valve1_spinning = True
            self.taskMgr.add(self.spin_valve1_task, "SpinValve1Task")
            self.taskMgr.doMethodLater(1.5, lambda task: self.stop_valve_spin(task, 1), "StopValve1Task")
        elif valve_num == 2:
            self.valve2_spinning = True
            self.taskMgr.add(self.spin_valve2_task, "SpinValve2Task")
            self.taskMgr.doMethodLater(1.5, lambda task: self.stop_valve_spin(task, 2), "StopValve2Task")
        elif valve_num == 3:
            self.valve3_spinning = True
            self.taskMgr.add(self.spin_valve3_task, "SpinValve3Task")
            self.taskMgr.doMethodLater(1.5, lambda task: self.stop_valve_spin(task, 3), "StopValve3Task")
        elif valve_num == 4:
            self.valve4_spinning = True
            self.taskMgr.add(self.spin_valve4_task, "SpinValve4Task")
            self.taskMgr.doMethodLater(1.5, lambda task: self.stop_valve_spin(task, 4), "StopValve4Task")
        elif valve_num == 5 and not self.valve5_moving:
            self.valve5_moving = True
            self.taskMgr.add(self.move_valve5_task, "MoveValve5Task")
        elif valve_num == 6 and not self.valve6_moving:
            self.valve6_moving = True
            self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")

    def check_training_step(self, valve_num, direction):
        if not self.training_mode or self.auto_mode:
            return

        scenario = self.scenarios[self.current_scenario]
        if self.current_step < len(scenario['steps']):
            step = scenario['steps'][self.current_step]

            if (step['action'] == 'rotate_valve' and
                    step['valve'] == valve_num and
                    (step['direction'] == direction or valve_num in [5, 6])):

                self.step_label['text'] = "Правильно! " + step['message']
                self.on_step_completed()
            else:
                self.step_label['text'] = "Неверное действие! " + scenario['steps'][self.current_step]['message']


app = MyApp()
app.run()