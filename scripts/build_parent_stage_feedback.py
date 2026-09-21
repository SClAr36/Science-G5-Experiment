from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "家长反馈"
OUTPUT_PATH = OUTPUT_DIR / "五年级实验科学_第1-5次课阶段反馈_家长版.docx"

ASCII_FONT = "Calibri"
CJK_FONT = "Microsoft YaHei"
NAVY = "0B2545"
BLUE = "2E74B5"
DARK_BLUE = "1F4D78"
GOLD = "C58B24"
GRAY = "5B6573"
LIGHT_GRAY = "F2F4F7"
LIGHT_BLUE = "E8EEF5"
PALE_BLUE = "F4F7FA"
BORDER = "D7DBE2"


def xml_text(value):
    return escape(str(value), {'"': "&quot;"})


def rpr(*, bold=False, italic=False, color=None, size=None):
    parts = [
        f'<w:rFonts w:ascii="{ASCII_FONT}" w:hAnsi="{ASCII_FONT}" w:eastAsia="{CJK_FONT}"/>'
    ]
    if bold:
        parts.append("<w:b/><w:bCs/>")
    if italic:
        parts.append("<w:i/><w:iCs/>")
    if color:
        parts.append(f'<w:color w:val="{color}"/>')
    if size:
        parts.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    return "<w:rPr>" + "".join(parts) + "</w:rPr>"


def run(text, *, bold=False, italic=False, color=None, size=None):
    return (
        "<w:r>"
        + rpr(bold=bold, italic=italic, color=color, size=size)
        + f'<w:t xml:space="preserve">{xml_text(text)}</w:t></w:r>'
    )


def para(
    runs,
    *,
    style=None,
    num=False,
    align=None,
    keep_next=False,
    page_break_before=False,
    extra_ppr="",
):
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if num:
        ppr.append(
            '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
        )
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    if keep_next:
        ppr.append("<w:keepNext/>")
    if page_break_before:
        ppr.append("<w:pageBreakBefore/>")
    if extra_ppr:
        ppr.append(extra_ppr)
    return "<w:p><w:pPr>" + "".join(ppr) + "</w:pPr>" + "".join(runs) + "</w:p>"


def heading(text, level):
    return para([run(text)], style=f"Heading{level}", keep_next=True)


def bullet(title, body):
    return para(
        [
            run(title, bold=True, color=NAVY),
            run(body),
        ],
        style="ParentBullet",
        num=True,
    )


def knowledge(text):
    return para(
        [
            run("知识点｜", bold=True, color=NAVY),
            run(text, color=NAVY),
        ],
        style="KnowledgeSummary",
    )


def callout(label, text, *, accent=BLUE, fill=LIGHT_BLUE, style="SchoolAlignment"):
    extra = (
        f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
        f'<w:pBdr><w:left w:val="single" w:sz="16" w:space="7" w:color="{accent}"/></w:pBdr>'
        '<w:ind w:left="230" w:right="144"/>'
    )
    return para(
        [
            run(label, bold=True, color=NAVY),
            run(text, color=NAVY),
        ],
        style=style,
        extra_ppr=extra,
    )


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def lesson(number, title, question, experiments, knowledge_text, school_text):
    parts = [
        heading(f"第 {number} 次课｜{title}", 2),
        para(
            [run(f"核心问题：{question}", italic=True, color=GRAY)],
            style="LessonQuestion",
            keep_next=True,
        ),
    ]
    parts.extend(bullet(exp_title, exp_body) for exp_title, exp_body in experiments)
    parts.append(knowledge(knowledge_text))
    parts.append(callout("School 对应｜", school_text))
    return "".join(parts)


def tc(text, width, *, fill=None, bold=False, align="left"):
    shading = (
        f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
    )
    tc_pr = (
        f'<w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>'
        '<w:vAlign w:val="center"/>'
        f"{shading}</w:tcPr>"
    )
    p = para(
        [run(text, bold=bold, color=NAVY if bold else None, size=18)],
        style="TableText",
        align=align,
    )
    return f"<w:tc>{tc_pr}{p}</w:tc>"


