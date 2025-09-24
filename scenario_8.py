from direct.gui import DirectGui
from direct.showbase.ShowBase import ShowBase
from panda3d.core import DirectionalLight, AmbientLight, Vec4, TextNode, FrameBufferProperties, WindowProperties, \
    GraphicsPipe, Vec3, Point3, Plane, TransparencyAttrib, RenderState, Material
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
from panda3d.core import Shader, TransparencyAttrib
from panda3d.core import TextureStage, TexGenAttrib  # Добавляем импорт
from panda3d.core import TextureAttrib, ColorAttrib, MaterialAttrib, TransparencyAttrib, LightAttrib

x = 7

class MyApp(ShowBase):
    def __init__(self):
        super().__init__()

        font = self.loader.load_font("arial.ttf")

        props = WindowProperties()
        props.setFullscreen(True)
        self.win.requestProperties(props)
        self.accept('escape', self.toggle_fullscreen)

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
            {
                'name': "Подача пены через стационарный лафетный ствол",
                'type': 'method',
                'method': 'fifth_scenario'
            },
            {
                'name': "Подача пены на 1 ГПС-600",
                'type': 'method',
                'method': 'sifth_scenario'
            },
            {
                'name': "Забор воды из открытого водоисточника при неисправной вакуумной системе (1 способ)",
                'type': 'method',
                'method': 'seven_scenario'
            },
            {
                'name': "Забор воды из открытого водоисточника при неисправной вакуумной системе (2 способ)",
                'type': 'method',
                'method': 'eight_scenario'
            },
            {
                'name': "Забор воды из открытого водоисточника при неисправной вакуумной системе (3 способ)",
                'type': 'method',
                'method': 'nineth_scenario'
            },
            {
                'name': "Забор воды из открытого водоисточника при помощи гидроэлеваторной системы(насос-гидроэлеватор-цистерна)",
                'type': 'method',
                'method': 'ten_scenario'
            },
            {
                'name': "Забор воды из открытого водоисточника при помощи гидроэлеваторной системы(насос-гидроэлеватор-водосборник-насос)",
                'type': 'method',
                'method': 'eleventh__scenario'
            },
            {
                'name': "Проверка на сухой вакуум",
                'type': 'method',
                'method': 'twelfth_scenario'

            },

        ]

        print(self.scenarios[x])
        self.scenarios = [self.scenarios[x]]


        outline_shader = Shader.load(Shader.SL_GLSL,
                                     vertex="""
            void main() {
                gl_Position = ftransform();
            }
            """,
                                     fragment="""
            uniform vec4 outline_color;
            void main() {
                gl_FragColor = outline_color;
            }
            """
                                     )

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
                "pos": Point3(0.281166 - 1, -7.5, 2),
                "look": Point3(0.281166 - 2.5, 0.26543, 0.267012)
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
                "look": Point3(0.281166 - 0.5, 0.26543 - 0.1, 0.468012 - 0.2)
            },
            "Дозатор": {
                "pos": Point3(0.281166 - 1.0, -1.5 - 0.3, 0.568012 - 0.2),
                "look": Point3(0.281166 - 0.8, 0.26543 - 0.1, 0.468012 - 0.2)
            },
            "Задвижка «Вакуумный кран»": {
                "pos": Point3(0.281166 - 0.2, -1.5 - 0.6, 0.568012 - 0.2),
                "look": Point3(0.281166 - 0.5, 0.26543 - 0.1, 0.468012 - 0.2)
            },
            "Тест": {
                "pos": Point3(0.281166 - 1, -7.5, 2),
                "look": Point3(0.281166 - 2.5, 0.26543, 0.267012)
            },
            "Пульт": {
                "pos": Point3(-0.4, -5.5, 0.5),
                "look": Point3(-0.4, -5.5, 0.5)
            },
            # "Пульт": {
            #     "pos": Point3(-0.4, -1, 0.5),
            #     "look": Point3(-0.4, -1, 0.5)
            # },
            "Вакуумный кран": {
                "pos": Point3(-0.45, -3.0, 0.768012),
                "look": Point3(-0.45, 1.0, 0.768012)
            },
            "Забор ПО": {
                "pos": Point3(-0.45 + 0.45, -3.0, 0.8),
                "look": Point3(-0.45 + 0.45, 1.0, 0.8)
            },

            "Manovakuummetr_Arrow": {
                "pos": Point3(0.281166 - 0.2, -1.5 - 0.6, 0.568012 - 0.65),
                "look": Point3(0.281166 - 0.5, 0.26543 - 0.1, 0.468012 - 0.65)
            },
            "Промывка пенодозатора": {
                "pos": Point3(-0.45 + 0.75, -3.0, 0.4),
                "look": Point3(-0.45 + 0.75, 1.0, 0.4)
            },
        }

        for key in self.preview_positions:
            self.preview_positions[key]["pos"] += offset
            self.preview_positions[key]["look"] += offset


        dlight = DirectionalLight("dlight")
        alight = AmbientLight("alight")
        dlight.set_color(Vec4(0.8, 0.8, 0.7, 1))
        alight.set_color(Vec4(0.2, 0.2, 0.2, 1))
        render.set_light(render.attach_new_node(dlight))
        render.set_light(render.attach_new_node(alight))


        self.model = self.loader.load_model("3.glb")
        self.model.reparent_to(self.render)
        self.model.set_scale(1)
        self.cam.look_at(self.model)

        valve6_geom = self.model.find("**/Manometr_Arrow")
        self.valve6_geom = valve6_geom
        point = self.model.find("**/point8")
        valve5_geom = self.model.find("**/COMPOUND2")
        self.valve5_geom = valve5_geom

        #
        pipe = self.render.find("**/pCylinder3.001")
        second_pipe = self.render.find("**/pCylinder2.001")
        center_pipe0 = self.render.find("**/polySurface8")
        center_pipe1 = self.render.find("**/pTorus4")
        center_pipe2 = self.render.find("**/mirrored_y_3")
        self.center_pipe0 = center_pipe0
        self.center_pipe1 = center_pipe1
        self.center_pipe2 = center_pipe2
        #center_
        self.pipe_left = pipe
        self.pipe_left_high = second_pipe

        self.foam_shader = Shader.make('''
            void vshader(float4 vtx_position : POSITION,
                        float2 vtx_texcoord0 : TEXCOORD0,
                        out float4 l_position : POSITION,
                        out float2 l_texcoord0 : TEXCOORD0,
                        uniform float4x4 mat_modelproj) {
                l_position = mul(mat_modelproj, vtx_position);
                l_texcoord0 = vtx_texcoord0;
            }

            void fshader(float2 l_texcoord0 : TEXCOORD0,
                        out float4 o_color : COLOR,
                        uniform float time) {
                // Движение пены вдоль трубы
                float flow_speed = 1.5;
                float flow_pos = l_texcoord0.x + time * flow_speed;

                // Создаем узор пузырьков
                float bubbles1 = sin(l_texcoord0.x * 35.0 + flow_pos * 10.0) * 0.5 + 0.5;
                float bubbles2 = cos(l_texcoord0.x * 28.0 + flow_pos * 8.0 + 2.0) * 0.5 + 0.5;
                float bubbles3 = sin(l_texcoord0.x * 42.0 + flow_pos * 12.0 + 4.0) * 0.5 + 0.5;

                // Комбинируем пузырьки
                float bubble_pattern = bubbles1 * bubbles2 * bubbles3;
                bubble_pattern = pow(bubble_pattern, 2.0); // Делаем более четкими

                // Текстура пены
                float foam_texture = sin(flow_pos * 8.0) * cos(l_texcoord0.x * 6.0);
                foam_texture = abs(foam_texture) * 0.7;

                // Основной цвет пены
                vec4 foam_color = vec4(0.9, 0.92, 0.95, 0.85);

                // Добавляем вариации цвета для реализма
                foam_color.r -= bubble_pattern * 0.1;
                foam_color.g -= bubble_pattern * 0.08;
                foam_color.b += bubble_pattern * 0.05;

                // Делаем некоторые области более плотными
                float density = foam_texture * 0.5 + bubble_pattern * 0.3;
                foam_color.a *= (0.7 + density * 0.3);

                o_color = foam_color;
            }
        ''', Shader.SL_Cg)

        self.water_shader = Shader.make('''
            void vshader(float4 vtx_position : POSITION,
                        float2 vtx_texcoord0 : TEXCOORD0,
                        out float4 l_position : POSITION,
                        out float2 l_texcoord0 : TEXCOORD0,
                        uniform float4x4 mat_modelproj) {
                l_position = mul(mat_modelproj, vtx_position);
                l_texcoord0 = vtx_texcoord0;
            }

            void fshader(float2 l_texcoord0 : TEXCOORD0,
                        out float4 o_color : COLOR,
                        uniform float time) {

                // Движение воды вдоль трубы
                float flow_speed = 0.8;
                float flow_pos = l_texcoord0.y + time * flow_speed;

                // Создаем волны и рябь на поверхности воды
                float waves1 = sin(l_texcoord0.x * 25.0 + flow_pos * 5.0) * 0.3;
                float waves2 = cos(l_texcoord0.x * 18.0 + flow_pos * 3.0 + 1.5) * 0.2;
                float waves3 = sin(l_texcoord0.x * 32.0 + flow_pos * 7.0 + 3.0) * 0.4;

                // Комбинируем волны
                float wave_pattern = (waves1 + waves2 + waves3) * 0.33;

                // Создаем эффект глубины воды
                float depth = 1.0 - abs(l_texcoord0.x - 0.5) * 2.0;
                depth = clamp(depth, 0.3, 1.0);

                // Основной цвет воды - синий с вариациями
                float4 water_color = float4(0.15, 0.35, 0.65, 0.9);

                // Добавляем градиент глубины
                water_color.rgb *= (0.7 + depth * 0.3);
                water_color.r -= depth * 0.1;
                water_color.g += depth * 0.05;
                water_color.b += depth * 0.15;

                // Добавляем волновые искажения цвета
                water_color.r += wave_pattern * 0.05;
                water_color.g += wave_pattern * 0.03;
                water_color.b -= wave_pattern * 0.02;

                // Создаем эффект течения (струи)
                float current = sin(flow_pos * 12.0) * 0.1;
                water_color.a *= (0.85 + current * 0.15);

                // Добавляем легкие блики (отражения света)
                float specular = pow(max(0.0, sin(time * 2.0 + l_texcoord0.y * 20.0)), 8.0);
                water_color.rgb += float3(specular * 0.25);

                // Легкие пузырьки (меньше и реже чем у пены)
                float bubbles = sin(l_texcoord0.x * 45.0 + flow_pos * 15.0) * 0.5 + 0.5;
                bubbles = pow(bubbles, 4.0) * 0.2; // Более редкие и мелкие пузырьки
                water_color.rgb += float3(bubbles * 0.1);

                o_color = water_color;
            }
        ''', Shader.SL_Cg)

        # self.left_pipe.setShader(water_shader)
        # self.left_pipe.setTransparency(TransparencyAttrib.MAlpha)
        # self.left_pipe.setShaderInput("time", 0.0)
        #
        # self.left_pipe_second.setShader(water_shader_second)
        # self.left_pipe_second.setTransparency(TransparencyAttrib.MAlpha)
        # self.left_pipe_second.setShaderInput("time", 0.0)
        #
        # Добавляем обновление времени
        # def update_water(task):
        #     self.left_pipe.setShaderInput("time", globalClock.getFrameTime())
        #     return task.cont
        #
        # self.taskMgr.add(update_water, "update_water")



        self.valve6_moving = False
        self.valve66_moving = False
        self.model.ls()

        point1 = self.model.find("**/point1")
        if point1.is_empty():
            print("❌ point1 не найден!")
        else:
            print(f"✅ point1 позиция: {point1.get_pos(render)}")

        valve5_geom = self.model.find("**/COMPOUND2")
        if valve5_geom.is_empty():
            print("❌ Рычаг не найден!")
        else:
            print("✅ Рычаг найден")

            pivot_node = self.model.find("**/point8")
            if pivot_node.is_empty():
                print("❌ Точка крепления не найдена!")
                return
            self.valve5_geom = valve5_geom
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

            valve5_geom.set_pos(saved_pos)
            self.valve5.name = "Задвижка на Лафетный ствол"
            self.valve5_pivot.set_p(0)
            self.valve5_target_angle = 85
            self.valve5_moving = False
            self.valve5_direction = 1


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
            self.plane14 = plane14
            self.plane14.name = "Панель"

            bounds = self.plane14.get_tight_bounds()
            center = (bounds[0] + bounds[1]) * 0.5


        plane11 = self.model.find("**/plane11")
        if plane11.is_empty():
            print("❌ кнопка не найдена!")
        else:
            print("✅ кнопка найдена")
            self.plane11 = plane11
            self.plane11.name = "Панель"
            # self.plane14.set_color_scale(1, 0, 0, 1)

            min_b, max_b = self.plane11.get_tight_bounds()
            center = (min_b + max_b) * 0.5
            extent = (max_b - min_b) * 0.5
            extent *= 1000


        plane3 = self.model.find("**/plane3")
        if plane3.is_empty():
            print("❌ кнопка не найдена!")
        else:
            print("✅ кнопка найдена")
            self.plane3 = plane3
            self.plane3.name = "Пульт"


        plane10 = self.model.find("**/plane10")
        if plane10.is_empty():
            print("❌ кнопка не найдена!")
        else:
            print("✅ кнопка найдена")
            self.plane10 = plane10
            self.plane10.name = "Пульт"

        valve2_geom = self.model.find("**/COMPOUND1")
        self.valve2_geom = valve2_geom
        point5 = self.model.find("**/point5")

        if valve2_geom.is_empty() or point5.is_empty():
            print("❌ Вентиль 2 или точка вращения не найдены!111")
        else:
            print("✅ Вентиль 2 и точка вращения найдены")

            # 1. Получаем трансформации
            pivot_pos = point5.get_pos(self.model)
            valve2_pos = valve2_geom.get_pos(self.model)
            valve2_hpr = valve2_geom.get_hpr(self.model)


            # 2. Создаем иерархию узлов
            self.valve2_root = self.model.attach_new_node("valve2_root")
            self.valve2_root.set_pos(pivot_pos)

            self.valve2_pivot = self.valve2_root.attach_new_node("valve2_pivot")
            self.valve2_pivot.set_pos(0, 0, 0)

            # 3. Переносим геометрию
            valve2_geom.wrt_reparent_to(self.valve2_pivot)
            valve2_geom.set_pos(valve2_pos - pivot_pos)
            valve2_geom.set_hpr(valve2_hpr)

            # 4. Настройки вращения
            self.valve2 = valve2_geom
            self.valve2.name = 'Левая напорная задвижка'
            self.valve2_pivot.set_hpr(0, 0, 0)
            self.valve2_target_angle = 90
            self.valve2_moving = False
            self.valve2_direction = 1

            # 5. Создаем контур (добавленный код)

           # self.valve2_outline = self.create_simple_outline(valve2_geom)
            # if self.valve2_outline:
            #     self.valve2_outline.hide()  # Скрываем по умолчанию

            # 6. Отладка
            self.debug_marker = self.loader.loadModel("models/smiley")
            self.debug_marker.reparent_to(self.render)
            self.debug_marker.set_pos(pivot_pos)
            self.debug_marker.set_scale(0.1)
            self.debug_marker.set_color(1, 0, 0, 1)

        # Добавляем метод в класс (вне этого блока кода)


        valve22_geom = self.model.find("**/COMPOUND6")
        point4 = self.model.find("**/point4")


        if valve22_geom.is_empty() or point4.is_empty():
            print("❌ Вентиль 2 или точка вращения не найдены!2222")
        else:
            print("✅ Вентиль 2 и точка вращения найдены")
            self.valve22_geom = valve22_geom
            original_mat = valve22_geom.get_mat(self.model)
            pivot_pos = point4.get_pos(self.model)
            valve22_pos = valve22_geom.get_pos(self.model)

            self.valve22_root = self.model.attach_new_node("valve22_root")
            self.valve22_root.set_pos(pivot_pos)

            self.valve22_pivot = self.valve22_root.attach_new_node("valve22_pivot")

            valve22_geom.wrt_reparent_to(self.valve22_pivot)
            self.valve22 = valve22_geom
            valve22_geom.set_mat(original_mat)

            relative_pos = valve22_pos - pivot_pos
            valve22_geom.set_pos(relative_pos)

            saved_pos = valve22_geom.get_pos()
            valve22_geom.set_pos(0, 0, 0)

            valve22_geom.set_pos(saved_pos)
            self.valve22.name = 'Правая напорная задвижка'
            self.valve22_pivot.set_p(0)
            self.valve22_target_angle = 90
            self.valve22_moving = False
            self.valve22_direction = 1


        valve4_geom = self.model.find("**/COMPOUND3")
        if valve4_geom.is_empty():

            print("❌ Рычаг не найден!")
        else:
            print("✅ Рычаг найден")

            pivot_node = self.model.find("**/point9")
            if pivot_node.is_empty():
                print("❌ Точка крепления не найдена!")
                return
            self.valve4_geom = valve4_geom
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
        self.valve13_geom = valve13_geom
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

            valve13_geom.set_pos(saved_pos)

            self.valve13_pivot.set_p(0)
            self.valve13_target_angle = 90
            self.valve13_moving = False
            self.valve13_direction = 1
            self.valve13.name = "Задвижка «В цистерну»"


        valve44_geom = self.model.find("**/COMPOUND4")
        point44 = self.model.find("**/point6")
        self.valve44_geom = valve44_geom
        if point44.is_empty():
            print("❌ point11 не найден!")
        else:
            print(f"✅ point44 позиция: {point44.get_pos(render)}")

        if valve44_geom.is_empty():
            print("❌ Рычаг1 не найден!")
        else:
            print(f"✅ Рыча44 1позиция: {point44.get_pos(render)}")
            self.valve44_moving = False

        if valve44_geom.is_empty():
            print("❌ Рычаг не найден!")
        else:
            print("✅ Рыча44г найден")

            original_mat = valve44_geom.get_mat(self.model)
            pivot_pos = point44.get_pos(self.model)
            valve44_pos = valve44_geom.get_pos(self.model)

            self.valve44_root = self.model.attach_new_node("valve44_root")
            self.valve44_root.set_pos(pivot_pos)

            self.valve44_pivot = self.valve44_root.attach_new_node("valve44_pivot")

            valve44_geom.reparent_to(self.valve44_pivot)
            self.valve44 = valve44_geom
            valve44_geom.set_mat(original_mat)

            relative_pos = valve44_pos - pivot_pos
            valve44_geom.set_pos(relative_pos)

            saved_pos = valve44_geom.get_pos()
            valve44_geom.set_pos(0, 0, 0)

            valve44_geom.set_pos(saved_pos)

            self.valve44_pivot.set_p(0)
            self.valve44_target_angle = 90
            self.valve44_moving = False
            self.valve44_direction = 1
            self.valve44.name = "Дозатор"

        valve8_geom = self.model.find("**/ COMPOUND8")
        point8 = self.model.find("**/point9.001")
        self.valve8_geom = valve8_geom
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

            valve8_geom.set_pos(saved_pos)
            self.valve8.name = "Вакуумный кран"
            self.valve8_pivot.set_p(0)
            self.valve8_target_angle = 85
            self.valve8_moving = False
            self.valve8_direction = 1

        valve12_geom = self.model.find("**/COMPOUND12")
        point12 = self.model.find("**/point9.004")
        self.valve12_geom = valve12_geom
        if valve12_geom.is_empty():
            print("❌ 12Рычаг не найден!")
        else:
            print("✅ 12Рычаг найден")

            pivot_node = self.model.find("**/point9.004")
            if pivot_node.is_empty():
                print("❌ 12Точка крепления не найдена!")
                return

            original_mat = valve12_geom.get_mat(self.model)
            pivot_pos = pivot_node.get_pos(self.model)
            valve12_pos = valve12_geom.get_pos(self.model)

            self.valve12_root = self.model.attach_new_node("valve12_root")
            self.valve12_root.set_pos(pivot_pos)

            self.valve12_pivot = self.valve12_root.attach_new_node("valve12_pivot")

            valve12_geom.reparent_to(self.valve12_pivot)
            self.valve12 = valve12_geom
            valve12_geom.set_mat(original_mat)

            relative_pos = valve12_pos - pivot_pos
            valve12_geom.set_pos(relative_pos)

            saved_pos = valve12_geom.get_pos()
            valve12_geom.set_pos(0, 0, 0)

            valve12_geom.set_pos(saved_pos)
            self.valve12.name = "Промывка пенодозатора"
            self.valve12_pivot.set_p(0)
            self.valve12_target_angle = 85
            self.valve12_moving = False
            self.valve12_direction = 1


        valve111_geom = self.model.find("**/COMPOUND11")
        point111 = self.model.find("**/point9.003")
        self.valve111_geom = valve111_geom
        if valve111_geom.is_empty():
            print("❌ 888Рычаг не найден!")
        else:
            print("✅ 8Рычаг найден")

            pivot_node = self.model.find("**/point9.003")
            if pivot_node.is_empty():
                print("❌ 11Точка крепления не найдена!")
                return


            original_mat = valve111_geom.get_mat(self.model)
            pivot_pos = pivot_node.get_pos(self.model)
            valve111_pos = valve111_geom.get_pos(self.model)


            self.valve111_root = self.model.attach_new_node("valve111_root")
            self.valve111_root.set_pos(pivot_pos)


            self.valve111_pivot = self.valve111_root.attach_new_node("valve111_pivot")


            valve111_geom.reparent_to(self.valve111_pivot)
            self.valve111 = valve111_geom
            valve111_geom.set_mat(original_mat)

            relative_pos = valve111_pos - pivot_pos
            valve111_geom.set_pos(relative_pos)

            saved_pos = valve111_geom.get_pos()
            valve111_geom.set_pos(0, 0, 0)

            valve111_geom.set_pos(saved_pos)
            self.valve111.name = "Забор ПО"
            self.valve111_pivot.set_r(0)
            self.valve111_target_angle = 85
            self.valve111_moving = False
            self.valve111_direction = 1

        # valve2_geom = self.model.find("**/COMPOUND1")
        # print(111)
        # print(valve2_geom)
        # point5 = self.model.find("**/point5")
        #
        # if valve2_geom.is_empty() or point5.is_empty():
        #     print("❌ Вентиль 2 или точка вращения не найдены!")
        # else:
        #     print("✅ Вентиль 2 и точка вращения найдены")
        #
        #     # Получаем начальные трансформации
        #     original_mat = valve2_geom.get_mat(self.model)
        #     pivot_pos = point5.get_pos(self.model)
        #     valve2_pos = valve2_geom.get_pos(self.model)
        #     valve2_hpr = valve2_geom.get_hpr(self.model)  # Сохраняем начальные углы поворота
        #
        #     # Создаем иерархию узлов
        #     self.valve2_root = self.model.attach_new_node("valve2_root")
        #     self.valve2_root.set_pos(pivot_pos)
        #
        #     self.valve2_pivot = self.valve2_root.attach_new_node("valve2_pivot")
        #     self.valve2_pivot.set_pos(0, 0, 0)
        #
        #     # Переносим геометрию с сохранением трансформации
        #     valve2_geom.wrt_reparent_to(self.valve2_pivot)
        #     self.valve2 = valve2_geom
        #     valve2_geom.set_mat(original_mat)
        #
        #     # Устанавливаем относительную позицию
        #     relative_pos = valve2_pos - pivot_pos
        #     valve2_geom.set_pos(relative_pos)
        #
        #     # Восстанавливаем начальный поворот (45 градусов)
        #     valve2_geom.set_hpr(valve2_hpr)
        #
        #     # Настройки вращения
        #     self.valve2.name = 'Левая напорная задвижка'
        #     self.valve2_pivot.set_p(0)  # Сброс начального угла вращения
        #     self.valve2_target_angle = 90  # Угол поворота
        #     self.valve2_moving = False
        #     self.valve2_direction = 1
        #
        #     # Отладочный маркер
        #     self.debug_marker = self.loader.loadModel("models/smiley")
        #     self.debug_marker.reparent_to(self.render)
        #     self.debug_marker.set_pos(pivot_pos)
        #     self.debug_marker.set_scale(0.1)
        #     self.debug_marker.set_color(1, 0, 0, 1)

        valve99_geom = self.model.find("**/COMPOUND99")
        self.valve99_geom = valve99_geom
        if valve99_geom.is_empty():
            print("❌ 99Рычаг не найден!")
        else:
            print("✅ 99Рычаг найден")

            pivot_node = self.model.find("**/point7")
            if pivot_node.is_empty():
                print("❌ 7Точка крепления не найдена!")
                return

            original_mat = valve99_geom.get_mat(self.model)
            pivot_pos = pivot_node.get_pos(self.model)
            valve99_pos = valve99_geom.get_pos(self.model)

            self.valve99_root = self.model.attach_new_node("valve99_root")
            self.valve99_root.set_pos(pivot_pos)

            self.valve99_pivot = self.valve99_root.attach_new_node("valve99_pivot")

            valve99_geom.reparent_to(self.valve99_pivot)
            self.valve99 = valve99_geom
            valve99_geom.set_mat(original_mat)

            relative_pos = valve99_pos - pivot_pos
            valve99_geom.set_pos(relative_pos)

            saved_pos = valve99_geom.get_pos()
            valve99_geom.set_pos(0, 0, 0)

            valve99_geom.set_pos(saved_pos)
            self.valve99.name = "Кран пеносмесителя"
            self.valve99_pivot.set_p(0)
            self.valve99_target_angle = 85
            self.valve99_moving = False
            self.valve99_direction = 1

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

            self.valve6_pivot.set_p(41.3)
            self.valve6_angle = 0
            self.valve6_start_angle = 0
            self.valve6_target_angle = 0

            tmp_node = self.valve6_pivot.attach_new_node("tmp_for_bounds")
            valve6_geom.instance_to(tmp_node)

            tmp_node.set_pos(0, 0, 0)
            tmp_node.flatten_light()

            print("🧩 Добавляю задачу MoveValve6Task")
        #            self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")

        valve66_geom = self.model.find("**/Manovakuummetr_Arrow")
        if valve66_geom.is_empty():
            print("❌ Manometr_Arrow не найден.")
            self.valve66 = None
            self.valve66_pivot = None
        else:
            print("✅ Manometr_Arrow найден.")

            pivot_node = self.model.find("**/point2")
            if pivot_node.is_empty():
                print("❌ Точка point2 не найдена.")
                return

            pivot_world = pivot_node.get_pos(render)
            valve66_world = valve66_geom.get_pos(render)

            self.valve66_root = self.model.attach_new_node("valve66_root")
            self.valve66_root.set_pos(render, pivot_world)

            self.valve66_pivot = self.valve66_root.attach_new_node("valve66_pivot")

            valve66_geom.wrt_reparent_to(self.valve66_pivot)
            self.valve66 = valve66_geom
            relative_pos = valve66_world - pivot_world
            valve66_geom.set_pos(relative_pos)

            self.valve66_pivot.set_p(0)
            # self.valve66_angle = 41.3
            # self.valve66_start_angle = 41.3
            # self.valve66_target_angle = 41.3

            tmp_node = self.valve66_pivot.attach_new_node("tmp_for_bounds")
            valve66_geom.instance_to(tmp_node)

            tmp_node.set_pos(0, 0, 0)
            tmp_node.flatten_light()

            # self.valve66_angle = 0
            # self.valve66_start_angle = 0
            # self.valve66_target_angle = 0
            # self.valve66_moving = False

            print("🧩 Добавляю задачу MoveValve66Task")
            self.taskMgr.add(self.move_valve66_task, "MoveValve66Task")

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
        # self.disableMouse()#

        self.preview_cam_distance = 1.5
        self.preview_cam_min_distance = 0.5
        self.preview_cam_max_distance = 3.0
        self.preview_cam_zoom_speed = 1.0

        self.preview_buffer = None
        self.preview_card = None
        self.setup_gui(font)

    # def create_outline(obj, color=(1, 0, 0, 1), thickness=1.03):
    #     """Создает контур вокруг объекта"""
    #     outline = obj.copy_to(obj.get_parent())
    #     outline.set_scale(thickness)
    #     outline.set_color(color)
    #     outline.set_transparency(TransparencyAttrib.M_alpha)
    #     outline.set_light_off(True)  # Игнорировать освещение
    #     outline.set_render_mode_wireframe()  # Контурный вид
    #     return outline


    # def show_effect(self, effect, geom):
    #     if effect == water:
    #         self.geom.setShader(self.water_shader)
    #         self.geom.setTransparency(TransparencyAttrib.MAlpha)
    #         self.geom.setShaderInput("time", 0.0)
    #
    #     elif effect = foam:
    #         self.geom.setShader(self.water_shader)
    #         self.geom.setTransparency(TransparencyAttrib.MAlpha)
    #         self.geom.setShaderInput("time", 0.0)
    #
    #
    #
    # def show_effect(self, geom):
    #     geom.setShaderOff()
    #     geom.setTransparency(TransparencyAttrib.MNone)
    #     geom.setDepthWrite(True)
    #     geom.clearBin()
    #     geom.clearShaderInputs()

    def show_effect(self, effect, geom, duration=5.0):
        self.original_shader = geom.getShader()
        self.original_transparency = geom.getTransparency()
        self.original_depth_write = geom.getDepthWrite()

        if effect == "water":
            print(self .pipe)
            geom.setShader(self.water_shader)
            geom.setTransparency(TransparencyAttrib.MAlpha)
            geom.setBin("fixed", 40)  # Важно добавить!
            geom.setDepthWrite(False)
            geom.setShaderInput("time", 0.0)

        elif effect == "foam":
            geom.setShader(self.foam_shader)  # Исправлено: должно быть foam_shader
            geom.setTransparency(TransparencyAttrib.MAlpha)
            geom.setBin("fixed", 40)  # Важно добавить!
            geom.setDepthWrite(False)
            geom.setShaderInput("time", 0.0)

        # Запускаем таймер для автоматического выключения через 5 секунд
        taskMgr.doMethodLater(duration, lambda task: self.hide_effect(geom, task), "hide_effect_task")

    def hide_effect(self, geom, task):
        # Восстанавливаем оригинальные настройки
        geom.setShaderOff()
        geom.setTransparency(TransparencyAttrib.MNone)
        geom.setDepthWrite(True)
        geom.clearBin()
        #geom.clearShaderInputs()

        return task.done  # Обязательно возвращаем task.done

    def apply_water_effect(self, pipe):
        """Применяем эффект воды к трубе"""
        from panda3d.core import TransparencyAttrib

        # 1. Делаем трубу полупрозрачной
        pipe.set_transparency(TransparencyAttrib.M_alpha)

        # 2. Устанавливаем синий цвет воды
        pipe.set_color(0.3, 0.5, 0.8, 0.6)  # R, G, B, A

        # 3. Загружаем текстуру воды (если есть)
        try:
            water_tex = loader.loadTexture("models/water_texture.jpg")
            pipe.set_texture(water_tex)
        except:
            print("Текстура воды не найдена, используем простой цвет")

        # 4. Запускаем анимацию течения
        self.start_water_animation(pipe)

    # def setup_water_pipe(self):
    #     """Простая настройка трубы с водой (без текстуры)"""
    #     pipe = self.pipe
    #
    #     if pipe and not pipe.is_empty():
    #         from panda3d.core import TransparencyAttrib
    #
    #         # Просто устанавливаем цвет и прозрачность
    #         pipe.set_transparency(TransparencyAttrib.M_alpha)
    #         pipe.set_color(0.2, 0.4, 0.8, 0.6)  # Синий, полупрозрачный

    def load_sounds(self):
        self.sounds = {}
        self.bg_music_playing = False

        # Предзагрузка звуков (если нужно)
        self.sounds["bg"] = loader.loadSfx("media/audio1.mp3")
        self.sounds["bg"].setLoop(True)
        self.sounds["bg"].setVolume(0.5)

        self.sounds["s1_a1"] = loader.loadSfx("media/s1/audio2.mp3")
        self.sounds["s1_a2"] = loader.loadSfx("media/s1/audio4.mp3")
        self.sounds["s2_a1"] = loader.loadSfx("media/s2/audio1.mp3")
        self.sounds["s2_a2"] = loader.loadSfx("media/s2/audio2.mp3")

    def play_sound(self, sound_path, loop=False, volume=1.0):
        if sound_path not in self.sounds:
            self.sounds[sound_path] = loader.loadSfx(sound_path)

        sound = self.sounds[sound_path]
        sound.setLoop(loop)
        sound.setVolume(volume)
        sound.play()
        return sound

    def stop_sound(self, sound_path):
        if sound_path in self.sounds:
            self.sounds[sound_path].stop()

    def start_background_music(self):
        if not self.bg_music_playing:
            self.play_sound("media/audio1.mp3", loop=True, volume=0.5)
            self.bg_music_playing = True

    def stop_background_music(self):
        self.stop_sound("media/audio1.mp3")
        self.bg_music_playing = False

    def play_delayed_sound(task, sound_path):
        self.play_sound(sound_path)
        return task.done

    def toggle_fullscreen(self):
        props = WindowProperties()
        props.setFullscreen(not self.win.getProperties().getFullscreen())
        props.setCursorHidden(not props.getFullscreen())
        self.win.requestProperties(props)

    def start_blink(self, task):
        t = globalClock.get_frame_time()
        blink = int(t * 2) % 2
        if blink:
            self.plane11.set_color_scale(1, 0, 0, 1)
        else:
            self.plane11.set_color_scale(1, 1, 1, 1)

        if task.time > 4.0:
            self.plane11.set_color_scale(1, 1, 1, 1)
            return task.done

        return task.cont

    def start_blink10(self, task):
        t = globalClock.get_frame_time()
        blink = int(t * 2) % 2

        if blink:
            self.plane10.set_color_scale(1, 0, 0, 1)
        else:
            self.plane10.set_color_scale(1, 1, 1, 1)


        if task.time > 4.0:
            self.plane10.set_color_scale(1, 1, 1, 1)
            return task.done

        return task.cont

    def stop_blink(self, task):
        self.plane11.set_color_scale(1, 1, 1, 1)
        self.plane10.set_color_scale(1, 1, 1, 1)
        return task.done


    def toggle_background_music(self):

        if self.bg_music_playing:
            print(self.bg_music_playing)
            self.stop_background_music()

        else:
            self.start_background_music()

    def create_menu_panel(self):

        self.menu_panel = DirectFrame(
            parent=self.aspect2d,
            frameColor=(0.1, 0.1, 0.15, 0.95),
            frameSize=(-5, 5, -3, 3),
            pos=(0, 0, 0),
            state=DirectGui.DGG.NORMAL
        )

    def setup_gui(self, font):
        self.bottom_panel = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-1.5, 1.5, -0.15, 0.15),
            pos=(0, 0, -0.85),
            relief=DirectGui.DGG.SUNKEN,
            borderWidth=(0.01, 0.01),
            state=DirectGui.DGG.NORMAL
        )

        self.main_menu_btn = DirectButton(
            parent=self.aspect2d,
            text="Главное меню",
            text_font=font,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.08, 0.08, 0.12, 0.85),
            frameSize=(-4, 4, -0.9, 0.9),
            scale=0.04,
            pos=(-1.5, 0, 0.9),
            relief=1,
            borderWidth=(0.015, 0.015),
            text_align=TextNode.A_center,
            pressEffect=1,
            rolloverSound=None,
            clickSound=None,
        )
        self.main_menu_btn.setTransparency(True)


        self.left_panel = DirectFrame(
            frameColor=(0.08, 0.08, 0.12, 0.85),
            frameSize=(-0.3, 0.54, -0.97, 0.455),
            pos=(-1.75, 0, 0.35),
            relief=DirectGui.DGG.RAISED,
            borderWidth=(0.015, 0.015),
            state=DirectGui.DGG.NORMAL
        )


        self.scenario_label = DirectLabel(
            parent=self.bottom_panel,
            text="Подача воды от цистерны",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            text_shadow=(0, 0, 0, 0.7),
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
            pos=(0, 0, -0))

        self.current_scenario = 0
        self.current_step = 0
        self.training_mode = False
        self.auto_mode = False
        self.update_scenario_display()

        # self.prev_btn = DirectButton(
        #     parent=self.bottom_panel,
        #     text="<",
        #     text_font=font,
        #     text_align=TextNode.A_center,
        #     text_fg=(1, 1, 1, 1),
        #     frameColor=(0.2, 0.2, 0.2, 0.7),
        #     scale=0.05,
        #     pos=(-1.4, 0, 0),
        #     relief=1,
        #     command=self.prev_scenario)
        #
        # self.next_btn = DirectButton(
        #     parent=self.bottom_panel,
        #     text=">",
        #     text_font=font,
        #     text_align=TextNode.A_center,
        #     text_fg=(1, 1, 1, 1),
        #     frameColor=(0.2, 0.2, 0.2, 0.7),
        #     scale=0.05,
        #     pos=(1.4, 0, 0),
        #     relief=1,
        #     command=self.next_scenario)

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
            # command=self.first_scenario)
            command=self.start_selected_scenario)

        self.next_step_btn = DirectButton(
            parent=self.aspect2d,
            text="Следующий шаг",
            text_font=font,
            text_align=TextNode.A_center,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.5, 0.2, 0.7),
            scale=0.05,
            pos=(0, 0, -0.75),
            relief=1,
            command=self._execute_next_step)

        self.next_step_btn.hide()

    def start_selected_scenario(self):
        self.start_btn.hide()
        self.next_step_btn.show()

        """Запускает выбранный сценарий через лямбда-функции"""
        if self.current_scenario == 0:
            self.start_first_scenario()
        if self.current_scenario == 1:
            self.start_second_scenario()
        if self.current_scenario == 2:
            self.start_third_scenario()
        if self.current_scenario == 3:
            self.start_fourth_scenario()
        if self.current_scenario == 4:
            self.start_fifth_scenario()
        if self.current_scenario == 5:
            self.start_sixth_scenario()
        if self.current_scenario == 6:
            self.start_seven_scenario()
        if self.current_scenario == 7:
            self.start_eight_scenario()
        if self.current_scenario == 8:
            self.start_nineth_scenario()
        if self.current_scenario == 9:
            self.start_ten_scenario()
        if self.current_scenario == 10:
            self.start_eleventh_scenario()
        if self.current_scenario == 11:
            self.start_twelfth_scenario()




        self._execute_next_step()

    def recolor_object(self, valve_geom, recolor=1):
        try:
            if recolor == 1:
                if not valve_geom.is_empty():
                    self.add_outline_shader(valve_geom)

            else:
                valve_geom.set_shader_off()
                valve_geom.set_transparency(TransparencyAttrib.M_none)
        except Exception as e:
            print(f"⚠️ Ошибка при перекрашивании: {str(e)}")



    def add_outline_shader(self, valve_geom, alpha=0.3):
        """Добавляет обводку через шейдер с управляемой прозрачностью"""
        from panda3d.core import Shader

        vertex_shader = """
        #version 130
        void main() {
            gl_Position = ftransform();
        }
        """

        fragment_shader = """
        #version 130
        uniform vec3 outline_color;
        uniform float alpha;
        void main() {
            gl_FragColor = vec4(outline_color, alpha);
        }
        """

        shader = Shader.make(Shader.SL_GLSL, vertex_shader, fragment_shader)
        valve_geom.set_shader(shader)
        valve_geom.set_shader_input("outline_color", (1, 0.4, 0.5))  # Только RGB
        valve_geom.set_shader_input("alpha", alpha)  # Прозрачность отдельно
        valve_geom.set_transparency(TransparencyAttrib.M_alpha)


    def remove_outline(self, outline_node):
        """Удаляет обводку"""
        if outline_node:
            outline_node.remove_node()

    def start_first_scenario(self):
        self.training_mode = True
        self.auto_mode = True


        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека", lambda: self.rotate_valve1(1)),
            ("Откройте задвижку «На лафетный ствол» или «Из цистерны»""", lambda: self.rotate_valve5(1)),
            ("Откройте задвижку «Из цистерны» или «На лафетный ствол»", lambda: self.rotate_valve4(1)),
            ("Закройте задвижку «На лафетный ствол»", lambda: self.rotate_valve5(-1)),
            ("Включите сцепление (стрелка манометра до 3 атм)", lambda: self.rotate_valve1_with_camera(1)),
            ("Откройте напорную задвижку", lambda: self.rotate_valve2(1)),
            ("Поднимите давление до 6 атм", lambda: self.rotate_valve11(1)),
            ("Сценарий завершен", self.end)
        ]
        self.current_step_index = 0

    def end(self):
        self.step_label['text'] = ""
        self.start_btn.show()

    def start_second_scenario(self):
        self.training_mode = True
        self.auto_mode = True

        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека или откройте вакуумный кран",
             lambda: self.rotate_valve1(1)),
            ("Откройте вакуумный кран или выключите сцепление из насосного отсека",
             lambda: self.rotate_valve8(1)),
            (
                "Нажмите кнопку вакуумного насоса (13) — стрелка мановакууметра опустится до -0,6 атм.",
                lambda: self.blink_valve13(1)),
            ("Отпустите кнопку и закройте вакуумный кран (4)»",
             lambda: self.rotate_valve8(-1)),
            ("Включите сцепление(стрелка манометра поднимается до 3атм)",
             lambda: self.rotate_valve1_with_camera(1)),
            ("Откройте напорную задвижку",
             lambda: self.rotate_valve2(1)),
            (
                "Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 6 атм",
                lambda: self.rotate_valve11(1)),
            (
                "Сценарий завершен",
                lambda: self.end()),

        ]
        self.current_step_index = 0


    def start_third_scenario(self):
        self.training_mode = True
        self.auto_mode = True
        print('исправить 1010 строка еще и монометр')
        self.scenario_sequence = [

            ("Выключите сцепление из насосного отсека или Откройте задвижку «В цистерну»",
                                        lambda: self.rotate_valve1(1)),
            ("Откройте задвижку «В цистерну» или Выключите сцепление из насосного отсек",
                                        lambda: self.rotate_valve13(1)),

            ("Включите сцепление(стрелка мановаууметра поднимается до 3атм)",
                                        lambda: self.rotate_valve66_with_camera(1, 3)),
            (
                "",
                lambda: self.end()),
        ]
        self.current_step_index = 0


    def start_fourth_scenario(self):
        self.training_mode = True
        self.auto_mode = True

        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека",
                                        lambda: self.rotate_valve1(1)),
            ("Откройте задвижку «На лафетный ствол» или «Из цистерны»",
                                        lambda: self.rotate_valve5(1)),
            ("Откройте задвижку «Из цистерны» или «На лафетный ствол»",
                                        lambda: self.rotate_valve4(1)),
            ("Включите сцепление(стрелка манометра поднимается до 3атм)",
                                        lambda: self.rotate_valve1_with_camera(1)),
            (
                "Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 6 атм",
                lambda: self.rotate_valve11(1)),
            (
                "Конец сценария",
                lambda: self.end()),
        ]
        self.current_step_index = 0


    def start_fifth_scenario(self):
        self.training_mode = True
        self.auto_mode = True

        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека",
             lambda: self.rotate_valve1(1)),
            ("Установите дозатор (6) в положение «3» ",
             lambda: self.rotate_valve44(1)),
            ("Откройте задвижку «Из цистерны» или «На лафетный ствол»",
             lambda: self.rotate_valve4(1)),
            ("Откройте задвижку «На лафетный ствол» или «Из цистерны»",
             lambda: self.rotate_valve5(1)),
            (
                "Откройте задвижку «ПО из пенобака»",
                lambda: self.rotate_valve111(1)),
            ("Включите сцепление(стрелка манометра поднимается до 3атм)",
             lambda: self.rotate_valve1_with_camera(1)),
            ("Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 6 атм",
             lambda: self.rotate_valve11(1)),
            (" Уменьшите давление до 3 атм. кнопкой (15).    ",
                lambda: self.blink_plane10_camera(-1, end=1)),

            (
                " Откройте кран промывки пенодозатора (14).  ",
                lambda: self.rotate_valve12(1)),
            ("Установите дозатор (6) в поочередно в положение «1» «6» «1» «6» 4 раза",
             lambda: self.rotate_valve44(1, 10)),
            (
                " Закройте кран промывки пенодозатора (14).  ",
                lambda: self.rotate_valve12(-1)),
            (
                "Выключите сцепление (Стрелка манометра падает до 3 атм).  ",
                lambda: self.end()),
            (
                "Сценарий завершен ",
                lambda: self.end()),

        ]

        self.current_step_index = 0


    def start_sixth_scenario(self):
        self.training_mode = True
        self.auto_mode = True
        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека",
             lambda: self.rotate_valve1(1)),
            ("Установите дозатор (6) в положение «1»",
             lambda: self.rotate_valve44(1,1)),
            ("Откройте кран пеносмесителя (5). или «Из цистерны»",
                                        lambda: self.rotate_valve99(1)),
            ("Откройте задвижку «Из цистерны» или откройте кран пеносмесителя",
             lambda: self.rotate_valve4(1)),
            (
                "Откройте задвижку «ПО из пенобака»",
                lambda: self.rotate_valve111(1)),
            ("Включите сцепление(стрелка манометра поднимается до 3атм)",
             lambda: self.rotate_valve1_with_camera(1)),
            ("Откройте напорную задвижку",
             lambda: self.rotate_valve2(1)),

            ("Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 8 атм",
             lambda: self.rotate_valve11(1, eight=True)),
            (" Уменьшите давление до 3 атм. кнопкой (15).    ",
                lambda: self.blink_plane10_camera(-1, end=1)),

            (
                " Откройте кран промывки пенодозатора (14).  ",
                lambda: self.rotate_valve12(1)),
            ("Установите дозатор (6) в поочередно в положение «1» «6» «1» «6» 4 раза",
             lambda: self.rotate_valve44(1,10)),

            (
                " Закройте кран промывки пенодозатора (14).  ",
                lambda: self.rotate_valve12(-1)),
            (
                "Включите сцепление(стрелка манометра поднимается до 3атм)",
                 lambda: self.rotate_valve1_with_camera(1)),
            (
                "Сценарий завершен ",
                lambda: self.end()),

        ]
        self.current_step_index = 0

    def start_seven_scenario(self):
        self.training_mode = True
        self.auto_mode = True


        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека",
             lambda: self.rotate_valve1(1)),
            ("Откройте задвижку «Из цистерны» или «На лафетный ствол»", lambda: self.rotate_valve4(1)),
            ("Откройте задвижку «На лафетный ствол» или «Из цистерны»", lambda: self.rotate_valve5(1)),

            ("Закройте задвижку «На лафетный ствол»", lambda: self.rotate_valve5(-1)),
            ("Закройте задвижку «Из цистерны»", lambda: self.rotate_valve4(-1)),
            ("Включите сцепление(стрелка манометра поднимается до 3атм)",
             lambda: self.rotate_valve1_with_camera(1)),
            ("Откройте напорную задвижку",
             lambda: self.rotate_valve2(1)),
            ("Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 6 атм",
             lambda: self.rotate_valve11(1)),

            (
                "Сценарий завершен ",
                lambda: self.end()),


        ]

        self.current_step_index = 0

    def start_eight_scenario(self):
        self.training_mode = True
        self.auto_mode = True
        print(1)

        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека",
             lambda: self.rotate_valve1(1)),
            ("Откройте задвижку «Из цистерны» или «На лафетный ствол»", lambda: self.rotate_valve4(1)),
            ("Откройте задвижку «На лафетный ствол» или «Из цистерны»", lambda: self.rotate_valve5(1)),

            ("Закройте задвижку «На лафетный ствол»", lambda: self.rotate_valve5(-1)),
            ("Включите сцепление(стрелка манометра поднимается до 3атм)",
             lambda: self.rotate_valve1_with_camera(1)),
            ("Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 6 атм",
             lambda: self.rotate_valve11(1)),
            ("Откройте напорную задвижку",
             lambda: self.rotate_valve2(1)),
            ("Закройте задвижку «Из цистерны»", lambda: self.rotate_valve4(-1)),
            (
                "Сценарий завершен ",
                lambda: self.end()),


        ]

        self.current_step_index = 0

    def start_nineth_scenario(self):
        self.training_mode = True
        self.auto_mode = True

        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека",
             lambda: self.rotate_valve1(1)),
            ("Откройте задвижку «Из цистерны» или «В цистерну»", lambda: self.rotate_valve4(1)),
            ("Откройте задвижку «В цистерну» или «Из цистерну»",
             lambda: self.rotate_valve13(1)),
            ("Включите сцепление(стрелка манометра поднимается до 3атм)",
             lambda: self.rotate_valve1_with_camera(1)),
            ("Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 6 атм",
             lambda: self.rotate_valve11(1)),
            ("Закройте задвижку «Из цистерны»", lambda: self.rotate_valve4(-1)),
            ("Откройте напорную задвижку или Закрыть задвижку «В цистерну»",
             lambda: self.rotate_valve2(1)),
            ("Закрыть задвижку «В цистерну» или Откройте напорную задвижку",
             lambda: self.rotate_valve13(-1)),
            (
                "Сценарий завершен ",
                lambda: self.end()),
        ]

        self.current_step_index = 0


    def start_ten_scenario(self):
        self.training_mode = True
        self.auto_mode = True

        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека",
             lambda: self.rotate_valve1(1)),
            ("Откройте задвижку «Из цистерны» или «На лафетный ствол»", lambda: self.rotate_valve4(1)),
            ("Откройте задвижку «На лафетный ствол» или «Из цистерны»", lambda: self.rotate_valve5(1)),
            ("Закройте задвижку «На лафетный ствол»", lambda: self.rotate_valve5(-1)),

            ("Включите сцепление(стрелка манометра поднимается до 3атм)",
             lambda: self.rotate_valve1_with_camera(1)),
            ("Откройте напорную задвижку на гидроэлеватор",
             lambda: self.rotate_valve2(1)),
            ("Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 9 атм",
             lambda: self.rotate_valve11(1, eight=True)),
            ("Откройте напорную задвижку на пожар",
             lambda: self.rotate_valve22(1)),

            (
                "Сценарий завершен ",
                lambda: self.end()),
        ]

        self.current_step_index = 0


    def start_eleventh_scenario(self):
        self.training_mode = True
        self.auto_mode = True

        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека",
             lambda: self.rotate_valve1(1)),
            ("Откройте задвижку «Из цистерны» или «На лафетный ствол»", lambda: self.rotate_valve4(1)),
            ("Откройте задвижку «На лафетный ствол» или «Из цистерны»", lambda: self.rotate_valve5(1)),
            ("Закройте задвижку «На лафетный ствол»", lambda: self.rotate_valve5(-1)),
            ("Включите сцепление(стрелка манометра поднимается до 3атм)",
             lambda: self.rotate_valve1_with_camera(1)),
            ("Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 9 атм",
             lambda: self.rotate_valve11(1, eight=True)),
            ("Закройте задвижку «Из цистерны»", lambda: self.rotate_valve4(-1)),
            ("Откройте напорную задвижку(неполностью)",
             lambda: self.rotate_valve2(1)),
            (
                "Сценарий завершен ",
                lambda: self.end()),
        ]

        self.current_step_index = 0


    def start_twelfth_scenario(self):
        self.training_mode = True
        self.auto_mode = True

        self.scenario_sequence = [
            ("Выключите сцепление из насосного отсека",
             lambda: self.rotate_valve1(1)),
            ("Откройте вакуумный кран",
             lambda: self.rotate_valve8(1)),
            (
                "Нажмите кнопку вакуумного насоса (13) — стрелка мановакууметра опустится до -0,76 атм.",
                lambda: self.blink_valve13(1)),
            ("Отпустите кнопку и закройте вакуумный кран (4)»",
             lambda: self.rotate_valve8(-1)),
            (
                "Сценарий завершен ",
                lambda: self.end()),

#            ("Откройте задвижку «Из цистерны»", lambda: self.rotate_valve4(1)),
#            ("Откройте задвижку «На лафетный ствол»", lambda: self.rotate_valve5(1)),
#            ("Закройте задвижку «На лафетный ствол»", lambda: self.rotate_valve5(-1)),
#            ("Включите сцепление(стрелка манометра поднимается до 3атм)",
#             lambda: self.rotate_valve1_with_camera(1)),
#            ("Кратковременными нажатиями кнопки увеличения оборотов двигателя поднимаем давления до 8 атм",
#             lambda: self.rotate_valve11(1, eight=True)),
#            ("Закройте задвижку «Из цистерны»", lambda: self.rotate_valve4(-1)),
#            ("Откройте напорную задвижку(неполностью)",
#             lambda: self.rotate_valve2(1)),
#            (
#                "Сценарий завершен ",
#                lambda: self.end()),
        ]

        self.current_step_index = 0



    def _execute_step(self, message, action):
        self.step_label['text'] = message
        self.current_action = action
        self.next_step_btn.show()

    def _execute_next_step(self):
        # Сразу скрываем кнопку
        self.next_step_btn.hide()

        if not hasattr(self, 'scenario_sequence'):
            return

        if self.current_step_index < len(self.scenario_sequence):
            message, action = self.scenario_sequence[self.current_step_index]

            self.step_label['text'] = message
            action()
            self.current_step_index += 1

            if self.current_step_index >= len(self.scenario_sequence):
                self._end_scenario()
            else:
                # Показываем кнопку через 5 секунд
                taskMgr.doMethodLater(5.0, self._show_next_button, "show_next_button")
        else:
            self._end_scenario()

    def _show_next_button(self, task):
        self.next_step_btn.show()
        return task.done

    def _end_scenario(self):
        self.step_label['text'] = "Сценарий завершен!"
        self.next_step_btn.hide()
        self.training_mode = False
        self.auto_mode = False


        if hasattr(self, 'scenario_sequence'):
            del self.scenario_sequence
        if hasattr(self, 'current_step_index'):
            del self.current_step_index

    def _execute_sequence(self, sequence, index=0):
        if index >= len(sequence):
            self.training_mode = False
            self.auto_mode = False
            return


        sequence[index]()

        if index + 1 < len(sequence):
            self.taskMgr.do_method_later(
                5.5,
                self._execute_sequence,
                f"scenario_step_{index}",
                extraArgs=[sequence, index + 1]
            )

    def add_decorative_elements(self):
        divider = DirectFrame(
            parent=self.bottom_panel,
            frameSize=(-1.55, 1.55, -0.005, 0.005),
            frameColor=(0.4, 0.6, 1.0, 0.8),
            pos=(0, 0, 0.12)
        )

        divider_bottom = DirectFrame(
            parent=self.bottom_panel,
            frameSize=(-1.55, 1.55, -0.003, 0.003),
            frameColor=(0.3, 0.5, 0.8, 0.6),
            pos=(0, 0, -0.1)
        )

        corner_size = 0.12
        corner_color = (0.4, 0.6, 1.0, 0.5)

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

        background_pattern = DirectFrame(
            parent=self.left_panel,
            frameSize=(-0.78, 0.78, -0.63, 0.63),
            frameColor=(0.15, 0.15, 0.2, 0.3),
            pos=(0, 0, 0)
        )

    def create_preview_camera(self, object_name, is_bottom=False):
        font = self.loader.load_font("arial.ttf")


        buffer_attr = 'preview_buffer_bottom' if is_bottom else 'preview_buffer_top'
        texture_attr = 'preview_texture_bottom' if is_bottom else 'preview_texture_top'
        card_attr = 'preview_card_bottom' if is_bottom else 'preview_card_top'
        label_attr = 'preview_label_bottom' if is_bottom else 'preview_label_top'
        cam_np_attr = 'preview_cam_np_bottom' if is_bottom else 'preview_cam_np_top'


        if getattr(self, buffer_attr, None):
            getattr(self, buffer_attr).remove_all_display_regions()
            self.graphicsEngine.remove_window(getattr(self, buffer_attr))


        target_node = self.model.find(f"**/{object_name}")
        if target_node.is_empty() and object_name in self.logical_parts:
            target_node = self.model.find(self.logical_parts[object_name])
        if target_node.is_empty():
            print(f"⚠️ Объект {object_name} не найден")
            return


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


        texture = Texture()
        buffer.add_render_texture(texture, GraphicsOutput.RTMCopyRam)
        setattr(self, texture_attr, texture)


        lens = OrthographicLens()
        lens.set_film_size(0.4, 0.4)
        preview_cam = self.make_camera(buffer, lens=lens)
        cam_np = NodePath(preview_cam)
        cam_np.reparent_to(render)


        setattr(self, cam_np_attr, cam_np)


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


        cm = CardMaker(f"{'bottom_' if is_bottom else 'top_'}preview_card")
        cm.set_frame(-0.48, 0.48, -0.48, 0.48)

        card = self.aspect2d.attach_new_node(cm.generate())
        card.set_texture(texture)
        card.set_pos(-1.55, 0, -0.28 if is_bottom else 0.47)
        card.set_scale(0.7)
        setattr(self, card_attr, card)


        label = DirectLabel(
            parent=self.aspect2d,
            text=f"{object_name if object_name != "Manometr_Arrow" else "Манометр"}",
            text_font=font,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            scale=0.045,
            pos=(-1.5, 0, 0.07 if is_bottom else 0.81),
            text_align=TextNode.A_center
        )
        setattr(self, label_attr, label)


        self.taskMgr.do_method_later(5, lambda task: self.destroy_preview_camera(is_bottom),
                                     f"DestroyPreviewCamera_{'bottom' if is_bottom else 'top'}")

    def destroy_preview_camera(self, is_bottom=False):
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
        if not self.preview_cam_np:
            return

        bounds = target_node.get_bounds()
        center = bounds.get_center()
        radius = bounds.get_radius()

        self.preview_cam_np.set_pos(center + Vec3(0, -self.preview_cam_distance * radius, radius * 0.3))
        self.preview_cam_np.look_at(center)

    def reset_plane14_color(self, task):
        self.plane14.clear_color_scale()
        return task.done

    def reset_plane10_color(self, task):
        self.plane10.clear_color_scale()
        return task.done

    def reset_plane3_color(self, task):
        self.plane3.clear_color_scale()
        return task.done

    def reset_plane11_color(self, task):
        self.plane11.clear_color_scale()
        return task.done

    def move_valve2_task(self, task):
        if not hasattr(self, 'valve2_pivot') or not self.valve2_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve2_start_time
        progress = min(elapsed / 2.0, 1.0)  # 2 секунды на поворот

        # Вращение ВОКРУГ ЛОКАЛЬНОЙ ОСИ Y (как у valve13)
        angle = progress * self.valve2_target_angle * self.valve2_direction
        self.valve2_pivot.set_p(angle)  # Используем set_h() вместо set_p()

        if progress >= 1.0:
            self.valve2_moving = False
            return task.done

        return task.cont
    def move_valve22_task(self, task):
        if not hasattr(self, 'valve22_pivot') or not self.valve22_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve22_start_time
        progress = min(elapsed / 5, 1.0)

        if self.valve22_direction > 0:
            target_angle = self.valve22_target_angle
        else:
            target_angle = 0

        new_angle = progress * target_angle
        self.valve22_pivot.set_p(new_angle)

        if progress >= 1.0:
            self.valve22_moving = False
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

            if self.valve5_direction > 0:
                self.valve5_is_open = True
            else:
                self.valve5_is_open = False

            if self.training_mode:
                self.on_step_completed()

                self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
            return task.done

        return task.cont

    def move_valve99_task(self, task):
        if not hasattr(self, 'valve99_pivot') or not self.valve99_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve99_start_time
        progress = min(elapsed / 5, 1.0)

        angle_change = progress * self.valve99_target_angle_change
        new_angle = self.valve99_start_angle + angle_change
        self.valve99_pivot.set_p(new_angle)

        if progress >= 1.0:
            self.valve99_moving = False
            self.valve99_current_angle = new_angle
            if self.valve99_direction > 0:
                self.valve99_is_open = True
            else:
                self.valve99_is_open = False

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

            if self.valve8_direction > 0:
                self.valve8_is_open = True
            else:
                self.valve8_is_open = False

            if self.training_mode:
                self.on_step_completed()

                self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
            return task.done

        return task.cont

    def move_valve12_task(self, task):
        if not hasattr(self, 'valve12_pivot') or not self.valve12_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve12_start_time
        progress = min(elapsed / 5, 1.0)

        angle_change = progress * self.valve12_target_angle_change
        new_angle = self.valve12_start_angle + angle_change
        self.valve12_pivot.set_p(new_angle)

        if progress >= 1.0:
            self.valve12_moving = False
            self.valve12_current_angle = new_angle

            if self.valve12_direction > 0:
                self.valve12_is_open = True
            else:
                self.valve12_is_open = False

            if self.training_mode:
                self.on_step_completed()

                self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
            return task.done

        return task.cont

    def move_valve111_task(self, task):
        if not hasattr(self, 'valve111_pivot') or not self.valve111_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve111_start_time
        progress = min(elapsed / 5, 1.0)

        angle_change = progress * self.valve111_target_angle_change
        new_angle = self.valve111_start_angle + angle_change
        self.valve111_pivot.set_r(new_angle)

        if progress >= 1.0:
            self.valve111_moving = False
            self.valve111_current_angle = new_angle

            if self.valve111_direction > 0:
                self.valve111_is_open = True
            else:
                self.valve111_is_open = False

            if self.training_mode:
                self.on_step_completed()

                self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
            return task.done

        return task.cont

    def move_valve6_task(self, task):
        if not hasattr(self, 'valve6_pivot') or not self.valve6_moving:
            return task.done

        elapsed = globalClock.getFrameTime() - self.valve6_start_time
        progress = min(elapsed / 2.0, 1.0)


        new_angle = self.valve6_start_angle + progress * (self.valve6_target_angle - self.valve6_start_angle)

        self.valve6_pivot.set_p(-new_angle)

        if progress >= 1.0:
            self.valve6_moving = False
            self.valve6_angle = self.valve6_target_angle
            if self.training_mode:
                self.on_step_completed()
                self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
            return task.done

        return task.cont

    def move_valve66_task(self, task):
        if not hasattr(self, 'valve66_pivot') or not hasattr(self, 'valve66'):
            return task.done

        if self.valve66_moving:
            elapsed = globalClock.getFrameTime() - self.valve66_start_time
            progress = min(elapsed / 2.0, 1.0)


            start_angle = self.valve66_start_angle
            target_angle = self.valve66_target_angle
            new_angle = start_angle + (target_angle) * progress


            self.valve66_pivot.set_p(-new_angle)

            if progress >= 1.0:
                self.valve66_moving = False
                self.valve66_angle = target_angle
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


    def move_valve44_task(self, task):
        if not hasattr(self, 'valve44_pivot') or not self.valve44_moving:
            return task.done


        if hasattr(self, 'valve44_sequence'):
            current_seq = self.valve44_sequence[self.valve44_sequence_index]
            elapsed = globalClock.getFrameTime() - self.valve44_start_time
            progress = min(elapsed / current_seq["time"], 1.0)


            target_angle = self.calculate_angle_for_position(current_seq["target"])
            start_angle = self.calculate_angle_for_position(1 if current_seq["target"] == 6 else 6)
            new_angle = start_angle + progress * (target_angle - start_angle)

            self.valve44_pivot.set_p(new_angle)

            if progress >= 1.0:
                self.valve44_sequence_index += 1
                if self.valve44_sequence_index >= len(self.valve44_sequence):
                    self.valve44_moving = False
                    del self.valve44_sequence
                    del self.valve44_sequence_index
                    if self.training_mode:
                        self.on_step_completed()
                        self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")
                    return task.done
                else:
                    self.valve44_start_time = globalClock.getFrameTime()
                    return task.cont
            return task.cont


        elapsed = globalClock.getFrameTime() - self.valve44_start_time
        progress = min(elapsed / 5, 1.0)  # 5 секунд на поворот

        new_angle = progress * self.valve44_target_angle
        self.valve44_pivot.set_p(new_angle)

        if progress >= 1.0:
            self.valve44_moving = False
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
        # self.step_label['text'] = "Нажмите Старт для начала"

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
        if not self._scenario_running:
            return

        scenario = self.scenarios[self.current_scenario]


        if self._current_task:
            taskMgr.remove(self._current_task)
            self._current_task = None


        if scenario.get('type') == 'method':
            method = getattr(self, scenario['method'])
            method()
            return


        if self.current_step >= len(scenario['steps']):
            self._finish_scenario()
            return

        step = scenario['steps'][self.current_step]
        self.step_label['text'] = step['message']

        if step['action'] == 'rotate_valve':
            valve_method = getattr(self, f'rotate_valve{step["valve"]}')
            valve_method(step['direction'])

            self._current_task = taskMgr.doMethodLater(
                step['duration'],
                self._next_step_handler,
                "ScenarioStep"
            )

    def _next_step_handler(self, task):
        if not self._scenario_running:
            return task.done

        self.current_step += 1
        self.execute_current_step()
        return task.done

    def _finish_scenario(self):
        self._scenario_running = False
        self.training_mode = False
        self.auto_mode = False

        if self._current_task:
            taskMgr.remove(self._current_task)
            self._current_task = None


    def next_scenario_step(self, task):
        self.current_step += 1
        self.execute_current_step()
        return task.done

    def blink_task(self, task):
        t = globalClock.get_frame_time()
        blink = int(t * 2) % 2

        if blink:
            self.plane11.set_color_scale(1, 0, 0, 1)
        else:
            self.plane11.set_color_scale(1, 1, 1, 1)

        return task.cont


    def blink_task10(self, task):
        t = globalClock.get_frame_time()
        blink = int(t * 2) % 2

        if blink:
            self.plane10.set_color_scale(1, 0, 0, 1)
        else:
            self.plane10.set_color_scale(1, 1, 1, 1)

        return task.cont

    def rotate_valve11(self, direction, eight = None):
        print("first stage")
        if hasattr(self, 'plane11'):
            print("second stage")
            self.taskMgr.add(self.start_blink, "BlinkTask")
            if hasattr(self, 'valve6_pivot'):
                if not hasattr(self, 'valve6_angle'):
                    self.valve6_angle = self.valve6_pivot.get_h()
                if eight is not None:
                    angle_plus = 55
                else:
                    angle_plus = 30
                angle_change = 30 * direction
                angle_change = angle_plus + angle_change
                self.valve6_target_angle = (self.valve6_angle + angle_change) % 360
                self.valve6_start_angle = self.valve6_angle
                self.valve6_moving = True
                self.valve6_start_time = globalClock.getFrameTime()

            self.play_sound("media/s1/audio4.mp3")
            self.create_preview_camera(self.plane11.name, is_bottom=False)
            print(self.plane11.name)

            self.create_preview_camera("Manometr_Arrow", is_bottom=True)

            self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")
            self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")

    def rotate_valve1_with_camera(self, direction,end = None):
        print(f"Вращаем вентиль 1, направление: {direction}")
        if hasattr(self, 'plane14'):
            self.plane14.set_color_scale(1, 0, 0, 1)
            self.taskMgr.do_method_later(3, self.reset_plane14_color, "ResetColor")

            if hasattr(self, 'valve6_pivot'):
                if not hasattr(self, 'valve6_angle'):
                    self.valve6_angle = self.valve6_pivot.get_h()

                angle_change = 19 * direction

                self.valve6_target_angle = (self.valve6_angle + angle_change) % 360
                print(  self.valve6_target_angle)
                if end is not None:
                    angle_change = -19
                    self.valve6_target_angle = 0
                else:
                    angle_change = 19 * direction
                    self.valve6_target_angle = (self.valve6_angle + angle_change) % 360

                self.valve6_start_angle = self.valve6_angle
                self.valve6_moving = True
                self.valve6_start_time = globalClock.getFrameTime()


            self.start_background_music()
            self.create_preview_camera(self.plane14.name, is_bottom=False)
            self.create_preview_camera("Manometr_Arrow", is_bottom=True)

            self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")

            self.taskMgr.do_method_later(5.0, self.next_scenario_step, "DelayedNextStep")

    def blink_plane10_camera(self, direction, end=None):
        print(f"Вращаем вентиль 1, направление: {direction}")
        if hasattr(self, 'plane10'):
            self.taskMgr.add(self.start_blink10, "BlinkTask")

            if hasattr(self, 'valve6_pivot'):
                if not hasattr(self, 'valve6_angle'):
                    self.valve6_angle = self.valve6_pivot.get_h()  # Текущий угол

                angle_change = 19 * direction

                self.valve6_target_angle = (self.valve6_angle + angle_change) % 360
                print(  self.valve6_target_angle)
                if end is not None:
                    angle_change = -19  # Фиксированное значение для обратного вращения
                    self.valve6_target_angle = 19  # Или другой целевой угол для обратного вращения
                else:
                    angle_change = 19 * direction
                    self.valve6_target_angle = (self.valve6_angle + angle_change) % 360

                self.valve6_start_angle = self.valve6_angle
                self.valve6_moving = True
                self.valve6_start_time = globalClock.getFrameTime()


            self.start_background_music()
            self.create_preview_camera(self.plane14.name, is_bottom=False)
            self.create_preview_camera("Manometr_Arrow", is_bottom=True)


            self.taskMgr.add(self.move_valve6_task, "MoveValve6Task")

            self.taskMgr.do_method_later(5.0, self.next_scenario_step, "DelayedNextStep")


    def rotate_valve66_with_camera(self, direction, kPa=3):
        print(f"Вращаем вентиль 1, направление: {direction}")
        if hasattr(self, 'plane14'):
            self.plane14.set_color_scale(1, 0, 0, 1)
            self.taskMgr.do_method_later(3, self.reset_plane14_color, "ResetColor")

            if hasattr(self, 'valve66_pivot'):
                if not hasattr(self, 'valve66_angle'):
                    self.valve66_angle = self.valve66_pivot.get_h()
                if kPa == 3:
                    angle_change = 135 * direction
                else:
                    angle_change = -18 * direction
                self.valve66_target_angle = (self.valve66_angle + angle_change) % 360
                self.valve66_start_angle = self.valve66_angle
                self.valve66_moving = True
                self.valve66_start_time = globalClock.getFrameTime()


            self.start_background_music()
            self.create_preview_camera(self.plane14.name, is_bottom=False)
            self.create_preview_camera("Manovakuummetr_Arrow", is_bottom=True)


            self.taskMgr.add(self.move_valve66_task, "MoveValve66Task")

            self.taskMgr.do_method_later(5.0, self.next_scenario_step, "DelayedNextStep")

    def rotate_valve1(self, direction):
        self.toggle_background_music()

        if hasattr(self, 'plane14'):
            self.plane14.set_shader_off()
            self.plane14.set_color_scale(1, 0, 0, 1)
            base.graphicsEngine.renderFrame()
            self.create_preview_camera(self.plane14.name)


            def update_camera(task):
                base.graphicsEngine.renderFrame()
                return task.done

            self.taskMgr.add(update_camera, 'force_render')
            self.taskMgr.do_method_later(3, self.reset_plane14_color, "ResetColor")
            self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")

    def blink_valve13(self, direction):
        if hasattr(self, 'plane3'):
            self.plane3.set_shader_off()
            self.plane3.set_color_scale(1, 0, 1, 1)
            self.play_sound("media/s2/audio1.mp3")

            if hasattr(self, 'valve66_pivot'):
                if not hasattr(self, 'valve66_angle'):
                    self.valve66_angle = self.valve66_pivot.get_p()

                angle_change = 10 * direction
                self.valve66_pivot.set_p(41.3)
                self.valve66_target_angle = (self.valve66_angle + angle_change) % 360
                self.valve66_start_angle = self.valve66_angle
                self.valve66_moving = True
                self.valve66_start_time = globalClock.getFrameTime()

            base.graphicsEngine.renderFrame()
            self.create_preview_camera(self.plane3.name)
            self.create_preview_camera("Manovakuummetr_Arrow", is_bottom=True)

            def update_camera(task):
                base.graphicsEngine.renderFrame()
                return task.done

            self.taskMgr.add(update_camera, 'force_render')
            self.play_sound("media/s1/audio2.mp3")
            self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")

    def stop_blink_valve13(self, direction):

        if hasattr(self, 'plane3'):
            self.taskMgr.do_method_later(0, self.reset_plane3_color, "ResetColor")

            def update_camera(task):
                base.graphicsEngine.renderFrame()
                return task.done

            self.taskMgr.add(update_camera, 'force_render')

            self.taskMgr.do_method_later(0.1, self.next_scenario_step, "DelayedNextStep")

    def rotate_valve2(self, direction):

        print(f"Вращаем вентиль 2, направление: {direction}")
        if hasattr(self, 'valve2_pivot'):
            #self.recolor_object(2)
            self.valve2_direction = direction
            self.valve2_moving = True
            self.valve2_start_time = globalClock.getFrameTime()
            self.create_preview_camera(self.valve2.name)
            self.recolor_object(self.valve2_geom, direction)
            self.show_effect("water", self.pipe_left)
            self.show_effect("water", self.pipe_left_high)
            self.taskMgr.add(self.move_valve2_task, "MoveValve2Task")


    def rotate_valve22(self, direction):
        if hasattr(self, 'valve22_pivot'):
            self.valve22_direction = direction
            self.valve22_moving = True
            self.valve22_start_time = globalClock.getFrameTime()
            self.create_preview_camera(self.valve22.name)
            self.recolor_object(self.valve22_geom, direction)
            self.taskMgr.add(self.move_valve22_task, "MoveValve22Task")

    def rotate_valve3(self, direction):
        if hasattr(self, 'valve3_pivot'):
            self.valve3_direction = direction
            self.valve3_moving = True
            self.valve3_start_time = globalClock.getFrameTime()
            self.create_preview_camera(self.valve3.name)
            self.taskMgr.add(self.move_valve3_task, "MoveValve3Task")

    def rotate_valve4(self, direction):
        if hasattr(self, 'valve4_pivot'):
            self.valve4_direction = direction
            self.valve4_moving = True
            self.valve4_start_time = globalClock.getFrameTime()
            self.create_preview_camera(self.valve4.name)
            self.play_sound("media/s1/audio2.mp3")
            self.recolor_object(self.valve4_geom, direction)
            self.show_effect("water", self.center_pipe0)
            self.show_effect("water", self.center_pipe1)
            self.show_effect("water", self.center_pipe2)

            self.taskMgr.add(self.move_valve4_task, "MoveValve4Task")

    def rotate_valve5(self, direction):
        print('точка входа')
        if hasattr(self, 'valve5_pivot'):
            if (direction > 0 and hasattr(self, 'valve5_is_open') and self.valve5_is_open) or \
                    (direction < 0 and hasattr(self, 'valve5_is_open') and not self.valve5_is_open):
                print('how')
                self.on_step_completed()
                return
            print('1')
            if not hasattr(self, 'valve5_current_angle'):
                self.valve5_current_angle = self.valve5_pivot.get_p()
            print('1')
            self.valve5_direction = direction
            self.valve5_moving = True
            self.valve5_start_time = globalClock.getFrameTime()
            self.valve5_start_angle = self.valve5_current_angle

            if direction > 0:
                self.valve5_target_angle_change = 85
                #self.show_effect("water", self.pipe_left)
                taskMgr.do_method_later(4, lambda task: self.show_effect("water", self.pipe_left), 'effect1')
                #self.show_effect("water", self.pipe_left_high)
                taskMgr.do_method_later(4, lambda task: self.show_effect("water", self.pipe_left_high), 'effect1')

            else:
                self.valve5_target_angle_change = -85


            self.recolor_object(self.valve5_geom,direction)
            self.create_preview_camera(self.valve5.name)
            self.taskMgr.add(self.move_valve5_task, "MoveValve5Task")


    def rotate_valve99(self, direction):
        if hasattr(self, 'valve99_pivot'):
            if (direction > 0 and hasattr(self, 'valve99_is_open') and self.valve99_is_open) or \
                    (direction < 0 and hasattr(self, 'valve99_is_open') and not self.valve99_is_open):
                self.on_step_completed()
                return

            if not hasattr(self, 'valve99_current_angle'):
                self.valve99_current_angle = self.valve99_pivot.get_p()

            self.valve99_direction = direction
            self.valve99_moving = True
            self.valve99_start_time = globalClock.getFrameTime()
            self.valve99_start_angle = self.valve99_current_angle

            if direction > 0:
                self.valve99_target_angle_change = 85
            else:
                self.valve99_target_angle_change = -85


            self.recolor_object(self.valve99_geom, direction)
            self.create_preview_camera(self.valve99.name)
            self.taskMgr.add(self.move_valve99_task, "MoveValve5Task")

    def rotate_valve111(self, direction):
        print(f"Вращаем рычаг (вентиль111), направление: {direction}")
        if hasattr(self, 'valve111_pivot'):
            if (direction > 0 and hasattr(self, 'valve111_is_open') and self.valve111_is_open) or \
                    (direction < 0 and hasattr(self, 'valve111_is_open') and not self.valve111_is_open):
                self.on_step_completed()
                return
            self.stop_blink_valve13(1)
            if not hasattr(self, 'valve111_current_angle'):
                self.valve111_current_angle = self.valve111_pivot.get_p()

            self.valve111_direction = direction
            self.valve111_moving = True
            self.valve111_start_time = globalClock.getFrameTime()
            self.valve111_start_angle = self.valve111_current_angle

            if direction > 0:
                self.valve111_target_angle_change = 180
            else:
                self.valve111_target_angle_change = -85

            self.play_sound("media/s1/audio2.mp3")

            self.create_preview_camera(self.valve111.name)
            self.recolor_object(self.valve111_geom, direction)
            self.taskMgr.add(self.move_valve111_task, "MoveValve111Task")

    def rotate_valve8(self, direction):
        print(f"Вращаем рычаг (вентиль8), направление: {direction}")
        if hasattr(self, 'valve8_pivot'):
            if (direction > 0 and hasattr(self, 'valve8_is_open') and self.valve8_is_open) or \
                    (direction < 0 and hasattr(self, 'valve8_is_open') and not self.valve8_is_open):
                self.on_step_completed()
                return
            self.stop_blink_valve13(1)
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


            self.recolor_object(self.valve8_geom, direction)
            self.create_preview_camera(self.valve8.name)
            self.taskMgr.add(self.move_valve8_task, "MoveValve5Task")

    def rotate_valve12(self, direction):
        print(f"Вращаем рычаг (вентиль8), направление: {direction}")
        if hasattr(self, 'valve12_pivot'):
            if (direction > 0 and hasattr(self, 'valve12_is_open') and self.valve12_is_open) or \
                    (direction < 0 and hasattr(self, 'valve12_is_open') and not self.valve12_is_open):
                self.on_step_completed()
                return
            self.stop_blink_valve13(1)
            if not hasattr(self, 'valve12_current_angle'):
                self.valve12_current_angle = self.valve12_pivot.get_p()

            self.valve12_direction = direction
            self.valve12_moving = True
            self.valve12_start_time = globalClock.getFrameTime()
            self.valve12_start_angle = self.valve12_current_angle

            if direction > 0:
                self.valve12_target_angle_change = 85
            else:
                self.valve12_target_angle_change = -85

            self.create_preview_camera(self.valve12.name)
            self.recolor_object(self.valve12_geom, direction)
            self.taskMgr.add(self.move_valve12_task, "MoveValve12Task")

    def rotate_valve6(self, direction):
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
        print(f"Вращаем вентиль 13, направление: {direction}")
        if hasattr(self, 'valve13_pivot'):
            self.valve13_direction = direction
            self.valve13_moving = True
            self.valve13_start_time = globalClock.getFrameTime()

            self.play_sound("media/s3/audio1.mp3")
            self.create_preview_camera(self.valve13.name)
            self.recolor_object(self.valve13_geom, direction)
            self.taskMgr.add(self.move_valve13_task, "MoveValve13Task")


    def rotate_valve44(self, direction, position=None):
        print(f"Вращаем вентиль 13, направление: {direction}, положение: {position}")

        if hasattr(self, 'valve44_pivot'):
            self.valve44_direction = direction
            self.valve44_moving = True
            self.valve44_start_time = globalClock.getFrameTime()

            if position == 10:
                self.valve44_sequence = [
                    {"target": 6, "time": 1.5},
                    {"target": 1, "time": 1.5},
                    {"target": 6, "time": 1.5},
                    {"target": 1, "time": 1.5}
                ]
                self.valve44_sequence_index = 0
                self.valve44_target_angle = self.calculate_angle_for_position(6)
            elif position is not None:

                self.valve44_target_angle = self.calculate_angle_for_position(position)
            else:
                self.valve44_target_angle = 360 if direction > 0 else 0

            self.play_sound("media/s3/audio1.mp3")
            self.create_preview_camera(self.valve44.name)
            self.recolor_object(self.valve44_geom, direction)
            self.taskMgr.add(self.move_valve44_task, "MoveValve44Task")

    def calculate_angle_for_position(self, position):
        """Вычисляет угол для заданного положения (1-6)"""
        return - (position - 1) * 60

    def on_step_completed(self):
        """Обрабатывает завершение шага сценария"""
        if not hasattr(self, 'current_scenario') or not hasattr(self, 'scenarios'):
            return

        scenario = self.scenarios[self.current_scenario]

        if scenario.get('type') == 'method':
            self.training_mode = False
            self.auto_mode = False
            # self.step_label['text'] = "Сценарий завершен!"
            return

        # Для пошаговых сценариев
        if 'steps' in scenario:
            self.current_step += 1
            if self.current_step >= len(scenario['steps']):
                self.training_mode = False
                self.auto_mode = False
            # self.step_label['text'] = "Сценарий завершен!"
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
