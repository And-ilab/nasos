from direct.showbase.ShowBase import ShowBase
from panda3d.core import DirectionalLight, AmbientLight, Vec4, TextNode, FrameBufferProperties, WindowProperties, \
    GraphicsPipe, Vec3, Point3, Plane
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
from panda3d.core import CollisionTraverser, CollisionHandlerQueue, CollisionRay, BitMask32, TextNode
from direct.gui.OnscreenText import OnscreenText

class MyApp(ShowBase):
    def __init__(self):
        super().__init__()

        font = self.loader.load_font("arial.ttf")

        self.logical_parts = {
            "вентиль1": "**/COMPOUND_NEW",
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
                'name': "Подача воды от цистерны ",
                'steps': [
                    {'action': 'rotate_valve', 'valve': 1, 'direction': 1,
                     'message': "Выключите сцепление из насосного отсека"},
                    {'action': 'rotate_valve', 'valve': 1, 'direction': 1,
                     'message': "Откройте задвижку «На лафетный ствол»"},
                    {'action': 'rotate_valve', 'valve': 3, 'direction': 1,
                     'message': " Откройте задвижку «Из цистерны»"},
                    {'action': 'rotate_valve', 'valve': 5, 'direction': 1,
                     'message': "Через 5 секунд закройте задвижку «На лафетный ствол»"},
                    {'action': 'rotate_valve', 'valve': 1, 'direction': 1,
                     'message': "Включите сцепление"},

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

        self.preview_positions = {
            "COMPOUND3": {
                "pos": Point3(-1.4, -9.0, 0.35),
                "look": Point3(-0.4, 1.1, 0.1)
            },
            "COMPOUND2": {
                "pos": Point3(-1.8, -3.0, 0.568012),
                "look": Point3(-0.5, 1.0, 0.468012)
            },
            "Manometr_Arrow": {
                "pos": Point3(0.281166, -1.5, 0.568012),
                "look": Point3(0.281166 - 0.2, 0.26543, 0.468012)
            },
            "plane14": {
                "pos": Point3(-1.7, -9.0, 2.35),
                "look": Point3(-1.7, 1.1, 0.1)
            }
        }



        # Свет
        dlight = DirectionalLight("dlight")
        alight = AmbientLight("alight")
        dlight.set_color(Vec4(0.8, 0.8, 0.7, 1))
        alight.set_color(Vec4(0.2, 0.2, 0.2, 1))
        render.set_light(render.attach_new_node(dlight))
        render.set_light(render.attach_new_node(alight))




        # Загрузка модели
        self.model = self.loader.load_model("111.glb")
        self.model.reparent_to(self.render)
        self.model.set_scale(1)
        self.cam.look_at(self.model)

        print("Valve6 task added to taskMgr")
        self.ctrl_pressed = False
        self.accept('control', self.set_ctrl_pressed, [True])
        self.accept('control-up', self.set_ctrl_pressed, [False])

        valve6_geom = self.model.find("**/Manometr_Arrow")
        point = self.model.find("**/point8")
        valve5_geom = self.model.find("**/COMPOUND2")

        self.valve6_moving = False
        self.model.ls()



        point1 = self.model.find("**/point1")
        if point1.is_empty():

            print("❌ point1 не найден!")
        else:
            print(f"✅ point1 позиция: {point1.get_pos(render)}")


        if valve5_geom.is_empty():

            print("❌ Рычаг не найден!")
        else:
            print(f"✅ Рычаг позиция: {point1.get_pos(render)}")

            self.valve5_moving = False

        if point.is_empty():
            print("❌ вау не найден.")
            self.valve6 = None
            self.valve6_pivot = None
        else:
            print("✅ --- найден.")

        plane14 = self.model.find("**/plane14")
        if plane14.is_empty():
            print("❌ кнопка не найдена!")
        else:
            print("✅ кнопка найдена")
            self.plane14 = plane14

            # Получаем границы в локальных координатах модели
            min_b, max_b = self.plane14.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5
            extent *= 1000

            print(f"Границы plane14 (локальные): min={min_b}, max={max_b}")
            print(f"Центр: {center}, Размер: {extent}")

            # Увеличиваем размер коллизии (если нужно)
            extent *= 1.2  # Небольшой запас

            # Создаем коллизионный объект
            cnode = CollisionNode("plane14_col")
            cnode.add_solid(CollisionBox(center, extent.x, extent.y, extent.z))
            cnode.set_from_collide_mask(BitMask32.bit(1))
            cnode.set_into_collide_mask(BitMask32.bit(1))

            # Прикрепляем коллизию к модели
            self.plane14_col_np = self.plane14.attach_new_node(cnode)
            self.plane14_col_np.show()  # Для визуальной проверки

            # Проверяем итоговую трансформацию
            print(f"Позиция коллизии (мир): {self.plane14_col_np.get_pos(render)}")
            print(f"Масштаб коллизии: {self.plane14_col_np.get_scale()}")



        valve4_geom = self.model.find("**/COMPOUND3")
        if valve4_geom.is_empty():
            print("❌ Рычаг не найден!")
        else:
            print("✅ Рычаг найден")

            # Находим точку крепления (point8)
            pivot_node = self.model.find("**/point9")
            #pivot_node = self.model.find("**/pCube")
            if pivot_node.is_empty():
                print("❌ Точка крепления не найдена!")
                return

            # Сохраняем оригинальную трансформацию
            original_mat = valve4_geom.get_mat(self.model)  # Получаем матрицу относительно модели
            pivot_pos = pivot_node.get_pos(self.model)
            valve4_pos = valve4_geom.get_pos(self.model)

            # 1. Создаем новую иерархию узлов
            self.valve4_root = self.model.attach_new_node("valve4_root")
            #self.valve4_root.set_mat(pivot_node.get_mat(self.model))
            self.valve4_root.set_pos(pivot_pos)  # Помещаем корень в точку крепления

            self.valve4_pivot = self.valve4_root.attach_new_node("valve4_pivot")

            # 2. Переносим геометрию
            valve4_geom.reparent_to(self.valve4_pivot)
            self.valve4 = valve4_geom
            #valve4_geom.set_pos(valve4_geom.get_pos(self.valve4_pivot))
            valve4_geom.set_mat(original_mat)  # Восстанавливаем оригинальную трансформацию

            # 3. Компенсируем смещение (относительно точки крепления)
            relative_pos = valve4_pos - pivot_pos
            valve4_geom.set_pos(relative_pos)

            saved_pos = valve4_geom.get_pos()
            valve4_geom.set_pos(0, 0, 0)
            # 4. Настройка коллизии (после всех перемещений)
            min_b, max_b = valve4_geom.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5

            extent *= 20

            cnode = CollisionNode("valve4_col")
            cnode.add_solid(CollisionBox(center, extent.x, extent.y, extent.z))
            cnode.set_from_collide_mask(BitMask32.bit(1))
            cnode.set_into_collide_mask(BitMask32.bit(1))

            self.valve4_col_np = valve4_geom.attach_new_node(cnode)
            self.valve4_col_np.show()

            # ВОЗВРАЩАЕМ позицию
            valve4_geom.set_pos(saved_pos)

            # Настройки вращения
            self.valve4_pivot.set_r(0)
            self.valve4_target_angle = 85
            self.valve4_moving = False
            self.valve4_direction = 1

            # Отладочная информация
            print(f"Позиция корня: {self.valve4_root.get_pos(render)}")
            print(f"Позиция pivot: {self.valve4_pivot.get_pos(render)}")
            print(f"Позиция геометрии: {valve4_geom.get_pos(render)}")
            print(f"Границы коллизии: {min_b} - {max_b}")

        valve5_geom = self.model.find("**/COMPOUND2")
        if valve5_geom.is_empty():
            print("❌ Рычаг не найден!")
        else:
            print("✅ Рычаг найден")

            # Находим точку крепления (point8)
            pivot_node = self.model.find("**/point8")
            if pivot_node.is_empty():
                print("❌ Точка крепления не найдена!")
                return

            # Сохраняем оригинальную трансформацию
            original_mat = valve5_geom.get_mat(self.model)  # Получаем матрицу относительно модели
            pivot_pos = pivot_node.get_pos(self.model)
            valve5_pos = valve5_geom.get_pos(self.model)

            # 1. Создаем новую иерархию узлов
            self.valve5_root = self.model.attach_new_node("valve5_root")
            self.valve5_root.set_pos(pivot_pos)  # Помещаем корень в точку крепления

            self.valve5_pivot = self.valve5_root.attach_new_node("valve5_pivot")

            # 2. Переносим геометрию
            valve5_geom.reparent_to(self.valve5_pivot)
            self.valve5 = valve5_geom
            valve5_geom.set_mat(original_mat)  # Восстанавливаем оригинальную трансформацию

            # 3. Компенсируем смещение (относительно точки крепления)
            relative_pos = valve5_pos - pivot_pos
            valve5_geom.set_pos(relative_pos)


            saved_pos = valve5_geom.get_pos()
            valve5_geom.set_pos(0, 0, 0)
            # 4. Настройка коллизии (после всех перемещений)
            min_b, max_b = valve5_geom.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5

            extent *= 20

            cnode = CollisionNode("valve5_col")
            cnode.add_solid(CollisionBox(center, extent.x, extent.y, extent.z))
            cnode.set_from_collide_mask(BitMask32.bit(1))
            cnode.set_into_collide_mask(BitMask32.bit(1))

            self.valve5_col_np = valve5_geom.attach_new_node(cnode)
            self.valve5_col_np.show()

            # ВОЗВРАЩАЕМ позицию
            valve5_geom.set_pos(saved_pos)

            # Настройки вращения
            self.valve5_pivot.set_p(0)
            self.valve5_target_angle = 85
            self.valve5_moving = False
            self.valve5_direction = 1

            # Отладочная информация
            print(f"Позиция корня: {self.valve5_root.get_pos(render)}")
            print(f"Позиция pivot: {self.valve5_pivot.get_pos(render)}")
            print(f"Позиция геометрии: {valve5_geom.get_pos(render)}")
            print(f"Границы коллизии: {min_b} - {max_b}")

        self.coord_display = OnscreenText(text="", pos=(-1.3, 0.9), fg=(1, 1, 0, 1), scale=0.05, align=TextNode.ALeft)

        self.coord_traverser = CollisionTraverser()
        self.coord_queue = CollisionHandlerQueue()

        self.coord_ray = CollisionRay()
        self.coord_picker_node = CollisionNode('coord_ray')
        self.coord_picker_node.set_from_collide_mask(BitMask32.bit(1))  # только по bit(1)
        self.coord_picker_node.set_into_collide_mask(BitMask32.all_off())
        self.coord_picker_np = camera.attach_new_node(self.coord_picker_node)
        self.coord_picker_node.add_solid(self.coord_ray)

        self.coord_traverser.add_collider(self.coord_picker_np, self.coord_queue)



        if valve6_geom.is_empty():
            print("❌ Manometr_Arrow не найден.")
            self.valve6 = None
            self.valve6_pivot = None

        else:
            print("✅ Manometr_Arrow найден.")

            # 1. Найдём точку вращения стрелки
            pivot_node = self.model.find("**/point1")
            if pivot_node.is_empty():
                print("❌ Точка point1 не найдена.")
                return

            # 2. Мировые позиции
            pivot_world = pivot_node.get_pos(render)
            valve6_world = valve6_geom.get_pos(render)

            # 3. Создаём иерархию узлов
            self.valve6_root = self.model.attach_new_node("valve6_root")
            self.valve6_root.set_pos(render, pivot_world)

            self.valve6_pivot = self.valve6_root.attach_new_node("valve6_pivot")

            # 4. Сохраняем текущую позицию и переносим геометрию
            valve6_geom.wrt_reparent_to(self.valve6_pivot)
            self.valve6 = valve6_geom
            relative_pos = valve6_world - pivot_world
            valve6_geom.set_pos(relative_pos)

            # 🎯 Самое важное: получить правильные границы
            # ВРЕМЕННО добавим узел для расчёта коллизии
            tmp_node = self.valve6_pivot.attach_new_node("tmp_for_bounds")
            valve6_geom.instance_to(tmp_node)

            tmp_node.set_pos(0, 0, 0)
            tmp_node.flatten_light()  # обязательно, чтобы границы считались как у оригинала

            min_b, max_b = tmp_node.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5
            tmp_node.remove_node()
            extent *= 1000

            # 5. Добавим коллизию к valve6_geom
            col_node = CollisionNode("valve6_col")
            col_node.add_solid(CollisionBox(center, extent.x, extent.y, extent.z))
            col_node.set_into_collide_mask(BitMask32.bit(1))
            col_node.set_from_collide_mask(BitMask32.bit(1))

            self.valve6_col_np = valve6_geom.attach_new_node(col_node)
            self.valve6_col_np.set_color(1, 0, 0, 1)
            self.valve6_col_np.set_render_mode_wireframe()
            self.valve6_col_np.show()

            # 6. Начальное состояние
            self.valve6_angle = 0
            self.valve6_target_angle = 0
            self.valve6_moving = False

            print("🧩 Добавляю задачу MoveValve6Task")
            self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")

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

        #self.model.set_pos(1.2, 6, -0.3)
        self.model.set_hpr(270, 90, 0)
        self.camera.set_pos(0, -10, 3)  # Отодвинули основную камеру
        self.camera.look_at(self.model)
        self.model.set_scale(2)

        # Управление мышью
        self.prev_mouse_pos = None
        self.rotation_speed = 180

        self.accept('mouse1', self.on_mouse_down)
        self.accept('mouse1-up', self.on_mouse_up)
        self.accept('wheel_up', self.on_zoom_in)
        self.accept('wheel_down', self.on_zoom_out)
        self.accept("control-wheel_up", self.on_preview_zoom_in)
        self.accept("control-wheel_down", self.on_preview_zoom_out)

        # Настройки превью-камеры
        self.preview_cam_distance = 1.5  # Ближе к объекту
        self.preview_cam_min_distance = 0.5
        self.preview_cam_max_distance = 3.0
        self.preview_cam_zoom_speed = 1.0

        self.preview_buffer = None
        self.preview_card = None

        # Задачи
        self.taskMgr.add(self.mouse_rotate_task, "MouseRotateTask")

        # GUI элементы
        self.setup_gui(font)


    def setup_gui(self, font):
        # Нижняя панель с названием сценария
        self.bottom_panel = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.7),
            frameSize=(-1.5, 1.5, -0.15, 0.15),
            pos=(0, 0, -0.85),
        )
        self.left_panel = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.7),
            frameSize=(-0.8, 0.8, -0.65, 0.65),
            pos=(-1.75,0, 0.35),
        )

        self.scenario_label = DirectLabel(
            parent=self.bottom_panel,
            text="Подача воды от цистерны ",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            scale=0.06,
            pos=(0, 0, 1.75))

        self.step_label = DirectLabel(
            parent=self.bottom_panel,
            text="",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            scale=0.05,
            pos=(0, 0, -0.07))

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
            pos=(-1.4, 0, 0),
            relief=1,
            command=self.prev_scenario)

        self.next_btn = DirectButton(
            parent=self.bottom_panel,
            text=">",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.2, 0.7),
            scale=0.05,
            pos=(1.4, 0, 0),
            relief=1,
            command=self.next_scenario)

        self.start_btn = DirectButton(
            parent=self.aspect2d,
            text="Старт",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.5, 0.2, 0.7),
            scale=0.05,
            pos=(0, 0, -0.75),
            relief=1,
            command=self.start_scenario)


    def create_preview_camera(self, object_name):
        if self.preview_buffer:
            self.destroy_preview_camera()

        # Буфер предпросмотра
        win_props = WindowProperties.size(500, 500)
        fb_props = FrameBufferProperties()
        fb_props.set_rgba_bits(8, 8, 8, 8)
        fb_props.set_depth_bits(24)

        self.preview_buffer = self.graphicsEngine.make_output(
            self.pipe, "PreviewBuffer", -2,
            fb_props, win_props,
            GraphicsPipe.BF_refuse_window,
            self.win.get_gsg(), self.win)

        self.preview_texture = Texture()
        self.preview_buffer.add_render_texture(self.preview_texture, GraphicsOutput.RTMCopyRam)

        # Линза предпросмотра
        lens = OrthographicLens()
        lens.set_film_size(0.4, 0.4)

        preview_cam = self.make_camera(self.preview_buffer, lens=lens)
        self.preview_cam_np = NodePath(preview_cam)
        self.preview_cam_np.reparent_to(render)

        # 📍 Используем координаты из словаря
        pos_data = self.preview_positions.get(object_name)
        print(object_name)
        if pos_data:
            self.preview_cam_np.set_pos(pos_data["pos"])
            self.preview_cam_np.look_at(pos_data["look"])
        else:
            print(f"⚠️ Нет позиции предпросмотра для: {object_name}")

        # Отображение карточки
        cm = CardMaker("preview_card")
        cm.set_frame(-0.6, 0.6, -0.6, 0.6)
        self.preview_card = self.aspect2d.attach_new_node(cm.generate())
        self.preview_card.set_texture(self.preview_texture)
        self.preview_card.set_pos(-1.4, 0, 0.7)
        self.preview_card.set_scale(0.7)

        self.accept('wheel_up', self.on_preview_zoom_in, extraArgs=[object_name])
        self.accept('wheel_down', self.on_preview_zoom_out, extraArgs=[object_name])





    def update_preview_camera_position(self, target_node):
        """Обновляет позицию превью-камеры с текущим расстоянием"""
        if not self.preview_cam_np:
            return

        # Позиция камеры - ближе к объекту и немного сверху
        self.preview_cam_np.set_pos(target_node.get_pos(render) + Vec3(0, -self.preview_cam_distance, 0.3))
        self.preview_cam_np.look_at(target_node)

    def on_preview_zoom_in(self, target_node):
        """Приближение превью-камеры"""
        if self.preview_buffer:
            self.preview_cam_distance = max(
                self.preview_cam_min_distance,
                self.preview_cam_distance - self.preview_cam_zoom_speed * globalClock.get_dt()
            )
            self.update_preview_camera_position(target_node)

    def on_preview_zoom_out(self, target_node):
        """Отдаление превью-камеры"""
        if self.preview_buffer:
            self.preview_cam_distance = min(
                self.preview_cam_max_distance,
                self.preview_cam_distance + self.preview_cam_zoom_speed * globalClock.get_dt()
            )
            self.update_preview_camera_position(target_node)

    def destroy_preview_camera(self):
        if self.preview_buffer:
            self.preview_buffer.remove_all_display_regions()
            self.graphics_engine.remove_window(self.preview_buffer)
            self.preview_buffer = None

        if self.preview_card:
            self.preview_card.remove_node()
            self.preview_card = None

        # Восстанавливаем стандартные обработчики колесика
        self.accept('wheel_up', self.on_zoom_in)
        self.accept('wheel_down', self.on_zoom_out)

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

    def reset_plane14_color(self, task):
        self.plane14.clear_color_scale()
        return task.done

    def on_mouse_down(self):
        if self.mouseWatcherNode.has_mouse() and not self.ctrl_pressed:
            mpos = self.mouseWatcherNode.get_mouse()
            self.picker_ray.set_from_lens(self.camNode, mpos.get_x(), mpos.get_y())
            self.picker.traverse(self.render)

            if self.pq.get_num_entries() > 0:
                self.pq.sort_entries()
                picked_entry = self.pq.get_entry(0)
                picked_np = picked_entry.get_into_node_path()

                if picked_np.get_name() == "valve6_col" and not self.valve6_moving:
                    # Обработка стрелки манометра
                    self.valve6_target_angle = (self.valve6_angle - 30) % 360
                    self.valve6_moving = True
                    self.create_preview_camera(self.valve6.name)

                elif picked_np.get_name() == "valve5_col" and not self.valve5_moving:
                    # Определяем направление движения (вперед/назад)
                    current_angle = self.valve5_pivot.get_p()
                    if abs(current_angle) < 0.1:  # Если рычаг в начальном положении
                        self.valve5_direction = 1
                    else:
                        self.valve5_direction = -1

                    self.valve5_moving = True
                    self.create_preview_camera(self.valve5.name)
                    self.taskMgr.add(self.move_valve5_task, "MoveValve5Task")

                elif picked_np.get_name() == "valve4_col" and not self.valve4_moving:
                    # Определяем направление движения (вперед/назад)
                    current_angle = self.valve4_pivot.get_r()
                    if abs(current_angle) < 0.1:  # Если рычаг в начальном положении
                        self.valve4_direction = 1
                    else:
                        self.valve4_direction = -1

                    self.valve4_moving = True
                    self.create_preview_camera(self.valve4.name)
                    print(self.valve4.name)
                    self.taskMgr.add(self.move_valve4_task, "MoveValve4Task")

                elif picked_np.get_name() == "plane14_col":
                    print("📌 Нажата кнопка plane14")
                    self.create_preview_camera(self.plane14.name)  # Показать в предпросмотре

                    # Визуальная подсветка (временно меняем цвет)
                    self.plane14.set_color_scale(1, 1, 0.5, 1)  # жёлтоватая подсветка
                    self.taskMgr.do_method_later(0.3, self.reset_plane14_color, "ResetColor")

    def move_valve4_task(self, task):
        if not hasattr(self, 'valve4_pivot') or not self.valve4_moving:
            return task.done

        speed = 90  # градусов в секунду
        current_angle = self.valve4_pivot.get_r()

        # Определяем целевой угол в зависимости от направления
        if self.valve4_direction > 0:
            target_angle = self.valve4_target_angle
        else:
            target_angle = 0

        # Плавное вращение
        if abs(current_angle - target_angle) > 0.1:
            delta = speed * globalClock.get_dt() * self.valve4_direction
            new_angle = current_angle + delta

            # Ограничиваем угол, чтобы не выйти за пределы
            if self.valve4_direction > 0:
                new_angle = min(new_angle, target_angle)
            else:
                new_angle = max(new_angle, target_angle)

            self.valve4_pivot.set_r(new_angle)
            return task.cont
        else:
            self.valve4_pivot.set_r(target_angle)
            self.valve4_moving = False

            # Если в тренировочном режиме, переходим к следующему шагу
            if self.training_mode:
                self.on_step_completed()

            return task.done

    def move_valve5_task(self, task):
        if not hasattr(self, 'valve5_pivot') or not self.valve5_moving:
            return task.done

        speed = 90  # градусов в секунду
        current_angle = self.valve5_pivot.get_p()

        # Определяем целевой угол в зависимости от направления
        if self.valve5_direction > 0:
            target_angle = self.valve5_target_angle
        else:
            target_angle = 0

        # Плавное вращение
        if abs(current_angle - target_angle) > 0.1:
            delta = speed * globalClock.get_dt() * self.valve5_direction
            new_angle = current_angle + delta

            # Ограничиваем угол, чтобы не выйти за пределы
            if self.valve5_direction > 0:
                new_angle = min(new_angle, target_angle)
            else:
                new_angle = max(new_angle, target_angle)

            self.valve5_pivot.set_p(new_angle)
            return task.cont
        else:
            self.valve5_pivot.set_p(target_angle)
            self.valve5_moving = False

            # Если в тренировочном режиме, переходим к следующему шагу
            if self.training_mode:
                self.on_step_completed()

            return task.done


    def move_valve6_task(self, task):
        if not hasattr(self, 'valve6_pivot') or not hasattr(self, 'valve6'):
            return task.cont

        if self.valve6_moving:  # Было valVe6
            speed = 180  # градусов в секунду
            delta = speed * globalClock.get_dt()

            current = self.valve6_angle
            target = self.valve6_target_angle

            if abs(current - target) > 0.1:
                # Плавное вращение к целевой позиции
                if current < target:
                    current = min(current + delta, target)
                else:
                    current = max(current - delta, target)

                self.valve6_angle = current
                # Изменено на set_h() для вращения как в часах
                self.valve6_pivot.set_p(current)  # Вращение вокруг вертикальной оси Y
            else:
                self.valve6_moving = False
                self.valve6_angle = target

        return task.cont


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

                if valve_num == 6:
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
        if valve_num == 6 and not self.valve6_moving:
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