def table_xml():
    widths = [1300, 4200, 1100, 2760]
    rows = [
        ("Unit 1", "Notes 01 · Observation and Inference", "第 1 次课", "核心覆盖；后续实验持续使用"),
        ("Unit 1", "Notes 02 · Quantitative and Qualitative Data", "第 1 次课", "核心覆盖；定性观察与定量测量"),
        ("Unit 1", "Notes 03 · Testable Questions", "第 1 次课", "核心覆盖；变量与公平实验"),
        ("Unit 2", "Notes 01 · Phases of Matter", "第 3 次课", "核心覆盖；三态、相变及变化判断"),
        ("Unit 2", "Notes 02 · Mixtures and Solutions", "第 2 次课", "核心覆盖；第 3 次课回看证据"),
        ("Unit 2", "Notes 03 · Atoms and Period Square", "第 3 次课", "基础衔接；原子、元素与原子重组"),
        ("Unit 3", "Notes 01 · Energy Forms and Transfers", "第 4 次课", "入门覆盖；能量转移与转化"),
        ("Unit 3", "Notes 02 · Thermal Energy Transfer", "第 4 次课", "核心覆盖；传导、对流、辐射"),
        ("Unit 3", "Notes 03 · Electromagnetic Spectrum", "第 5 次课", "聚焦可见光及光与物质作用"),
        ("Unit 3", "Homework 02 · Light Energy Book", "第 5 次课", "用四组实验完成应用与解释"),
    ]
    tbl_pr = (
        '<w:tblPr><w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblInd w:w="120" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
        '<w:tblCellMar>'
        '<w:top w:w="80" w:type="dxa"/><w:start w:w="120" w:type="dxa"/>'
        '<w:bottom w:w="80" w:type="dxa"/><w:end w:w="120" w:type="dxa"/>'
        '</w:tblCellMar>'
        '<w:tblBorders>'
        f'<w:top w:val="single" w:sz="6" w:color="{BORDER}"/>'
        f'<w:left w:val="single" w:sz="6" w:color="{BORDER}"/>'
        f'<w:bottom w:val="single" w:sz="6" w:color="{BORDER}"/>'
        f'<w:right w:val="single" w:sz="6" w:color="{BORDER}"/>'
        f'<w:insideH w:val="single" w:sz="6" w:color="{BORDER}"/>'
        f'<w:insideV w:val="single" w:sz="6" w:color="{BORDER}"/>'
        "</w:tblBorders></w:tblPr>"
    )
    grid = "<w:tblGrid>" + "".join(
        f'<w:gridCol w:w="{width}"/>' for width in widths
    ) + "</w:tblGrid>"
    headers = ["School Unit", "School 材料（哪一节）", "本课程", "覆盖说明"]
    header = (
        '<w:tr><w:trPr><w:tblHeader w:val="true"/><w:cantSplit/></w:trPr>'
        + "".join(
            tc(text, width, fill=LIGHT_GRAY, bold=True, align="center")
            for text, width in zip(headers, widths)
        )
        + "</w:tr>"
    )
    body = []
    for unit, material, course_lesson, scope in rows:
        unit_fill = "EEF4FA" if unit == "Unit 1" else "F6F2E8" if unit == "Unit 2" else "EEF5F0"
        body.append(
            '<w:tr><w:trPr><w:cantSplit/></w:trPr>'
            + tc(unit, widths[0], fill=unit_fill, bold=True, align="center")
            + tc(material, widths[1])
            + tc(course_lesson, widths[2], align="center")
            + tc(scope, widths[3])
            + "</w:tr>"
        )
    return "<w:tbl>" + tbl_pr + grid + header + "".join(body) + "</w:tbl>"


