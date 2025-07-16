from direct.gui import DirectGui
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


        self.load_sounds()

        # Запуск фоновой музыки
        self.start_background_music()


        self.valve2_start_time = 0
        self.valve4_start_time = 0
        self.valve5_start_time = 0
        self.valve6_start_time = 0

        self._scenario_running = False  # Флаг выполнения сценария
        self._current_task = None


        self.scenarios = [
            {
                'name': "Подача воды от цистерны",
                'type': 'method',
                'method': 'first_scenario'
            },
            {
                'name': "Забор воды от открытого водоисточника",
                'type': 'method',
                'method': 'second_scenario'
            },
            {
                'name': "Забор воды от гидранта",
                'type': 'method',
                'method': 'third_scenario'
            },
            {
                'name': "Подача воды из цистерны через стационарный лафетный ствол",
                'type': 'method',
                'method': 'fourth_scenario'
            },
        ]

        offset = Vec3(1.1, 6, -0.3)

        self.preview_positions = {
            "Задвижка «Из цистерны»": {
                "pos": Point3(-1.4, -9.0, 0.35),
                "look": Point3(-0.4, 1.1, 0.1)
            },
            "Задвижка на Лафетный ствол": {
                "pos": Point3(-1.8, -3.0, 0.568012),
                "look": Point3(-0.5, 1.0, 0.468012)
            },
            "Манометр": {
                "pos": Point3(0.281166, -1.5, 0.568012),
                "look": Point3(0.281166 - 0.2, 0.26543, 0.468012)
            },
            "Панель": {
                "pos": Point3(-1.7, -9.0, 2.35),
                "look": Point3(-1.7, 1.1, 0.1)
            },
            "Левая напорная задвижка": {
                "pos": Point3(-1.7, -5.0, 0.8),
                "look": Point3(-1.7, 1.1, 0.1)
            },
            "Manometr_Arrow": {
                "pos": Point3(0.281166, -1.5, 0.568012),
                "look": Point3(0.281166 - 0.2, 0.26543, 0.468012)
            },
            "Задвижка «В цистерну»": {
                "pos": Point3(0.281166 - 0.2, -1.5 - 0.6, 0.568012 - 0.2),
                "look": Point3(0.281166 - 0.5, 0.26543-0.1, 0.468012 - 0.2)
            },
            "Задвижка «Вакуумный кран»": {
                "pos": Point3(0.281166 - 0.2, -1.5 - 0.6, 0.568012 - 0.2),
                "look": Point3(0.281166 - 0.5, 0.26543 - 0.1, 0.468012 - 0.2)
            },

        }

        for key in self.preview_positions:
            self.preview_positions[key]["pos"] += offset
            self.preview_positions[key]["look"] += offset

        # Свет
        dlight = DirectionalLight("dlight")
        alight = AmbientLight("alight")
        dlight.set_color(Vec4(0.8, 0.8, 0.7, 1))
        alight.set_color(Vec4(0.2, 0.2, 0.2, 1))
        render.set_light(render.attach_new_node(dlight))
        render.set_light(render.attach_new_node(alight))

        # Загрузка модели
        self.model = self.loader.load_model("1111.glb")
        self.model.reparent_to(self.render)
        self.model.set_scale(1)
        self.cam.look_at(self.model)


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
            self.plane14.name = "Панель"

            min_b, max_b = self.plane14.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5
            extent *= 1000

            print(f"Границы plane14 (локальные): min={min_b}, max={max_b}")
            print(f"Центр: {center}, Размер: {extent}")

            extent *= 1.2

            cnode = CollisionNode("plane14_col")
            cnode.add_solid(CollisionBox(center, extent.x, extent.y, extent.z))
            cnode.set_from_collide_mask(BitMask32.bit(1))
            cnode.set_into_collide_mask(BitMask32.bit(1))

            self.plane14_col_np = self.plane14.attach_new_node(cnode)
            self.plane14_col_np.show()

            print(f"Позиция коллизии (мир): {self.plane14_col_np.get_pos(render)}")
            print(f"Масштаб коллизии: {self.plane14_col_np.get_scale()}")

        plane11 = self.model.find("**/plane11")
        if plane11.is_empty():
            print("❌ кнопка не найдена!")
        else:
            print("✅ кнопка найдена")
            self.plane11 = plane11
            self.plane11.name = "Панель"

            min_b, max_b = self.plane11.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5
            extent *= 1000

            print(f"Границы plane11 (локальные): min={min_b}, max={max_b}")
            print(f"Центр: {center}, Размер: {extent}")

            extent *= 1.2

            cnode = CollisionNode("plane11_col")
            cnode.add_solid(CollisionBox(center, extent.x, extent.y, extent.z))
            cnode.set_from_collide_mask(BitMask32.bit(1))
            cnode.set_into_collide_mask(BitMask32.bit(1))

            self.plane11_col_np = self.plane11.attach_new_node(cnode)
            self.plane11_col_np.show()

            print(f"Позиция коллизии (мир): {self.plane11_col_np.get_pos(render)}")
            print(f"Масштаб коллизии: {self.plane11_col_np.get_scale()}")


        valve2_geom = self.model.find("**/COMPOUND1")
        point5 = self.model.find("**/point5")

        if valve2_geom.is_empty() or point5.is_empty():
            print("❌ Вентиль 2 или точка вращения не найдены!")
        else:
            print("✅ Вентиль 2 и точка вращения найдены")

            # Сохраняем оригинальную трансформацию
            original_mat = valve2_geom.get_mat(self.model)
            pivot_pos = point5.get_pos(self.model)
            valve2_pos = valve2_geom.get_pos(self.model)

            # Создаем иерархию для вращения
            self.valve2_root = self.model.attach_new_node("valve2_root")
            self.valve2_root.set_pos(pivot_pos)


            self.valve2_pivot = self.valve2_root.attach_new_node("valve2_pivot")

            # Переносим геометрию с сохранением трансформации
            valve2_geom.wrt_reparent_to(self.valve2_pivot)
            self.valve2 = valve2_geom
            valve2_geom.set_mat(original_mat)

            # Устанавливаем относительную позицию
            relative_pos = valve2_pos - pivot_pos
            valve2_geom.set_pos(relative_pos)

            # Настройка коллизии
            saved_pos = valve2_geom.get_pos()
            valve2_geom.set_pos(0, 0, 0)

            min_b, max_b = valve2_geom.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5
            extent *= 200

            cnode = CollisionNode("valve2_col")
            cnode.add_solid(CollisionBox(center, extent.x, extent.y, extent.z))
            cnode.set_from_collide_mask(BitMask32.bit(1))
            cnode.set_into_collide_mask(BitMask32.bit(1))

            self.valve2_col_np = valve2_geom.attach_new_node(cnode)
            self.valve2_col_np.show()

            valve2_geom.set_pos(saved_pos)
            self.valve2.name = 'Левая напорная задвижка'
            # Настройки вращения (как у valve13)
            self.valve2_pivot.set_p(0)  # Сброс начального угла
            self.valve2_target_angle = 90
            self.valve2_moving = False
            self.valve2_direction = 1

        valve4_geom = self.model.find("**/COMPOUND3")
        if valve4_geom.is_empty():
            print("❌ Рычаг не найден!")
        else:
            print("✅ Рычаг найден")

            pivot_node = self.model.find("**/point9")
            if pivot_node.is_empty():
                print("❌ Точка крепления не найдена!")
                return

            original_mat = valve4_geom.get_mat(self.model)
            pivot_pos = pivot_node.get_pos(self.model)
            valve4_pos = valve4_geom.get_pos(self.model)


            self.valve4_root = self.model.attach_new_node("valve4_root")
            self.valve4_root.set_pos(pivot_pos)

            self.valve4_pivot = self.valve4_root.attach_new_node("valve4_pivot")

            valve4_geom.reparent_to(self.valve4_pivot)
            self.valve4 = valve4_geom
            valve4_geom.set_mat(original_mat)

            relative_pos = valve4_pos - pivot_pos
            valve4_geom.set_pos(relative_pos)

            saved_pos = valve4_geom.get_pos()
            valve4_geom.set_pos(0, 0, 0)

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

            valve4_geom.set_pos(saved_pos)

            self.valve4_pivot.set_r(0)
            self.valve4_target_angle = 85
            self.valve4_moving = False
            self.valve4_direction = 1
            self.valve4.name = "Задвижка «Из цистерны»"
            print(f"Позиция корня: {self.valve4_root.get_pos(render)}")
            print(f"Позиция pivot: {self.valve4_pivot.get_pos(render)}")
            print(f"Позиция геометрии: {valve4_geom.get_pos(render)}")
            print(f"Границы коллизии: {min_b} - {max_b}")

        valve13_geom = self.model.find("**/COMPOUND5")
        point13 = self.model.find("**/point3")
        if point13.is_empty():
            print("❌ point11 не найден!")
        else:
            print(f"✅ point11 позиция: {point13.get_pos(render)}")

        if valve13_geom.is_empty():
            print("❌ Рычаг1 не найден!")
        else:
            print(f"✅ Рычаг 1позиция: {point13.get_pos(render)}")
            self.valve13_moving = False

        if valve13_geom.is_empty():
            print("❌ Рычаг не найден!")
        else:
            print("✅ Рыча~~г найден")

            original_mat = valve13_geom.get_mat(self.model)
            pivot_pos = point13.get_pos(self.model)
            valve13_pos = valve13_geom.get_pos(self.model)


            self.valve13_root = self.model.attach_new_node("valve13_root")
            self.valve13_root.set_pos(pivot_pos)

            self.valve13_pivot = self.valve13_root.attach_new_node("valve13_pivot")

            valve13_geom.reparent_to(self.valve13_pivot)
            self.valve13 = valve13_geom
            valve13_geom.set_mat(original_mat)

            relative_pos = valve13_pos - pivot_pos
            valve13_geom.set_pos(relative_pos)

            saved_pos = valve13_geom.get_pos()
            valve13_geom.set_pos(0, 0, 0)

            min_b, max_b = valve13_geom.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5
            extent *= 200

            cnode = CollisionNode("valve13_col")
            cnode.add_solid(CollisionBox(center, extent.x, extent.y, extent.z))
            cnode.set_from_collide_mask(BitMask32.bit(1))
            cnode.set_into_collide_mask(BitMask32.bit(1))

            self.valve13_col_np = valve13_geom.attach_new_node(cnode)
            self.valve13_col_np.show()

            valve13_geom.set_pos(saved_pos)

            self.valve13_pivot.set_p(0)
            self.valve13_target_angle = 90
            self.valve13_moving = False
            self.valve13_direction = 1
            self.valve13.name = "Задвижка «В цистерну»"



        valve8_geom = self.model.find("**/ COMPOUND8")
        point8 = self.model.find("**/point9.001")
        if valve8_geom.is_empty():
            print("❌ 8Рычаг не найден!")
        else:
            print("✅ 8Рычаг найден")

            pivot_node = self.model.find("**/point9.001")
            if pivot_node.is_empty():
                print("❌ 8Точка крепления не найдена!")
                return

            original_mat = valve8_geom.get_mat(self.model)
            pivot_pos = pivot_node.get_pos(self.model)
            valve8_pos = valve8_geom.get_pos(self.model)

            self.valve8_root = self.model.attach_new_node("valve8_root")
            self.valve8_root.set_pos(pivot_pos)

            self.valve8_pivot = self.valve8_root.attach_new_node("valve8_pivot")

            valve8_geom.reparent_to(self.valve8_pivot)
            self.valve8 = valve8_geom
            valve8_geom.set_mat(original_mat)

            relative_pos = valve8_pos - pivot_pos
            valve8_geom.set_pos(relative_pos)

            saved_pos = valve8_geom.get_pos()
            valve8_geom.set_pos(0, 0, 0)

            min_b, max_b = valve8_geom.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5
            extent *= 20

            cnode = CollisionNode("valve8_col")
            cnode.add_solid(CollisionBox(center, extent.x, extent.y, extent.z))
            cnode.set_from_collide_mask(BitMask32.bit(1))
            cnode.set_into_collide_mask(BitMask32.bit(1))

            self.valve8_col_np = valve8_geom.attach_new_node(cnode)
            self.valve8_col_np.show()

            valve8_geom.set_pos(saved_pos)
            self.valve8.name = "Вакуумный кран"
            self.valve8_pivot.set_p(0)
            self.valve8_target_angle = 85
            self.valve8_moving = False
            self.valve8_direction = 1



        valve5_geom = self.model.find("**/COMPOUND2")
        if valve5_geom.is_empty():
            print("❌ Рычаг не найден!")
        else:
            print("✅ Рычаг найден")

            pivot_node = self.model.find("**/point8")
            if pivot_node.is_empty():
                print("❌ Точка крепления не найдена!")
                return

            original_mat = valve5_geom.get_mat(self.model)
            pivot_pos = pivot_node.get_pos(self.model)
            valve5_pos = valve5_geom.get_pos(self.model)


            self.valve5_root = self.model.attach_new_node("valve5_root")
            self.valve5_root.set_pos(pivot_pos)

            self.valve5_pivot = self.valve5_root.attach_new_node("valve5_pivot")

            valve5_geom.reparent_to(self.valve5_pivot)
            self.valve5 = valve5_geom
            valve5_geom.set_mat(original_mat)

            relative_pos = valve5_pos - pivot_pos
            valve5_geom.set_pos(relative_pos)

            saved_pos = valve5_geom.get_pos()
            valve5_geom.set_pos(0, 0, 0)

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

            valve5_geom.set_pos(saved_pos)
            self.valve5.name = "Задвижка на Лафетный ствол"
            self.valve5_pivot.set_p(0)
            self.valve5_target_angle = 85
            self.valve5_moving = False
            self.valve5_direction = 1


        self.coord_display = OnscreenText(text="", pos=(-1.3, 0.9), fg=(1, 1, 0, 1), scale=0.05, align=TextNode.ALeft)
        self.coord_traverser = CollisionTraverser()
        self.coord_queue = CollisionHandlerQueue()
        self.coord_ray = CollisionRay()
        self.coord_picker_node = CollisionNode('coord_ray')
        self.coord_picker_node.set_from_collide_mask(BitMask32.bit(1))
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

            pivot_node = self.model.find("**/point1")
            if pivot_node.is_empty():
                print("❌ Точка point1 не найдена.")
                return

            pivot_world = pivot_node.get_pos(render)
            valve6_world = valve6_geom.get_pos(render)

            self.valve6_root = self.model.attach_new_node("valve6_root")
            self.valve6_root.set_pos(render, pivot_world)

            self.valve6_pivot = self.valve6_root.attach_new_node("valve6_pivot")

            valve6_geom.wrt_reparent_to(self.valve6_pivot)
            self.valve6 = valve6_geom
            relative_pos = valve6_world - pivot_world
            valve6_geom.set_pos(relative_pos)
            self.valve6_pivot.set_p(41.3)  # H (heading) — ось Z

            tmp_node = self.valve6_pivot.attach_new_node("tmp_for_bounds")
            valve6_geom.instance_to(tmp_node)

            tmp_node.set_pos(0, 0, 0)
            tmp_node.flatten_light()

            min_b, max_b = tmp_node.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5
            tmp_node.remove_node()
            extent *= 1000

            col_node = CollisionNode("valve6_col")
            col_node.add_solid(CollisionBox(center, extent.x, extent.y, extent.z))
            col_node.set_into_collide_mask(BitMask32.bit(1))
            col_node.set_from_collide_mask(BitMask32.bit(1))

            self.valve6_col_np = valve6_geom.attach_new_node(col_node)
            self.valve6_col_np.set_color(1, 0, 0, 1)
            self.valve6_col_np.set_render_mode_wireframe()
            self.valve6_col_np.show()

            self.valve6_angle = 0
            self.valve6_start_angle = 0
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

        self.model.set_pos(1.1, 6, -0.3)
        self.model.set_hpr(270, 90, 0)
        self.camera.set_pos(0, -10, 3)
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
        self.preview_cam_distance = 1.5
        self.preview_cam_min_distance = 0.5
        self.preview_cam_max_distance = 3.0
        self.preview_cam_zoom_speed = 1.0

        self.preview_buffer = None
        self.preview_card = None

        # Задачи
        self.taskMgr.add(self.mouse_rotate_task, "MouseRotateTask")

        # GUI элементы
        self.setup_gui(font)

    def load_sounds(self):
        """Загрузка всех звуковых ресурсов"""
        # Фоновая музыка
        self.bg_sound = loader.loadSfx("media/audio1.mp3")
        self.sound_one = loader.loadSfx("media/audio2.mp3")
        self.sound_two = loader.loadSfx("media/audio3.mp3")
        self.bg_sound.setLoop(True)
        self.bg_sound.setVolume(0.5)
        self.bg_music_playing = False

        # Звук вентиля
        self.valve_sound = loader.loadSfx("media/valve_sound.wav")
        self.is_valve_sound_playing = False


    def start_first_music(self):
        """Запуск фоновой музыки"""
        if not self.bg_music_playing:
            self.sound_one.play()

    def start_second_music(self):
        """Запуск фоновой музыки"""
        if not self.bg_music_playing:
            self.sound_two.play()


    def start_background_music(self):
        """Запуск фоновой музыки"""
        if not self.bg_music_playing:
            self.bg_sound.play()
            self.bg_music_playing = True

    def stop_background_music(self):
        """Остановка фоновой музыки"""
        if self.bg_music_playing:
            self.bg_sound.stop()
            self.bg_music_playing = False

    def toggle_background_music(self):
        """Переключение фоновой музыки"""
        if self.bg_music_playing:
            self.stop_background_music()
        else:
            self.start_background_music()

    def create_menu_panel(self):
        # Создаем панель меню (изначально скрытую)
        self.menu_panel = DirectFrame(
            parent=self.aspect2d,
            frameColor=(0.1, 0.1, 0.15, 0.95),
            frameSize=(-5, 5, -3, 3),
            pos=(0, 0, 0),
            state=DirectGui.DGG.NORMAL
        )



    def setup_gui(self, font):
        self.bottom_panel = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.9),  # Более непрозрачная
            frameSize=(-1.5, 1.5, -0.15, 0.15),
            pos=(0, 0, -0.85),
            relief=DirectGui.DGG.SUNKEN,  # Добавляем рельеф
            borderWidth=(0.01, 0.01),  # Тонкая рамка
            state=DirectGui.DGG.NORMAL
        )

        self.main_menu_btn = DirectButton(
            parent=self.aspect2d,
            text="Главное меню",
            text_font=font,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.08, 0.08, 0.12, 0.85),  # основной цвет
            frameSize=(-4, 4, -0.9, 0.9),  # чуть шире (с учетом scale)
            scale=0.04,
            pos=(-1.5, 0, 0.9),  # правый верхний угол
            relief=1,
            borderWidth=(0.015, 0.015),
            text_align=TextNode.A_center,
            pressEffect=1,
            rolloverSound=None,
            clickSound=None,
            #command=self.show_menu_panel
        )
        self.main_menu_btn.setTransparency(True)


        # Левая панель с градиентным эффектом
        self.left_panel = DirectFrame(
            frameColor=(0.08, 0.08, 0.12, 0.85),
            frameSize=(-0.3, 0.54, -0.97, 0.455),
            pos=(-1.75, 0, 0.35),
            relief=DirectGui.DGG.RAISED,  # Рельефная рамка
            borderWidth=(0.015, 0.015),  # Более толстая рамка
            state=DirectGui.DGG.NORMAL
        )

        # Метка сценария с тенью
        self.scenario_label = DirectLabel(
            parent=self.bottom_panel,
            text="Подача воды от цистерны",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            text_shadow=(0, 0, 0, 0.7),  # Тень текста
            text_shadowOffset=(0.08, 0.08),
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
            #command=self.first_scenario)
            command=self.start_selected_scenario)

    def start_selected_scenario(self):
        """Запускает выбранный сценарий через лямбда-функции"""
        if self.current_scenario == 0:
            self.start_first_scenario()
        if self.current_scenario == 1:
            self.start_second_scenario()
        if self.current_scenario == 2:
            self.start_third_scenario()
        if self.current_scenario == 3:
            self.start_fourth_scenario()


    def start_first_scenario(self):
        """Подача воды от цистерны (лямбда-реализация)"""
        self.training_mode = True
        self.auto_mode = True

        scenario_sequence = [
            (lambda: self._execute_step("Выключите сцепление из насосного отсека",
                                        lambda: self.rotate_valve1(1))),
            (lambda: self._execute_step("Откройте задвижку «На лафетный ствол»",
                                        lambda: self.rotate_valve5(1))),
            (lambda: self._execute_step("Откройте задвижку «Из цистерны»",
                                        lambda: self.rotate_valve4(1))),
            (lambda: self._execute_step("Закройте задвижку «На лафетный ствол»",
                                        lambda: self.rotate_valve5(-1))),
            (lambda: self._execute_step("Включите сцепление(стрелка манометра поднимается до 3атм)",
                                        lambda: self.rotate_valve1_with_camera(1))),
            (lambda: self._execute_step("Откройте напорную задвижку",
                                        lambda: self.rotate_valve2(1))),
            (lambda: self._execute_step("Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 6 атм",
                                        lambda: self.rotate_valve11(1))),

        ]

        self._execute_sequence(scenario_sequence)

    def start_second_scenario(self):
        """Второй сценарий (пример)"""
        self.training_mode = True
        self.auto_mode = True

        scenario_sequence = [
            (lambda: self._execute_step("Выключите сцепление из насосного отсека",
                                        lambda: self.rotate_valve1(1))),
            (lambda: self._execute_step("Откройте вакуумный кран",
                                        lambda: self.rotate_valve8(1))),
            (lambda: self._execute_step("Нажмите кнопку вакуумного насоса (13) — стрелка мановакууметра опустится до -0,6 атм.",
                                        lambda: self.rotate_valve5(1))),
            (lambda: self._execute_step("Отпустите кнопку",
                                        lambda: self.rotate_valve5(1))),
            (lambda: self._execute_step("Закройте вакуумный кран (4)»",
                                        lambda: self.rotate_valve8(-1))),
            (lambda: self._execute_step("Включите сцепление(стрелка манометра поднимается до 3атм)",
                                        lambda: self.rotate_valve1_with_camera(1))),
            (lambda: self._execute_step("Откройте напорную задвижку",
                                        lambda: self.rotate_valve2(1))),
            (lambda: self._execute_step(
                "Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 6 атм",
                lambda: self.rotate_valve2(1))),
        ]

        self._execute_sequence(scenario_sequence)

    def start_third_scenario(self):
        self.training_mode = True
        self.auto_mode = True

        scenario_sequence = [
            (lambda: self._execute_step("Выключите сцепление из насосного отсека",
                                        lambda: self.rotate_valve1(1))),
            (lambda: self._execute_step("Откройте задвижку «В цистерну»",
                                        lambda: self.rotate_valve13(1))),
            (lambda: self._execute_step("Включите сцепление(стрелка манометра поднимается до 3атм)",
                                        lambda: self.rotate_valve1_with_camera(1))),
        ]

        self._execute_sequence(scenario_sequence)

    def start_fourth_scenario(self):
        self.training_mode = True
        self.auto_mode = True

        scenario_sequence = [
            (lambda: self._execute_step("Выключите сцепление из насосного отсека",
                                        lambda: self.rotate_valve1(1))),
            (lambda: self._execute_step("Откройте задвижку «На лафетный ствол»",
                                        lambda: self.rotate_valve5(1))),
            (lambda: self._execute_step("Откройте задвижку «Из цистерны»",
                                        lambda: self.rotate_valve4(1))),
            (lambda: self._execute_step("Включите сцепление(стрелка манометра поднимается до 3атм)",
                                        lambda: self.rotate_valve1_with_camera(1))),
            (lambda: self._execute_step(
                "Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 6 атм",
                lambda: self.rotate_valve2(1))),
        ]

        self._execute_sequence(scenario_sequence)

    def _execute_step(self, message, action):
        """Выполняет один шаг сценария"""
        self.step_label['text'] = message
        action()

    def _execute_sequence(self, sequence, index=0):
        """Рекурсивно выполняет последовательность шагов"""
        if index >= len(sequence):
            self.step_label['text'] = "Сценарий завершен!"
            self.training_mode = False
            self.auto_mode = False
            return

        # Выполняем текущий шаг
        sequence[index]()

        # Планируем следующий шаг через 5.5 секунд (5 сек анимация + 0.5 сек запас)
        if index + 1 < len(sequence):
            self.taskMgr.do_method_later(
                5.5,
                self._execute_sequence,
                f"scenario_step_{index}",
                extraArgs=[sequence, index + 1]
            )

    def add_decorative_elements(self):
        # Улучшенные разделители с градиентом
        divider = DirectFrame(
            parent=self.bottom_panel,
            frameSize=(-1.55, 1.55, -0.005, 0.005),
            frameColor=(0.4, 0.6, 1.0, 0.8),  # Более яркий цвет
            pos=(0, 0, 0.12)
        )

        # Добавляем второй разделитель для симметрии
        divider_bottom = DirectFrame(
            parent=self.bottom_panel,
            frameSize=(-1.55, 1.55, -0.003, 0.003),
            frameColor=(0.3, 0.5, 0.8, 0.6),
            pos=(0, 0, -0.1)
        )

        # Угловые акценты с анимационным потенциалом
        corner_size = 0.12
        corner_color = (0.4, 0.6, 1.0, 0.5)  # Более яркий цвет

        # Создаем угловые элементы с разными стилями
        corner_styles = [
            {"frameColor": corner_color, "borderWidth": (0.01, 0.01)},
            {"frameColor": (0.8, 0.9, 1.0, 0.4), "relief": DirectGui.DGG.RAISED},
            {"frameColor": (0.2, 0.4, 0.8, 0.6), "relief": DirectGui.DGG.SUNKEN},
            {"frameColor": corner_color, "borderWidth": (0.01, 0.01)}
        ]

        positions = [(-1, 1), (1, 1), (-1, -1), (1, -1)]

        for (x, y), style in zip(positions, corner_styles):
            corner = DirectFrame(
                parent=self.left_panel,
                frameSize=(-corner_size, corner_size, -corner_size, corner_size),
                pos=(x * 0.75, 0, y * 0.65),
                **style
            )

        # Добавляем фоновую текстуру или узор
        background_pattern = DirectFrame(
            parent=self.left_panel,
            frameSize=(-0.78, 0.78, -0.63, 0.63),
            frameColor=(0.15, 0.15, 0.2, 0.3),
            pos=(0, 0, 0)
        )

    def create_preview_camera(self, object_name, is_bottom=False):
        """Создает камеру предпросмотра с раздельными буферами"""
        font = self.loader.load_font("arial.ttf")

        # Определяем атрибуты для верхней/нижней камеры
        buffer_attr = 'preview_buffer_bottom' if is_bottom else 'preview_buffer_top'
        texture_attr = 'preview_texture_bottom' if is_bottom else 'preview_texture_top'
        card_attr = 'preview_card_bottom' if is_bottom else 'preview_card_top'
        label_attr = 'preview_label_bottom' if is_bottom else 'preview_label_top'
        cam_np_attr = 'preview_cam_np_bottom' if is_bottom else 'preview_cam_np_top'

        # Удаляем предыдущую камеру того же типа
        if getattr(self, buffer_attr, None):
            getattr(self, buffer_attr).remove_all_display_regions()
            self.graphicsEngine.remove_window(getattr(self, buffer_attr))

        # Поиск целевого объекта
        target_node = self.model.find(f"**/{object_name}")
        if target_node.is_empty() and object_name in self.logical_parts:
            target_node = self.model.find(self.logical_parts[object_name])
        if target_node.is_empty():
            print(f"⚠️ Объект {object_name} не найден")
            return

        # Создаем буфер рендеринга
        win_props = WindowProperties.size(500, 500)
        fb_props = FrameBufferProperties()
        fb_props.set_rgba_bits(8, 8, 8, 8)
        fb_props.set_depth_bits(24)

        buffer = self.graphicsEngine.make_output(
            self.pipe, f"PreviewBuffer_{'bottom' if is_bottom else 'top'}", -2,
            fb_props, win_props,
            GraphicsPipe.BF_refuse_window,
            self.win.get_gsg(), self.win)

        setattr(self, buffer_attr, buffer)

        # Создаем и настраиваем текстуру
        texture = Texture()
        buffer.add_render_texture(texture, GraphicsOutput.RTMCopyRam)
        setattr(self, texture_attr, texture)

        # Настройка камеры
        lens = OrthographicLens()
        lens.set_film_size(0.4, 0.4)
        preview_cam = self.make_camera(buffer, lens=lens)
        cam_np = NodePath(preview_cam)
        cam_np.reparent_to(render)
        setattr(self, cam_np_attr, cam_np)

        # Позиционирование камеры
        pos_data = self.preview_positions.get(object_name)
        if pos_data:
            cam_np.set_pos(pos_data["pos"])
            cam_np.look_at(pos_data["look"])
        else:
            bounds = target_node.get_bounds()
            center = bounds.get_center() if not bounds.is_empty() else target_node.get_pos(render)
            radius = bounds.get_radius() if not bounds.is_empty() else 1.0
            cam_np.set_pos(center + Vec3(0, -radius * 2, radius * 0.5))
            cam_np.look_at(center)


        # Создаем карточку для отображения
        cm = CardMaker(f"{'bottom_' if is_bottom else 'top_'}preview_card")
        cm.set_frame(-0.48, 0.48, -0.48, 0.48)

        card = self.aspect2d.attach_new_node(cm.generate())
        card.set_texture(texture)
        card.set_pos(-1.55, 0, -0.28 if is_bottom else 0.47)  # Нижняя карточка смещена вниз
        card.set_scale(0.7)
        setattr(self, card_attr, card)

        # Создаем подпись
        label = DirectLabel(
            parent=self.aspect2d,
            text=f"{object_name if object_name != "Manometr_Arrow" else "Манометр"}",
            text_font=font,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            scale=0.045,
            pos=(-1.5, 0, 0.07 if is_bottom else 0.81),  # Позиционируем подписи
            text_align=TextNode.A_center
        )
        setattr(self, label_attr, label)

        # Таймер закрытия
        self.taskMgr.do_method_later(5, lambda task: self.destroy_preview_camera(is_bottom),
                                     f"DestroyPreviewCamera_{'bottom' if is_bottom else 'top'}")

    def destroy_preview_camera(self, is_bottom=False):
        """Уничтожает указанную камеру предпросмотра"""
        buffer_attr = 'preview_buffer_bottom' if is_bottom else 'preview_buffer_top'
        card_attr = 'preview_card_bottom' if is_bottom else 'preview_card_top'
        label_attr = 'preview_label_bottom' if is_bottom else 'preview_label_top'
        cam_np_attr = 'preview_cam_np_bottom' if is_bottom else 'preview_cam_np_top'

        if getattr(self, buffer_attr, None):
            getattr(self, buffer_attr).remove_all_display_regions()
            self.graphicsEngine.remove_window(getattr(self, buffer_attr))
            setattr(self, buffer_attr, None)

        for attr in [card_attr, label_attr, cam_np_attr]:
            if hasattr(self, attr):
                getattr(self, attr).remove_node()
                delattr(self, attr)


    def update_preview_camera_position(self, target_node):
        """Обновляет позицию превью-камеры"""
        if not self.preview_cam_np:
            return

        bounds = target_node.get_bounds()
        center = bounds.get_center()
        radius = bounds.get_radius()

        self.preview_cam_np.set_pos(center + Vec3(0, -self.preview_cam_distance * radius, radius * 0.3))
        self.preview_cam_np.look_at(center)

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



    def set_ctrl_pressed(self, pressed):
        self.ctrl_pressed = pressed

    def reset_plane14_color(self, task):
        self.plane14.clear_color_scale()
        return task.done

    def reset_plane11_color(self, task):
        self.plane11.clear_color_scale()
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
                    self.valve6_target_angle = (self.valve6_angle - 30) % 360
                    self.valve6_moving = True
                    self.valve6_start_time = globalClock.getFrameTime()
                    self.create_preview_camera(self.valve6.name)
                    self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")

                elif picked_np.get_name() == "valve5_col" and not self.valve5_moving:
                    current_angle = self.valve5_pivot.get_p()
                    if abs(current_angle) < 0.1:
                        self.valve5_direction = 1
                    else:
                        self.valve5_direction = -1

                    self.valve5_moving = True
                    self.valve5_start_time = globalClock.getFrameTime()
                    self.create_preview_camera(self.valve5.name)
                    self.taskMgr.add(self.move_valve5_task, "MoveValve5Task")

                elif picked_np.get_name() == "valve4_col" and not self.valve4_moving:
                    current_angle = self.valve4_pivot.get_r()
                    if abs(current_angle) < 0.1:
                        self.valve4_direction = 1
                    else:
                        self.valve4_direction = -1

                    self.valve4_moving = True
                    self.valve4_start_time = globalClock.getFrameTime()
                    self.create_preview_camera(self.valve4.name)
                    self.taskMgr.add(self.move_valve4_task, "MoveValve4Task")

                elif picked_np.get_name() == "plane14_col":
                    print("📌 Нажата кнопка plane14")
                    self.create_preview_camera(self.plane14.name)
                    self.plane14.set_color_scale(1, 1, 0.5, 1)
                    self.taskMgr.do_method_later(0.3, self.reset_plane14_color, "ResetColor")

                elif picked_np.get_name() == "valve2_col" and not self.valve2_moving:
                    current_angle = self.valve2_pivot.get_r()
                    if abs(current_angle) < 0.1:
                        self.valve2_direction = 1
                    else:
                        self.valve2_direction = -1

                    self.valve2_moving = True
                    self.valve2_start_time = globalClock.getFrameTime()
                    self.create_preview_camera(self.valve2.name)
                    self.taskMgr.add(self.move_valve2_task, "MoveValve2Task")

    def move_valve2_task(self, task):
        if not hasattr(self, 'valve2_pivot') or not self.valve2_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve2_start_time
        progress = min(elapsed / 5, 1.0)

        if self.valve2_direction > 0:
            target_angle = self.valve2_target_angle
        else:
            target_angle = 0

        new_angle = progress * target_angle
        self.valve2_pivot.set_p(new_angle)

        if progress >= 1.0:
            self.valve2_moving = False
            if self.training_mode:
                self.on_step_completed()

                self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
            return task.done

        return task.cont

    def move_valve4_task(self, task):
        if not hasattr(self, 'valve4_pivot') or not self.valve4_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve4_start_time
        progress = min(elapsed / 5, 1.0)

        if self.valve4_direction > 0:
            target_angle = self.valve4_target_angle
        else:
            target_angle = 0

        new_angle = progress * target_angle
        self.valve4_pivot.set_r(new_angle)

        if progress >= 1.0:
            self.valve4_moving = False
            if self.training_mode:
                self.on_step_completed()

                self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
            return task.done

        return task.cont

    def move_valve5_task(self, task):
        if not hasattr(self, 'valve5_pivot') or not self.valve5_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve5_start_time
        progress = min(elapsed / 5, 1.0)

        angle_change = progress * self.valve5_target_angle_change
        new_angle = self.valve5_start_angle + angle_change
        self.valve5_pivot.set_p(new_angle)

        if progress >= 1.0:
            self.valve5_moving = False
            self.valve5_current_angle = new_angle
            # Важно: сохраняем новое состояние
            if self.valve5_direction > 0:
                self.valve5_is_open = True
            else:
                self.valve5_is_open = False

            if self.training_mode:
                self.on_step_completed()

                self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
            return task.done

        return task.cont

    def move_valve8_task(self, task):
        if not hasattr(self, 'valve8_pivot') or not self.valve8_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve8_start_time
        progress = min(elapsed / 5, 1.0)

        angle_change = progress * self.valve8_target_angle_change
        new_angle = self.valve8_start_angle + angle_change
        self.valve8_pivot.set_p(new_angle)

        if progress >= 1.0:
            self.valve8_moving = False
            self.valve8_current_angle = new_angle
            # Важно: сохраняем новое состояние
            if self.valve8_direction > 0:
                self.valve8_is_open = True
            else:
                self.valve8_is_open = False

            if self.training_mode:
                self.on_step_completed()

                self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
            return task.done

        return task.cont

    def move_valve6_task(self, task):
        if not hasattr(self, 'valve6_pivot') or not hasattr(self, 'valve6'):
            return task.done  # Используем done вместо cont

        if self.valve6_moving:
            elapsed = globalClock.getFrameTime() - self.valve6_start_time
            progress = min(elapsed / 2.0, 1.0)  # Уменьшил время до 1 секунды

            # Плавная интерполяция угла
            start_angle = self.valve6_start_angle  # Новый атрибут для сохранения начального угла
            target_angle = self.valve6_target_angle
            new_angle = start_angle + (target_angle) * progress

            # Вращение вокруг оси Z (горизонтальное)
            self.valve6_pivot.set_p(-new_angle)  # Отрицательное значение для правильного направления

            if progress >= 1.0:
                self.valve6_moving = False
                self.valve6_angle = target_angle  # Сохраняем конечный угол
                if self.training_mode:
                    self.on_step_completed()
                    self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
                return task.done

        return task.cont

    def move_valve13_task(self, task):
        if not hasattr(self, 'valve13_pivot') or not self.valve13_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve13_start_time
        progress = min(elapsed / 5, 1.0)

        if self.valve13_direction > 0:
            target_angle = self.valve13_target_angle
        else:
            target_angle = 0

        new_angle = progress * target_angle
        self.valve13_pivot.set_p(new_angle)

        if progress >= 1.0:
            self.valve13_moving = False
            if self.training_mode:
                self.on_step_completed()

                self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
            return task.done

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

    def start_scenario(self, scenario_index):
        """Запускает сценарий с защитой от повторного входа"""
        if self._scenario_running:
            print("Сценарий уже выполняется!")
            return

        self.current_scenario = scenario_index
        self._scenario_running = True
        self.training_mode = True
        self.auto_mode = True
        self.current_step = 0
        self.execute_current_step()

    def execute_current_step(self):
        """Выполняет текущий шаг с защитой от повторных вызовов"""
        if not self._scenario_running:
            return

        scenario = self.scenarios[self.current_scenario]

        # Очищаем предыдущую задачу
        if self._current_task:
            taskMgr.remove(self._current_task)
            self._current_task = None

        # Для сценариев-методов
        if scenario.get('type') == 'method':
            method = getattr(self, scenario['method'])
            method()
            return

        # Для пошаговых сценариев
        if self.current_step >= len(scenario['steps']):
            self._finish_scenario()
            return

        step = scenario['steps'][self.current_step]
        self.step_label['text'] = step['message']

        if step['action'] == 'rotate_valve':
            valve_method = getattr(self, f'rotate_valve{step["valve"]}')
            valve_method(step['direction'])

            # Планируем следующий шаг с сохранением задачи
            self._current_task = taskMgr.doMethodLater(
                step['duration'],
                self._next_step_handler,
                "ScenarioStep"
            )

    def _next_step_handler(self, task):
        """Обработчик перехода к следующему шагу"""
        if not self._scenario_running:
            return task.done

        self.current_step += 1
        self.execute_current_step()
        return task.done

    def _finish_scenario(self):
        """Корректно завершает выполнение сценария"""
        self._scenario_running = False
        self.training_mode = False
        self.auto_mode = False

        if self._current_task:
            taskMgr.remove(self._current_task)
            self._current_task = None

        self.step_label['text'] = "Сценарий завершен!"

    def next_scenario_step(self, task):
        """Переходит к следующему шагу сценария"""
        self.current_step += 1
        self.execute_current_step()
        return task.done


    def rotate_valve11(self, direction):
        if hasattr(self, 'plane11'):
            self.plane11.set_color_scale(1, 0, 0, 1)
            self.taskMgr.do_method_later(1, self.reset_plane11_color, "ResetColor")


            if hasattr(self, 'valve6_pivot'):
                if not hasattr(self, 'valve6_angle'):
                    self.valve6_angle = self.valve6_pivot.get_h()  # Текущий угол

                angle_change = 30 * direction  # Угол поворота (направление: 1 или -1)
                self.valve6_target_angle = (self.valve6_angle + angle_change) % 360
                self.valve6_start_angle = self.valve6_angle
                self.valve6_moving = True  # Разрешаем движение
                self.valve6_start_time = globalClock.getFrameTime()  # Время начала

            self.start_second_music()
            self.create_preview_camera(self.plane11.name, is_bottom=False)
            self.create_preview_camera("Manometr_Arrow", is_bottom=True)

            self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")
            self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")

    def rotate_valve1_with_camera(self, direction):
        """Вращение вентиля с двумя камерами"""
        print(f"Вращаем вентиль 1, направление: {direction}")
        if hasattr(self, 'plane14'):
            self.plane14.set_color_scale(1, 0, 0, 1)
            self.taskMgr.do_method_later(3, self.reset_plane14_color, "ResetColor")

            # Инициализация вращения valve6 (если нужно)
            if hasattr(self, 'valve6_pivot'):
                if not hasattr(self, 'valve6_angle'):
                    self.valve6_angle = self.valve6_pivot.get_h()  # Текущий угол

                angle_change = 30 * direction  # Угол поворота (направление: 1 или -1)
                self.valve6_target_angle = (self.valve6_angle + angle_change) % 360
                self.valve6_start_angle = self.valve6_angle
                self.valve6_moving = True  # Разрешаем движение
                self.valve6_start_time = globalClock.getFrameTime()  # Время начала

            # Создаем обе камеры
            self.create_preview_camera(self.plane14.name, is_bottom=False)
            self.create_preview_camera("Manometr_Arrow", is_bottom=True)

            # Запускаем задачу вращения valve6
            self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")

            self.taskMgr.do_method_later(5.0, self.next_scenario_step, "DelayedNextStep")


    def rotate_valve1(self, direction):
        """Вращение вентиля 1 со звуком"""
        print(f"Вращаем вентиль 1, направление: {direction}")

        if  self.bg_music_playing:
            self.bg_sound.stop()
            self.bg_music_playing = False
        else:
            self.bg_sound.play()
            self.bg_music_playing = True


        # Визуальные эффекты
        if hasattr(self, 'plane14'):
            # Сначала изменяем цвет
            self.plane14.set_color_scale(1, 0, 0, 1)  # Красный цвет

            self.create_preview_camera(self.plane14.name)

            # Сброс цвета через 3 секунды
            self.taskMgr.do_method_later(3, self.reset_plane14_color, "ResetColor")

            # Принудительное обновление кадра


            # Звуковые эффекты
            self.taskMgr.do_method_later(0, self.stop_valve_sound, "StopSound")
            self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")

    def stop_valve_sound(self, task):
        """Остановка звука вентиля"""
        self.valve_sound.stop()
        self.is_valve_sound_playing = False
        return task.done

    def stop_valve_sound(self, task):
        """Остановка звука вентиля"""
        self.valve_sound.stop()
        self.is_valve_sound_playing = False
        return task.done

    def rotate_valve1_with_camera(self, direction):
        """Вращение вентиля с двумя камерами"""
        print(f"Вращаем вентиль 1, направление: {direction}")
        if hasattr(self, 'plane14'):
            self.plane14.set_color_scale(1, 0, 0, 1)
            self.taskMgr.do_method_later(3, self.reset_plane14_color, "ResetColor")

            # Инициализация вращения valve6 (если нужно)
            if hasattr(self, 'valve6_pivot'):
                if not hasattr(self, 'valve6_angle'):
                    self.valve6_angle = self.valve6_pivot.get_h()  # Текущий угол

                angle_change = 30 * direction  # Угол поворота (направление: 1 или -1)
                self.valve6_target_angle = (self.valve6_angle + angle_change) % 360
                self.valve6_start_angle = self.valve6_angle
                self.valve6_moving = True  # Разрешаем движение
                self.valve6_start_time = globalClock.getFrameTime()  # Время начала

            # Создаем обе камеры
            self.create_preview_camera(self.plane14.name, is_bottom=False)
            self.create_preview_camera("Manometr_Arrow", is_bottom=True)

            # Запускаем задачу вращения valve6
            self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")

            self.taskMgr.do_method_later(5.0, self.next_scenario_step, "DelayedNextStep")


    def rotate_valve2(self, direction):
        """Вращение вентиля 2"""
        print(f"Вращаем вентиль 2, направление: {direction}")
        if hasattr(self, 'valve2_pivot'):
            self.valve2_direction = direction
            self.valve2_moving = True
            self.valve2_start_time = globalClock.getFrameTime()
            self.create_preview_camera(self.valve2.name)
            self.taskMgr.add(self.move_valve2_task, "MoveValve2Task")

    def rotate_valve3(self, direction):
        if hasattr(self, 'valve3_pivot'):
            self.valve3_direction = direction
            self.valve3_moving = True
            self.valve3_start_time = globalClock.getFrameTime()
            self.create_preview_camera(self.valve3.name)
            self.taskMgr.add(self.move_valve3_task, "MoveValve3Task")

 # Предварительно загружаем звук

    def rotate_valve4(self, direction):
        """Вращение вентиля 4 (рычаг) со звуком"""
        print(f"Вращаем рычаг (вентиль 4), направление: {direction}")


        if hasattr(self, 'valve4_pivot'):
            self.valve4_direction = direction
            self.valve4_moving = True
            self.valve4_start_time = globalClock.getFrameTime()
            self.create_preview_camera(self.valve4.name)
            self.start_first_music()
            self.taskMgr.add(self.move_valve4_task, "MoveValve4Task")

    def rotate_valve5(self, direction):
        """Вращение вентиля 5 (рычаг)"""
        print(f"Вращаем рычаг (вентиль 5), направление: {direction}")
        if hasattr(self, 'valve5_pivot'):
            # Если клапан уже в нужном положении - пропускаем анимацию
            if (direction > 0 and hasattr(self, 'valve5_is_open') and self.valve5_is_open) or \
                    (direction < 0 and hasattr(self, 'valve5_is_open') and not self.valve5_is_open):
                self.on_step_completed()
                return

            if not hasattr(self, 'valve5_current_angle'):
                self.valve5_current_angle = self.valve5_pivot.get_p()

            self.valve5_direction = direction
            self.valve5_moving = True
            self.valve5_start_time = globalClock.getFrameTime()
            self.valve5_start_angle = self.valve5_current_angle

            if direction > 0:
                self.valve5_target_angle_change = 85
            else:
                self.valve5_target_angle_change = -85

            self.create_preview_camera(self.valve5.name)
            self.taskMgr.add(self.move_valve5_task, "MoveValve5Task")


    def rotate_valve8(self, direction):
        """Вращение вентиля 5 (рычаг)"""
        print(f"Вращаем рычаг (вентиль8), направление: {direction}")
        if hasattr(self, 'valve8_pivot'):
            # Если клапан уже в нужном положении - пропускаем анимацию
            if (direction > 0 and hasattr(self, 'valve8_is_open') and self.valve8_is_open) or \
                    (direction < 0 and hasattr(self, 'valve8_is_open') and not self.valve8_is_open):
                self.on_step_completed()
                return

            if not hasattr(self, 'valve8_current_angle'):
                self.valve8_current_angle = self.valve8_pivot.get_p()

            self.valve8_direction = direction
            self.valve8_moving = True
            self.valve8_start_time = globalClock.getFrameTime()
            self.valve8_start_angle = self.valve8_current_angle

            if direction > 0:
                self.valve8_target_angle_change = 85
            else:
                self.valve8_target_angle_change = -85

            self.create_preview_camera(self.valve8.name)
            self.taskMgr.add(self.move_valve8_task, "MoveValve5Task")

    def rotate_valve6(self, direction):
        """Вращение стрелки манометра (вентиль 6)"""
        print(f"Вращаем стрелку манометра, направление: {direction}")
        if hasattr(self, 'valve6_pivot'):
            if not hasattr(self, 'valve6_angle'):
                self.valve6_angle = self.valve6_pivot.get_h()  # Инициализация при первом вызове

            angle_change = 30 * (-1 if direction < 0 else 1)  # Умножаем на направление
            self.valve6_target_angle = (self.valve6_angle + angle_change) % 360
            self.valve6_start_angle = self.valve6_angle  # Сохраняем начальный угол
            self.valve6_moving = True
            self.rotate_valve1_with_camera(self.valve13.name)
            self.valve6_start_time = globalClock.getFrameTime()

            self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")

    def rotate_valve13(self, direction):
        """Вращение вентиля 2"""
        print(f"Вращаем вентиль 13, направление: {direction}")
        if hasattr(self, 'valve13_pivot'):
            self.valve13_direction = direction
            self.valve13_moving = True
            self.valve13_start_time = globalClock.getFrameTime()
            self.create_preview_camera(self.valve13.name)
            self.taskMgr.add(self.move_valve13_task, "MoveValve13Task")


    def on_step_completed(self):
        """Обрабатывает завершение шага сценария"""
        if not hasattr(self, 'current_scenario') or not hasattr(self, 'scenarios'):
            return

        scenario = self.scenarios[self.current_scenario]

        # Для сценариев типа 'method' просто завершаем выполнение
        if scenario.get('type') == 'method':
            self.training_mode = False
            self.auto_mode = False
            self.step_label['text'] = "Сценарий завершен!"
            return

        # Для пошаговых сценариев
        if 'steps' in scenario:
            self.current_step += 1
            if self.current_step >= len(scenario['steps']):
                self.training_mode = False
                self.auto_mode = False
                self.step_label['text'] = "Сценарий завершен!"
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



    def execute_sequence(self, sequence, callback=None):
        """Запускает выполнение последовательности действий"""
        self._current_sequence = sequence
        self._sequence_index = 0
        self._sequence_callback = callback

        # Запускаем первый шаг сразу
        self._execute_next_sequence_step()

    def _execute_sequence_step(self):
        """Выполняет шаг последовательности"""
        if self._sequence_index >= len(self._scenario_sequence):
            self._finish_scenario()
            return

        action, delay, message = self._scenario_sequence[self._sequence_index]
        self.step_label['text'] = message
        action()

        self._sequence_index += 1
        self._current_task = taskMgr.doMethodLater(
            delay,
            self._execute_sequence_step,
            "SequenceStep"
        )

app = MyApp()
app.run()