def build_body():
    parts = [
        para([run("PARENT LEARNING UPDATE", bold=True, color=GOLD)], style="ParentKicker", keep_next=True),
        para([run("五年级实验科学阶段反馈")], style="ParentTitle", keep_next=True),
        para([run("第 1–5 次课｜从“会做实验”走向“会用证据解释”")], style="ParentSubtitle", keep_next=True),
        para(
            [
                run(
                    "本阶段覆盖：School Unit 1 · Nature of Science ｜ Unit 2 · Properties of Matter ｜ Unit 3 · Energy and Its Forms",
                    color=GRAY,
                )
            ],
            style="ParentMeta",
            keep_next=True,
        ),
        callout(
            "阶段主线｜",
            "前五次课先用单摆建立科学探究方法，再把同一套方法用于物质、热和光。课堂不以“做完步骤”为终点，而是要求学生先预测、控制条件、记录定性与定量证据，并根据结果修正原有想法。",
            accent=GOLD,
            fill=PALE_BLUE,
            style="ParentLead",
        ),
        callout(
            "课程调整说明｜",
            "第 1 次课原先主要作为实验方法的起点。课程结束后，家长提出希望系统过一遍五年级 School Science 内容；我们据此重新梳理学校材料，并把后续课程改为按 Unit 1–5 主线进行实验化复习。本阶段因此在第 2–3 次课进入 Unit 2，在第 4–5 次课进入 Unit 3，同时继续保留第 1 次课建立的科学探究方法。",
            accent=BLUE,
            fill=LIGHT_BLUE,
            style="SchoolAlignment",
        ),
        heading("五次课做了哪些实验", 1),
    ]

    parts.append(
        lesson(
            "1",
            "摆钟会听谁的话？",
            "摆长、摆锤质量和释放角度，哪些会影响单摆周期？",
            [
                ("改变摆长：", "保持摆锤和释放角度相同，比较短、中、长三种摆长；每种条件测量 10 次完整摆动并重复 3 次。数据帮助学生确认摆越长，周期越长，同时理解“明显趋势”要大于测量波动。"),
                ("改变摆锤质量：", "在摆长和释放角度不变时更换轻、中、重摆锤。结果通常显示周期差异很小，学生据此学习用数据检验直觉，而不是凭“更重就更快”下结论。"),
                ("改变释放角度：", "比较 10°、25°和40°的释放位置，并与重复测量的波动对照。学生练习在证据不够清晰时保留判断，区分最低点速度与完成一次往返所需的时间。"),
            ],
            "可检验问题（testable question）、观察与推论、定性与定量数据、自变量/因变量/控制变量、公平实验、重复测量、平均值与实验误差。",
            "Unit 1 — Notes 01 Observation and Inference、Notes 02 Quantitative and Qualitative Data、Notes 03 Testable Questions。三节科学方法内容在本课集中落实，并在后续四次课持续使用。",
        )
    )
    parts.append(
        lesson(
            "2",
            "盐真的消失了吗？",
            "盐溶进水以后去了哪里，过滤后还能不能把它找回来？",
            [
                ("溶解前后总质量：", "称量水和食盐的总质量，再比较食盐完全溶解后的读数。前后质量在仪器波动范围内接近，说明“看不见”不等于“消失”，也让学生关注转移残留、溅出和秤的误差。"),
                ("盐水与石英砂的过滤对比：", "石英砂会沉降并被滤纸截留，而盐水通过滤纸后仍然清澈。实验说明普通滤纸能截留较大的不溶颗粒，却不能分离已经分散在水中的盐。"),
                ("蒸发与结晶：", "加热盐水滤液，使水逐渐减少并重新出现白色晶体。晶体证明食盐一直存在于滤液中，也把“溶解—分离—找回物质”连成完整证据链。"),
                ("不同物质溶解时的温度变化：", "在相同水量、固体质量和读数时间下比较食盐、尿素和氯化钙。尿素常使温度降低、氯化钙使温度升高，帮助学生认识吸热与放热溶解，并区分“没有测出明显变化”和“绝对没有能量转移”。"),
            ],
            "溶质（solute）、溶剂（solvent）、溶液（solution）、不溶物、均一混合物、过滤、滤液、蒸发、结晶，以及溶解过程中的能量转移。",
            "Unit 2 — Notes 02 Mixtures and Solutions。核心覆盖溶液/混合物、solute/solvent、过滤与粒子尺度；实验也为第 3 次课判断物理变化提供了证据。",
        )
    )
    parts.append(
        lesson(
            "3",
            "改变状态，还是变成新物质？",
            "出现气泡、变色或温度变化，就一定说明发生了化学变化吗？",
            [
                ("蜡烛的两种变化：", "观察蜡受热熔化、熄灭后凝固，同时把火焰中的燃烧单独记录。学生由同一支蜡烛看见：相变不产生新物质，而燃烧会形成新物质。"),
                ("水的汽化与凝结：", "在水面上方放置底面干燥、上方盛冰的冷盖，观察盖底出现液滴。实验把“直接观察到液滴”和“推论水蒸气遇冷凝结”分开，并连接固、液、气三态粒子模型。"),
                ("碳酸钙与白醋的对照实验：", "比较“碳酸钙＋水”“白醋单独放置”和“碳酸钙＋白醋”三组，记录持续气泡、固体减少及开放系统中的质量变化。多条证据共同支持生成了新物质，并解释逸出的气体为什么会使秤上读数下降。"),
                ("澄清溶液形成沉淀：", "把上一实验得到的醋酸钙滤液与小苏打溶液混合，并设置加水对照；实验组出现白色固体。这个现象说明两种看似澄清的溶液也能通过反应形成具有不同性质的新物质。"),
            ],
            "物理变化与化学变化的判断标准、六种相变、三态粒子模型、原子（atom）、元素（element）、分子（molecule）、化合物（compound），以及“化学变化是原子重新组合”。",
            "Unit 2 — Notes 01 Phases of Matter 为核心覆盖；Notes 03 Atoms and Period Square 只完成原子、元素、分子/化合物和原子重组的基础衔接；同时回看 Notes 02 的溶解与结晶证据。",
        )
    )
    parts.append(
        lesson(
            "4",
            "热能怎样传递？",
            "传导、对流和辐射分别怎样把热能从一处带到另一处？",
            [
                ("温水与冷水混合：", "记录两杯初温和混合后的温度变化，观察最终温度落在两者之间并逐渐稳定。学生由数据建立共同规律：热能净传递方向由温度差决定，从较高温处到较低温处。"),
                ("三种筷子的传导比较：", "把不锈钢、竹木和塑料筷的下端同时放入温水，用黄油固定的小纸旗显示热量何时传到上方。金属筷通常最先使黄油软化，说明能量可以沿接触的固体逐步传递。"),
                ("有色暖水与冷水的对流：", "把红色暖水和蓝色冷水分别缓慢加入静止水中，观察暖水上升、冷水下沉。实验把“热往上走”的口号改成更准确的解释：流体整体运动并携带能量。"),
                ("黑白表面的辐射吸收：", "让距离和角度相同的黑、白两杯接受同一热辐射源，比较两杯水的温升。两杯都能在不接触灯的情况下升温，黑色表面通常温升更大，支持辐射无需接触且不同表面吸收表现不同。"),
            ],
            "能量转移与转化、温度与热能的区别、热传递方向、传导（conduction）、对流（convection）、辐射（radiation）及公平比较。",
            "Unit 3 — Notes 01 Energy Forms and Transfers 的基础概念，以及 Notes 02 Thermal Energy Transfer 的核心内容。第 4 次课重点完成三种热传递方式及其证据。",
        )
    )
    parts.append(
        lesson(
            "5",
            "光遇到物质会发生什么？",
            "白光里有什么，光遇到不同物质后颜色和传播方向怎样改变？",
            [
                ("三棱镜展开白光：", "让窄白光通过三棱镜，在白纸上形成从红到紫的可见光谱。学生用“不同波长在玻璃中偏折程度不同”解释色散，并把可见光放回电磁波谱中。"),
                ("彩色照明改变物体颜色：", "在白光、红光、绿光和蓝光下比较红、绿、蓝、白、黑纸片的颜色与亮度。实验说明物体的所见颜色取决于光源提供了哪些波长，以及材料选择性反射、透射或吸收了哪些光。"),
                ("用数据检验反射定律：", "让激光沿 20°、40°和60°三条入射线照到平面镜，分别测量反射角。三组数据都应接近“入射角等于反射角”，并强调两个角都从法线测量。"),
                ("折射与水流全反射：", "先观察激光从空气斜射入水后向法线偏折，再让光沿弯曲水流传播。两段现象分别对应折射和全反射，也让学生理解光纤导光的基本原理。"),
            ],
            "电磁波谱与可见光、波长与频率、色散、反射/透射/吸收、选择性反射、反射定律、折射、临界角与全反射。",
            "Unit 3 — Notes 03 Electromagnetic Spectrum 的可见光重点，以及 Homework 02 Light Energy Book。第 5 次课聚焦光与物质作用，不把电磁波谱讲义中所有延伸术语都算作已完成。",
        )
    )

    parts.extend(
        [
            page_break(),
            heading("与 School 课程的对应总表", 1),
            para(
                [
                    run(
                        "前五次课共覆盖 School 的 Unit 1、Unit 2 和 Unit 3。下表按学校材料原编号列出“哪一个 Unit、哪一节 Notes/Homework、在本课程第几次课落实”。"
                    )
                ]
            ),
            table_xml(),
            heading("覆盖范围说明", 2),
            bullet("Unit 1：", "Notes 01–03 的科学方法核心已经覆盖，并继续贯穿第 2–5 次课。"),
            bullet("Unit 2：", "Notes 01、02 的实验核心已经覆盖；Notes 03 目前只完成原子与元素等基础，Period Square、Bohr model、ions/isotopes 等尚未计入本阶段。"),
            bullet("Unit 3：", "Notes 01 完成能量转移/转化的入口，Notes 02 完成三种热传递核心，Notes 03 完成可见光及光与物质作用的重点；运动、加速度与牛顿定律属于后续课程。"),
            bullet("Unit 4–5：", "生命科学与空间科学不在第 1–5 次课范围内，将在后续阶段展开。"),
            heading("本阶段形成的学习习惯", 2),
            bullet("先问清楚变量：", "能说出这次实验改变什么、测量什么、哪些条件必须保持不变。"),
            bullet("把观察和解释分开：", "先记录看见的现象和数据，再说明这些证据支持什么结论。"),
            bullet("允许数据修正猜想：", "当结果与直觉不一致时，不改记录，而是检查误差、补做测量或修改原来的判断。"),
            bullet("建立中英文概念连接：", "在真实实验情境中使用 school notes 里的关键词，而不是脱离现象单独背词。"),
            callout(
                "给家长的一句话｜",
                "在家中回顾时，可以少问“记住了哪个答案”，多问“你观察到了什么、怎样保证比较公平、哪条证据支持你的解释”。这正是前五次课反复练习的科学思维。",
                accent=BLUE,
                fill=PALE_BLUE,
                style="ParentLead",
            ),
        ]
    )
    return "".join(parts)


def styles_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault><w:rPr><w:rFonts w:ascii="{ASCII_FONT}" w:hAnsi="{ASCII_FONT}" w:eastAsia="{CJK_FONT}"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:rPrDefault>
    <w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/><w:widowControl/></w:pPr></w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="0" w:after="120" w:line="264" w:lineRule="auto"/><w:widowControl/></w:pPr><w:rPr><w:rFonts w:ascii="{ASCII_FONT}" w:hAnsi="{ASCII_FONT}" w:eastAsia="{CJK_FONT}"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="320" w:after="160"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:rFonts w:ascii="{ASCII_FONT}" w:hAnsi="{ASCII_FONT}" w:eastAsia="{CJK_FONT}"/><w:b/><w:bCs/><w:color w:val="{BLUE}"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:rFonts w:ascii="{ASCII_FONT}" w:hAnsi="{ASCII_FONT}" w:eastAsia="{CJK_FONT}"/><w:b/><w:bCs/><w:color w:val="{BLUE}"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="80"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:bCs/><w:color w:val="{DARK_BLUE}"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="ParentTitle"><w:name w:val="Parent Title"/><w:basedOn w:val="Normal"/><w:next w:val="ParentSubtitle"/><w:pPr><w:keepNext/><w:spacing w:before="0" w:after="140"/></w:pPr><w:rPr><w:b/><w:bCs/><w:color w:val="{NAVY}"/><w:sz w:val="56"/><w:szCs w:val="56"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="ParentSubtitle"><w:name w:val="Parent Subtitle"/><w:basedOn w:val="Normal"/><w:next w:val="ParentMeta"/><w:pPr><w:keepNext/><w:spacing w:before="0" w:after="360"/></w:pPr><w:rPr><w:color w:val="{GRAY}"/><w:sz w:val="27"/><w:szCs w:val="27"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="ParentKicker"><w:name w:val="Parent Kicker"/><w:basedOn w:val="Normal"/><w:next w:val="ParentTitle"/><w:pPr><w:keepNext/><w:spacing w:before="0" w:after="40"/></w:pPr><w:rPr><w:b/><w:bCs/><w:color w:val="{GOLD}"/><w:sz w:val="19"/><w:szCs w:val="19"/><w:spacing w:val="12"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="ParentMeta"><w:name w:val="Parent Meta"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="0" w:after="240"/></w:pPr><w:rPr><w:color w:val="{GRAY}"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="ParentLead"><w:name w:val="Parent Lead"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="40" w:after="240" w:line="283" w:lineRule="auto"/></w:pPr><w:rPr><w:color w:val="{NAVY}"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="LessonQuestion"><w:name w:val="Lesson Question"/><w:basedOn w:val="Normal"/><w:next w:val="ParentBullet"/><w:pPr><w:keepNext/><w:spacing w:before="0" w:after="120"/></w:pPr><w:rPr><w:i/><w:iCs/><w:color w:val="{GRAY}"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="ParentBullet"><w:name w:val="Parent Bullet"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="0" w:after="160" w:line="280" w:lineRule="auto"/><w:widowControl/></w:pPr><w:rPr><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="KnowledgeSummary"><w:name w:val="Knowledge Summary"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="40" w:after="140" w:line="271" w:lineRule="auto"/></w:pPr><w:rPr><w:color w:val="{NAVY}"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="SchoolAlignment"><w:name w:val="School Alignment"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="60" w:after="200" w:line="269" w:lineRule="auto"/></w:pPr><w:rPr><w:color w:val="{DARK_BLUE}"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="0" w:after="40" w:line="252" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>
</w:styles>'''


def numbering_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="0">
    <w:multiLevelType w:val="singleLevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>
      <w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs><w:ind w:left="720" w:hanging="360"/><w:spacing w:after="160" w:line="280" w:lineRule="auto"/></w:pPr>
      <w:rPr><w:rFonts w:ascii="{ASCII_FONT}" w:hAnsi="{ASCII_FONT}" w:eastAsia="{CJK_FONT}"/></w:rPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>'''


def header_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:tabs><w:tab w:val="right" w:pos="9360"/></w:tabs><w:spacing w:after="80"/><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="4" w:color="{BORDER}"/></w:pBdr></w:pPr>
    <w:r>{rpr(bold=True, color=GRAY, size=17)}<w:t>SCIENCE G5 · 阶段反馈</w:t></w:r>
    <w:r><w:tab/></w:r>
    <w:r>{rpr(color=GRAY, size=17)}<w:t>第 1–5 次课</w:t></w:r>
  </w:p>
</w:hdr>'''


def footer_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p><w:pPr><w:jc w:val="right"/></w:pPr>
    <w:r>{rpr(color=GRAY, size=17)}<w:t xml:space="preserve">家长版  ·  </w:t></w:r>
    <w:r>{rpr(color=GRAY, size=17)}<w:fldChar w:fldCharType="begin"/></w:r>
    <w:r>{rpr(color=GRAY, size=17)}<w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
    <w:r>{rpr(color=GRAY, size=17)}<w:fldChar w:fldCharType="end"/></w:r>
  </w:p>
</w:ftr>'''


def document_xml():
    body = build_body()
    sect = '''<w:sectPr>
      <w:headerReference w:type="default" r:id="rId5"/>
      <w:footerReference w:type="default" r:id="rId6"/>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>
      <w:cols w:space="720"/><w:docGrid w:linePitch="312"/>
    </w:sectPr>'''
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>{body}{sect}</w:body>
</w:document>'''


def content_types_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''


def root_rels_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''


def document_rels_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>'''


def settings_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:zoom w:percent="100"/><w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/>
  <w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>
</w:settings>'''


def font_table_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:font w:name="{ASCII_FONT}"><w:family w:val="swiss"/><w:pitch w:val="variable"/></w:font>
  <w:font w:name="{CJK_FONT}"><w:family w:val="swiss"/><w:pitch w:val="variable"/></w:font>
</w:fonts>'''


def core_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>五年级实验科学第1-5次课阶段反馈（家长版）</dc:title>
  <dc:subject>Science G5 · School Units 1–3 阶段课程反馈</dc:subject>
  <dc:creator>Science G5</dc:creator><cp:lastModifiedBy>Science G5</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">2026-08-02T00:00:00Z</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">2026-08-02T00:00:00Z</dcterms:modified>
</cp:coreProperties>'''


def app_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office Word</Application><AppVersion>16.0000</AppVersion>
  <Company>Science G5</Company><DocSecurity>0</DocSecurity><ScaleCrop>false</ScaleCrop>
</Properties>'''


def write_docx():
    parts = {
        "[Content_Types].xml": content_types_xml(),
        "_rels/.rels": root_rels_xml(),
        "docProps/core.xml": core_xml(),
        "docProps/app.xml": app_xml(),
        "word/document.xml": document_xml(),
        "word/styles.xml": styles_xml(),
        "word/numbering.xml": numbering_xml(),
        "word/settings.xml": settings_xml(),
        "word/fontTable.xml": font_table_xml(),
        "word/header1.xml": header_xml(),
        "word/footer1.xml": footer_xml(),
        "word/_rels/document.xml.rels": document_rels_xml(),
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT_PATH, "w", ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content.encode("utf-8"))
    print(OUTPUT_PATH)


if __name__ == "__main__":
    write_docx()
